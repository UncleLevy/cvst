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


SAVE_FIELDS = (
    "cve_id", "title", "description", "severity", "cvss_score", "port",
    "service", "evidence", "recommendation", "references",
)


def _save_findings(scan: Scan, findings: list[dict], source: str) -> None:
    Vulnerability.objects.bulk_create(
        Vulnerability(scan=scan, source=source, **{k: f[k] for k in SAVE_FIELDS if k in f})
        for f in findings
    )


def _run_real_scan(scan: Scan) -> None:
    """Run the real scanners for this scan type and store what they found."""
    # Imported lazily so the app still boots without python-nmap/Nmap.
    from apps.detection.nmap_scanner import run_nmap_discovery
    from apps.detection.web_scanner import run_web_scan

    if scan.scan_type in {"network", "full"}:
        _save_findings(scan, run_nmap_discovery(target_host(scan.target)), "nmap")
    _update(scan, status="analysing", progress=50)

    if scan.scan_type in {"web", "full"}:
        _save_findings(scan, run_web_scan(scan.target), "web")


def _run_simulated_scan(scan: Scan) -> None:
    """Demo-mode findings. Clearly labelled so they are never mistaken for real results."""
    time.sleep(3)  # simulated discovery
    _update(scan, status="analysing", progress=50)
    time.sleep(2)  # simulated analysis
    _save_findings(scan, simulated_findings(scan), "simulated")


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

        if settings.CVST_REAL_SCANS:
            _run_real_scan(scan)
        else:
            _run_simulated_scan(scan)

        _update(scan, status="reporting", progress=85)
        _update(scan, status="completed", progress=100, finished_at=timezone.now())
        return f"Scan {scan_id} completed"

    except Exception as exc:  # noqa: BLE001 - record any failure on the scan
        scan.vulnerabilities.all().delete()  # never leave a half-finished result set
        _update(scan, status="failed", error_message=str(exc)[:1000], finished_at=timezone.now())
        raise
