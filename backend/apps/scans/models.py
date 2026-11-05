from django.conf import settings
from django.db import models

from apps.targets.models import Target


class Scan(models.Model):
    STATUS_CHOICES = (
        ("idle", "Idle"),
        ("queued", "Queued"),
        ("scanning", "Scanning"),
        ("analysing", "Analysing"),
        ("reporting", "Reporting"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    SCAN_TYPES = (
        ("network", "Network Discovery"),
        ("web", "Web Application"),
        ("full", "Full Assessment"),
    )

    name = models.CharField(max_length=255)
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name="scans")
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPES, default="network")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="scans",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    progress = models.PositiveIntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.status}"
