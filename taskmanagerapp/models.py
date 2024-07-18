# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

class TestModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    import datetime

    class Status(models.TextChoices):
        TODO = 'To Do', 'To Do'
        IN_PROGRESS = 'In Progress', 'In Progress'
        IN_REVIEW = 'In Review', 'In Review'
        DONE = 'Done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'
        VERY_HIGH = 'Very High', 'Very High'

    title = models.CharField(max_length=250)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status, default=Status.TODO) #status enum
    assignee = models.ForeignKey(User, on_delete=models.CASCADE) #Foreign key to default user table
    startDate = models.DateTimeField(default=datetime.date.today)
    deadline = models.DateTimeField(default=datetime.date.today)
    priority = models.CharField(max_length=20, choices=Priority, default=Priority.HIGH) #priority enum

