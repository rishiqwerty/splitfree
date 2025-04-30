from django.db.models.signals import pre_save
from django.dispatch import receiver

from expenses.utils import get_expense_icon
from .models import Expense


@receiver(pre_save, sender=Expense)
def set_default_category(sender, instance, **kwargs):
    print("Setting default category")
    if instance.id:
        prev_expense = Expense.objects.get(id=instance.id)
        if instance.title != prev_expense.title or instance.notes != prev_expense.notes:
            instance.expense_icon = get_expense_icon(instance.title, instance.notes)
            print("Expense icon set to:", instance.expense_icon)
