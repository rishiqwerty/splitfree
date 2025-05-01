from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth as firebase_auth
from django.contrib.auth import get_user_model
from rest_framework import exceptions

User = get_user_model()


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None  # no auth header, let it through for optional auth or return 401 in permissions

        try:
            id_token = auth_header.split(" ")[1]
            decoded_token = firebase_auth.verify_id_token(id_token)
            try:
                user = User.objects.get(email=decoded_token["email"])
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed("User not found")
            return (user, None)
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")
