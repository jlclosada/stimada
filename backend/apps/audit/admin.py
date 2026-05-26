from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user_email", "entity_type", "entity_id", "field_name", "action"]
    list_filter = ["entity_type", "action", "field_name"]
    search_fields = ["user_email", "entity_repr", "field_name", "old_value", "new_value"]
    readonly_fields = [
        "user", "user_email", "entity_type", "entity_id", "entity_repr",
        "field_name", "old_value", "new_value", "reason", "action", "timestamp",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
