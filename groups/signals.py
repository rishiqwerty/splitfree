from django.db.models.signals import pre_save
from django.dispatch import receiver

from expenses.utils import get_expense_icon
from .models import ExpenseGroup

@receiver(pre_save, sender=ExpenseGroup)
def set_default_category(sender, instance, **kwargs):
    if instance.id:
        prev_expense = ExpenseGroup.objects.get(id=instance.id)
        if instance.name != prev_expense.name or instance.description != prev_expense.description:
            instance.expense_icon = get_expense_icon(instance.name, instance.description)
            print("Expense icon set to:", instance.expense_icon)

