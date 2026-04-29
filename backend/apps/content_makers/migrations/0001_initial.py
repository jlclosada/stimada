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
            name="ContentMakerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("stimada_id", models.CharField(max_length=30, unique=True)),
                ("nombre", models.CharField(max_length=100)),
                ("apellidos", models.CharField(blank=True, max_length=150)),
                ("tipo_cm", models.CharField(blank=True, max_length=50)),
                ("sexo", models.CharField(blank=True, max_length=20)),
                ("status", models.CharField(blank=True, max_length=50)),
                ("desempeno", models.CharField(blank=True, max_length=200)),
                ("calidad_contenido", models.CharField(blank=True, max_length=50)),
                ("apariencia", models.CharField(blank=True, max_length=50)),
                ("es_mama", models.BooleanField(default=False)),
                ("categorias_contenido", models.CharField(blank=True, max_length=200)),
                ("sigue_stimada", models.BooleanField(default=False)),
                ("stimada_en_bio", models.BooleanField(default=False)),
                ("contrato_firmado", models.BooleanField(default=False)),
                ("fee_instagram", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("categoria_seguidores_ig", models.CharField(blank=True, max_length=50)),
                ("seguidores_instagram", models.IntegerField(blank=True, null=True)),
                ("instagram_handle", models.CharField(blank=True, max_length=100)),
                ("link_instagram", models.URLField(blank=True, max_length=300)),
                ("fee_tiktok", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("categoria_seguidores_tt", models.CharField(blank=True, max_length=50)),
                ("seguidores_tiktok", models.IntegerField(blank=True, null=True)),
                ("tiktok_handle", models.CharField(blank=True, max_length=100)),
                ("link_tiktok", models.URLField(blank=True, max_length=300)),
                ("talla_arriba", models.CharField(blank=True, max_length=50)),
                ("talla_abajo", models.CharField(blank=True, max_length=50)),
                ("talla_pie", models.CharField(blank=True, max_length=50)),
                ("altura_medidas", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("direccion_facturacion", models.TextField(blank=True)),
                ("codigo_postal", models.CharField(blank=True, max_length=10)),
                ("provincia", models.CharField(blank=True, max_length=100)),
                ("pais", models.CharField(blank=True, max_length=100)),
                ("dni_cif", models.CharField(blank=True, max_length=20)),
                ("iban", models.CharField(blank=True, max_length=40)),
                ("comentarios", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_maker_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Content Maker", "verbose_name_plural": "Content Makers", "ordering": ["stimada_id"]},
        ),
    ]
