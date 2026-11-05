from rest_framework import serializers

from apps.core.permissions import is_admin
from apps.targets.serializers import TargetSerializer

from .models import Scan


class ScanSerializer(serializers.ModelSerializer):
    target_detail = TargetSerializer(source="target", read_only=True)
    # Present when the queryset is annotated (list/retrieve); skipped otherwise.
    vulnerability_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Scan
        fields = [
            "id",
            "name",
            "target",
            "target_detail",
            "scan_type",
            "status",
            "progress",
            "started_at",
            "finished_at",
            "error_message",
            "created_by",
            "created_at",
            "vulnerability_count",
        ]
        read_only_fields = [
            "id",
            "status",
            "progress",
            "started_at",
            "finished_at",
            "error_message",
            "created_by",
            "created_at",
        ]

    def validate_target(self, target):
        user = self.context["request"].user
        if not target.is_active:
            raise serializers.ValidationError("This target has been removed.")
        if not is_admin(user) and target.created_by_id != user.id:
            raise serializers.ValidationError("You can only scan your own targets.")
        return target
