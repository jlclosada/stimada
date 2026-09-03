from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ContentMakerStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Estado de Content Maker"
        verbose_name_plural = "Estados de Content Maker"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ContentMakerType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tipo de Content Maker"
        verbose_name_plural = "Tipos de Content Maker"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class PerformanceOption(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opción de desempeño"
        verbose_name_plural = "Opciones de desempeño"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class SizingCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    field = models.CharField(
        max_length=30, unique=True,
        help_text="Nombre del campo en el perfil (ej: top_size, bottom_size, shoe_size)",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Categoría de tallaje"
        verbose_name_plural = "Categorías de tallaje"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class SizingOption(models.Model):
    category = models.ForeignKey(
        SizingCategory, on_delete=models.CASCADE, related_name="options",
    )
    value = models.CharField(max_length=20)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Opción de tallaje"
        verbose_name_plural = "Opciones de tallaje"
        ordering = ["category", "order"]
        unique_together = ["category", "value"]

    def __str__(self):
        return f"{self.category.name} — {self.value}"


class ContentMakerProfile(models.Model):
    # Tipo de perfil (Content Maker vs Colaborador)
    TYPE_CONTENT_MAKER = "content_maker"
    TYPE_COLLABORATOR = "colaborador"
    TYPE_CHOICES = [
        (TYPE_CONTENT_MAKER, "Content Maker"),
        (TYPE_COLLABORATOR, "Colaborador"),
    ]

    # Identificador Stimada
    stimada_id = models.CharField(max_length=30, unique=True, blank=True)

    # Datos personales
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150, blank=True)
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_CONTENT_MAKER,
        db_index=True,
    )
    cm_type = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, blank=True)

    # Valoración interna
    performance = models.CharField(max_length=200, blank=True)
    content_quality = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    performance_options = models.ManyToManyField(
        "PerformanceOption", blank=True, related_name="content_makers",
    )
    appearance = models.CharField(max_length=50, blank=True)
    is_mother = models.BooleanField(default=False)
    content_categories = models.CharField(max_length=200, blank=True)

    # Relación con Stimada
    follows_stimada = models.BooleanField(default=False)
    stimada_in_bio = models.BooleanField(default=False)
    contract_signed = models.BooleanField(default=False)

    # Instagram
    fee_instagram = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    instagram_followers_category = models.CharField(max_length=50, blank=True)
    instagram_followers = models.IntegerField(null=True, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    instagram_link = models.URLField(max_length=300, blank=True)

    # TikTok
    fee_tiktok = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    tiktok_followers_category = models.CharField(max_length=50, blank=True)
    tiktok_followers = models.IntegerField(null=True, blank=True)
    tiktok_handle = models.CharField(max_length=100, blank=True)
    tiktok_link = models.URLField(max_length=300, blank=True)

    # Tallaje
    top_size = models.CharField(max_length=50, blank=True)
    bottom_size = models.CharField(max_length=50, blank=True)
    shoe_size = models.CharField(max_length=50, blank=True)
    height_measurements = models.TextField(blank=True)

    # Contacto y facturación
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    billing_address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    dni_cif = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=40, blank=True)

    # Foto de perfil
    photo = models.ImageField(upload_to="content_makers/fotos/", null=True, blank=True)

    # Notas
    comments = models.TextField(blank=True)

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
        self.instagram_link = self._build_instagram_url(self.instagram_handle)
        self.tiktok_link = self._build_tiktok_url(self.tiktok_handle)
        # Auto-compute follower category from follower count.
        self.instagram_followers_category = self._compute_followers_category(
            self.instagram_followers
        )
        self.tiktok_followers_category = self._compute_followers_category(
            self.tiktok_followers
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
        return f"{self.stimada_id} — {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_account(self):
        return self.user_id is not None
