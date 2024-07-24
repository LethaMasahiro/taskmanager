from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):

    assignee_username = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'assignee',
            'assignee_username',
            'status',
            'startDate',
            'deadline',
            'priority'
        ]

    def get_assignee_username(self, obj):
        return obj.assignee.username if obj.assignee else 'N/A'  # Get the username directly
