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
    # Identificador Stimada
    stimada_id = models.CharField(max_length=30, unique=True, blank=True)

    # Datos personales
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150, blank=True)
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
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stimada_id} — {self.nombre} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}".strip()

    @property
    def tiene_cuenta(self):
        return self.user_id is not None
