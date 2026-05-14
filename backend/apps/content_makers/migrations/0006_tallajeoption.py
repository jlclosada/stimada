from django.db import migrations, models


def seed_tallaje_options(apps, schema_editor):
    TallajeOption = apps.get_model("content_makers", "TallajeOption")

    options = []
    # Parte de arriba
    for i, val in enumerate(["XS", "S", "M", "L", "XL", "XXL"]):
        options.append(TallajeOption(categoria="arriba", valor=val, orden=i))
    # Parte de abajo
    for i, val in enumerate(["34", "36", "38", "40", "42", "44", "46"]):
        options.append(TallajeOption(categoria="abajo", valor=val, orden=i))
    # Pie
    for i, val in enumerate(range(33, 46)):
        options.append(TallajeOption(categoria="pie", valor=str(val), orden=i))

    TallajeOption.objects.bulk_create(options)


def reverse_seed(apps, schema_editor):
    TallajeOption = apps.get_model("content_makers", "TallajeOption")
    TallajeOption.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0005_alter_contentmakerprofile_stimada_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="TallajeOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("categoria", models.CharField(choices=[("arriba", "Parte de arriba"), ("abajo", "Parte de abajo"), ("pie", "Pie")], max_length=20)),
                ("valor", models.CharField(max_length=20)),
                ("orden", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Opción de tallaje",
                "verbose_name_plural": "Opciones de tallaje",
                "ordering": ["categoria", "orden"],
                "unique_together": {("categoria", "valor")},
            },
        ),
        migrations.RunPython(seed_tallaje_options, reverse_seed),
    ]
