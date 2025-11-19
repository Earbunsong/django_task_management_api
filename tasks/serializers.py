from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, TaskAssignment, MediaFile

User = get_user_model()


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ('id', 'file_url', 'file_type', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class AssignedUserSerializer(serializers.ModelSerializer):
    """Serializer for users assigned to a task"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role')
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    media_files = MediaFileSerializer(many=True, read_only=True)
    assigned_users = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'due_date', 'priority', 'status', 'owner', 'media_files',
            'assigned_users', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at', 'assigned_users')

    def get_assigned_users(self, obj):
        """Get list of users assigned to this task"""
        assignments = TaskAssignment.objects.filter(task=obj).select_related('user')
        return AssignedUserSerializer([a.user for a in assignments], many=True).data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['owner'] = request.user
        return super().create(validated_data)
