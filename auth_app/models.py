from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model

User = get_user_model()

class Activity(models.Model):
    """
    Model to represent an activity in the system.
    """
    name = models.CharField(max_length=255)  # Activity name (e.g., "Group Updated", "Expense Added")
    description = models.TextField(blank=True, null=True)  # Optional description of the activity
    timestamp = models.DateTimeField(auto_now_add=True)  # When the activity occurred
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # User who performed the activity

    # Generic relation to associate the activity with any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.name} by {self.user} on {self.timestamp}"