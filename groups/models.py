from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
# Group Model: Represents a group of users
class ExpenseGroup(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, through='GroupMembership', related_name='expense_groups')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups', null=True, blank=True)
    def __str__(self):
        return self.name

    def total_balance(self):
        # Calculate the total balance (e.g., sum of expenses divided by number of members)
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0

class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey('ExpenseGroup', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(default=timezone.now)  # Timestamp for when the user joined

    class Meta:
        unique_together = ('user', 'group')  # Ensure a user can only join a group once

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"