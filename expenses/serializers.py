from collections import defaultdict
from decimal import Decimal
from rest_framework import serializers

from auth_app.serializers import UserSerializer
from auth_app.utils import log_activity
from expenses.utils import get_expense_icon
from .models import Expense, Split
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count

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
        fields = ['id', 'group', 'expense_icon', 'title', 'amount', 'paid_by', 'paid_by_id', 'split_between', 'splits_detail', 'splits', 'notes', 'created_at', 'expense_date']
    
    def validate(self, data):
        group = data.get('group')
        split_users = data.get('split_between')
        paid_by = data.get('paid_by') or data.get('paid_by_id')
        splits = data.get('splits', [])

        if group is None:
            raise serializers.ValidationError("Group is required.")

        group_members = group.members.all()

        # Check if paid_by user is part of the group
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
        expense.expense_icon=get_expense_icon(expense.title, expense.notes)
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
        paid_by_user = validated_data.pop('paid_by_id')

        splits_data = validated_data.pop('splits', None)
        print(" Te-------->>>>> ",validated_data.get('expense_date'))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if split_between_users is not None:
            instance.split_between.set(split_between_users)  # Update the split users
        if paid_by_user is not None:
            instance.paid_by = paid_by_user
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

class UserExpenseDetailSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    owed = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_transactions = serializers.DecimalField(max_digits=10, decimal_places=2)
class ExpenseSummarySerializer(serializers.Serializer):
    total_spend = serializers.DecimalField(max_digits=10, decimal_places=2)
    users_expense_details = UserExpenseDetailSerializer(many=True)
    total_balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    def to_representation(self, instance):
        """
        Calculate and return the summary of expenses.
        """
        group = instance  # Assuming `instance` is an ExpenseGroup
        expenses = group.expenses.all()  # Get all expenses for the group
        transactions = group.transactions.all()  # Get all transactions for the group
        # Calculate total spend
        total_spend = expenses.aggregate(total=models.Sum('amount'))['total'] or 0

        # Calculate user expense details
        user_details = []
        balances = {}
        users = group.members.all()  # Get all members of the group
        for user in users:
            # Calculate total paid by the user
            print("count before exclude", expenses.count())
            expenses=expenses.annotate(split_count=Count('splits')).exclude(split_count=1)
            print("count after exclude", expenses.count())
            paid = expenses.filter(paid_by=user).aggregate(total=models.Sum('amount'))['total'] or 0
            paid_transactions = transactions.filter(from_user=user).aggregate(total=models.Sum('amount'))['total'] or 0
            # Calculate total owed by the user
            owed = (
                Split.objects.filter(expense__in=expenses, user=user)
                .annotate(split_count=Count('expense__splits'))
                .exclude(split_count=1)
                .aggregate(total=models.Sum('amount'))['total']
                or 0
            )
            net_balance = paid - owed + paid_transactions
            balances[user.id] = net_balance

            user_details.append({
                'user': UserSerializer(user).data,
                'paid': paid,
                'owed': abs(net_balance) if net_balance < 0 else 0,
                'paid_transactions': paid_transactions,
            })
            serialized_user_details = UserExpenseDetailSerializer(user_details, many=True).data
        request = self.context.get('request')
        simplify_enable = request.query_params.get('simplify', 'none').lower()
        if simplify_enable == 'true' and not group.simplify_debt:
            group.simplify_debt = True
            group.save()
            log_activity(
                user=request.user,
                name='Group Simplified',
                description=f"Group '{group.name}' debts simplified.",
                related_object=group,
            )
        elif simplify_enable == 'false' and group.simplify_debt:
            group.simplify_debt = False
            group.save()
            log_activity(
                user=request.user,
                name='Group Simplified',
                description=f"Group '{group.name}' debts unsimplified.",
                related_object=group,
            )
        simplified_det = []
        simplify = group.simplify_debt
        if simplify:
            
            simplified_det = self.simplify_debts(balances)
        else:
            # Calculate non-simplified debts
            non_simplified_transactions = self.calculate_non_simplified_debts(expenses, transactions)
        # Calculate total balance
        total_balance = sum(detail['paid'] - detail['owed'] for detail in user_details)

        # Return the calculated data
        return {
            'total_spend': total_spend,
            'users_expense_details': serialized_user_details,
            'total_balance': total_balance,
            'simplified_transactions':simplified_det if simplify else None,
            'non_simplified_transactions': non_simplified_transactions if not simplify else None,
        }        

    def calculate_non_simplified_debts(self, expenses, transactions):
        """
        Calculate non-simplified debts for each expense, including paid transactions.
        """
        consolidated_transactions = []
        grouped_transactions = defaultdict(lambda: defaultdict(Decimal))
        paid_transactions_tracker = defaultdict(lambda: defaultdict(Decimal))  # Track applied paid transactions
        for expense in expenses:
            splits = expense.splits.all()
            for split in splits:
                if split.user != expense.paid_by:
                    # Adjust the amount owed by including paid transactions
                    paid_transactions = transactions.filter(from_user=split.user, to_user=expense.paid_by).aggregate(
                        total=models.Sum('amount')
                    )['total'] or 0

                    already_applied = paid_transactions_tracker[split.user.id][expense.paid_by.id]
                    remaining_paid_transactions = paid_transactions - already_applied

                    adjusted_amount = split.amount - max(remaining_paid_transactions,Decimal(0))
                    if remaining_paid_transactions > 0:
                        paid_transactions_tracker[split.user.id][expense.paid_by.id] += min(split.amount, remaining_paid_transactions)

                    # if adjusted_amount > 0:
                    #     non_simplified_transactions.append({
                    #         'from_user': UserSerializer(split.user).data,
                    #         'to_user': UserSerializer(expense.paid_by).data,
                    #         'amount': adjusted_amount
                    #     })
                    if adjusted_amount > 0:
                        grouped_transactions[split.user.id][expense.paid_by.id] += adjusted_amount
            # 2️⃣ Consolidate pairwise debts
            consolidated_transactions = []
            processed_pairs = set()

            for from_user_id in list(grouped_transactions.keys()):
                to_user_dict = grouped_transactions[from_user_id]
                for to_user_id in list(to_user_dict.keys()):
                    amount = to_user_dict[to_user_id]
                    if amount <= 0:
                        continue

                    pair_key = tuple(sorted([from_user_id, to_user_id]))
                    if pair_key in processed_pairs:
                        continue

                    reverse_amount = grouped_transactions[to_user_id].get(from_user_id, Decimal(0))
                    net_amount = amount - reverse_amount

                    if net_amount > 0:
                        consolidated_transactions.append({
                            'from_user': UserSerializer(User.objects.get(id=from_user_id)).data,
                            'to_user': UserSerializer(User.objects.get(id=to_user_id)).data,
                            'amount': net_amount,
                        })
                    elif net_amount < 0:
                        consolidated_transactions.append({
                            'from_user': UserSerializer(User.objects.get(id=to_user_id)).data,
                            'to_user': UserSerializer(User.objects.get(id=from_user_id)).data,
                            'amount': abs(net_amount),
                        })

                    processed_pairs.add(pair_key)

        return consolidated_transactions

    def simplify_debts(self, balances):
        """
        Simplify debts between users to minimize the number of transactions.
        """
        # Separate users into creditors (positive balance) and debtors (negative balance)
        creditors = []
        debtors = []
        for user_id, balance in balances.items():
            if balance > 0:
                creditors.append((user_id, balance))
            elif balance < 0:
                debtors.append((user_id, -balance))  # Convert to positive for easier calculations

        # Simplify transactions
        transactions = []
        while creditors and debtors:
            creditor_id, credit_amount = creditors.pop(0)
            debtor_id, debt_amount = debtors.pop(0)

            # Determine the transaction amount (minimum of credit and debt)
            transaction_amount = min(credit_amount, debt_amount)
            debter = UserSerializer(User.objects.get(id=debtor_id)).data
            creditor = UserSerializer(User.objects.get(id=creditor_id)).data
            # Record the transaction
            transactions.append({
                'from_user': debter,
                'to_user': creditor,
                'amount': transaction_amount,
            })

            # Update remaining balances
            credit_remaining = credit_amount - transaction_amount
            debt_remaining = debt_amount - transaction_amount

            if credit_remaining > 0:
                creditors.insert(0, (creditor_id, credit_remaining))
            if debt_remaining > 0:
                debtors.insert(0, (debtor_id, debt_remaining))

        return transactions