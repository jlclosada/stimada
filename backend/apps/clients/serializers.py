from rest_framework import serializers

from apps.clients.models import Brand, ClientProfile, ClientType


class ClientTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientType
        fields = ["id", "nombre", "slug"]


class ClientProfileListSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id", "cliente_id", "nombre_cliente", "tipo_cliente", "tipo_nombre",
            "web_instagram", "cif", "ciudad", "pais", "contrato_firmado", "es_agencia",
            "estado", "semaforo_cliente",
            "created_by_name", "created_at",
        ]

    def get_tipo_nombre(self, obj):
        return obj.tipo_cliente.nombre if obj.tipo_cliente_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by_id else None


class ClientProfileDetailSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    contrato_url = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    has_account = serializers.SerializerMethodField()
    marcas = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = "__all__"

    def get_tipo_nombre(self, obj):
        return obj.tipo_cliente.nombre if obj.tipo_cliente_id else None

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by_id else None

    def get_contrato_url(self, obj):
        if obj.contrato:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.contrato.url) if request else obj.contrato.url
        return None

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_user_name(self, obj):
        return obj.user.full_name if obj.user else None

    def get_has_account(self, obj):
        return obj.user_id is not None

    def get_marcas(self, obj):
        brands = obj.brands.select_related("tipo_marca").all()
        return [
            {
                "id": b.id,
                "brand_id": b.brand_id,
                "nombre": b.nombre,
                "tipo_marca_nombre": b.tipo_marca.nombre if b.tipo_marca_id else None,
                "web_instagram": b.web_instagram,
                "estado": b.estado,
            }
            for b in brands
        ]




class ClientProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        exclude = ["created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "cliente_id": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class BrandListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True)
    tipo_marca_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id", "brand_id", "nombre", "client", "client_name",
            "tipo_marca", "tipo_marca_nombre", "web_instagram",
            "estado", "created_at",
        ]

    def get_tipo_marca_nombre(self, obj):
        return obj.tipo_marca.nombre if obj.tipo_marca_id else None


class BrandDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True)
    tipo_marca_nombre = serializers.SerializerMethodField()
    proyectos = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            "id", "brand_id", "nombre", "client", "client_name",
            "tipo_marca", "tipo_marca_nombre", "web_instagram",
            "notas", "estado", "created_at", "proyectos",
        ]

    def get_tipo_marca_nombre(self, obj):
        return obj.tipo_marca.nombre if obj.tipo_marca_id else None

    def get_proyectos(self, obj):
        projects = obj.projects.select_related("status", "content_maker").order_by("-created_at")
        return [
            {
                "id": p.id,
                "project_id": p.project_id,
                "nombre": p.nombre,
                "status_name": p.status.nombre if p.status else None,
                "fecha_servicio": p.fecha_servicio,
                "content_maker_name": f"{p.content_maker.nombre} {p.content_maker.apellidos}".strip() if p.content_maker else None,
            }
            for p in projects
        ]


class BrandCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["nombre", "client", "tipo_marca", "web_instagram", "notas", "estado"]
