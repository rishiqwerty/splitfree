from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from groups.models import ExpenseGroup
from expenses.models import Expense

User = get_user_model()


class ExpenseViewTests(APITestCase):
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

        # Create a group and add users
        self.group = ExpenseGroup.objects.create(name="Test Group")
        self.group.members.add(self.user1, self.user2)

        # Create an expense
        self.expense = Expense.objects.create(
            title="Test Expense",
            amount=100,
            group=self.group,
            paid_by=self.user1,
        )

        # Authenticate user1
        self.client.force_authenticate(user=self.user1)

        # URLs
        self.create_expense_url = reverse("create_expense")
        # self.create_expense_url = "create_expense"
        self.delete_expense_url = reverse("expense_delete", args=[self.expense.id])
        self.update_expense_url = reverse("expense_update", args=[self.expense.id])
        self.list_expenses_url = reverse("list_expenses", args=[self.group.id])
        self.summary_url = reverse("expense_summary", args=[self.group.id])

    def test_create_expense_success(self):
        """
        Test creating an expense successfully.
        """
        data = {
            "title": "New Expense",
            "amount": 200,
            "group": self.group.id,
            "paid_by_id": self.user1.id,
            "split_between": [self.user2.id],
            "splits": [
                {"amount": "200.00", "user": self.user2.id},
            ],  # Correct format
            "notes": "",
            "expense_date": "2025-04-30T18:28",
        }
        response = self.client.post(self.create_expense_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Expense")
        self.assertEqual(response.data["amount"], "200.00")

    def test_create_expense_not_in_group(self):
        """
        Test creating an expense when the user is not in the group.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        data = {
            "title": "New Expense",
            "amount": 200,
            "group": self.group.id,
            "paid_by_id": self.user1.id,
        }
        response = self.client.post(self.create_expense_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            "Payer must be a member of the group.", response.data["non_field_errors"][0]
        )

    def test_delete_expense_success(self):
        """
        Test deleting an expense successfully.
        """
        response = self.client.delete(self.delete_expense_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Expense deleted successfully.")
        self.assertFalse(Expense.objects.filter(id=self.expense.id).exists())

    def test_delete_expense_not_in_group(self):
        """
        Test deleting an expense when the user is not in the group.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        response = self.client.delete(self.delete_expense_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("expenses.serializers.get_expense_icon")
    def test_update_expense_success(self, mock_get_expense_icon):
        """
        Test updating an expense successfully.
        """
        mock_get_expense_icon.return_value = "💸"  # Mock the icon retrieval
        data = {
            "title": "Tea Expense",
            "amount": 150,
            "paid_by_id": self.user1.id,
            "group": self.group.id,
        }
        response = self.client.put(self.update_expense_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Tea Expense")
        self.assertEqual(response.data["amount"], "150.00")

    def test_update_expense_not_in_group(self):
        """
        Test updating an expense when the user is not in the group.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        data = {
            "title": "Updated Expense",
            "amount": 150,
        }
        response = self.client.put(self.update_expense_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_expenses_success(self):
        """
        Test listing expenses for a group successfully.
        """
        response = self.client.get(self.list_expenses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Test Expense")

    def test_list_expenses_not_in_group(self):
        """
        Test listing expenses when the user is not in the group.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        response = self.client.get(self.list_expenses_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_success(self):
        """
        Test retrieving the expense summary for a group successfully.
        """
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_spend", response.data)

    def test_summary_not_in_group(self):
        """
        Test retrieving the expense summary when the user is not in the group.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
