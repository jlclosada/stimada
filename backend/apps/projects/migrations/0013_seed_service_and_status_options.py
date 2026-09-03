from django.db import migrations


def seed(apps, schema_editor):
    ServiceType = apps.get_model("projects", "ServiceType")
    RedSocial = apps.get_model("projects", "RedSocial")
    Formato = apps.get_model("projects", "Formato")
    ProjectStatus = apps.get_model("projects", "ProjectStatus")

    # ── Tipos de servicio ────────────────────────────────────────────────
    # Opciones visibles: UGC, UGC en Perfiles, Mix, Shooting.
    # "UGC en Perfiles" y "Mix" habilitan las secciones Red Social + Formato.
    service_types = [
        {"nombre": "UGC", "orden": 1, "requiere_perfiles": False},
        {"nombre": "UGC en Perfiles", "orden": 2, "requiere_perfiles": True},
        {"nombre": "Mix", "orden": 3, "requiere_perfiles": True},
        {"nombre": "Shooting", "orden": 4, "requiere_perfiles": False},
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

    # Desactivar tipos de servicio antiguos que ya no forman parte del display.
    ServiceType.objects.filter(
        nombre__in=["UGC & UGC en Perfiles", "Gifting"]
    ).update(activo=False)

    # ── Redes sociales ───────────────────────────────────────────────────
    redes = [
        {"nombre": "Instagram", "orden": 1},
        {"nombre": "TikTok", "orden": 2},
    ]
    for r in redes:
        RedSocial.objects.get_or_create(
            nombre=r["nombre"], defaults={"orden": r["orden"], "activo": True}
        )

    # ── Formatos ─────────────────────────────────────────────────────────
    formatos = [
        {"nombre": "Stories", "orden": 1},
        {"nombre": "Reel", "orden": 2},
        {"nombre": "Carrousel", "orden": 3},
        {"nombre": "TikTok", "orden": 4},
        {"nombre": "Foto de portada", "orden": 5},
    ]
    for f in formatos:
        Formato.objects.get_or_create(
            nombre=f["nombre"], defaults={"orden": f["orden"], "activo": True}
        )

    # ── Estados disponibles al crear ─────────────────────────────────────
    # Sólo "Perfiles Propuestos" y "Perfiles Aprobados" pueden ser el estado
    # inicial de un proyecto recién creado.
    ProjectStatus.objects.filter(
        nombre__in=["Perfiles Propuestos", "Perfiles Aprobados"]
    ).update(disponible_en_creacion=True)


def reverse(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    ProjectStatus.objects.filter(
        nombre__in=["Perfiles Propuestos", "Perfiles Aprobados"]
    ).update(disponible_en_creacion=False)


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0012_formato_redsocial_project_descuento_activo_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]
