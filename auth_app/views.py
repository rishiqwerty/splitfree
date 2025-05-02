import base64
import json
from .serializers import UserSerializer
from firebase_admin import auth as firebase_auth, credentials, initialize_app
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse

import os

firebase_cred = os.getenv("FIREBASE_CREDENTIALS")
firebase_b64 = os.getenv("FIREBASE_CREDENTIALS_B64")
if firebase_b64 or firebase_cred:
    if firebase_b64:
        decoded = base64.b64decode(firebase_b64)
        FIREBASE_CREDENTIALS = json.loads(decoded)
    else:
        FIREBASE_CREDENTIALS = firebase_cred
    
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    initialize_app(cred)

User = get_user_model()


class GoogleLoginView(APIView):
    """
    API view to handle Google login.

    This view verifies the Google ID token provided by the frontend,
    retrieves the user's email and name, and creates or retrieves a user
    in the database. It then generates an authentication token for the user
    and returns it in the response.

    Methods:
        post(request): Handles the Google login process.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return Response({"error": "ID token required"}, status=400)

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            email = decoded.get("email")
            name = decoded.get("name")

            if not email:
                return Response({"error": "Email not found"}, status=400)

            user, _ = User.objects.get_or_create(
                username=email, defaults={"email": email, "first_name": name}
            )
            token, _ = Token.objects.get_or_create(user=user)

            return Response({"token": token.key})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class GetUserView(APIView):
    """
    API view to retrieve the currently authenticated user's details.

    This view returns the details of the user associated with the
    authentication token provided in the request.

    Methods:
        get(request): Retrieves the authenticated user's details.
    """

    def get(self, request):
        user = request.user  # Get the currently authenticated user
        serializer = UserSerializer(user)  # Serialize the user data
        return Response(serializer.data)


class LogoutView(APIView):
    """
    API view to log out a user by deleting their authentication token.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully"}, status=200)


def health_check(request):
    """
    Health check view to verify the server is running.
    """
    return JsonResponse({"status": "ok"}, status=200)
