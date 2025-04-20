from rest_framework import generics
from django.core.exceptions import PermissionDenied

from groups.models import ExpenseGroup
from .serializers import GroupSerializer
# Create your views here.
class GroupMembersView(generics.ListAPIView):
    """
    View to list all members of a group.
    """
    serializer_class = GroupSerializer  # Replace with your serializer class

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = ExpenseGroup.objects.get(id=group_id)
        if self.request.user not in group.members.all():
            raise PermissionDenied("You are not a member of this group.")
        print('here')
        return ExpenseGroup.objects.filter(id=group_id)