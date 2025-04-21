import base64
import json
from firebase_admin import auth as firebase_auth, credentials, initialize_app
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import os

firebase_cred = os.getenv('FIREBASE_CREDENTIALS')
firebase_b64 = os.getenv("FIREBASE_CREDENTIALS_B64")

if firebase_b64:
    decoded = base64.b64decode(firebase_b64)
    FIREBASE_CREDENTIALS = json.loads(decoded)
else:
    FIREBASE_CREDENTIALS = firebase_cred

cred = credentials.Certificate(FIREBASE_CREDENTIALS)
initialize_app(cred)

User = get_user_model()

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'ID token required'}, status=400)

        try:
            decoded = firebase_auth.verify_id_token(id_token)
            email = decoded.get('email')
            name = decoded.get('name')

            if not email:
                return Response({'error': 'Email not found'}, status=400)

            user, _ = User.objects.get_or_create(username=email, defaults={"email": email, "first_name": name})
            token, _ = Token.objects.get_or_create(user=user)

            return Response({'token': token.key})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
