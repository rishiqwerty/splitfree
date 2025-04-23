from django.urls import path
from . import views

urlpatterns = [
    # path('expenses/', views.ExpenseCreateView.as_view(), name='create_expense'),
    path('<int:group_id>/', views.GroupMembersView.as_view(), name='list_group_members'),
    path('<uuid:uuid>/', views.GroupAll.as_view(), name='list_group_members_by_uuid'),
    path('',views.GroupMembersView.as_view(), name='list_groups'),
    path('create/', views.CreateGroupView.as_view(), name='create_group'),
    path('<uuid:uuid>/add-user/', views.AddUserToGroupView.as_view(), name='add-user-to-group')
]