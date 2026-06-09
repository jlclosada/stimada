from rest_framework import serializers

from apps.content_makers.models import ContentMakerProfile, DesempenoOption


class ContentMakerProjectSerializer(serializers.Serializer):
    """Lightweight project info for the CM detail view."""
    id = serializers.IntegerField()
    project_id = serializers.CharField()
    nombre = serializers.CharField()
    brand_name = serializers.CharField(allow_null=True)
    status_name = serializers.CharField(allow_null=True)
    fecha_servicio = serializers.DateField(allow_null=True)


class ContentMakerListSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    tiene_cuenta = serializers.BooleanField(read_only=True)
    user_email = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ContentMakerProfile
        fields = [
            "id", "stimada_id", "nombre_completo", "nombre", "apellidos",
            "tipo", "tipo_display",
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
    foto_url = serializers.SerializerMethodField()
    proyectos_asociados = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    desempeno_opciones = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DesempenoOption.objects.all(), required=False,
    )
    desempeno_opciones_display = serializers.SerializerMethodField()

    class Meta:
        model = ContentMakerProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]

    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None

    def get_foto_url(self, obj):
        if obj.foto:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None

    def get_desempeno_opciones_display(self, obj):
        return [{"id": o.id, "nombre": o.nombre} for o in obj.desempeno_opciones.all()]

    def update(self, instance, validated_data):
        desempeno_opciones = validated_data.pop("desempeno_opciones", None)
        instance = super().update(instance, validated_data)
        if desempeno_opciones is not None:
            instance.desempeno_opciones.set(desempeno_opciones)
        return instance

    def get_proyectos_asociados(self, obj):
        from apps.projects.models import Project, ProjectContentMaker

        # Projects where CM accepted/selected via ProjectContentMaker
        participation_project_ids = ProjectContentMaker.objects.filter(
            content_maker=obj,
            status__in=[ProjectContentMaker.STATUS_ACCEPTED, ProjectContentMaker.STATUS_SELECTED],
        ).values_list("project_id", flat=True)

        # Projects where CM is directly assigned
        direct_project_ids = Project.objects.filter(content_maker=obj).values_list("id", flat=True)

        all_ids = set(participation_project_ids) | set(direct_project_ids)
        if not all_ids:
            return []

        projects = Project.objects.filter(id__in=all_ids).select_related("brand", "status").order_by("-created_at")
        return ContentMakerProjectSerializer([
            {
                "id": p.id,
                "project_id": p.project_id,
                "nombre": p.nombre,
                "brand_name": p.brand.nombre if p.brand else None,
                "status_name": p.status.nombre if p.status else None,
                "fecha_servicio": p.fecha_servicio,
            }
            for p in projects
        ], many=True).data


class CreateAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class ContentMakerPublicSerializer(serializers.ModelSerializer):
    """Limited view for clients — hides sensitive/internal data like fees, billing, status."""
    nombre_completo = serializers.CharField(read_only=True)
    foto_url = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ContentMakerProfile
        fields = [
            "id", "stimada_id", "nombre", "apellidos", "nombre_completo",
            "tipo", "tipo_display",
            "tipo_cm", "sexo", "categorias_contenido",
            "es_mama",
            "instagram_handle", "link_instagram",
            "seguidores_instagram", "categoria_seguidores_ig",
            "tiktok_handle", "link_tiktok",
            "seguidores_tiktok", "categoria_seguidores_tt",
            "talla_arriba", "talla_abajo", "talla_pie", "altura_medidas",
            "foto_url",
        ]

    def get_foto_url(self, obj):
        if obj.foto:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None


class ContentMakerCreateSerializer(serializers.ModelSerializer):
    desempeno_opciones = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DesempenoOption.objects.all(), required=False,
    )

    class Meta:
        model = ContentMakerProfile
        exclude = ["user", "created_at", "updated_at"]
        extra_kwargs = {
            "stimada_id": {"required": False, "allow_blank": True},
            "dni_cif": {"required": True, "allow_blank": False},
            "direccion_facturacion": {"required": True, "allow_blank": False},
            "codigo_postal": {"required": True, "allow_blank": False},
            "provincia": {"required": True, "allow_blank": False},
            "pais": {"required": True, "allow_blank": False},
            "iban": {"required": True, "allow_blank": False},
        }

    def create(self, validated_data):
        desempeno_opciones = validated_data.pop("desempeno_opciones", [])
        instance = super().create(validated_data)
        if desempeno_opciones:
            instance.desempeno_opciones.set(desempeno_opciones)
        return instance

    def validate_link_instagram(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value

    def validate_link_tiktok(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value
