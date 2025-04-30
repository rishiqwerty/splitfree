from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from groups.models import ExpenseGroup


class Expense(models.Model):
    group = models.ForeignKey(
        ExpenseGroup, related_name="expenses", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(
        User, related_name="paid_expenses", on_delete=models.CASCADE
    )
    split_between = models.ManyToManyField(User, related_name="split_expenses")
    created_at = models.DateTimeField(default=timezone.now)
    expense_date = models.DateTimeField(default=timezone.now)  # Date of the expense
    notes = models.TextField(blank=True, null=True)
    expense_icon = models.CharField(
        max_length=255, blank=True, null=True, default="💸"
    )  # Optional icon for the expense

    def __str__(self):
        return f"{self.title} - {self.amount} paid by {self.paid_by.username}"

    def split_amount(self):
        # Split amount evenly among users
        num_users = self.split_between.count()
        if num_users > 0:
            return self.amount / num_users
        return 0


class Split(models.Model):
    expense = models.ForeignKey(
        "Expense", on_delete=models.CASCADE, related_name="splits"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} owes {self.amount} for {self.expense.title}"


# Paid by multiple users
