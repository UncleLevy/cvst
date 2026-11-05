from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def create(self, request, *args, **kwargs):
        if not settings.CVST_ALLOW_REGISTRATION:
            raise PermissionDenied("Self-registration is disabled.")
        return super().create(request, *args, **kwargs)


class AuthConfigView(APIView):
    """Public flags the login screen needs (e.g. whether to offer sign-up)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request):
        return Response({"registration_enabled": settings.CVST_ALLOW_REGISTRATION})


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
