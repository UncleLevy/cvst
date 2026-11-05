from django.contrib import admin

from .models import Vulnerability


@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ("title", "cve_id", "severity", "cvss_score", "port", "scan", "discovered_at")
    list_filter = ("severity",)
    search_fields = ("title", "cve_id")
