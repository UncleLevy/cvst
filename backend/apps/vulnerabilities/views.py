from rest_framework import permissions, viewsets

from apps.core.permissions import is_admin

from .models import Vulnerability
from .serializers import VulnerabilitySerializer


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["scan", "severity", "service"]

    def get_queryset(self):
        qs = Vulnerability.objects.select_related("scan")
        if not is_admin(self.request.user):
            qs = qs.filter(scan__created_by=self.request.user)
        return qs
