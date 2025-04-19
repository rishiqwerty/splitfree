from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Group Model: Represents a group of users
class ExpenseGroup(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='expense_groups')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def total_balance(self):
        # Calculate the total balance (e.g., sum of expenses divided by number of members)
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0
