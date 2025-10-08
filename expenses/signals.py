from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.cache import cache


from expenses.summray_calculate import ExpenseSummary
from expenses.utils import get_expense_icon
from utils.gemini_api_call import generate_content
from .models import Expense


@receiver(pre_save, sender=Expense)
def set_default_category(sender, instance, **kwargs):
    if instance.id:
        prev_expense = Expense.objects.get(id=instance.id)
        if instance.title != prev_expense.title or instance.notes != prev_expense.notes:
            instance.expense_icon = get_expense_icon(instance.title, instance.notes)


@receiver(post_save, sender=Expense)
def update_group_overview_cache(sender, instance, created, **kwargs):
    if created and instance.group:
        expense = ExpenseSummary(instance.group).get_summary()
        ai_overview = generate_content(
            f"""Generate a one liner random summary for current
                                        month  using following json response also add one
                                       random money savings tip:  json:{expense.data} make sure curreny is rupees"""
        ).replace("\n", "")
        cache.set(f"ai_overview_{instance.group.id}", ai_overview)
