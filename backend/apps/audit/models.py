from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Registro inmutable de cambios sobre datos sensibles.
    No se puede editar ni eliminar una vez creado.
    """

    ENTITY_CONTENT_MAKER = "content_maker"
    ENTITY_CLIENT = "client"
    ENTITY_BRAND = "brand"
    ENTITY_PROJECT = "project"
    ENTITY_USER = "user"
    ENTITY_CHOICES = [
        (ENTITY_CONTENT_MAKER, "Content Maker"),
        (ENTITY_CLIENT, "Cliente"),
        (ENTITY_BRAND, "Marca"),
        (ENTITY_PROJECT, "Proyecto"),
        (ENTITY_USER, "Usuario"),
    ]

    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_OVERRIDE = "override"
    ACTION_CHOICES = [
        (ACTION_CREATE, "Creación"),
        (ACTION_UPDATE, "Actualización"),
        (ACTION_DELETE, "Eliminación"),
        (ACTION_OVERRIDE, "Override manual"),
    ]

    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    user_email = models.EmailField(
        help_text="Copia del email del usuario en el momento del cambio (inmutable)."
    )

    # What
    entity_type = models.CharField(max_length=30, choices=ENTITY_CHOICES)
    entity_id = models.PositiveIntegerField()
    entity_repr = models.CharField(
        max_length=300,
        blank=True,
        help_text="Representación legible de la entidad en el momento del cambio.",
    )
    field_name = models.CharField(max_length=100)

    # Values
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    # Override manual reason (for project status overrides)
    reason = models.TextField(
        blank=True,
        help_text="Motivo del cambio (obligatorio en override manual de estado de proyecto).",
    )

    # Action type
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default=ACTION_UPDATE)

    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["user"]),
            models.Index(fields=["field_name"]),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user_email} → {self.entity_type}#{self.entity_id}.{self.field_name}"

    def save(self, *args, **kwargs):
        # Only allow creation, not update
        if self.pk:
            raise ValueError("Los registros de auditoría son inmutables y no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Los registros de auditoría son inmutables y no se pueden eliminar.")
