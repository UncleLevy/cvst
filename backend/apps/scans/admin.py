from django.contrib import admin

from .models import Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("name", "target", "scan_type", "status", "progress", "created_by", "created_at")
    list_filter = ("status", "scan_type")
    search_fields = ("name", "target__name", "target__value")
