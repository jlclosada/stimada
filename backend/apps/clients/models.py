from django.conf import settings
from django.db import models


class ClientType(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tipo de cliente"
        verbose_name_plural = "Tipos de cliente"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ClientProfile(models.Model):
    # Cuenta de usuario
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="client_profile",
    )

    # Identificación
    nombre_cliente = models.CharField(max_length=200, verbose_name="Nombre comercial")
    cliente_id = models.CharField(max_length=50, unique=True, blank=True)
    tipo_cliente = models.ForeignKey(
        ClientType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clientes",
    )
    web_instagram = models.URLField(max_length=300, blank=True, verbose_name="Web / Instagram")

    # Contacto
    persona_contacto = models.CharField(max_length=200, blank=True, verbose_name="Persona de contacto")
    email_contacto = models.EmailField(blank=True, verbose_name="Email de contacto")
    telefono = models.CharField(max_length=30, blank=True)

    # Facturación
    nombre_facturacion = models.CharField(max_length=200, verbose_name="Razón social")
    cif = models.CharField(max_length=20)
    email_facturacion = models.EmailField()
    direccion_facturacion = models.TextField()
    codigo_postal = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100, default="España")

    # Contrato
    contrato_firmado = models.BooleanField(default=False)
    contrato = models.FileField(upload_to="contratos/clientes/", null=True, blank=True)

    # Estado y evaluación
    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
    ]
    SEMAFORO_CHOICES = [(1, "1"), (2, "2"), (3, "3")]

    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO
    )
    semaforo_cliente = models.PositiveSmallIntegerField(
        choices=SEMAFORO_CHOICES, null=True, blank=True,
        verbose_name="Semáforo cliente",
    )
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")

    # Agencia / Marca
    es_agencia = models.BooleanField(
        default=False,
        help_text="Si es agencia, puede tener múltiples marcas asociadas.",
    )

    # Content Makers favoritas
    favorite_cms = models.ManyToManyField(
        "content_makers.ContentMakerProfile",
        blank=True,
        related_name="favorited_by_clients",
    )

    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clientes_creados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre_cliente"]

    @staticmethod
    def generate_next_id():
        """Generate the next sequential numeric client ID (zero-padded to 5 digits)."""
        import re
        ids = ClientProfile.objects.values_list("cliente_id", flat=True)
        nums = [int(m.group()) for cid in ids if (m := re.search(r"\d+", cid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.cliente_id:
            self.cliente_id = self.generate_next_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente_id} — {self.nombre_cliente}"


class Brand(models.Model):
    """Marca asociada a un cliente (agencia). Si el cliente es marca propia, se crea una marca con su mismo nombre."""
    ESTADO_ACTIVA = "activa"
    ESTADO_INACTIVA = "inactiva"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVA, "Activa"),
        (ESTADO_INACTIVA, "Inactiva"),
    ]

    brand_id = models.CharField(max_length=50, unique=True, blank=True)
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="brands",
    )
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Marca")
    tipo_marca = models.ForeignKey(
        ClientType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="marcas",
        verbose_name="Tipo de marca",
    )
    web_instagram = models.URLField(max_length=300, blank=True, verbose_name="Web / Instagram")
    notas = models.TextField(blank=True)
    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES, default=ESTADO_ACTIVA
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]
        unique_together = ["client", "nombre"]

    @staticmethod
    def generate_next_id():
        """Generate the next sequential brand ID (zero-padded to 5 digits)."""
        import re
        ids = Brand.objects.values_list("brand_id", flat=True)
        nums = [int(m.group()) for bid in ids if (m := re.search(r"\d+", bid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.brand_id:
            self.brand_id = self.generate_next_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.client.nombre_cliente})"
