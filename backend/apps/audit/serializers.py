from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "user_email", "entity_type", "entity_id", "entity_repr",
            "field_name", "old_value", "new_value", "reason", "action", "timestamp",
        ]
