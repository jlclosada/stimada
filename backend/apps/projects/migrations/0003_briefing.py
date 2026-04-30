from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("content_makers", "0001_initial"),
        ("projects", "0002_seed_statuses_and_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("project_cm_select", "Seleccionar Content Maker"),
                    ("project_cm_request", "Solicitud a Content Maker"),
                    ("project_cm_accepted", "Content Maker aceptó"),
                    ("project_cm_rejected", "Content Maker rechazó"),
                    ("briefing_submitted", "Briefing enviado"),
                ],
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="Briefing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("link_referencia", models.URLField(blank=True, max_length=500)),
                ("comentarios", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content_maker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="briefings",
                        to="content_makers.contentmakerprofile",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="briefings_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="briefings",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "verbose_name": "Briefing",
                "verbose_name_plural": "Briefings",
                "unique_together": {("project", "content_maker")},
            },
        ),
    ]
