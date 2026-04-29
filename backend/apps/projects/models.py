from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProjectStatus(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Estado de proyecto"
        verbose_name_plural = "Estados de proyecto"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ServiceType(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tipo de servicio"
        verbose_name_plural = "Tipos de servicio"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Project(models.Model):
    CM_SELECTION_DEFINED = "defined"
    CM_SELECTION_RECOMMENDED = "recommended"
    CM_SELECTION_CLIENT_CHOOSES = "client_chooses"
    CM_SELECTION_CHOICES = [
        (CM_SELECTION_DEFINED, "Definida"),
        (CM_SELECTION_RECOMMENDED, "Recomendadas"),
        (CM_SELECTION_CLIENT_CHOOSES, "El cliente elige"),
    ]

    # Identificación
    project_id = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)

    # Relaciones
    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.PROTECT,
        related_name="projects",
    )
    brand = models.ForeignKey(
        "clients.Brand",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    status = models.ForeignKey(
        ProjectStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    service_type = models.ForeignKey(
        ServiceType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )

    # Precio
    base_imponible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def precio_total(self):
        return self.base_imponible + self.impuestos

    # Fechas
    fecha_venta = models.DateField(null=True, blank=True)
    fecha_servicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    # Content Maker selection
    cm_selection_mode = models.CharField(
        max_length=20,
        choices=CM_SELECTION_CHOICES,
        default=CM_SELECTION_CLIENT_CHOOSES,
    )
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects_assigned",
        help_text="Content maker definitiva asignada al proyecto.",
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project_id} — {self.nombre}"

    def save(self, *args, **kwargs):
        if not self.fecha_fin and self.fecha_venta:
            self.fecha_fin = self.fecha_venta + timedelta(days=14)
        super().save(*args, **kwargs)


class ProjectContentMaker(models.Model):
    """Content makers recomendadas o candidatas para un proyecto."""
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_SELECTED = "selected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_ACCEPTED, "Aceptada"),
        (STATUS_REJECTED, "Rechazada"),
        (STATUS_SELECTED, "Seleccionada por cliente"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="content_makers",
    )
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile",
        on_delete=models.CASCADE,
        related_name="project_participations",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    is_recommended = models.BooleanField(default=False)
    note = models.TextField(blank=True, help_text="Nota interna sobre la recomendación.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Content Maker del proyecto"
        verbose_name_plural = "Content Makers del proyecto"
        unique_together = ["project", "content_maker"]

    def __str__(self):
        return f"{self.content_maker} → {self.project.project_id}"


class Notification(models.Model):
    TYPE_PROJECT_CM_SELECT = "project_cm_select"
    TYPE_PROJECT_CM_REQUEST = "project_cm_request"
    TYPE_PROJECT_CM_ACCEPTED = "project_cm_accepted"
    TYPE_PROJECT_CM_REJECTED = "project_cm_rejected"
    TYPE_CHOICES = [
        (TYPE_PROJECT_CM_SELECT, "Seleccionar Content Maker"),
        (TYPE_PROJECT_CM_REQUEST, "Solicitud a Content Maker"),
        (TYPE_PROJECT_CM_ACCEPTED, "Content Maker aceptó"),
        (TYPE_PROJECT_CM_REJECTED, "Content Maker rechazó"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] → {self.recipient.email}"
