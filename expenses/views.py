from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

from auth_app.utils import log_activity

from .models import Expense
from groups.models import ExpenseGroup
from .serializers import ExpenseSerializer, ExpenseSummarySerializer

class ExpenseCreateView(generics.CreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    def perform_create(self, serializer):
        group_id = self.request.data.get('group')

        group = ExpenseGroup.objects.get(id=group_id)
        
        # Check if the user is part of the group
        print("Geree!!!!!")
        if self.request.user not in group.members.all():
            raise PermissionDenied("You are not a member of this group."
            )
        print(self.request.data)
        # Save the expense if the user is a part of the group
        serializer.save(paid_by=self.request.user)
        print('serializer', serializer.data)
        log_activity(
            user=self.request.user,
            name='Expense Created',
            description=f"An expense of {serializer.data.get('amount')} was added to group '{group.name}'.",
            related_object=serializer.instance,
        )

class ExpenseListView(generics.ListAPIView):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = ExpenseGroup.objects.get(id=group_id)
        if self.request.user not in group.members.all():
            raise PermissionDenied("You are not a member of this group.")
        return Expense.objects.filter(group_id=group_id)

class ExpenseSummaryView(APIView):
    """
    API view to get the summary of expenses for a group.
    """
    def get(self, request, group_id):
        # Get the group
        group = get_object_or_404(ExpenseGroup, id=group_id)

        # Ensure the user is a member of the group
        if request.user not in group.members.all():
            return Response({'error': 'You are not a member of this group.'}, status=403)
        # Serialize the expense summary
        serializer = ExpenseSummarySerializer(group, context={'request': request})
        return Response(serializer.data)
