import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=100)),
                ("slug", models.SlugField(unique=True)),
                ("activo", models.BooleanField(default=True)),
                ("orden", models.PositiveIntegerField(default=0)),
            ],
            options={"verbose_name": "Tipo de cliente", "verbose_name_plural": "Tipos de cliente", "ordering": ["orden", "nombre"]},
        ),
        migrations.CreateModel(
            name="ClientProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre_cliente", models.CharField(max_length=200)),
                ("cliente_id", models.CharField(max_length=50, unique=True)),
                ("nombre_facturacion", models.CharField(max_length=200)),
                ("cif", models.CharField(max_length=20)),
                ("email_facturacion", models.EmailField()),
                ("direccion_facturacion", models.TextField()),
                ("codigo_postal", models.CharField(max_length=10)),
                ("ciudad", models.CharField(max_length=100)),
                ("pais", models.CharField(default="España", max_length=100)),
                ("contrato_firmado", models.BooleanField(default=False)),
                ("contrato", models.FileField(blank=True, null=True, upload_to="contratos/clientes/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tipo_cliente",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="clientes",
                        to="clients.clienttype",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="clientes_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Cliente", "verbose_name_plural": "Clientes", "ordering": ["nombre_cliente"]},
        ),
    ]
