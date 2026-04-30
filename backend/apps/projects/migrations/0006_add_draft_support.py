from django.db import migrations, models
import django.db.models.deletion


def seed_borrador_status(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    ProjectStatus.objects.get_or_create(nombre="Borrador", defaults={"orden": 0})


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_add_recommended_status"),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="is_draft",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="project",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="projects",
                to="clients.clientprofile",
            ),
        ),
        migrations.RunPython(seed_borrador_status, reverse),
    ]
