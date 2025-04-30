from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from groups.models import ExpenseGroup

# Create your models here.
class Transaction(models.Model):
    from_user = models.ForeignKey(
        User, related_name="sent_transactions", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="received_transactions", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    group = models.ForeignKey(
        ExpenseGroup, related_name="transactions", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)
    transaction_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction from {self.from_user.username} to {self.to_user.username} for {self.amount}"
