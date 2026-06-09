import django.core.validators
from django.db import migrations, models


def seed_desempeno_options(apps, schema_editor):
    DesempenoOption = apps.get_model("content_makers", "DesempenoOption")
    defaults = [
        ("Bueno", 1),
        ("Malo", 2),
        ("Brillante", 3),
        ("Regular", 4),
        ("Excelente", 5),
    ]
    for nombre, orden in defaults:
        DesempenoOption.objects.get_or_create(nombre=nombre, defaults={"orden": orden})


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0006_tallajeoption"),
    ]

    operations = [
        # Create DesempenoOption lookup table
        migrations.CreateModel(
            name="DesempenoOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("orden", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Opción de desempeño",
                "verbose_name_plural": "Opciones de desempeño",
                "ordering": ["orden", "nombre"],
            },
        ),
        # Remove old CharField calidad_contenido and re-add as IntegerField (0-5)
        migrations.RemoveField(
            model_name="contentmakerprofile",
            name="calidad_contenido",
        ),
        migrations.AddField(
            model_name="contentmakerprofile",
            name="calidad_contenido",
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        # Add M2M desempeno_opciones
        migrations.AddField(
            model_name="contentmakerprofile",
            name="desempeno_opciones",
            field=models.ManyToManyField(
                blank=True,
                related_name="content_makers",
                to="content_makers.desempenooption",
            ),
        ),
        # Seed desempeño options
        migrations.RunPython(seed_desempeno_options, migrations.RunPython.noop),
    ]
