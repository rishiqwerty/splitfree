# auth/urls.py
from django.urls import path
from .views import GoogleLoginView, GetUserView

urlpatterns = [
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('get-user/', GetUserView.as_view(), name='get-user'),
]
