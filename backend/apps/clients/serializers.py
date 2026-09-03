from rest_framework import serializers

from apps.clients.models import Brand, ClientProfile, ClientType


class ClientTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientType
        fields = ["id", "name", "slug"]


class ClientProfileListSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    has_account = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id", "client_id", "name", "client_type", "type_name",
            "web_instagram", "cif", "city", "country", "contract_signed", "is_agency",
            "status", "traffic_light", "has_account",
            "created_by_name", "created_at",
        ]

    def get_type_name(self, obj):
        return obj.client_type.name if obj.client_type_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by_id else None

    def get_has_account(self, obj):
        return obj.user_id is not None


class ClientProfileDetailSerializer(serializers.ModelSerializer):
    type_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    contract_url = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    has_account = serializers.SerializerMethodField()
    brands = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = "__all__"

    def get_type_name(self, obj):
        return obj.client_type.name if obj.client_type_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by_id else None

    def get_contract_url(self, obj):
        if obj.contract:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.contract.url) if request else obj.contract.url
        return None

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else None

    def get_has_account(self, obj):
        return obj.user_id is not None

    def get_brands(self, obj):
        brands = obj.brands.select_related("brand_type").all()
        return [
            {
                "id": b.id,
                "brand_id": b.brand_id,
                "name": b.name,
                "brand_type_name": b.brand_type.name if b.brand_type_id else None,
                "web_instagram": b.web_instagram,
                "status": b.status,
            }
            for b in brands
        ]




class ClientProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        exclude = ["created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "client_id": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        instance = super().create(validated_data)

        # If the client is NOT an agency, an eponymous brand is automatically
        # created with the data inherited from the client (own brand).
        if not instance.is_agency:
            Brand.objects.get_or_create(
                client=instance,
                name=instance.name,
                defaults={
                    "brand_type": instance.client_type,
                    "web_instagram": instance.web_instagram,
                    "contact_person": instance.contact_person,
                    "contact_email": instance.contact_email,
                    "phone": instance.phone,
                    "status": Brand.STATUS_ACTIVE,
                },
            )
        return instance


class BrandListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    brand_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id", "brand_id", "name", "client", "client_name",
            "brand_type", "brand_type_name", "web_instagram",
            "status", "created_at",
        ]

    def get_brand_type_name(self, obj):
        return obj.brand_type.name if obj.brand_type_id else None


class BrandDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    brand_type_name = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()
    client_data = serializers.SerializerMethodField()
    effective_contact = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id", "brand_id", "name", "client", "client_name",
            "brand_type", "brand_type_name", "web_instagram",
            "contact_person", "contact_email", "phone",
            "notes", "status", "created_at", "projects",
            "client_data", "effective_contact",
        ]

    def get_brand_type_name(self, obj):
        return obj.brand_type.name if obj.brand_type_id else None

    def get_projects(self, obj):
        projects = obj.projects.select_related("status", "content_maker").order_by("-created_at")
        return [
            {
                "id": p.id,
                "project_id": p.project_id,
                "name": p.name,
                "status_name": p.status.name if p.status else None,
                "service_date": p.service_date,
                "content_maker_name": f"{p.content_maker.first_name} {p.content_maker.last_name}".strip() if p.content_maker else None,
            }
            for p in projects
        ]

    def get_client_data(self, obj):
        """Return inherited client data for the brand detail view."""
        c = obj.client
        return {
            "id": c.id,
            "client_id": c.client_id,
            "name": c.name,
            "is_agency": c.is_agency,
            "type_name": c.client_type.name if c.client_type_id else None,
            "web_instagram": c.web_instagram,
            "contact_person": c.contact_person,
            "contact_email": c.contact_email,
            "phone": c.phone,
            "billing_name": c.billing_name,
            "cif": c.cif,
            "billing_email": c.billing_email,
            "billing_address": c.billing_address,
            "postal_code": c.postal_code,
            "city": c.city,
            "country": c.country,
            "status": c.status,
        }

    def get_effective_contact(self, obj):
        """Return effective contact: brand's own if set, otherwise inherited from client."""
        c = obj.client
        has_own = bool(obj.contact_person or obj.contact_email or obj.phone)
        return {
            "contact_person": obj.contact_person or c.contact_person,
            "contact_email": obj.contact_email or c.contact_email,
            "phone": obj.phone or c.phone,
            "is_own": has_own,
        }


class BrandCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "name", "client", "brand_type", "web_instagram",
            "contact_person", "contact_email", "phone",
            "notes", "status",
        ]
