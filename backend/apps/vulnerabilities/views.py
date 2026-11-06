from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import status as http
from rest_framework.response import Response

from apps.core.permissions import is_admin

from . import nvd, scoring
from .models import Vulnerability
from .serializers import VulnerabilitySerializer

SEVERITIES = [value for value, _label in Vulnerability.SEVERITY_CHOICES]


class VulnerabilityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["title", "cve_id", "description", "service"]
    ordering_fields = ["cvss_score", "risk_score", "discovered_at"]
    filterset_fields = ["scan", "severity", "service"]

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

    @action(detail=False, methods=["get"], url_path=r"cve/(?P<cve_id>[A-Za-z0-9-]+)")
    def cve(self, request, cve_id=None):
        """Look a CVE up in the NVD: GET /api/vulnerabilities/cve/CVE-2021-41773/"""
        try:
            return Response(nvd.lookup_cve(cve_id))
        except nvd.CveNotFound as exc:
            return Response({"error": str(exc)}, status=http.HTTP_404_NOT_FOUND)
        except nvd.NvdError as exc:
            return Response({"error": str(exc)}, status=http.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=["post"])
    def enrich(self, request, pk=None):
        """Refresh this finding's CVSS score, vector and references from the NVD."""
        vuln = self.get_object()
        if not vuln.cve_id:
            return Response({"error": "This finding has no CVE identifier."}, status=http.HTTP_400_BAD_REQUEST)
        try:
            info = nvd.lookup_cve(vuln.cve_id)
        except nvd.CveNotFound as exc:
            return Response({"error": str(exc)}, status=http.HTTP_404_NOT_FOUND)
        except nvd.NvdError as exc:
            return Response({"error": str(exc)}, status=http.HTTP_502_BAD_GATEWAY)

        data = nvd.apply_cve(
            {
                "cvss_score": vuln.cvss_score, "cvss_vector": vuln.cvss_vector, "severity": vuln.severity,
                "description": vuln.description, "references": vuln.references, "cve_id": vuln.cve_id,
                "service": vuln.service,
            },
            info,
        )
        scoring.finalise(data)
        for field in ("cvss_score", "cvss_vector", "severity", "description", "references", "risk_score"):
            setattr(vuln, field, data[field])
        vuln.save(update_fields=["cvss_score", "cvss_vector", "severity", "description", "references", "risk_score"])
        return Response(self.get_serializer(vuln).data)
