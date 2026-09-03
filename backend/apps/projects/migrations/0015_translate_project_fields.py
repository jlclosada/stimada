from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0014_add_ugc_mix_service_type"),
    ]

    operations = [
        # ── Model renames ───────────────────────────────────────────────
        migrations.RenameModel(old_name="RedSocial", new_name="SocialNetwork"),
        migrations.RenameModel(old_name="Formato", new_name="Format"),
        migrations.RenameModel(old_name="ModalidadEconomica", new_name="EconomicModel"),
        migrations.RenameModel(old_name="LogisticaProducto", new_name="ProductLogistics"),
        migrations.RenameModel(old_name="RecogidaProducto", new_name="ProductPickup"),
        migrations.RenameModel(old_name="QuienGraba", new_name="WhoRecords"),
        migrations.RenameModel(old_name="QuienRevisa", new_name="WhoReviews"),
        migrations.RenameModel(old_name="QuienPublica", new_name="WhoPublishes"),
        migrations.RenameModel(old_name="Entregable", new_name="Deliverable"),

        # ── ProjectStatus ───────────────────────────────────────────────
        migrations.RenameField("projectstatus", "nombre", "name"),
        migrations.RenameField("projectstatus", "orden", "order"),
        migrations.RenameField("projectstatus", "activo", "is_active"),
        migrations.RenameField("projectstatus", "disponible_en_creacion", "available_on_creation"),

        # ── ServiceType ─────────────────────────────────────────────────
        migrations.RenameField("servicetype", "nombre", "name"),
        migrations.RenameField("servicetype", "orden", "order"),
        migrations.RenameField("servicetype", "activo", "is_active"),
        migrations.RenameField("servicetype", "requiere_perfiles", "requires_profiles"),

        # ── SocialNetwork (was RedSocial) ───────────────────────────────
        migrations.RenameField("socialnetwork", "nombre", "name"),
        migrations.RenameField("socialnetwork", "orden", "order"),
        migrations.RenameField("socialnetwork", "activo", "is_active"),

        # ── Format (was Formato) ────────────────────────────────────────
        migrations.RenameField("format", "nombre", "name"),
        migrations.RenameField("format", "orden", "order"),
        migrations.RenameField("format", "activo", "is_active"),

        # ── EconomicModel (was ModalidadEconomica) ──────────────────────
        migrations.RenameField("economicmodel", "nombre", "name"),
        migrations.RenameField("economicmodel", "orden", "order"),
        migrations.RenameField("economicmodel", "activo", "is_active"),

        # ── ProductLogistics (was LogisticaProducto) ────────────────────
        migrations.RenameField("productlogistics", "nombre", "name"),
        migrations.RenameField("productlogistics", "orden", "order"),
        migrations.RenameField("productlogistics", "activo", "is_active"),

        # ── ProductPickup (was RecogidaProducto) ────────────────────────
        migrations.RenameField("productpickup", "nombre", "name"),
        migrations.RenameField("productpickup", "orden", "order"),
        migrations.RenameField("productpickup", "activo", "is_active"),

        # ── WhoRecords (was QuienGraba) ─────────────────────────────────
        migrations.RenameField("whorecords", "nombre", "name"),
        migrations.RenameField("whorecords", "orden", "order"),
        migrations.RenameField("whorecords", "activo", "is_active"),

        # ── WhoReviews (was QuienRevisa) ────────────────────────────────
        migrations.RenameField("whoreviews", "nombre", "name"),
        migrations.RenameField("whoreviews", "orden", "order"),
        migrations.RenameField("whoreviews", "activo", "is_active"),

        # ── WhoPublishes (was QuienPublica) ─────────────────────────────
        migrations.RenameField("whopublishes", "nombre", "name"),
        migrations.RenameField("whopublishes", "orden", "order"),
        migrations.RenameField("whopublishes", "activo", "is_active"),

        # ── WinStatus ───────────────────────────────────────────────────
        migrations.RenameField("winstatus", "nombre", "name"),
        migrations.RenameField("winstatus", "orden", "order"),
        migrations.RenameField("winstatus", "activo", "is_active"),

        # ── Project ─────────────────────────────────────────────────────
        migrations.RenameField("project", "nombre", "name"),
        migrations.RenameField("project", "descripcion", "description"),
        migrations.RenameField("project", "modalidad_economica", "economic_model"),
        migrations.RenameField("project", "logistica_producto", "product_logistics"),
        migrations.RenameField("project", "recogida_producto", "product_pickup"),
        migrations.RenameField("project", "quien_graba", "who_records"),
        migrations.RenameField("project", "quien_revisa", "who_reviews"),
        migrations.RenameField("project", "quien_publica", "who_publishes"),
        migrations.RenameField("project", "devolucion_producto", "product_return"),
        migrations.RenameField("project", "semaforo_proyecto", "traffic_light"),
        migrations.RenameField("project", "retrasado", "delayed"),
        migrations.RenameField("project", "comentarios", "comments"),
        migrations.RenameField("project", "redes_sociales", "social_networks"),
        migrations.RenameField("project", "formatos", "formats"),
        migrations.RenameField("project", "num_contenidos", "num_contents"),
        migrations.RenameField("project", "num_perfiles", "num_profiles"),
        migrations.RenameField("project", "descuento_activo", "discount_active"),
        migrations.RenameField("project", "descuento_porcentaje", "discount_percentage"),
        migrations.RenameField("project", "base_imponible", "tax_base"),
        migrations.RenameField("project", "impuestos", "taxes"),
        migrations.RenameField("project", "fecha_venta", "sale_date"),
        migrations.RenameField("project", "fecha_servicio", "service_date"),
        migrations.RenameField("project", "fecha_llegada_producto", "product_arrival_date"),
        migrations.RenameField("project", "fecha_limite_entrega", "delivery_deadline"),
        migrations.RenameField("project", "fecha_fin", "end_date"),

        # ── ProjectContentMaker ─────────────────────────────────────────
        migrations.RenameField("projectcontentmaker", "is_suplente", "is_substitute"),

        # ── Briefing ────────────────────────────────────────────────────
        migrations.RenameField("briefing", "comentarios", "comments"),

        # ── BriefingLink ────────────────────────────────────────────────
        migrations.RenameField("briefinglink", "titulo", "title"),
        migrations.RenameField("briefinglink", "orden", "order"),

        # ── BriefingPhoto ───────────────────────────────────────────────
        migrations.RenameField("briefingphoto", "imagen", "image"),
        migrations.RenameField("briefingphoto", "descripcion", "description"),
        migrations.RenameField("briefingphoto", "orden", "order"),

        # ── Deliverable (was Entregable) ────────────────────────────────
        migrations.RenameField("deliverable", "archivo", "file"),
        migrations.RenameField("deliverable", "descripcion", "description"),
    ]
