from django.contrib import admin

from .models import Target


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ("name", "target_type", "value", "created_by", "is_active", "created_at")
    list_filter = ("target_type", "is_active")
    search_fields = ("name", "value")
