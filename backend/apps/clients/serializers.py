from rest_framework import serializers

from apps.clients.models import ClientProfile, ClientType


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
            "cif", "ciudad", "pais", "contrato_firmado",
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


class ClientProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        exclude = ["created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
