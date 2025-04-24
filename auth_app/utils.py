from django.contrib.contenttypes.models import ContentType
from .models import Activity

def log_activity(user, name, description, related_object):
    """
    Logs an activity in the system.

    Args:
        user (User): The user who performed the activity.
        name (str): The name of the activity (e.g., "Group Updated").
        description (str): A description of the activity.
        related_object (Model): The object related to the activity (e.g., a group or expense).
    """
    content_type = ContentType.objects.get_for_model(related_object.__class__)
    Activity.objects.create(
        user=user,
        name=name,
        description=description,
        content_type=content_type,
        object_id=related_object.id,
    )