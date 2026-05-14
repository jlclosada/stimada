from rest_framework import serializers

from apps.clients.models import ClientProfile, ClientType


class ClientProjectSerializer(serializers.Serializer):
    """Lightweight project info for the client detail view."""
    id = serializers.IntegerField()
    project_id = serializers.CharField()
    nombre = serializers.CharField()
    brand_name = serializers.CharField(allow_null=True)
    status_name = serializers.CharField(allow_null=True)
    fecha_servicio = serializers.DateField(allow_null=True)
    content_maker_name = serializers.CharField(allow_null=True)


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
            "id", "cliente_id", "nombre_cliente", "tipo_nombre",
            "cif", "ciudad", "pais", "contrato_firmado", "es_agencia",
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
    proyectos_asociados = serializers.SerializerMethodField()

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

    def get_proyectos_asociados(self, obj):
        from apps.projects.models import Project

        projects = Project.objects.filter(client=obj).select_related("brand", "status", "content_maker").order_by("-created_at")
        return ClientProjectSerializer([
            {
                "id": p.id,
                "project_id": p.project_id,
                "nombre": p.nombre,
                "brand_name": p.brand.nombre if p.brand else None,
                "status_name": p.status.nombre if p.status else None,
                "fecha_servicio": p.fecha_servicio,
                "content_maker_name": f"{p.content_maker.nombre} {p.content_maker.apellidos}".strip() if p.content_maker else None,
            }
            for p in projects
        ], many=True).data


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
