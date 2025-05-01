from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from expenses.serializers import ExpenseSummarySerializer

User = get_user_model()


class SimplifyDebtsTests(APITestCase):
    def setUp(self):
        """
        Set up test data.
        """
        # Create users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password1"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password2"
        )
        self.user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="password3"
        )
        self.user4 = User.objects.create_user(
            username="user4", email="user4@example.com", password="password4"
        )

    def test_simplify_debts(self):
        """
        Test the simplify_debts method.
        """
        serializer = ExpenseSummarySerializer()
        # Example balances
        # user1 owes 50 to user2
        # user2 owes 30 to user3
        # user1 owes 20 to user3
        balances = {
            self.user1.id: -70,  # Total owed by user1
            self.user2.id: 20,  # Net balance for user2
            self.user3.id: 50,  # Total owed to user3
        }
        simplified_transactions = serializer.simplify_debts(balances)

        # Expected simplified transactions:
        # user1 pays 50 to user3
        # user1 pays 20 to user2
        self.assertEqual(len(simplified_transactions), 2)

        transaction1 = simplified_transactions[1]
        self.assertEqual(transaction1["from_user"]["id"], self.user1.id)
        self.assertEqual(transaction1["to_user"]["id"], self.user3.id)
        self.assertEqual(transaction1["amount"], 50)

        transaction2 = simplified_transactions[0]
        self.assertEqual(transaction2["from_user"]["id"], self.user1.id)
        self.assertEqual(transaction2["to_user"]["id"], self.user2.id)
        self.assertEqual(transaction2["amount"], 20)

    def test_simplify_debts_no_balances(self):
        """
        Test simplify_debts with no balances (empty dictionary).
        """
        balances = {}
        serializer = ExpenseSummarySerializer()
        simplified_transactions = serializer.simplify_debts(balances)

        # Assert no transactions are generated
        self.assertEqual(len(simplified_transactions), 0)

    def test_simplify_debts_single_creditor_and_debtor(self):
        """
        Test simplify_debts with one creditor and one debtor.
        """
        balances = {
            self.user1.id: -50,  # Debtor
            self.user2.id: 50,  # Creditor
        }
        serializer = ExpenseSummarySerializer()
        simplified_transactions = serializer.simplify_debts(balances)

        # Assert one transaction is generated
        self.assertEqual(len(simplified_transactions), 1)
        transaction = simplified_transactions[0]
        self.assertEqual(transaction["from_user"]["id"], self.user1.id)
        self.assertEqual(transaction["to_user"]["id"], self.user2.id)
        self.assertEqual(transaction["amount"], 50)

    def test_simplify_debts_multiple_creditors_and_debtors(self):
        """
        Test simplify_debts with multiple creditors and debtors.
        """
        balances = {
            self.user1.id: -70,  # Debtor
            self.user2.id: 20,  # Creditor
            self.user3.id: 50,  # Creditor
        }
        serializer = ExpenseSummarySerializer()
        simplified_transactions = serializer.simplify_debts(balances)

        # Assert two transactions are generated
        self.assertEqual(len(simplified_transactions), 2)

        transaction1 = simplified_transactions[1]
        self.assertEqual(transaction1["from_user"]["id"], self.user1.id)
        self.assertEqual(transaction1["to_user"]["id"], self.user3.id)
        self.assertEqual(transaction1["amount"], 50)

        transaction2 = simplified_transactions[0]
        self.assertEqual(transaction2["from_user"]["id"], self.user1.id)
        self.assertEqual(transaction2["to_user"]["id"], self.user2.id)
        self.assertEqual(transaction2["amount"], 20)

    def test_simplify_debts_balanced_group(self):
        """
        Test simplify_debts with a balanced group (no net debts).
        """
        balances = {
            self.user1.id: 0,
            self.user2.id: 0,
            self.user3.id: 0,
        }
        serializer = ExpenseSummarySerializer()
        simplified_transactions = serializer.simplify_debts(balances)

        # Assert no transactions are generated
        self.assertEqual(len(simplified_transactions), 0)

    def test_simplify_debts_large_group(self):
        """
        Test simplify_debts with a larger group of creditors and debtors.
        """
        balances = {
            self.user1.id: -100,  # Debtor
            self.user2.id: -50,  # Debtor
            self.user3.id: 100,  # Creditor
            self.user4.id: 50,  # Creditor
        }
        serializer = ExpenseSummarySerializer()
        simplified_transactions = serializer.simplify_debts(balances)

        self.assertEqual(len(simplified_transactions), 2)

        transaction1 = simplified_transactions[0]
        transaction2 = simplified_transactions[1]

        self.assertEqual(transaction1["amount"] + transaction2["amount"], 150)
