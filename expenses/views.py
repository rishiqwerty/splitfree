from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.pagination import CursorPagination
from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

from auth_app.utils import log_activity

from .models import Expense
from groups.models import ExpenseGroup
from .serializers import (
    ExpenseSerializer,
    ExpenseSummarySerializer,
    UserExpenseSerializer,
)

from django.utils.dateparse import parse_date


class ExpenseCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-expense_date"


class ExpenseCreateView(generics.CreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        group_id = self.request.data.get("group")

        group = ExpenseGroup.objects.get(id=group_id)

        # Check if the user is part of the group
        if not group.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a member of this group.")
        # Save the expense if the user is a part of the group
        serializer.save(paid_by=self.request.user)
        log_activity(
            user=self.request.user,
            name="Expense Created",
            description=f"An expense of {serializer.data.get('amount')} was added to group '{group.name}'.",
            related_object=serializer.instance,
        )


class ExpenseDeleteView(generics.DestroyAPIView):
    """
    API view to delete an expense.
    """

    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def delete(self, request, *args, **kwargs):
        expense_id = self.kwargs.get("expense_id")
        expense = get_object_or_404(Expense, id=expense_id)

        # Check if the user is part of the group associated with the expense
        if not expense.group.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied(
                "You are not a member of the group associated with this expense."
            )

        # Log the activity before deletion
        log_activity(
            user=request.user,
            name="Expense Deleted",
            description=f"An expense of {expense.amount} was deleted from group '{expense.group.name}'.",
            related_object=expense.group,
        )

        # Delete the expense
        expense.delete()
        return Response({"message": "Expense deleted successfully."}, status=200)


class ExpenseUpdateView(generics.UpdateAPIView):
    """
    API view to update an expense.
    """

    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def update(self, request, *args, **kwargs):
        expense_id = self.kwargs.get("pk")
        expense = get_object_or_404(Expense, id=expense_id)

        # Check if the user is part of the group associated with the expense
        if not expense.group.members.filter(id=request.user.id).exists():
            raise PermissionDenied(
                "You are not a member of the group associated with this expense."
            )

        # Perform the update
        response = super().update(request, *args, **kwargs)

        # Log the activity
        log_activity(
            user=request.user,
            name="Expense Updated",
            description=f"""An expense of {expense.amount} of {expense.title} was updated in group
              '{expense.group.name} paid_by {expense.paid_by.username}'.
              New Changes: {response.data.get('amount')} of {response.data.get('title')} paid_by {response.data.get('paid_by',{}).get('username')}""",
            related_object=expense.group,
        )

        return response


class ExpenseListView(generics.ListAPIView):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        group = ExpenseGroup.objects.get(id=group_id)
        if not group.members.filter(id=self.request.user.id).exists():
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
        if not group.members.filter(id=self.request.user.id).exists():
            return Response(
                {"error": "You are not a member of this group."}, status=403
            )
        # Serialize the expense summary
        serializer = ExpenseSummarySerializer(group, context={"request": request})
        return Response(serializer.data)


class UserExpenseListView(generics.ListAPIView):
    """
    API view to get the list of expenses for a user in a group.
    """

    serializer_class = ExpenseSerializer
    pagination_class = ExpenseCursorPagination

    def get_queryset(self):
        user_id = self.request.user.id
        group_id = self.kwargs.get("group_id")
        start_date_str = self.request.query_params.get("start_date")
        end_date_str = self.request.query_params.get("end_date")

        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else datetime.now().date()

        expenses = Expense.objects.filter(split_between__id=user_id)

        if group_id:
            expense_group = get_object_or_404(ExpenseGroup, id=group_id)
            if not expense_group.members.filter(id=self.request.user.id).exists():
                raise PermissionDenied("You are not a member of this group.")
            expenses = expenses.filter(group_id=group_id)
        if start_date:
            expenses = expenses.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                split_between__id__contains=user_id,
            ).order_by("-expense_date")

        else:
            expenses = expenses.filter(split_between__id__contains=user_id).order_by(
                "-expense_date"
            )
        return expenses


class UserTotalSpentView(APIView):
    def get(self, request):
        user = request.user
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        group_id = request.query_params.get("group_id")

        start_date = parse_date(start_date) if start_date else None
        end_date = parse_date(end_date) if end_date else datetime.now().date()

        # Optional group filter
        expenses = Expense.objects.filter(split_between__id=user.id)
        if group_id:
            expenses = expenses.filter(group_id=group_id)

        if start_date:
            expenses = expenses.filter(expense_date__range=(start_date, end_date))

        total_current_month_expenses = UserExpenseSerializer(
            expenses,
            context={
                "user_id": user.id,
                "start_date": start_date,
                "end_date": end_date,
            },
        ).data

        return Response(
            {"total_spent": total_current_month_expenses.get("total_spent", 0)}
        )
