from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models
from .models import Task, TaskAssignment, MediaFile
from .serializers import TaskSerializer, MediaFileSerializer

User = get_user_model()


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
        serializer.save(owner=self.request.user)

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

    @action(detail=True, methods=['post', 'get'], url_path='media')
    def media(self, request, pk=None):
        task = self.get_object()
        if request.method.lower() == 'get':
            files = task.media_files.all()
            return Response(MediaFileSerializer(files, many=True).data)
        file_url = request.data.get('file_url')
        file_type = request.data.get('file_type', '')
        if not file_url:
            return Response({"detail": "file_url is required (Cloudinary URL)"}, status=status.HTTP_400_BAD_REQUEST)
        media = MediaFile.objects.create(task=task, file_url=file_url, file_type=file_type)
        return Response(MediaFileSerializer(media).data, status=status.HTTP_201_CREATED)
