from django.urls import path
from . import views

urlpatterns = [
    path("", views.TransactionCreateView.as_view(), name="create_transaction"),
    # path('transactions/<int:group_id>/', views.TransactionListView.as_view(), name='list_transactions'),
    # path('transactions/<int:group_id>/summary/', views.TransactionSummaryView.as_view(), name='transaction_summary'),
    # path('transaction/delete/<int:transaction_id>/', views.TransactionDeleteView.as_view(), name='transaction_detail'),
    # path('transaction/update/<int:pk>/', views.TransactionUpdateView.as_view(), name='transaction_update'),
]
