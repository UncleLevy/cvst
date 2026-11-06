from django.urls import path

from .views import ScanReportPdfView, ScanReportView

urlpatterns = [
    path("scans/<int:scan_id>/", ScanReportView.as_view(), name="scan-report"),
    path("scans/<int:scan_id>/pdf/", ScanReportPdfView.as_view(), name="scan-report-pdf"),
]
