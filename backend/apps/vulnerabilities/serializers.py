from rest_framework import serializers

from .models import Vulnerability


class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            "id",
            "scan",
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
