from django.db import migrations, models
import django.db.models.deletion


def migrate_categories(apps, schema_editor):
    """Create TallajeCategory entries and link existing TallajeOption rows."""
    TallajeCategory = apps.get_model("content_makers", "TallajeCategory")
    TallajeOption = apps.get_model("content_makers", "TallajeOption")

    # Map old slug keys to display names and field names
    category_map = {
        "arriba": ("Parte de arriba", "talla_arriba"),
        "abajo": ("Parte de abajo", "talla_abajo"),
        "pie": ("Pie", "talla_pie"),
    }

    # Create category objects
    created = {}
    for i, (key, (nombre, campo)) in enumerate(category_map.items(), start=1):
        cat, _ = TallajeCategory.objects.get_or_create(
            nombre=nombre, defaults={"campo": campo, "orden": i}
        )
        created[key] = cat

    # Link existing options (use .order_by() to bypass Meta ordering referencing renamed field)
    for opt in TallajeOption.objects.order_by("id").all():
        old_key = opt.categoria_old
        if old_key in created:
            opt.categoria_new = created[old_key]
            opt.save(update_fields=["categoria_new"])


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0007_valoracion_fields"),
    ]

    operations = [
        # 1. Create TallajeCategory model
        migrations.CreateModel(
            name="TallajeCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=50, unique=True)),
                ("campo", models.CharField(max_length=30, unique=True, help_text="Nombre del campo en el perfil (ej: talla_arriba, talla_abajo, talla_pie)")),
                ("orden", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Categoría de tallaje",
                "verbose_name_plural": "Categorías de tallaje",
                "ordering": ["orden", "nombre"],
            },
        ),
        # 2. Drop unique_together BEFORE renaming field
        migrations.AlterUniqueTogether(
            name="tallajeoption",
            unique_together=set(),
        ),
        # 3. Rename old categoria field
        migrations.RenameField(
            model_name="tallajeoption",
            old_name="categoria",
            new_name="categoria_old",
        ),
        # 4. Add new FK field (nullable temporarily)
        migrations.AddField(
            model_name="tallajeoption",
            name="categoria_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="opciones",
                to="content_makers.tallajecategory",
            ),
        ),
        # 5. Migrate data
        migrations.RunPython(migrate_categories, migrations.RunPython.noop),
        # 6. Remove old field
        migrations.RemoveField(
            model_name="tallajeoption",
            name="categoria_old",
        ),
        # 7. Rename new field to 'categoria'
        migrations.RenameField(
            model_name="tallajeoption",
            old_name="categoria_new",
            new_name="categoria",
        ),
        # 8. Make FK non-nullable
        migrations.AlterField(
            model_name="tallajeoption",
            name="categoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="opciones",
                to="content_makers.tallajecategory",
            ),
        ),
        # 9. Re-add unique_together with new FK
        migrations.AlterUniqueTogether(
            name="tallajeoption",
            unique_together={("categoria", "valor")},
        ),
    ]
