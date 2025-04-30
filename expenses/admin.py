from django.contrib import admin
from .models import Expense, Split

# Register your models here.
admin.site.register(Expense)
admin.site.register(Split)
