from django.urls import path
from . import views

urlpatterns = [
    # path('expenses/', views.ExpenseCreateView.as_view(), name='create_expense'),
    path('<int:group_id>/', views.GroupMembersView.as_view(), name='list_group_members'),
]