from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0008_tallaje_category_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentmakerprofile",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("content_maker", "Content Maker"),
                    ("colaborador", "Colaborador"),
                ],
                db_index=True,
                default="content_maker",
                max_length=20,
            ),
        ),
    ]
