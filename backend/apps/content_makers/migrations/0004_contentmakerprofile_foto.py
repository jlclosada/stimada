from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0003_seed_status_and_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentmakerprofile",
            name="foto",
            field=models.ImageField(blank=True, null=True, upload_to="content_makers/fotos/"),
        ),
    ]
