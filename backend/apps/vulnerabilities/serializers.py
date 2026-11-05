from rest_framework import serializers

from .models import Vulnerability


class VulnerabilitySerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)
    target_value = serializers.CharField(source="scan.target.value", read_only=True)

    class Meta:
        model = Vulnerability
        fields = [
            "id",
            "scan",
            "scan_name",
            "target_value",
            "cve_id",
            "title",
            "description",
            "severity",
            "cvss_score",
            "port",
            "service",
            "discovered_at",
        ]
        read_only_fields = fields
