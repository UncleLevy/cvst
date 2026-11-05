from rest_framework import serializers

from .models import Target
from .validators import validate_target_value


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = [
            "id",
            "name",
            "target_type",
            "value",
            "description",
            "is_active",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate(self, attrs):
        target_type = attrs.get("target_type", getattr(self.instance, "target_type", None))
        value = attrs.get("value", getattr(self.instance, "value", None))
        if value is not None:
            try:
                attrs["value"] = validate_target_value(target_type, value)
            except ValueError as exc:
                raise serializers.ValidationError({"value": str(exc)}) from None
        return attrs
