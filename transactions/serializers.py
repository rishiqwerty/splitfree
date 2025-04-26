from rest_framework import serializers

from auth_app.serializers import UserSerializer
from .models import Transaction
from django.contrib.auth import get_user_model
User = get_user_model()

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaction model.
    """
    to_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    from_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    reciever = UserSerializer(read_only=True, source='to_user')
    sender = UserSerializer(read_only=True, source='from_user')
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'reciever', 'sender']
        extra_kwargs = {
            'amount': {'required': True},
            'description': {'required': False},
            'transaction_date': {'required': True},
            'from_user': {'required': True},
            'to_user': {'required': True},
        }