from rest_framework import viewsets, permissions
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from config.pagination import FlexiblePageNumberPagination


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API de solo lectura para el log de auditoría. Solo accesible por Admin."""
    serializer_class = AuditLogSerializer
    pagination_class = FlexiblePageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "admin":
            return AuditLog.objects.none()

        qs = AuditLog.objects.all()
        params = self.request.query_params

        entity_type = params.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        entity_id = params.get("entity_id")
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        field_name = params.get("field_name")
        if field_name:
            qs = qs.filter(field_name=field_name)

        user_email = params.get("user_email")
        if user_email:
            qs = qs.filter(user_email__icontains=user_email)

        action = params.get("action")
        if action:
            qs = qs.filter(action=action)

        date_from = params.get("date_from")
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = params.get("date_to")
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        return qs
