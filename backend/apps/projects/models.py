from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProjectStatus(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Estado de proyecto"
        verbose_name_plural = "Estados de proyecto"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ServiceType(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de servicio"
        verbose_name_plural = "Tipos de servicio"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ModalidadEconomica(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Modalidad económica"
        verbose_name_plural = "Modalidades económicas"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class LogisticaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Logística de producto"
        verbose_name_plural = "Opciones de logística de producto"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class RecogidaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Recogida de producto"
        verbose_name_plural = "Opciones de recogida de producto"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class QuienGraba(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién graba"
        verbose_name_plural = "Opciones de quién graba"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class QuienRevisa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién revisa"
        verbose_name_plural = "Opciones de quién revisa"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class QuienPublica(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién publica"
        verbose_name_plural = "Opciones de quién publica"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class WinStatus(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Estado Win"
        verbose_name_plural = "Estados Win"
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
    project_id = models.CharField(max_length=50, unique=True, blank=True)
    nombre = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True, verbose_name="Brief / Descripción")
    is_draft = models.BooleanField(default=False)

    # Relaciones
    client = models.ForeignKey(
        "clients.ClientProfile",
        null=True,
        blank=True,
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

    # Modalidad operativa
    modalidad_economica = models.ForeignKey(
        ModalidadEconomica,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Modalidad económica",
    )
    logistica_producto = models.ForeignKey(
        LogisticaProducto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Logística producto",
    )
    recogida_producto = models.ForeignKey(
        RecogidaProducto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Recogida del producto",
    )
    quien_graba = models.ForeignKey(
        QuienGraba,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién graba",
    )
    quien_revisa = models.ForeignKey(
        QuienRevisa,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién revisa",
    )
    quien_publica = models.ForeignKey(
        QuienPublica,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién publica",
    )
    devolucion_producto = models.BooleanField(
        default=False,
        verbose_name="Devolución de producto",
    )

    # Estado y pipeline
    win_status = models.ForeignKey(
        WinStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Win?",
    )
    semaforo_proyecto = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3")],
        null=True,
        blank=True,
        verbose_name="Semáforo proyecto",
    )
    retrasado = models.BooleanField(
        default=False,
        help_text="Flag paralelo: se activa si llega la fecha límite sin entregable.",
    )
    comentarios = models.TextField(blank=True, verbose_name="Comentarios")

    # Precio
    base_imponible = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def precio_total(self):
        return self.base_imponible + self.impuestos

    @property
    def is_active(self):
        """Derivado del estado: False si Cerrado."""
        if self.status and self.status.nombre.lower() == "cerrado":
            return False
        return True

    # Fechas
    fecha_venta = models.DateField(null=True, blank=True)
    fecha_servicio = models.DateField(null=True, blank=True, verbose_name="Fecha de inicio del servicio")
    fecha_llegada_producto = models.DateField(null=True, blank=True, verbose_name="Fecha de llegada del producto")
    fecha_limite_entrega = models.DateField(null=True, blank=True, verbose_name="Fecha límite de entrega")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de fin del proyecto")

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

    @staticmethod
    def generate_next_id():
        """Generate the next sequential numeric project ID (zero-padded to 5 digits)."""
        import re
        ids = Project.objects.values_list("project_id", flat=True)
        nums = [int(m.group()) for pid in ids if (m := re.search(r"\d+", pid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.project_id:
            self.project_id = self.generate_next_id()
        # Auto-calculate fecha_limite_entrega: llegada producto + 14 days (for UGC services)
        if not self.fecha_limite_entrega and self.fecha_llegada_producto:
            if self.service_type and "ugc" in self.service_type.nombre.lower():
                self.fecha_limite_entrega = self.fecha_llegada_producto + timedelta(days=14)
        if not self.fecha_fin and self.fecha_servicio:
            self.fecha_fin = self.fecha_servicio + timedelta(days=14)
        # Auto-inherit client from brand
        if self.brand_id and not self.client_id:
            self.client = self.brand.client
        super().save(*args, **kwargs)


class ProjectContentMaker(models.Model):
    """Content makers recomendadas o candidatas para un proyecto."""
    STATUS_RECOMMENDED = "recommended"
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_SELECTED = "selected"
    STATUS_CHOICES = [
        (STATUS_RECOMMENDED, "Recomendada"),
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
    is_suplente = models.BooleanField(
        default=False,
        help_text="Si es suplente, recibe la solicitud automáticamente si una Principal rechaza.",
    )
    note = models.TextField(blank=True, help_text="Nota interna sobre la recomendación.")
    responded_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp de aceptación/rechazo.")
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
    TYPE_BRIEFING_SUBMITTED = "briefing_submitted"
    TYPE_DEADLINE_REMINDER = "deadline_reminder"
    TYPE_DEADLINE_OVERDUE = "deadline_overdue"
    TYPE_DELIVERY_UPLOADED = "delivery_uploaded"
    TYPE_REVISION_REQUESTED = "revision_requested"
    TYPE_DELIVERY_APPROVED = "delivery_approved"
    TYPE_CM_PROMOTED = "cm_promoted"
    TYPE_ACCOUNT_CREATED = "account_created"
    TYPE_STATUS_CHANGED = "status_changed"
    TYPE_CHOICES = [
        (TYPE_PROJECT_CM_SELECT, "Seleccionar Content Maker"),
        (TYPE_PROJECT_CM_REQUEST, "Solicitud a Content Maker"),
        (TYPE_PROJECT_CM_ACCEPTED, "Content Maker aceptó"),
        (TYPE_PROJECT_CM_REJECTED, "Content Maker rechazó"),
        (TYPE_BRIEFING_SUBMITTED, "Briefing enviado"),
        (TYPE_DEADLINE_REMINDER, "Recordatorio pre-entrega"),
        (TYPE_DEADLINE_OVERDUE, "Entrega vencida"),
        (TYPE_DELIVERY_UPLOADED, "Entregable subido"),
        (TYPE_REVISION_REQUESTED, "Revisión solicitada"),
        (TYPE_DELIVERY_APPROVED, "Entregable aprobado"),
        (TYPE_CM_PROMOTED, "Suplente promovida"),
        (TYPE_ACCOUNT_CREATED, "Cuenta creada"),
        (TYPE_STATUS_CHANGED, "Estado del proyecto cambiado"),
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


class Briefing(models.Model):
    """Briefing del cliente para cada content maker en un proyecto."""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="briefings",
    )
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile",
        on_delete=models.CASCADE,
        related_name="briefings",
    )
    comentarios = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="briefings_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Briefing"
        verbose_name_plural = "Briefings"
        unique_together = ["project", "content_maker"]

    def __str__(self):
        return f"Briefing: {self.project.project_id} → {self.content_maker}"


class BriefingLink(models.Model):
    """Enlace de referencia adjunto a un briefing."""
    briefing = models.ForeignKey(
        Briefing,
        on_delete=models.CASCADE,
        related_name="links",
    )
    url = models.URLField(max_length=500)
    titulo = models.CharField(max_length=200, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.url


class BriefingPhoto(models.Model):
    """Fotografía adjunta a un briefing."""
    briefing = models.ForeignKey(
        Briefing,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    imagen = models.ImageField(upload_to="briefings/photos/%Y/%m/")
    descripcion = models.CharField(max_length=300, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.descripcion or f"Foto {self.id}"


class Entregable(models.Model):
    """Entregable subido por una Content Maker para un proyecto."""
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REVISION = "revision"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente de revisión"),
        (STATUS_APPROVED, "Aprobado"),
        (STATUS_REVISION, "Requiere cambios"),
        (STATUS_REJECTED, "Rechazado"),
    ]

    MAX_REVISION_ROUNDS = 2

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="entregables",
    )
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile",
        on_delete=models.CASCADE,
        related_name="entregables",
    )
    archivo = models.FileField(upload_to="entregables/")
    descripcion = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    revision_round = models.PositiveSmallIntegerField(
        default=1,
        help_text="Ronda de revisión actual (máximo 2).",
    )
    revision_notes = models.TextField(
        blank=True,
        help_text="Notas de la PM para la revisión.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entregables_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de publicación del contenido.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entregable"
        verbose_name_plural = "Entregables"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Entregable: {self.project.project_id} → {self.content_maker} (R{self.revision_round})"

    @property
    def can_request_revision(self):
        """Only allow revision if we haven't exceeded max rounds."""
        return self.revision_round < self.MAX_REVISION_ROUNDS


class StatusChangeLog(models.Model):
    """Log de cambios de estado del proyecto (automáticos y manuales)."""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="status_changes",
    )
    from_status = models.ForeignKey(
        ProjectStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    to_status = models.ForeignKey(
        ProjectStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    is_manual = models.BooleanField(
        default=False,
        help_text="True si el cambio fue forzado manualmente por Admin/Empleada.",
    )
    reason = models.TextField(
        blank=True,
        help_text="Motivo obligatorio cuando es override manual.",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="status_changes_made",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cambio de estado"
        verbose_name_plural = "Cambios de estado"
        ordering = ["-timestamp"]

    def __str__(self):
        from_name = self.from_status.nombre if self.from_status else "—"
        to_name = self.to_status.nombre if self.to_status else "—"
        return f"{self.project.project_id}: {from_name} → {to_name}"

