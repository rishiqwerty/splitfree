from rest_framework import serializers
from .models import Expense
from django.contrib.auth.models import User

class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    split_between = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'group', 'title', 'amount', 'paid_by', 'split_between', 'notes', 'created_at']
    
    def validate(self, data):
        group = data.get('group')
        split_users = data.get('split_between')
        paid_by = data.get('paid_by')

        if group is None:
            raise serializers.ValidationError("Group is required.")

        group_members = group.members.all()

        # Check if paid_by user is part of the group
        if paid_by not in group_members:
            raise serializers.ValidationError("Payer must be a member of the group.")

        # Check if all users in split_between are part of the group
        invalid_users = [user for user in split_users if user not in group_members]
        if invalid_users:
            names = ", ".join([user.username for user in invalid_users])
            raise serializers.ValidationError(f"The following users are not in the group: {names}")

        return data

    def create(self, validated_data):
        # Handle the creation of an expense
        split_between_users = validated_data.pop('split_between')
        expense = Expense.objects.create(**validated_data)
        expense.split_between.set(split_between_users)  # Set the split users
        expense.save()
        return expense

    def update(self, instance, validated_data):
        # Handle updates to an existing expense
        split_between_users = validated_data.pop('split_between', None)
        instance = super().update(instance, validated_data)
        if split_between_users is not None:
            instance.split_between.set(split_between_users)  # Update the split users
        instance.save()
        return instance
