from django.db import migrations


def seed(apps, schema_editor):
    ServiceType = apps.get_model("projects", "ServiceType")

    # Reordena e incluye "UGC & UGC en Perfiles" como tipo de servicio visible.
    # Tanto "UGC en Perfiles" como "UGC & UGC en Perfiles" habilitan las
    # secciones de Red Social y Formato (requiere_perfiles=True).
    service_types = [
        {"nombre": "UGC", "orden": 1, "requiere_perfiles": False},
        {"nombre": "UGC en Perfiles", "orden": 2, "requiere_perfiles": True},
        {"nombre": "UGC & UGC en Perfiles", "orden": 3, "requiere_perfiles": True},
        {"nombre": "Mix", "orden": 4, "requiere_perfiles": True},
        {"nombre": "Shooting", "orden": 5, "requiere_perfiles": False},
    ]
    for st in service_types:
        obj, created = ServiceType.objects.get_or_create(
            nombre=st["nombre"],
            defaults={
                "orden": st["orden"],
                "activo": True,
                "requiere_perfiles": st["requiere_perfiles"],
            },
        )
        if not created:
            obj.orden = st["orden"]
            obj.activo = True
            obj.requiere_perfiles = st["requiere_perfiles"]
            obj.save()


def reverse(apps, schema_editor):
    ServiceType = apps.get_model("projects", "ServiceType")
    ServiceType.objects.filter(nombre="UGC & UGC en Perfiles").update(activo=False)


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0013_seed_service_and_status_options"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]
