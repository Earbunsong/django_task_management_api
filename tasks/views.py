from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models
from .models import Task, TaskAssignment, MediaFile
from .serializers import TaskSerializer, MediaFileSerializer

User = get_user_model()

# Task creation limits
BASIC_USER_TASK_LIMIT = 5


class IsOwnerOrAssignee(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Task):
        if obj.owner_id == request.user.id:
            return True
        return TaskAssignment.objects.filter(task=obj, user=request.user).exists()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignee]

    def get_queryset(self):
        user = self.request.user
        # Owner or assigned tasks
        assigned_ids = TaskAssignment.objects.filter(user=user).values_list('task_id', flat=True)
        return Task.objects.filter(models.Q(owner=user) | models.Q(id__in=assigned_ids)).distinct()

    def perform_create(self, serializer):
        user = self.request.user

        # Check task creation limit for basic users
        if not user.is_pro() and not user.is_staff:
            current_task_count = Task.objects.filter(owner=user).count()
            if current_task_count >= BASIC_USER_TASK_LIMIT:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    f"Basic users are limited to {BASIC_USER_TASK_LIMIT} tasks. "
                    "Upgrade to Pro for unlimited tasks."
                )

        serializer.save(owner=user)

    @action(detail=False, methods=['get'], url_path='count')
    def task_count(self, request):
        """Get current user's task count and limit"""
        user = request.user
        current_count = Task.objects.filter(owner=user).count()

        if user.is_pro() or user.is_staff:
            limit = None  # Unlimited
            remaining = None
        else:
            limit = BASIC_USER_TASK_LIMIT
            remaining = max(0, limit - current_count)

        return Response({
            'current_count': current_count,
            'limit': limit,
            'remaining': remaining,
            'is_pro': user.is_pro(),
        })

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        task = self.get_object()
        if not request.user.is_pro():
            return Response({"detail": "Only Pro users can assign tasks."}, status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            assignee = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        assignment, created = TaskAssignment.objects.get_or_create(task=task, user=assignee)

        # Send push notification to assignee
        if created:
            try:
                from notifications.fcm_utils import send_task_assignment_notification
                send_task_assignment_notification(task, assignee)
            except Exception as e:
                # Don't fail the request if notification fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send task assignment notification: {str(e)}")

            # Create in-app notification
            from notifications.models import Notification
            Notification.objects.create(
                user=assignee,
                message=f"You've been assigned to task: {task.title}"
            )

        return Response({"message": "Task assigned"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'get', 'delete'], url_path='media')
    def media(self, request, pk=None):
        task = self.get_object()

        # GET: List all media files for this task
        if request.method.lower() == 'get':
            files = task.media_files.all()
            return Response(MediaFileSerializer(files, many=True).data)

        # DELETE: Remove a specific media file
        if request.method.lower() == 'delete':
            media_id = request.data.get('media_id')
            if not media_id:
                return Response({"detail": "media_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                media = MediaFile.objects.get(id=media_id, task=task)
                # Try to delete from Cloudinary
                from .cloudinary_utils import delete_file
                if media.file_url and 'cloudinary.com' in media.file_url:
                    # Extract public_id from URL (if it's a Cloudinary URL)
                    # Format: https://res.cloudinary.com/cloud_name/resource_type/upload/public_id.ext
                    try:
                        parts = media.file_url.split('/upload/')
                        if len(parts) == 2:
                            public_id = parts[1].rsplit('.', 1)[0]  # Remove extension
                            delete_file(public_id, resource_type=media.file_type or 'image')
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Could not delete from Cloudinary: {e}")

                media.delete()
                return Response({"message": "Media file deleted successfully"}, status=status.HTTP_200_OK)
            except MediaFile.DoesNotExist:
                return Response({"detail": "Media file not found"}, status=status.HTTP_404_NOT_FOUND)

        # POST: Upload new media file
        # Check if file is provided (multipart/form-data)
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            # Upload to Cloudinary
            from .cloudinary_utils import upload_file, get_file_type_from_url

            result = upload_file(uploaded_file, folder="task_media")
            if not result:
                return Response(
                    {"detail": "Failed to upload file to Cloudinary. Please check Cloudinary configuration."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create MediaFile record
            file_type = get_file_type_from_url(result['url'])
            media = MediaFile.objects.create(
                task=task,
                file_url=result['url'],
                file_type=file_type
            )
            return Response(MediaFileSerializer(media).data, status=status.HTTP_201_CREATED)

        # Fallback: Accept pre-uploaded Cloudinary URL (for Flutter direct upload)
        file_url = request.data.get('file_url')
        file_type = request.data.get('file_type', '')

        if not file_url:
            return Response(
                {"detail": "Either 'file' (multipart) or 'file_url' (JSON) is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        media = MediaFile.objects.create(task=task, file_url=file_url, file_type=file_type)
        return Response(MediaFileSerializer(media).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='unassign')
    def unassign(self, request, pk=None):
        """Unassign a user from a task (Pro only)"""
        task = self.get_object()
        if not request.user.is_pro():
            return Response({"detail": "Only Pro users can unassign tasks."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment = TaskAssignment.objects.get(task=task, user_id=user_id)
            assignment.delete()

            # Create in-app notification
            from notifications.models import Notification
            assignee = User.objects.get(pk=user_id)
            Notification.objects.create(
                user=assignee,
                message=f"You've been unassigned from task: {task.title}"
            )

            return Response({"message": "Task unassigned"}, status=status.HTTP_200_OK)
        except TaskAssignment.DoesNotExist:
            return Response({"detail": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='users')
    def get_users(self, request):
        """Get list of users for task assignment (Pro only)"""
        if not request.user.is_pro():
            return Response({"detail": "Only Pro users can access user list."}, status=status.HTTP_403_FORBIDDEN)

        # Return list of active verified users (excluding current user)
        users = User.objects.filter(
            is_active=True,
            is_verified=True
        ).exclude(id=request.user.id).values('id', 'username', 'email', 'role')

        return Response(list(users), status=status.HTTP_200_OK)
