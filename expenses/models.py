from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from groups.models import ExpenseGroup

class Expense(models.Model):
    group = models.ForeignKey(ExpenseGroup, related_name='expenses', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, related_name='paid_expenses', on_delete=models.CASCADE)
    split_between = models.ManyToManyField(User, related_name='split_expenses')
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.amount} paid by {self.paid_by.username}"

    def split_amount(self):
        # Split amount evenly among users
        num_users = self.split_between.count()
        if num_users > 0:
            return self.amount / num_users
        return 0
