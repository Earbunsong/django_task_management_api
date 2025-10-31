from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, TaskAssignment, MediaFile

User = get_user_model()


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ('id', 'file_url', 'file_type', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


class TaskSerializer(serializers.ModelSerializer):
    media_files = MediaFileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'due_date', 'priority', 'status', 'owner', 'media_files', 'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context['request']
        validated_data['owner'] = request.user
        return super().create(validated_data)
