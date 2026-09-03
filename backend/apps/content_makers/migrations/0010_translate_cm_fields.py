from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("content_makers", "0009_contentmakerprofile_tipo"),
    ]

    operations = [
        # ── Model renames ───────────────────────────────────────────────
        migrations.RenameModel(old_name="DesempenoOption", new_name="PerformanceOption"),
        migrations.RenameModel(old_name="TallajeCategory", new_name="SizingCategory"),
        migrations.RenameModel(old_name="TallajeOption", new_name="SizingOption"),

        # ── ContentMakerStatus ──────────────────────────────────────────
        migrations.RenameField("contentmakerstatus", "nombre", "name"),
        migrations.RenameField("contentmakerstatus", "orden", "order"),

        # ── ContentMakerType ────────────────────────────────────────────
        migrations.RenameField("contentmakertype", "nombre", "name"),
        migrations.RenameField("contentmakertype", "orden", "order"),

        # ── PerformanceOption (was DesempenoOption) ─────────────────────
        migrations.RenameField("performanceoption", "nombre", "name"),
        migrations.RenameField("performanceoption", "orden", "order"),

        # ── SizingCategory (was TallajeCategory) ────────────────────────
        migrations.RenameField("sizingcategory", "nombre", "name"),
        migrations.RenameField("sizingcategory", "campo", "field"),
        migrations.RenameField("sizingcategory", "orden", "order"),

        # ── SizingOption (was TallajeOption) ────────────────────────────
        migrations.RenameField("sizingoption", "categoria", "category"),
        migrations.RenameField("sizingoption", "valor", "value"),
        migrations.RenameField("sizingoption", "orden", "order"),

        # ── ContentMakerProfile ─────────────────────────────────────────
        migrations.RenameField("contentmakerprofile", "nombre", "first_name"),
        migrations.RenameField("contentmakerprofile", "apellidos", "last_name"),
        migrations.RenameField("contentmakerprofile", "tipo", "type"),
        migrations.RenameField("contentmakerprofile", "tipo_cm", "cm_type"),
        migrations.RenameField("contentmakerprofile", "sexo", "gender"),
        migrations.RenameField("contentmakerprofile", "desempeno", "performance"),
        migrations.RenameField("contentmakerprofile", "calidad_contenido", "content_quality"),
        migrations.RenameField("contentmakerprofile", "desempeno_opciones", "performance_options"),
        migrations.RenameField("contentmakerprofile", "apariencia", "appearance"),
        migrations.RenameField("contentmakerprofile", "es_mama", "is_mother"),
        migrations.RenameField("contentmakerprofile", "categorias_contenido", "content_categories"),
        migrations.RenameField("contentmakerprofile", "sigue_stimada", "follows_stimada"),
        migrations.RenameField("contentmakerprofile", "stimada_en_bio", "stimada_in_bio"),
        migrations.RenameField("contentmakerprofile", "contrato_firmado", "contract_signed"),
        migrations.RenameField("contentmakerprofile", "categoria_seguidores_ig", "instagram_followers_category"),
        migrations.RenameField("contentmakerprofile", "seguidores_instagram", "instagram_followers"),
        migrations.RenameField("contentmakerprofile", "link_instagram", "instagram_link"),
        migrations.RenameField("contentmakerprofile", "categoria_seguidores_tt", "tiktok_followers_category"),
        migrations.RenameField("contentmakerprofile", "seguidores_tiktok", "tiktok_followers"),
        migrations.RenameField("contentmakerprofile", "link_tiktok", "tiktok_link"),
        migrations.RenameField("contentmakerprofile", "talla_arriba", "top_size"),
        migrations.RenameField("contentmakerprofile", "talla_abajo", "bottom_size"),
        migrations.RenameField("contentmakerprofile", "talla_pie", "shoe_size"),
        migrations.RenameField("contentmakerprofile", "altura_medidas", "height_measurements"),
        migrations.RenameField("contentmakerprofile", "telefono", "phone"),
        migrations.RenameField("contentmakerprofile", "direccion_facturacion", "billing_address"),
        migrations.RenameField("contentmakerprofile", "codigo_postal", "postal_code"),
        migrations.RenameField("contentmakerprofile", "provincia", "province"),
        migrations.RenameField("contentmakerprofile", "pais", "country"),
        migrations.RenameField("contentmakerprofile", "foto", "photo"),
        migrations.RenameField("contentmakerprofile", "comentarios", "comments"),
    ]
