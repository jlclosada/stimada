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
    # Identificación
    nombre_cliente = models.CharField(max_length=200)
    cliente_id = models.CharField(max_length=50, unique=True)
    tipo_cliente = models.ForeignKey(
        ClientType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clientes",
    )

    # Facturación
    nombre_facturacion = models.CharField(max_length=200)
    cif = models.CharField(max_length=20)
    email_facturacion = models.EmailField()
    direccion_facturacion = models.TextField()
    codigo_postal = models.CharField(max_length=10)
    ciudad = models.CharField(max_length=100)
    pais = models.CharField(max_length=100, default="España")

    # Contrato
    contrato_firmado = models.BooleanField(default=False)
    contrato = models.FileField(upload_to="contratos/clientes/", null=True, blank=True)

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

    def __str__(self):
        return f"{self.cliente_id} — {self.nombre_cliente}"
