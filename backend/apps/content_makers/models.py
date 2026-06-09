from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ContentMakerStatus(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Estado de Content Maker"
        verbose_name_plural = "Estados de Content Maker"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ContentMakerType(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tipo de Content Maker"
        verbose_name_plural = "Tipos de Content Maker"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class DesempenoOption(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opción de desempeño"
        verbose_name_plural = "Opciones de desempeño"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class TallajeCategory(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    campo = models.CharField(
        max_length=30, unique=True,
        help_text="Nombre del campo en el perfil (ej: talla_arriba, talla_abajo, talla_pie)",
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Categoría de tallaje"
        verbose_name_plural = "Categorías de tallaje"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class TallajeOption(models.Model):
    categoria = models.ForeignKey(
        TallajeCategory, on_delete=models.CASCADE, related_name="opciones",
    )
    valor = models.CharField(max_length=20)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opción de tallaje"
        verbose_name_plural = "Opciones de tallaje"
        ordering = ["categoria", "orden"]
        unique_together = ["categoria", "valor"]

    def __str__(self):
        return f"{self.categoria.nombre} — {self.valor}"


class ContentMakerProfile(models.Model):
    # Tipo de perfil (Content Maker vs Colaborador)
    TIPO_CONTENT_MAKER = "content_maker"
    TIPO_COLABORADOR = "colaborador"
    TIPO_CHOICES = [
        (TIPO_CONTENT_MAKER, "Content Maker"),
        (TIPO_COLABORADOR, "Colaborador"),
    ]

    # Identificador Stimada
    stimada_id = models.CharField(max_length=30, unique=True, blank=True)

    # Datos personales
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150, blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_CONTENT_MAKER,
        db_index=True,
    )
    tipo_cm = models.CharField(max_length=50, blank=True)
    sexo = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, blank=True)

    # Valoración interna
    desempeno = models.CharField(max_length=200, blank=True)
    calidad_contenido = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    desempeno_opciones = models.ManyToManyField(
        "DesempenoOption", blank=True, related_name="content_makers",
    )
    apariencia = models.CharField(max_length=50, blank=True)
    es_mama = models.BooleanField(default=False)
    categorias_contenido = models.CharField(max_length=200, blank=True)

    # Relación con Stimada
    sigue_stimada = models.BooleanField(default=False)
    stimada_en_bio = models.BooleanField(default=False)
    contrato_firmado = models.BooleanField(default=False)

    # Instagram
    fee_instagram = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    categoria_seguidores_ig = models.CharField(max_length=50, blank=True)
    seguidores_instagram = models.IntegerField(null=True, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    link_instagram = models.URLField(max_length=300, blank=True)

    # TikTok
    fee_tiktok = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    categoria_seguidores_tt = models.CharField(max_length=50, blank=True)
    seguidores_tiktok = models.IntegerField(null=True, blank=True)
    tiktok_handle = models.CharField(max_length=100, blank=True)
    link_tiktok = models.URLField(max_length=300, blank=True)

    # Tallaje
    talla_arriba = models.CharField(max_length=50, blank=True)
    talla_abajo = models.CharField(max_length=50, blank=True)
    talla_pie = models.CharField(max_length=50, blank=True)
    altura_medidas = models.TextField(blank=True)

    # Contacto y facturación
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion_facturacion = models.TextField(blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    dni_cif = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=40, blank=True)

    # Foto de perfil
    foto = models.ImageField(upload_to="content_makers/fotos/", null=True, blank=True)

    # Notas
    comentarios = models.TextField(blank=True)

    # Vinculación con cuenta de usuario (null hasta que se crea la cuenta)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_maker_profile",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Content Maker"
        verbose_name_plural = "Content Makers"
        ordering = ["stimada_id"]

    @staticmethod
    def generate_next_id():
        """Generate the next sequential numeric CM ID (zero-padded to 5 digits)."""
        import re
        ids = ContentMakerProfile.objects.values_list("stimada_id", flat=True)
        nums = [int(m.group()) for sid in ids if (m := re.search(r"\d+", sid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.stimada_id:
            self.stimada_id = self.generate_next_id()
        # Normalize handles (strip "@" and whitespace) before persisting.
        self.instagram_handle = self._normalize_handle(self.instagram_handle)
        self.tiktok_handle = self._normalize_handle(self.tiktok_handle)
        # Auto-generate links from handles.
        self.link_instagram = self._build_instagram_url(self.instagram_handle)
        self.link_tiktok = self._build_tiktok_url(self.tiktok_handle)
        # Auto-compute follower category from follower count.
        self.categoria_seguidores_ig = self._compute_followers_category(
            self.seguidores_instagram
        )
        self.categoria_seguidores_tt = self._compute_followers_category(
            self.seguidores_tiktok
        )
        super().save(*args, **kwargs)

    # ─── Helpers: handles & links ──────────────────────────────────────────────
    @staticmethod
    def _normalize_handle(handle):
        """Strip leading '@' and whitespace from a social handle."""
        if not handle:
            return ""
        return handle.strip().lstrip("@").strip()

    @staticmethod
    def _build_instagram_url(handle):
        if not handle:
            return ""
        return f"https://www.instagram.com/{handle}/"

    @staticmethod
    def _build_tiktok_url(handle):
        if not handle:
            return ""
        return f"https://www.tiktok.com/@{handle}"

    # Follower range definitions (in order). The first range whose `max` is
    # greater than or equal to the count wins; the last is the open-ended one.
    FOLLOWER_RANGES = [
        (1_000, "<1k"),
        (4_000, "1k – 4k"),
        (8_000, "4k – 8k"),
        (14_000, "8k – 14k"),
        (19_000, "14k – 19k"),
        (28_000, "19k – 28k"),
        (35_000, "28k – 35k"),
        (50_000, "35k – 50k"),
        (100_000, "50k – 100k"),
    ]
    FOLLOWER_RANGE_TOP = ">100k"

    @classmethod
    def _compute_followers_category(cls, count):
        if count is None or count == "":
            return ""
        try:
            n = int(count)
        except (TypeError, ValueError):
            return ""
        if n < 1_000:
            return "<1k"
        for upper, label in cls.FOLLOWER_RANGES[1:]:
            if n < upper:
                return label
        return cls.FOLLOWER_RANGE_TOP

    def __str__(self):
        return f"{self.stimada_id} — {self.nombre} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}".strip()

    @property
    def tiene_cuenta(self):
        return self.user_id is not None
