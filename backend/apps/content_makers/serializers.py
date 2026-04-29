from rest_framework import serializers

from apps.content_makers.models import ContentMakerProfile


class ContentMakerListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    tiene_cuenta = serializers.BooleanField(read_only=True)
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = ContentMakerProfile
        fields = [
            "id", "stimada_id", "nombre_completo", "nombre", "apellidos",
            "tipo_cm", "status", "categorias_contenido",
            "instagram_handle", "seguidores_instagram",
            "tiktok_handle", "seguidores_tiktok",
            "tiene_cuenta", "user_email", "email",
        ]

    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None


class ContentMakerDetailSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    tiene_cuenta = serializers.BooleanField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True, allow_null=True)
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = ContentMakerProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]

    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None


class CreateAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class ContentMakerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentMakerProfile
        exclude = ["user", "created_at", "updated_at"]

    def validate_stimada_id(self, value):
        if ContentMakerProfile.objects.filter(stimada_id=value).exists():
            raise serializers.ValidationError("Este ID de Stimada ya existe.")
        return value

    def validate_link_instagram(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value

    def validate_link_tiktok(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value
