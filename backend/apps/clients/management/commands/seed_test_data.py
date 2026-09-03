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
                "name": "Zara España",
                "client_id": "CLI-001",
                "client_type": fashion,
                "billing_name": "Industria de Diseño Textil S.A.",
                "cif": "A15075062",
                "billing_email": "facturacion@zara.com",
                "billing_address": "Avda. de la Diputación, Edificio Inditex",
                "postal_code": "15142",
                "city": "Arteixo",
                "country": "España",
                "contract_signed": True,
            },
            {
                "name": "L'Oréal Dermatológica",
                "client_id": "CLI-002",
                "client_type": pharma,
                "billing_name": "L'Oréal España S.A.",
                "cif": "A28015937",
                "billing_email": "admin@loreal.es",
                "billing_address": "Calle Albasanz 16",
                "postal_code": "28037",
                "city": "Madrid",
                "country": "España",
                "contract_signed": True,
            },
            {
                "name": "Coca-Cola Iberia",
                "client_id": "CLI-003",
                "client_type": food,
                "billing_name": "Coca-Cola European Partners Iberia S.L.",
                "cif": "B86561412",
                "billing_email": "billing@cocacola.es",
                "billing_address": "Paseo de la Castellana 259C, Torre de Cristal",
                "postal_code": "28046",
                "city": "Madrid",
                "country": "España",
                "contract_signed": False,
            },
            {
                "name": "Mango Fashion",
                "client_id": "CLI-004",
                "client_type": fashion,
                "billing_name": "Punto Fa S.L.",
                "cif": "B08598289",
                "billing_email": "contabilidad@mango.com",
                "billing_address": "Paseo de Gracia 55",
                "postal_code": "08007",
                "city": "Barcelona",
                "country": "España",
                "contract_signed": True,
            },
            {
                "name": "Nestlé Health Science",
                "client_id": "CLI-005",
                "client_type": pharma,
                "billing_name": "Nestlé España S.A.",
                "cif": "A08005449",
                "billing_email": "finance@nestle.es",
                "billing_address": "Gran Vía de les Corts Catalanes 4",
                "postal_code": "08902",
                "city": "Esplugues de Llobregat",
                "country": "España",
                "contract_signed": False,
            },
        ]

        created = 0
        for data in clients_data:
            _, was_created = ClientProfile.objects.get_or_create(
                client_id=data["client_id"],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Clientes: {created} creados, {len(clients_data) - created} ya existían")

    def _create_test_content_makers(self):
        cms_data = [
            {
                "stimada_id": "[CM] - TEST01",
                "first_name": "Lucía",
                "last_name": "García Martínez",
                "cm_type": "Influencer",
                "gender": "Mujer",
                "status": "Alta",
                "performance": "Excelente",
                "content_quality": "Alta",
                "appearance": "Trendy",
                "is_mother": False,
                "content_categories": "Moda, Lifestyle",
                "follows_stimada": True,
                "stimada_in_bio": True,
                "contract_signed": True,
                "fee_instagram": 350,
                "instagram_followers_category": "50K-100K",
                "instagram_followers": 78500,
                "instagram_handle": "luciagm_style",
                "instagram_link": "https://instagram.com/luciagm_style",
                "fee_tiktok": 250,
                "tiktok_followers_category": "25K-50K",
                "tiktok_followers": 34200,
                "tiktok_handle": "@luciagm_style",
                "tiktok_link": "https://tiktok.com/@luciagm_style",
                "top_size": "S",
                "bottom_size": "36",
                "shoe_size": "37",
                "height_measurements": "165cm · 85-62-90",
                "email": "lucia.garcia@email.com",
                "phone": "+34 612 345 678",
                "billing_address": "Calle Serrano 45, 3ºB",
                "postal_code": "28001",
                "province": "Madrid",
                "country": "España",
                "dni_cif": "12345678A",
                "iban": "ES12 1234 5678 9012 3456 7890",
                "comments": "Muy profesional, entrega contenido a tiempo. Excelente engagement.",
            },
            {
                "stimada_id": "[CM] - TEST02",
                "first_name": "María",
                "last_name": "López Fernández",
                "cm_type": "Micro-influencer",
                "gender": "Mujer",
                "status": "Alta",
                "performance": "Bueno",
                "content_quality": "Alta",
                "appearance": "Natural",
                "is_mother": True,
                "content_categories": "Maternidad, Lifestyle, Hogar",
                "follows_stimada": True,
                "stimada_in_bio": False,
                "contract_signed": True,
                "fee_instagram": 200,
                "instagram_followers_category": "10K-25K",
                "instagram_followers": 18700,
                "instagram_handle": "marialopez_mama",
                "instagram_link": "https://instagram.com/marialopez_mama",
                "fee_tiktok": 150,
                "tiktok_followers_category": "10K-25K",
                "tiktok_followers": 12400,
                "tiktok_handle": "@marialopez_mama",
                "tiktok_link": "https://tiktok.com/@marialopez_mama",
                "top_size": "M",
                "bottom_size": "38",
                "shoe_size": "38",
                "height_measurements": "170cm · 90-66-95",
                "email": "maria.lopez@email.com",
                "phone": "+34 623 456 789",
                "billing_address": "Avda. Diagonal 210, 5ºA",
                "postal_code": "08018",
                "province": "Barcelona",
                "country": "España",
                "dni_cif": "23456789B",
                "iban": "ES23 2345 6789 0123 4567 8901",
                "comments": "Contenido muy auténtico. Audiencia muy fiel en temática maternidad.",
            },
            {
                "stimada_id": "[CM] - TEST03",
                "first_name": "Carmen",
                "last_name": "Ruiz Sánchez",
                "cm_type": "UGC Creator",
                "gender": "Mujer",
                "status": "Alta",
                "performance": "Excelente",
                "content_quality": "Premium",
                "appearance": "Elegante",
                "is_mother": False,
                "content_categories": "Belleza, Skincare, Wellness",
                "follows_stimada": True,
                "stimada_in_bio": True,
                "contract_signed": True,
                "fee_instagram": 500,
                "instagram_followers_category": "100K-500K",
                "instagram_followers": 142000,
                "instagram_handle": "carmenruiz_beauty",
                "instagram_link": "https://instagram.com/carmenruiz_beauty",
                "fee_tiktok": 400,
                "tiktok_followers_category": "50K-100K",
                "tiktok_followers": 89000,
                "tiktok_handle": "@carmenruiz_beauty",
                "tiktok_link": "https://tiktok.com/@carmenruiz_beauty",
                "top_size": "XS",
                "bottom_size": "34",
                "shoe_size": "36",
                "height_measurements": "158cm · 80-58-86",
                "email": "carmen.ruiz@email.com",
                "phone": "+34 634 567 890",
                "billing_address": "Plaza Mayor 12, 2ºC",
                "postal_code": "46001",
                "province": "Valencia",
                "country": "España",
                "dni_cif": "34567890C",
                "iban": "ES34 3456 7890 1234 5678 9012",
                "comments": "Top creator. Trabaja con marcas premium. Resultados excepcionales en beauty.",
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
