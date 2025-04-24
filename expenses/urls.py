from django.urls import path
from . import views

urlpatterns = [
    path('expenses/', views.ExpenseCreateView.as_view(), name='create_expense'),
    path('expenses/<int:group_id>/', views.ExpenseListView.as_view(), name='list_expenses'),
    path('expenses/<int:group_id>/summary/', views.ExpenseSummaryView.as_view(), name='expense_summary'),
]