from django.contrib import admin

from .models import ExpenseGroup, GroupMembership

class GroupMembershipInline(admin.TabularInline):  # Use TabularInline for a table-like display
    model = GroupMembership
    extra = 1 

class ExpenseGroupAdmin(admin.ModelAdmin):
    inlines = [GroupMembershipInline]  # Add the inline for managing members
    list_display = ('name', 'created_at', 'uuid')  # Display these fields in the admin list view
    search_fields = ('name',)

# @admin.register(GroupMembership)
# class GroupMembershipAdmin(admin.ModelAdmin):
#     list_display = ('user', 'group', 'joined_at')
#     list_filter = ('group',)
#     search_fields = ('user__username', 'group__name')
admin.site.register(ExpenseGroup, ExpenseGroupAdmin)