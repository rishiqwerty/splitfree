from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied

from .models import Expense
from groups.models import ExpenseGroup
from .serializers import ExpenseSerializer

class ExpenseCreateView(generics.CreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    def perform_create(self, serializer):
        group_id = self.request.data.get('group')

        group = ExpenseGroup.objects.get(id=group_id)
        
        # Check if the user is part of the group
        if self.request.user not in group.members.all():
            return Response(
                {"detail": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Save the expense if the user is a part of the group
        serializer.save(paid_by=self.request.user)


class ExpenseListView(generics.ListAPIView):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = ExpenseGroup.objects.get(id=group_id)
        if self.request.user not in group.members.all():
            raise PermissionDenied("You are not a member of this group.")
        return Expense.objects.filter(group_id=group_id)