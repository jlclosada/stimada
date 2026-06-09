from django.db import migrations


def add_briefing_status(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    ProjectStatus.objects.get_or_create(nombre="Briefing", defaults={"orden": 2})
    # Shift existing statuses
    ProjectStatus.objects.filter(nombre="Activo").update(orden=3)
    ProjectStatus.objects.filter(nombre="Finalizado").update(orden=4)


def reverse(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    ProjectStatus.objects.filter(nombre="Briefing").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0003_briefing"),
    ]

    operations = [
        migrations.RunPython(add_briefing_status, reverse),
    ]
