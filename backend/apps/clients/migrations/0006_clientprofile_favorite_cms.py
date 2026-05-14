from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0005_alter_clientprofile_cliente_id"),
        ("content_makers", "0005_alter_contentmakerprofile_stimada_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientprofile",
            name="favorite_cms",
            field=models.ManyToManyField(
                blank=True,
                related_name="favorited_by_clients",
                to="content_makers.contentmakerprofile",
            ),
        ),
    ]
