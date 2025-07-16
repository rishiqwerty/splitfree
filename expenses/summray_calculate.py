from collections import defaultdict
from decimal import Decimal

from django.db import models
from django.db.models import Count

from auth_app.serializers import UserSerializer
from .models import Expense, Split
from django.contrib.auth.models import User


class ExpenseSummary:
    def __init__(self, instance=None):
        self.instance = instance

    def get_summary(self):
        """
        Calculate and return the summary of expenses.
        """
        group = self.instance  # Assuming `instance` is an ExpenseGroup
        expenses = group.expenses.all()  # Get all expenses for the group
        transactions = group.transactions.all()  # Get all transactions for the group
        # Calculate total spend
        total_spend = expenses.aggregate(total=models.Sum("amount"))["total"] or 0

        # Calculate user expense details
        balances = {}
        users = group.members.all()  # Get all members of the group
        for user in users:
            # Calculate total paid by the user
            expenses = expenses.annotate(split_count=Count("splits"))
            # .exclude(
            #     split_count=1
            # )
            paid = (
                expenses.filter(paid_by=user).aggregate(total=models.Sum("amount"))[
                    "total"
                ]
                or 0
            )
            paid_transactions = (
                transactions.filter(from_user=user).aggregate(
                    total=models.Sum("amount")
                )["total"]
                or 0
            )
            # Calculate total owed by the user
            owed = (
                Split.objects.filter(expense__in=expenses, user=user).annotate(
                    split_count=Count("expense__splits")
                )
                # .exclude(split_count=1)
                .aggregate(total=models.Sum("amount"))["total"]
                or 0
            )
            net_balance = paid - owed + paid_transactions
            balances[user.id] = net_balance

        # request = self.context.get("request")
        # simplify_enable = request.query_params.get("simplify", "none").lower()
        # if simplify_enable == "true" and not group.simplify_debt:
        #     group.simplify_debt = True
        #     group.save()
        #     log_activity(
        #         user=request.user,
        #         name="Group Simplified",
        #         description=f"Group '{group.name}' debts simplified.",
        #         related_object=group,
        #     )
        # elif simplify_enable == "false" and group.simplify_debt:
        #     group.simplify_debt = False
        #     group.save()
        #     log_activity(
        #         user=request.user,
        #         name="Group Simplified",
        #         description=f"Group '{group.name}' debts unsimplified.",
        #         related_object=group,
        #     )
        simplified_det = []
        simplify = group.simplify_debt
        if simplify:

            simplified_det = self.simplify_debts(balances)
        else:
            # Calculate non-simplified debts
            non_simplified_transactions = self.calculate_non_simplified_debts(
                expenses, transactions
            )

        # Return the calculated data
        return {
            "total_spend": total_spend,
            "simplified_transactions": simplified_det if simplify else None,
            "non_simplified_transactions": non_simplified_transactions
            if not simplify
            else None,
        }

    def calculate_non_simplified_debts(self, expenses, transactions):
        """
        Calculate non-simplified debts for each expense, including paid transactions.
        """
        consolidated_transactions = []
        grouped_transactions = defaultdict(lambda: defaultdict(Decimal))
        paid_transactions_tracker = defaultdict(
            lambda: defaultdict(Decimal)
        )  # Track applied paid transactions
        for expense in expenses:
            splits = expense.splits.all()
            for split in splits:
                if split.user != expense.paid_by:
                    # Adjust the amount owed by including paid transactions
                    paid_transactions = (
                        transactions.filter(
                            from_user=split.user, to_user=expense.paid_by
                        ).aggregate(total=models.Sum("amount"))["total"]
                        or 0
                    )

                    already_applied = paid_transactions_tracker[split.user.id][
                        expense.paid_by.id
                    ]
                    remaining_paid_transactions = paid_transactions - already_applied

                    adjusted_amount = split.amount - max(
                        remaining_paid_transactions, Decimal(0)
                    )
                    if remaining_paid_transactions > 0:
                        paid_transactions_tracker[split.user.id][
                            expense.paid_by.id
                        ] += min(split.amount, remaining_paid_transactions)

                    if adjusted_amount > 0:
                        grouped_transactions[split.user.id][
                            expense.paid_by.id
                        ] += adjusted_amount
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

                    reverse_amount = grouped_transactions[to_user_id].get(
                        from_user_id, Decimal(0)
                    )
                    net_amount = amount - reverse_amount

                    if net_amount > 0:
                        consolidated_transactions.append(
                            {
                                "from_user": UserSerializer(
                                    User.objects.get(id=from_user_id)
                                ).data,
                                "to_user": UserSerializer(
                                    User.objects.get(id=to_user_id)
                                ).data,
                                "amount": net_amount,
                            }
                        )
                    elif net_amount < 0:
                        consolidated_transactions.append(
                            {
                                "from_user": UserSerializer(
                                    User.objects.get(id=to_user_id)
                                ).data,
                                "to_user": UserSerializer(
                                    User.objects.get(id=from_user_id)
                                ).data,
                                "amount": abs(net_amount),
                            }
                        )

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
                debtors.append(
                    (user_id, -balance)
                )  # Convert to positive for easier calculations

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
            transactions.append(
                {
                    "from_user": debter,
                    "to_user": creditor,
                    "amount": transaction_amount,
                }
            )

            # Update remaining balances
            credit_remaining = credit_amount - transaction_amount
            debt_remaining = debt_amount - transaction_amount

            if credit_remaining > 0:
                creditors.insert(0, (creditor_id, credit_remaining))
            if debt_remaining > 0:
                debtors.insert(0, (debtor_id, debt_remaining))
        print("sdaas", transactions)
        return transactions
