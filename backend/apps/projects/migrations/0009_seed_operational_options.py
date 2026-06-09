from django.db import migrations


def seed_options(apps, schema_editor):
    ServiceType = apps.get_model("projects", "ServiceType")
    ModalidadEconomica = apps.get_model("projects", "ModalidadEconomica")
    LogisticaProducto = apps.get_model("projects", "LogisticaProducto")
    RecogidaProducto = apps.get_model("projects", "RecogidaProducto")
    QuienGraba = apps.get_model("projects", "QuienGraba")
    QuienRevisa = apps.get_model("projects", "QuienRevisa")
    QuienPublica = apps.get_model("projects", "QuienPublica")
    WinStatus = apps.get_model("projects", "WinStatus")
    ProjectStatus = apps.get_model("projects", "ProjectStatus")

    # Service Types
    service_types = ["UGC", "UGC en Perfiles", "UGC & UGC en Perfiles", "Shooting", "Gifting"]
    for i, name in enumerate(service_types):
        ServiceType.objects.get_or_create(nombre=name, defaults={"orden": i + 1, "activo": True})

    # Modalidad Económica
    modalidades = ["Fee", "Gifting"]
    for i, name in enumerate(modalidades):
        ModalidadEconomica.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Logística Producto
    logisticas = ["Desplazamiento", "Asistencia libre", "Envío", "N/A"]
    for i, name in enumerate(logisticas):
        LogisticaProducto.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Recogida Producto
    recogidas = ["Recibe en casa", "Recoge previamente", "In situ"]
    for i, name in enumerate(recogidas):
        RecogidaProducto.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Quién Graba
    quien_graba = ["Marca", "Content Maker"]
    for i, name in enumerate(quien_graba):
        QuienGraba.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Quién Revisa
    quien_revisa = ["Nadie", "Stimada", "Marca"]
    for i, name in enumerate(quien_revisa):
        QuienRevisa.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Quién Publica
    quien_publica = ["Marca", "Content Maker", "Marca & Content Maker"]
    for i, name in enumerate(quien_publica):
        QuienPublica.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Win Status
    win_statuses = ["Ganado", "Perdido", "En proceso"]
    for i, name in enumerate(win_statuses):
        WinStatus.objects.get_or_create(nombre=name, defaults={"orden": i + 1})

    # Project Statuses (ensure the pipeline ones exist)
    statuses = [
        "Borrador",
        "Perfiles Propuestos",
        "Perfiles Aprobados",
        "Producto Enviado",
        "Briefing",
        "Producto Recibido",
        "En producción",
        "Revisión",
        "Publicado",
        "Producto a Recoger",
        "Proyecto Finalizado",
        "Cerrado",
    ]
    for i, name in enumerate(statuses):
        ProjectStatus.objects.get_or_create(nombre=name, defaults={"orden": i + 1, "activo": True})


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0008_expand_project_operational_fields"),
    ]

    operations = [
        migrations.RunPython(seed_options, reverse_seed),
    ]
