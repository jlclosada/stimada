"""
Servicio de auditoría para registrar cambios en campos sensibles.
Uso:
    from apps.audit.services import audit_changes
    audit_changes(request.user, instance, old_data, new_data)
"""
from apps.audit.models import AuditLog


# Campos auditados por entidad
AUDITED_FIELDS = {
    "content_maker": [
        "fee_instagram", "fee_tiktok", "iban", "dni_cif",
        "billing_address", "status", "cm_type", "contract_signed",
    ],
    "client": [
        "cif", "billing_address", "billing_email",
        "contract_signed", "contract", "status", "traffic_light",
    ],
    "brand": [
        "status", "client",
    ],
    "project": [
        "tax_base", "taxes", "status", "content_maker",
        "win_status", "end_date",
    ],
    "user": [
        "is_active", "role",
    ],
}


def get_entity_type(instance):
    """Determine entity type from model instance."""
    from apps.content_makers.models import ContentMakerProfile
    from apps.clients.models import ClientProfile, Brand
    from apps.projects.models import Project
    from apps.accounts.models import CustomUser

    model_map = {
        ContentMakerProfile: AuditLog.ENTITY_CONTENT_MAKER,
        ClientProfile: AuditLog.ENTITY_CLIENT,
        Brand: AuditLog.ENTITY_BRAND,
        Project: AuditLog.ENTITY_PROJECT,
        CustomUser: AuditLog.ENTITY_USER,
    }
    for model_class, entity_type in model_map.items():
        if isinstance(instance, model_class):
            return entity_type
    return None


def audit_changes(user, instance, old_data: dict, new_data: dict, reason: str = "", action: str = AuditLog.ACTION_UPDATE):
    """
    Compare old_data and new_data dicts, create audit logs for changes on audited fields.
    old_data/new_data should be dicts with field_name -> value.
    """
    entity_type = get_entity_type(instance)
    if not entity_type:
        return

    audited = AUDITED_FIELDS.get(entity_type, [])
    user_email = user.email if user else "system@stimada.com"
    entity_repr = str(instance)[:300]

    logs = []
    for field in audited:
        old_val = str(old_data.get(field, "")) if old_data.get(field) is not None else None
        new_val = str(new_data.get(field, "")) if new_data.get(field) is not None else None
        if old_val != new_val:
            logs.append(AuditLog(
                user=user,
                user_email=user_email,
                entity_type=entity_type,
                entity_id=instance.pk,
                entity_repr=entity_repr,
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                reason=reason,
                action=action,
            ))

    if logs:
        AuditLog.objects.bulk_create(logs)
    return logs


def audit_status_override(user, project, old_status_name: str, new_status_name: str, reason: str):
    """Specialized audit for manual project status override."""
    user_email = user.email if user else "system@stimada.com"
    AuditLog.objects.create(
        user=user,
        user_email=user_email,
        entity_type=AuditLog.ENTITY_PROJECT,
        entity_id=project.pk,
        entity_repr=str(project)[:300],
        field_name="status",
        old_value=old_status_name,
        new_value=new_status_name,
        reason=reason,
        action=AuditLog.ACTION_OVERRIDE,
    )


def audit_cm_assignment_change(user, project, field_name: str, old_value: str, new_value: str):
    """Audit changes to CM assignments (principales/suplentes)."""
    user_email = user.email if user else "system@stimada.com"
    AuditLog.objects.create(
        user=user,
        user_email=user_email,
        entity_type=AuditLog.ENTITY_PROJECT,
        entity_id=project.pk,
        entity_repr=str(project)[:300],
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        action=AuditLog.ACTION_UPDATE,
    )


def audit_user_lifecycle(user, target_user, action_type: str, details: str = ""):
    """Audit user creation, deactivation, and role changes."""
    user_email = user.email if user else "system@stimada.com"
    AuditLog.objects.create(
        user=user,
        user_email=user_email,
        entity_type=AuditLog.ENTITY_USER,
        entity_id=target_user.pk,
        entity_repr=str(target_user)[:300],
        field_name="lifecycle",
        old_value=None,
        new_value=details,
        action=action_type,
    )
