# auth/urls.py
from django.urls import path
from .views import GoogleLoginView, GetUserView, LogoutView

urlpatterns = [
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
    path('get-user/', GetUserView.as_view(), name='get-user'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
