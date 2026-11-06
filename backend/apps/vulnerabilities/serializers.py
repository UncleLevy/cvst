from rest_framework import serializers

from .models import Vulnerability
from .scoring import PRIORITIES


class VulnerabilitySerializer(serializers.ModelSerializer):
    priority = serializers.CharField(read_only=True)
    priority_label = serializers.SerializerMethodField()
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
            "cvss_vector",
            "risk_score",
            "priority",
            "priority_label",
            "port",
            "service",
            "source",
            "evidence",
            "recommendation",
            "references",
            "discovered_at",
        ]
        read_only_fields = fields

    def get_priority_label(self, obj) -> str:
        return PRIORITIES[obj.priority]
