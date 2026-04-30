from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0004_add_briefing_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectcontentmaker",
            name="status",
            field=models.CharField(
                choices=[
                    ("recommended", "Recomendada"),
                    ("pending", "Pendiente"),
                    ("accepted", "Aceptada"),
                    ("rejected", "Rechazada"),
                    ("selected", "Seleccionada por cliente"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
