from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response

from auth_app.utils import log_activity
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer


class TransactionCreateView(generics.CreateAPIView):
    """
    API view to create a new transaction.
    """

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        # Perform any additional actions before saving the transaction
        serializer.save()
        print(serializer.data)
        log_activity(
            user=self.request.user,
            name="Settle Up Posted!!",
            description=f"""{serializer.data.get('sender', {}).get('username')} settled up with {serializer.data.get('reciever', {}).get('username')}
                  of amount {serializer.data.get('amount')} on {serializer.data.get('transaction_date')}.""",
            related_object=serializer.instance,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
