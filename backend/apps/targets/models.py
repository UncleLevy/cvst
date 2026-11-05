from django.conf import settings
from django.db import models


class Target(models.Model):
    TARGET_TYPES = (
        ("ip", "IP Address"),
        ("hostname", "Hostname"),
        ("url", "URL"),
        ("network", "Network Range"),
    )

    name = models.CharField(max_length=255)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    value = models.CharField(max_length=512)  # e.g. 192.168.1.10 or https://example.com
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="targets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.value})"
