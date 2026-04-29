from django.db import migrations


def seed_statuses_and_types(apps, schema_editor):
    ContentMakerStatus = apps.get_model("content_makers", "ContentMakerStatus")
    ContentMakerType = apps.get_model("content_makers", "ContentMakerType")
    ContentMakerProfile = apps.get_model("content_makers", "ContentMakerProfile")

    # Seed statuses from existing data
    statuses = (
        ContentMakerProfile.objects.exclude(status="")
        .values_list("status", flat=True)
        .distinct()
        .order_by("status")
    )
    for i, name in enumerate(statuses):
        ContentMakerStatus.objects.get_or_create(nombre=name, defaults={"orden": i})

    # Seed types from existing data
    tipos = (
        ContentMakerProfile.objects.exclude(tipo_cm="")
        .values_list("tipo_cm", flat=True)
        .distinct()
        .order_by("tipo_cm")
    )
    for i, name in enumerate(tipos):
        ContentMakerType.objects.get_or_create(nombre=name, defaults={"orden": i})


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0002_add_status_and_type_models"),
    ]

    operations = [
        migrations.RunPython(seed_statuses_and_types, migrations.RunPython.noop),
    ]
