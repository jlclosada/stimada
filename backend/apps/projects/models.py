from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProjectStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    available_on_creation = models.BooleanField(
        default=False,
        verbose_name="Disponible al crear",
        help_text="Si está activo, este estado puede seleccionarse como estado inicial al crear un proyecto.",
    )

    class Meta:
        verbose_name = "Estado de proyecto"
        verbose_name_plural = "Estados de proyecto"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    requires_profiles = models.BooleanField(
        default=False,
        verbose_name="Requiere red social y formato",
        help_text="Si está activo, al seleccionar este tipo de servicio se mostrarán las secciones de Red Social y Formato.",
    )

    class Meta:
        verbose_name = "Tipo de servicio"
        verbose_name_plural = "Tipos de servicio"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class SocialNetwork(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Red social"
        verbose_name_plural = "Redes sociales"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Format(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Formato"
        verbose_name_plural = "Formatos"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class EconomicModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Modalidad económica"
        verbose_name_plural = "Modalidades económicas"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ProductLogistics(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Logística de producto"
        verbose_name_plural = "Opciones de logística de producto"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ProductPickup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Recogida de producto"
        verbose_name_plural = "Opciones de recogida de producto"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class WhoRecords(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién graba"
        verbose_name_plural = "Opciones de quién graba"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class WhoReviews(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién revisa"
        verbose_name_plural = "Opciones de quién revisa"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class WhoPublishes(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Quién publica"
        verbose_name_plural = "Opciones de quién publica"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class WinStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Estado Win"
        verbose_name_plural = "Estados Win"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


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
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, verbose_name="Brief / Descripción")
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
    economic_model = models.ForeignKey(
        EconomicModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Modalidad económica",
    )
    product_logistics = models.ForeignKey(
        ProductLogistics,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Logística producto",
    )
    product_pickup = models.ForeignKey(
        ProductPickup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Recogida del producto",
    )
    who_records = models.ForeignKey(
        WhoRecords,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién graba",
    )
    who_reviews = models.ForeignKey(
        WhoReviews,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién revisa",
    )
    who_publishes = models.ForeignKey(
        WhoPublishes,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        verbose_name="Quién publica",
    )
    product_return = models.BooleanField(
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
    traffic_light = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3")],
        null=True,
        blank=True,
        verbose_name="Semáforo proyecto",
    )
    delayed = models.BooleanField(
        default=False,
        help_text="Flag paralelo: se activa si llega la fecha límite sin entregable.",
    )
    comments = models.TextField(blank=True, verbose_name="Comentarios")

    # Servicio: red social y formato (aplican a servicios "en perfiles")
    social_networks = models.ManyToManyField(
        SocialNetwork,
        blank=True,
        related_name="projects",
        verbose_name="Redes sociales",
    )
    formats = models.ManyToManyField(
        Format,
        blank=True,
        related_name="projects",
        verbose_name="Formatos",
    )

    # Propuesta económica
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Fee (€/contenido)",
    )
    num_contents = models.PositiveIntegerField(
        default=0,
        verbose_name="Nº de contenidos",
    )
    num_profiles = models.PositiveIntegerField(
        default=0,
        verbose_name="Nº de perfiles",
    )
    gifting = models.BooleanField(
        default=False,
        verbose_name="Gifting",
        help_text="Si está activo, Stimada invita al contenido y el importe final es 0 €.",
    )
    discount_active = models.BooleanField(
        default=False,
        verbose_name="Aplicar descuento",
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Descuento (%)",
    )

    # Precio
    tax_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def gross_price(self):
        """Precio antes de gifting/descuento: fee × nº contenidos × nº perfiles."""
        return (self.fee or Decimal("0")) * (self.num_contents or 0) * (self.num_profiles or 0)

    @property
    def final_price(self):
        """Precio efectivo tras aplicar gifting o descuento."""
        if self.gifting:
            return Decimal("0")
        bruto = self.gross_price
        if self.discount_active and self.discount_percentage:
            factor = Decimal("1") - (Decimal(self.discount_percentage) / Decimal("100"))
            return (bruto * factor).quantize(Decimal("0.01"))
        return bruto

    @property
    def total_price(self):
        return self.tax_base + self.taxes

    @property
    def is_active(self):
        """Derivado del estado: False si Cerrado."""
        if self.status and self.status.name.lower() == "cerrado":
            return False
        return True

    # Fechas
    sale_date = models.DateField(null=True, blank=True)
    service_date = models.DateField(null=True, blank=True, verbose_name="Fecha de inicio del servicio")
    product_arrival_date = models.DateField(null=True, blank=True, verbose_name="Fecha de llegada del producto")
    delivery_deadline = models.DateField(null=True, blank=True, verbose_name="Fecha límite de entrega")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de fin del proyecto")
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
        return f"{self.project_id} — {self.name}"

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
        # Derive tax_base from the economic proposal when available.
        if self.fee and self.num_contents and self.num_profiles:
            self.tax_base = self.final_price
        # Auto-calculate delivery_deadline: llegada producto + 14 days (for UGC services)
        if not self.delivery_deadline and self.product_arrival_date:
            if self.service_type and "ugc" in self.service_type.name.lower():
                self.delivery_deadline = self.product_arrival_date + timedelta(days=14)
        if not self.end_date and self.service_date:
            self.end_date = self.service_date + timedelta(days=14)
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
    is_substitute = models.BooleanField(
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
    comments = models.TextField(blank=True)
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
    title = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.url


class BriefingPhoto(models.Model):
    """Fotografía adjunta a un briefing."""
    briefing = models.ForeignKey(
        Briefing,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="briefings/photos/%Y/%m/")
    description = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.description or f"Foto {self.id}"


class Deliverable(models.Model):
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
        related_name="deliverables",
    )
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile",
        on_delete=models.CASCADE,
        related_name="deliverables",
    )
    file = models.FileField(upload_to="entregables/")
    description = models.TextField(blank=True)
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
        from_name = self.from_status.name if self.from_status else "—"
        to_name = self.to_status.name if self.to_status else "—"
        return f"{self.project.project_id}: {from_name} → {to_name}"

