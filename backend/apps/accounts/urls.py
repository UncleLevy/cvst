from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AuthConfigView, CustomTokenObtainPairView, MeView, RegisterView

urlpatterns = [
    path("config/", AuthConfigView.as_view(), name="auth_config"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]
