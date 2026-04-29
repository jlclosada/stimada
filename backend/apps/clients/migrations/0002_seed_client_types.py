from django.db import migrations


INITIAL_TYPES = [
    ("Fashion", "fashion", 1),
    ("Health & Beauty", "health-beauty", 2),
    ("Food & Drinks", "food-drinks", 3),
    ("Centros Comerciales", "centros-comerciales", 4),
    ("Pharma", "pharma", 5),
    ("Otros", "otros", 99),
]


def seed(apps, schema_editor):
    ClientType = apps.get_model("clients", "ClientType")
    for nombre, slug, orden in INITIAL_TYPES:
        ClientType.objects.get_or_create(slug=slug, defaults={"nombre": nombre, "orden": orden})


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
