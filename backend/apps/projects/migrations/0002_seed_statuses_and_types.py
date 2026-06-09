from django.db import migrations


def seed_data(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    ServiceType = apps.get_model("projects", "ServiceType")

    statuses = [
        {"nombre": "Pendiente", "orden": 1},
        {"nombre": "Activo", "orden": 2},
        {"nombre": "Finalizado", "orden": 3},
    ]
    for s in statuses:
        ProjectStatus.objects.get_or_create(nombre=s["nombre"], defaults={"orden": s["orden"]})

    service_types = [
        {"nombre": "Shooting", "orden": 1},
        {"nombre": "Gifting", "orden": 2},
    ]
    for st in service_types:
        ServiceType.objects.get_or_create(nombre=st["nombre"], defaults={"orden": st["orden"]})


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse),
    ]
