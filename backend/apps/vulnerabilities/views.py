from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.core.permissions import is_admin

from .models import Vulnerability
from .serializers import VulnerabilitySerializer

SEVERITIES = [value for value, _label in Vulnerability.SEVERITY_CHOICES]


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["scan", "severity", "service"]
    search_fields = ["title", "cve_id", "description", "service"]
    ordering_fields = ["cvss_score", "discovered_at"]

    def get_queryset(self):
        qs = Vulnerability.objects.select_related("scan", "scan__target")
        if not is_admin(self.request.user):
            qs = qs.filter(scan__created_by=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Finding counts per severity (optionally for one scan via ?scan=<id>)."""
        qs = self.get_queryset()
        scan_id = request.query_params.get("scan")
        if scan_id and scan_id.isdigit():
            qs = qs.filter(scan_id=int(scan_id))
        counts = dict.fromkeys(SEVERITIES, 0)
        for row in qs.order_by().values("severity").annotate(n=Count("id")):
            counts[row["severity"]] = row["n"]
        return Response({"total": sum(counts.values()), "by_severity": counts})
