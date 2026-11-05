from rest_framework import permissions, viewsets

from apps.core.permissions import is_admin

from .models import Target
from .serializers import TargetSerializer


class TargetViewSet(viewsets.ModelViewSet):
    serializer_class = TargetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["target_type"]

    def get_queryset(self):
        qs = Target.objects.filter(is_active=True)
        if not is_admin(self.request.user):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        # Soft delete: keeps scan history intact.
        instance.is_active = False
        instance.save(update_fields=["is_active"])
