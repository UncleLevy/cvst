from django.db import models

from apps.scans.models import Scan


class Vulnerability(models.Model):
    SEVERITY_CHOICES = (
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("info", "Informational"),
    )

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="vulnerabilities")
    cve_id = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="info")
    cvss_score = models.FloatField(null=True, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    service = models.CharField(max_length=100, blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cvss_score", "-discovered_at"]
        verbose_name_plural = "vulnerabilities"

    def __str__(self):
        return f"{self.cve_id or self.title} ({self.severity})"
