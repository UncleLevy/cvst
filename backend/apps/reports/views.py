from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import is_admin
from apps.scans.models import Scan

from .builder import build_report, render_pdf


class _ScanReportBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_scan(self, request, scan_id):
        qs = Scan.objects.select_related("target")
        if not is_admin(request.user):
            qs = qs.filter(created_by=request.user)
        return get_object_or_404(qs, pk=scan_id)

    def get_report(self, request, scan_id):
        scan = self.get_scan(request, scan_id)
        if scan.status != "completed":
            return None, Response({"error": "A report is available once the scan has completed."}, status=409)
        return build_report(scan), None


class ScanReportView(_ScanReportBase):
    """GET /api/reports/scans/<id>/  - prioritised findings as JSON."""

    def get(self, request, scan_id):
        report, error = self.get_report(request, scan_id)
        return error or Response(report)


class ScanReportPdfView(_ScanReportBase):
    """GET /api/reports/scans/<id>/pdf/  - downloadable PDF."""

    def get(self, request, scan_id):
        report, error = self.get_report(request, scan_id)
        if error:
            return error
        response = HttpResponse(render_pdf(report), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="cvst-report-scan-{scan_id}.pdf"'
        return response
