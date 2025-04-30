from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from groups.models import ExpenseGroup
from transactions.models import Transaction

User = get_user_model()


class TransactionCreateViewTests(APITestCase):
    def setUp(self):
        """
        Set up test data and API client.
        """
        self.client = APIClient()

        # Create users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password1"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password2"
        )
        self.group = ExpenseGroup.objects.create(name="Test Group")
        self.group.members.add(self.user1, self.user2)

        # Authenticate user1
        self.client.force_authenticate(user=self.user1)

        # URL for creating a transaction
        self.create_transaction_url = reverse("create_transaction")

    @patch("transactions.views.log_activity")
    def test_create_transaction_success(self, mock_log_activity):
        """
        Test creating a transaction successfully.
        """
        data = {
            "amount": 500,
            "description": "Settling up",
            "transaction_date": "2025-05-01T10:00:00Z",
            "from_user": self.user1.id,
            "to_user": self.user2.id,
            "group": self.group.id,
        }

        response = self.client.post(self.create_transaction_url, data, format="json")
        # Assert the response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert the transaction was created
        transaction = Transaction.objects.get(id=response.data["id"])
        self.assertEqual(transaction.amount, 500)
        self.assertEqual(transaction.from_user, self.user1)
        self.assertEqual(transaction.to_user, self.user2)

        # Assert that log_activity was called with the correct arguments
        mock_log_activity.assert_called_once_with(
            user=self.user1,
            name="Settle Up Posted!!",
            description=(
                f"{self.user1.username} settled up with {self.user2.username} "
                "of amount 500.00 on 2025-05-01T10:00:00Z."
            ),
            related_object=transaction,
        )

    def test_create_transaction_missing_fields(self):
        """
        Test creating a transaction with missing required fields.
        """
        data = {
            "amount": 500,
            # Missing "from_user" and "to_user"
        }

        response = self.client.post(self.create_transaction_url, data, format="json")

        # Assert the response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Assert the error messages
        self.assertIn("from_user", response.data)
        self.assertIn("to_user", response.data)
        self.assertEqual(response.data["from_user"][0], "This field is required.")
        self.assertEqual(response.data["to_user"][0], "This field is required.")
