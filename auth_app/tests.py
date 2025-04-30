from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from unittest.mock import patch
from firebase_admin.auth import InvalidIdTokenError

User = get_user_model()


class AuthAppTests(APITestCase):
    def setUp(self):
        """
        Set up test data and API client.
        """
        self.client = APIClient()
        self.google_login_url = "/auth/google-login/"
        self.get_user_url = "/auth/get-user/"
        self.logout_url = "/auth/logout/"
        self.user_email = "testuser@example.com"
        self.user_name = "Test User"

    @patch("firebase_admin.auth.verify_id_token")
    def test_google_login_success(self, mock_verify_id_token):
        """
        Test successful Google login.
        """
        mock_verify_id_token.return_value = {
            "email": self.user_email,
            "name": self.user_name,
        }

        response = self.client.post(self.google_login_url, {"id_token": "valid_token"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

        # Verify user and token creation
        user = User.objects.get(email=self.user_email)
        self.assertEqual(user.username, self.user_email)
        self.assertEqual(user.first_name, self.user_name)
        self.assertTrue(Token.objects.filter(user=user).exists())

    @patch("firebase_admin.auth.verify_id_token")
    def test_google_login_invalid_token(self, mock_verify_id_token):
        """
        Test Google login with an invalid token.
        """
        mock_verify_id_token.side_effect = InvalidIdTokenError("Invalid token")

        response = self.client.post(
            self.google_login_url, {"id_token": "invalid_token"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Invalid token")

    def test_google_login_missing_id_token(self):
        """
        Test Google login with missing ID token.
        """
        response = self.client.post(self.google_login_url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "ID token required")

    def test_get_user_authenticated(self):
        """
        Test retrieving user details when authenticated.
        """
        user = User.objects.create_user(username=self.user_email, email=self.user_email)
        token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(self.get_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user_email)

    def test_get_user_unauthenticated(self):
        """
        Test retrieving user details when not authenticated.
        """
        response = self.client.get(self.get_user_url)
        self.assertEqual(response.status_code, 401)

    def test_logout_authenticated(self):
        """
        Test logging out when authenticated.
        """
        user = User.objects.create_user(username=self.user_email, email=self.user_email)
        token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Logged out successfully")

        # Verify token deletion
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_logout_unauthenticated(self):
        """
        Test logging out when not authenticated.
        """
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 401)
