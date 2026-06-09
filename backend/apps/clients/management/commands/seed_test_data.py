from django.core.management.base import BaseCommand

from apps.accounts.models import CustomUser
from apps.clients.models import ClientProfile, ClientType
from apps.content_makers.models import ContentMakerProfile


class Command(BaseCommand):
    help = "Crea perfiles de prueba para clientes y content makers."

    def handle(self, *args, **options):
        self._create_test_clients()
        self._create_test_content_makers()
        self.stdout.write(self.style.SUCCESS("Datos de prueba creados correctamente."))

    def _create_test_clients(self):
        fashion = ClientType.objects.filter(slug="fashion").first()
        pharma = ClientType.objects.filter(slug="pharma").first()
        food = ClientType.objects.filter(slug="food-drinks").first()

        clients_data = [
            {
                "nombre_cliente": "Zara España",
                "cliente_id": "CLI-001",
                "tipo_cliente": fashion,
                "nombre_facturacion": "Industria de Diseño Textil S.A.",
                "cif": "A15075062",
                "email_facturacion": "facturacion@zara.com",
                "direccion_facturacion": "Avda. de la Diputación, Edificio Inditex",
                "codigo_postal": "15142",
                "ciudad": "Arteixo",
                "pais": "España",
                "contrato_firmado": True,
            },
            {
                "nombre_cliente": "L'Oréal Dermatológica",
                "cliente_id": "CLI-002",
                "tipo_cliente": pharma,
                "nombre_facturacion": "L'Oréal España S.A.",
                "cif": "A28015937",
                "email_facturacion": "admin@loreal.es",
                "direccion_facturacion": "Calle Albasanz 16",
                "codigo_postal": "28037",
                "ciudad": "Madrid",
                "pais": "España",
                "contrato_firmado": True,
            },
            {
                "nombre_cliente": "Coca-Cola Iberia",
                "cliente_id": "CLI-003",
                "tipo_cliente": food,
                "nombre_facturacion": "Coca-Cola European Partners Iberia S.L.",
                "cif": "B86561412",
                "email_facturacion": "billing@cocacola.es",
                "direccion_facturacion": "Paseo de la Castellana 259C, Torre de Cristal",
                "codigo_postal": "28046",
                "ciudad": "Madrid",
                "pais": "España",
                "contrato_firmado": False,
            },
            {
                "nombre_cliente": "Mango Fashion",
                "cliente_id": "CLI-004",
                "tipo_cliente": fashion,
                "nombre_facturacion": "Punto Fa S.L.",
                "cif": "B08598289",
                "email_facturacion": "contabilidad@mango.com",
                "direccion_facturacion": "Paseo de Gracia 55",
                "codigo_postal": "08007",
                "ciudad": "Barcelona",
                "pais": "España",
                "contrato_firmado": True,
            },
            {
                "nombre_cliente": "Nestlé Health Science",
                "cliente_id": "CLI-005",
                "tipo_cliente": pharma,
                "nombre_facturacion": "Nestlé España S.A.",
                "cif": "A08005449",
                "email_facturacion": "finance@nestle.es",
                "direccion_facturacion": "Gran Vía de les Corts Catalanes 4",
                "codigo_postal": "08902",
                "ciudad": "Esplugues de Llobregat",
                "pais": "España",
                "contrato_firmado": False,
            },
        ]

        created = 0
        for data in clients_data:
            _, was_created = ClientProfile.objects.get_or_create(
                cliente_id=data["cliente_id"],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Clientes: {created} creados, {len(clients_data) - created} ya existían")

    def _create_test_content_makers(self):
        cms_data = [
            {
                "stimada_id": "[CM] - TEST01",
                "nombre": "Lucía",
                "apellidos": "García Martínez",
                "tipo_cm": "Influencer",
                "sexo": "Mujer",
                "status": "Alta",
                "desempeno": "Excelente",
                "calidad_contenido": "Alta",
                "apariencia": "Trendy",
                "es_mama": False,
                "categorias_contenido": "Moda, Lifestyle",
                "sigue_stimada": True,
                "stimada_en_bio": True,
                "contrato_firmado": True,
                "fee_instagram": 350,
                "categoria_seguidores_ig": "50K-100K",
                "seguidores_instagram": 78500,
                "instagram_handle": "luciagm_style",
                "link_instagram": "https://instagram.com/luciagm_style",
                "fee_tiktok": 250,
                "categoria_seguidores_tt": "25K-50K",
                "seguidores_tiktok": 34200,
                "tiktok_handle": "@luciagm_style",
                "link_tiktok": "https://tiktok.com/@luciagm_style",
                "talla_arriba": "S",
                "talla_abajo": "36",
                "talla_pie": "37",
                "altura_medidas": "165cm · 85-62-90",
                "email": "lucia.garcia@email.com",
                "telefono": "+34 612 345 678",
                "direccion_facturacion": "Calle Serrano 45, 3ºB",
                "codigo_postal": "28001",
                "provincia": "Madrid",
                "pais": "España",
                "dni_cif": "12345678A",
                "iban": "ES12 1234 5678 9012 3456 7890",
                "comentarios": "Muy profesional, entrega contenido a tiempo. Excelente engagement.",
            },
            {
                "stimada_id": "[CM] - TEST02",
                "nombre": "María",
                "apellidos": "López Fernández",
                "tipo_cm": "Micro-influencer",
                "sexo": "Mujer",
                "status": "Alta",
                "desempeno": "Bueno",
                "calidad_contenido": "Alta",
                "apariencia": "Natural",
                "es_mama": True,
                "categorias_contenido": "Maternidad, Lifestyle, Hogar",
                "sigue_stimada": True,
                "stimada_en_bio": False,
                "contrato_firmado": True,
                "fee_instagram": 200,
                "categoria_seguidores_ig": "10K-25K",
                "seguidores_instagram": 18700,
                "instagram_handle": "marialopez_mama",
                "link_instagram": "https://instagram.com/marialopez_mama",
                "fee_tiktok": 150,
                "categoria_seguidores_tt": "10K-25K",
                "seguidores_tiktok": 12400,
                "tiktok_handle": "@marialopez_mama",
                "link_tiktok": "https://tiktok.com/@marialopez_mama",
                "talla_arriba": "M",
                "talla_abajo": "38",
                "talla_pie": "38",
                "altura_medidas": "170cm · 90-66-95",
                "email": "maria.lopez@email.com",
                "telefono": "+34 623 456 789",
                "direccion_facturacion": "Avda. Diagonal 210, 5ºA",
                "codigo_postal": "08018",
                "provincia": "Barcelona",
                "pais": "España",
                "dni_cif": "23456789B",
                "iban": "ES23 2345 6789 0123 4567 8901",
                "comentarios": "Contenido muy auténtico. Audiencia muy fiel en temática maternidad.",
            },
            {
                "stimada_id": "[CM] - TEST03",
                "nombre": "Carmen",
                "apellidos": "Ruiz Sánchez",
                "tipo_cm": "UGC Creator",
                "sexo": "Mujer",
                "status": "Alta",
                "desempeno": "Excelente",
                "calidad_contenido": "Premium",
                "apariencia": "Elegante",
                "es_mama": False,
                "categorias_contenido": "Belleza, Skincare, Wellness",
                "sigue_stimada": True,
                "stimada_en_bio": True,
                "contrato_firmado": True,
                "fee_instagram": 500,
                "categoria_seguidores_ig": "100K-500K",
                "seguidores_instagram": 142000,
                "instagram_handle": "carmenruiz_beauty",
                "link_instagram": "https://instagram.com/carmenruiz_beauty",
                "fee_tiktok": 400,
                "categoria_seguidores_tt": "50K-100K",
                "seguidores_tiktok": 89000,
                "tiktok_handle": "@carmenruiz_beauty",
                "link_tiktok": "https://tiktok.com/@carmenruiz_beauty",
                "talla_arriba": "XS",
                "talla_abajo": "34",
                "talla_pie": "36",
                "altura_medidas": "158cm · 80-58-86",
                "email": "carmen.ruiz@email.com",
                "telefono": "+34 634 567 890",
                "direccion_facturacion": "Plaza Mayor 12, 2ºC",
                "codigo_postal": "46001",
                "provincia": "Valencia",
                "pais": "España",
                "dni_cif": "34567890C",
                "iban": "ES34 3456 7890 1234 5678 9012",
                "comentarios": "Top creator. Trabaja con marcas premium. Resultados excepcionales en beauty.",
            },
        ]

        created = 0
        for data in cms_data:
            _, was_created = ContentMakerProfile.objects.get_or_create(
                stimada_id=data["stimada_id"],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Content Makers test: {created} creados, {len(cms_data) - created} ya existían")
