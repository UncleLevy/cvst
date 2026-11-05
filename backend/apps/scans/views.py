import logging

from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import is_admin

from .models import Scan
from .serializers import ScanSerializer
from .tasks import run_scan_task

logger = logging.getLogger(__name__)

SEVERITIES = ("critical", "high", "medium", "low", "info")


def enqueue_scan(scan: Scan) -> None:
    """Queue the scan; if the broker is unreachable, fail the scan visibly."""
    try:
        run_scan_task.delay(scan.id)
    except Exception as exc:  # noqa: BLE001 - e.g. Redis is not running
        logger.exception("Could not queue scan %s", scan.id)
        scan.status = "failed"
        scan.error_message = f"Could not queue scan (is Redis/Celery running?): {exc}"
        scan.finished_at = timezone.now()
        scan.save(update_fields=["status", "error_message", "finished_at"])


class ScanViewSet(viewsets.ModelViewSet):
    serializer_class = ScanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "scan_type", "target"]

    def get_queryset(self):
        qs = (
            Scan.objects.select_related("target")
            .annotate(vulnerability_count=Count("vulnerabilities"))
            .order_by("-created_at", "-id")  # annotate() drops Meta.ordering
        )
        if not is_admin(self.request.user):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def perform_create(self, serializer):
        scan = serializer.save(created_by=self.request.user, status="queued")
        enqueue_scan(scan)

    @action(detail=True, methods=["post"])
    def restart(self, request, pk=None):
        scan = self.get_object()
        if scan.status not in ("completed", "failed"):
            return Response(
                {"error": "Can only restart completed or failed scans"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        scan.status = "queued"
        scan.progress = 0
        scan.error_message = ""
        scan.started_at = None
        scan.finished_at = None
        scan.save()
        enqueue_scan(scan)
        return Response({"status": "restarted"})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Overall scan counts for the dashboard (not limited to one page)."""
        qs = Scan.objects.all()
        if not is_admin(request.user):
            qs = qs.filter(created_by=request.user)
        by_status = {r["status"]: r["n"] for r in qs.order_by().values("status").annotate(n=Count("id"))}
        total = sum(by_status.values())
        completed = by_status.get("completed", 0)
        failed = by_status.get("failed", 0)
        return Response(
            {"total": total, "completed": completed, "failed": failed, "active": total - completed - failed}
        )

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        scan = self.get_object()
        counts = dict.fromkeys(SEVERITIES, 0)
        rows = scan.vulnerabilities.values("severity").annotate(n=Count("id"))
        for row in rows:
            counts[row["severity"]] = row["n"]
        return Response({"scan": scan.id, "total": sum(counts.values()), "by_severity": counts})
