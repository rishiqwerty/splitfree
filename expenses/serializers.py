from rest_framework import serializers

from auth.serializers import UserSerializer
from .models import Expense, Split
from django.contrib.auth.models import User

class SplitInputSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class SplitSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # shows username (or email, etc.)

    class Meta:
        model = Split
        fields = ['user', 'amount']


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    paid_by_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    # paid_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    split_between = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    splits = SplitInputSerializer(many=True, write_only=True, required=False)
    splits_detail = SplitSerializer(source='splits', many=True, read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'group', 'title', 'amount', 'paid_by', 'paid_by_id', 'split_between', 'splits_detail', 'splits', 'notes', 'created_at']
    
    def validate(self, data):
        group = data.get('group')
        split_users = data.get('split_between')
        paid_by = data.get('paid_by') or data.get('paid_by_id')
        splits = data.get('splits', [])

        if group is None:
            raise serializers.ValidationError("Group is required.")

        group_members = group.members.all()

        # Check if paid_by user is part of the group
        print("Paid by user:", paid_by)
        if not group_members.filter(id=paid_by.id):
            raise serializers.ValidationError("Payer must be a member of the group.")

        # Check if all users in split_between are part of the group
        invalid_users = [user for user in split_users if user not in group_members]
        if invalid_users:
            names = ", ".join([user.username for user in invalid_users])
            raise serializers.ValidationError(f"The following users are not in the group: {names}")

        if splits:
            split_user_ids = {split['user'].id for split in splits}
            expected_user_ids = {user.id for user in split_users}
            if split_user_ids != expected_user_ids:
                raise serializers.ValidationError("Mismatch between split_between users and splits data.")

            total_split = sum(split['amount'] for split in splits)
            if total_split != data['amount']:
                raise serializers.ValidationError("Split amounts must add up to total expense.")

        return data

    def create(self, validated_data):
        # Handle the creation of an expense
        split_between_users = validated_data.pop('split_between')
        paid_by_user = validated_data.pop('paid_by_id')
        print("Split between users:", validated_data)

        splits_data = validated_data.pop('splits')
    
        expense = Expense.objects.create(**validated_data)
        expense.paid_by = paid_by_user
        expense.split_between.set(split_between_users)
        expense.save()

        for split in splits_data:
            Split.objects.create(
                expense=expense,
                user=split['user'],
                amount=split['amount']
            )

        return expense

    def update(self, instance, validated_data):
        # Handle updates to an existing expense
        split_between_users = validated_data.pop('split_between', None)
        instance = super().update(instance, validated_data)
        splits_data = validated_data.pop('splits', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if split_between_users is not None:
            instance.split_between.set(split_between_users)  # Update the split users
        instance.save()
        if splits_data is not None:
            # Remove old splits
            instance.splits.all().delete()
            # Add new ones
            for split in splits_data:
                Split.objects.create(
                    expense=instance,
                    user=split['user'],
                    amount=split['amount']
                )
        return instance

{"group": 1,"title": "Groceries","amount": "100.00","paid_by": 1,"split_between": [1,2],"splits":[{"amount": "50.00","user": 1,},{"amount": "50.00","user": 2,}],"notes": "Cucumber\r\nBittergourd","created_at": "2025-04-20T06:28:04Z"}