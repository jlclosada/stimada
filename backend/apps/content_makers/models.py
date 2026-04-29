from django.conf import settings
from django.db import models


class ContentMakerProfile(models.Model):
    # Identificador Stimada
    stimada_id = models.CharField(max_length=30, unique=True)

    # Datos personales
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150, blank=True)
    tipo_cm = models.CharField(max_length=50, blank=True)
    sexo = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=50, blank=True)

    # Valoración interna
    desempeno = models.CharField(max_length=200, blank=True)
    calidad_contenido = models.CharField(max_length=50, blank=True)
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

    def __str__(self):
        return f"{self.stimada_id} — {self.nombre} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}".strip()

    @property
    def tiene_cuenta(self):
        return self.user_id is not None
