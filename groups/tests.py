from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from groups.models import ExpenseGroup, GroupMembership
from unittest.mock import patch

User = get_user_model()


class GroupAPITests(APITestCase):
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

        # Authenticate user1
        self.client.force_authenticate(user=self.user1)

        # Create a group
        self.group = ExpenseGroup.objects.create(name="Test Group")
        self.group.members.add(self.user1)

        # URLs
        # self.group_members_url = f"/groups/{self.group.id}/members/"
        self.group_members_url = reverse("list_group_members", args=[self.group.id])
        self.create_group_url = reverse("create_group")
        self.add_user_to_group_url = reverse(
            "add-user-to-group", args=[self.group.uuid]
        )
        self.group_activity_url = reverse("group_activities", args=[self.group.id])
        self.group_overview_url = reverse("group_overview", args=[self.group.id])

    def test_list_group_members_success(self):
        """
        Test listing members of a group successfully.
        """
        response = self.client.get(self.group_members_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["members"][0]["username"], self.user1.username
        )

    def test_list_group_members_not_in_group(self):
        """
        Test listing members of a group when the user is not a member.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        response = self.client.get(self.group_members_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_group_success(self):
        """
        Test creating a group successfully.
        """
        data = {"name": "New Group"}
        response = self.client.post(self.create_group_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Group")

    @patch("groups.views.log_activity")
    def test_add_user_to_group_success(self, mock_log_activity):
        """
        Test adding a user to a group successfully.
        """
        self.client.force_authenticate(user=self.user2)  # Authenticate as user2
        response = self.client.post(self.add_user_to_group_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            GroupMembership.objects.filter(user=self.user2, group=self.group).exists()
        )

        # Assert that log_activity was called
        mock_log_activity.assert_called_once_with(
            user=self.user2,
            name="User Joined Group",
            description=f"User {self.user2.username} joined group '{self.group.name} via url'.",
            related_object=self.group,
        )

    def test_add_user_to_group_already_member(self):
        """
        Test adding a user to a group when they are already a member.
        """
        response = self.client.post(self.add_user_to_group_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["error"], "You are already a member of this group."
        )

    def test_group_activity_success(self):
        """
        Test retrieving group activities successfully.
        """
        response = self.client.get(self.group_activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("groups.serializers.generate_content")
    def test_group_overview_success(self, mock_generate_content):
        """
        Test retrieving the overview of a group successfully.
        """
        mock_generate_content.return_value = "This is a test overview."
        response = self.client.get(self.group_overview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ai_overview", response.data)

    def test_group_overview_not_in_group(self):
        """
        Test retrieving the overview of a group when the user is not a member.
        """
        self.group.members.remove(self.user1)  # Remove user1 from the group
        response = self.client.get(self.group_overview_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
