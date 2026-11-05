import time

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.targets.validators import target_host
from apps.vulnerabilities.models import Vulnerability

from .models import Scan
from .simulation import simulated_findings


def _update(scan: Scan, **fields) -> None:
    for key, value in fields.items():
        setattr(scan, key, value)
    scan.save(update_fields=list(fields))


def _create_simulated_findings(scan: Scan) -> None:
    """Demo-mode findings. Clearly labelled so they are never mistaken for real results."""
    Vulnerability.objects.bulk_create(
        Vulnerability(scan=scan, **finding) for finding in simulated_findings(scan)
    )


@shared_task
def run_scan_task(scan_id: int) -> str:
    scan = Scan.objects.select_related("target").filter(id=scan_id).first()
    if scan is None:
        return f"Scan {scan_id} not found"

    try:
        # Restarted scans begin with a clean slate.
        scan.vulnerabilities.all().delete()
        _update(
            scan,
            status="scanning",
            progress=10,
            started_at=timezone.now(),
            finished_at=None,
            error_message="",
        )

        use_nmap = settings.CVST_USE_NMAP and scan.scan_type in {"network", "full"}

        if use_nmap:
            # Imported lazily so the app still boots without python-nmap/Nmap.
            from apps.detection.nmap_scanner import run_nmap_discovery

            run_nmap_discovery(scan, target_host(scan.target))
            _update(scan, status="analysing", progress=40)
        else:
            time.sleep(3)  # simulated discovery
            _update(scan, status="analysing", progress=40)
            time.sleep(2)  # simulated analysis
            _create_simulated_findings(scan)

        _update(scan, status="reporting", progress=80)
        time.sleep(1)
        _update(scan, status="completed", progress=100, finished_at=timezone.now())
        return f"Scan {scan_id} completed"

    except Exception as exc:  # noqa: BLE001 - record any failure on the scan
        _update(scan, status="failed", error_message=str(exc), finished_at=timezone.now())
        raise
