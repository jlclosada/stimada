from rest_framework import serializers

from apps.clients.models import Brand, ClientProfile
from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    ServiceType,
)


class ProjectStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStatus
        fields = ["id", "nombre"]


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ["id", "nombre"]


class ProjectContentMakerSerializer(serializers.ModelSerializer):
    content_maker_id = serializers.IntegerField(source="content_maker.id", read_only=True)
    user_id = serializers.IntegerField(source="content_maker.user_id", read_only=True)
    nombre = serializers.SerializerMethodField()
    instagram_handle = serializers.CharField(
        source="content_maker.instagram_handle", read_only=True
    )
    seguidores_instagram = serializers.IntegerField(
        source="content_maker.seguidores_instagram", read_only=True
    )

    class Meta:
        model = ProjectContentMaker
        fields = [
            "id",
            "content_maker_id",
            "user_id",
            "nombre",
            "instagram_handle",
            "seguidores_instagram",
            "status",
            "is_recommended",
            "note",
        ]

    def get_nombre(self, obj):
        cm = obj.content_maker
        return f"{cm.nombre} {cm.apellidos}".strip()


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True)
    brand_name = serializers.CharField(source="brand.nombre", read_only=True, default=None)
    status_name = serializers.CharField(source="status.nombre", read_only=True, default=None)
    service_type_name = serializers.CharField(
        source="service_type.nombre", read_only=True, default=None
    )
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    content_maker_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "project_id",
            "nombre",
            "client_name",
            "brand_name",
            "status_name",
            "service_type_name",
            "base_imponible",
            "impuestos",
            "precio_total",
            "fecha_venta",
            "fecha_servicio",
            "fecha_fin",
            "cm_selection_mode",
            "content_maker_name",
            "created_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.nombre} {obj.content_maker.apellidos}".strip()
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True)
    brand_name = serializers.CharField(source="brand.nombre", read_only=True, default=None)
    status_name = serializers.CharField(source="status.nombre", read_only=True, default=None)
    service_type_name = serializers.CharField(
        source="service_type.nombre", read_only=True, default=None
    )
    precio_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    content_makers = ProjectContentMakerSerializer(many=True, read_only=True)
    content_maker_name = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "project_id",
            "nombre",
            "descripcion",
            "client",
            "client_name",
            "brand",
            "brand_name",
            "status",
            "status_name",
            "service_type",
            "service_type_name",
            "base_imponible",
            "impuestos",
            "precio_total",
            "fecha_venta",
            "fecha_servicio",
            "fecha_fin",
            "cm_selection_mode",
            "content_maker",
            "content_maker_name",
            "content_makers",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.nombre} {obj.content_maker.apellidos}".strip()
        return None


class ProjectCreateSerializer(serializers.ModelSerializer):
    recommended_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        default=[],
    )

    class Meta:
        model = Project
        fields = [
            "project_id",
            "nombre",
            "descripcion",
            "client",
            "brand",
            "status",
            "service_type",
            "base_imponible",
            "impuestos",
            "fecha_venta",
            "fecha_servicio",
            "fecha_fin",
            "cm_selection_mode",
            "content_maker",
            "recommended_cms",
        ]

    def validate(self, data):
        mode = data.get("cm_selection_mode", Project.CM_SELECTION_CLIENT_CHOOSES)
        if mode == Project.CM_SELECTION_DEFINED and not data.get("content_maker"):
            raise serializers.ValidationError(
                {"content_maker": "Debes seleccionar una content maker en modo 'definida'."}
            )
        if mode == Project.CM_SELECTION_RECOMMENDED and not data.get("recommended_cms"):
            raise serializers.ValidationError(
                {"recommended_cms": "Debes recomendar al menos una content maker."}
            )
        return data

    def create(self, validated_data):
        recommended_cms = validated_data.pop("recommended_cms", [])
        project = Project.objects.create(**validated_data)

        # Create recommended CM entries
        if recommended_cms:
            cms = ContentMakerProfile.objects.filter(id__in=recommended_cms)
            ProjectContentMaker.objects.bulk_create([
                ProjectContentMaker(
                    project=project,
                    content_maker=cm,
                    is_recommended=True,
                    status=ProjectContentMaker.STATUS_PENDING,
                )
                for cm in cms
            ])

        # If a CM is directly defined, also add to junction table
        if project.content_maker:
            ProjectContentMaker.objects.get_or_create(
                project=project,
                content_maker=project.content_maker,
                defaults={"status": ProjectContentMaker.STATUS_ACCEPTED},
            )

        # Create notifications based on selection mode
        self._create_notifications(project)

        return project

    def _create_notifications(self, project):
        mode = project.cm_selection_mode

        # Always notify the client about the new project (if they have an account)
        if project.client.user:
            if mode == Project.CM_SELECTION_CLIENT_CHOOSES or mode == Project.CM_SELECTION_RECOMMENDED:
                Notification.objects.create(
                    recipient=project.client.user,
                    notification_type=Notification.TYPE_PROJECT_CM_SELECT,
                    title="Selecciona una Content Maker",
                    message=f'El proyecto "{project.nombre}" necesita que elijas una Content Maker.',
                    project=project,
                )
            else:
                Notification.objects.create(
                    recipient=project.client.user,
                    notification_type=Notification.TYPE_PROJECT_CM_SELECT,
                    title="Nuevo proyecto creado",
                    message=f'Se ha creado el proyecto "{project.nombre}" con una Content Maker ya asignada.',
                    project=project,
                )

        # Notify the CM if already defined
        if mode == Project.CM_SELECTION_DEFINED and project.content_maker:
            if project.content_maker.user:
                Notification.objects.create(
                    recipient=project.content_maker.user,
                    notification_type=Notification.TYPE_PROJECT_CM_REQUEST,
                    title="Nuevo proyecto disponible",
                    message=f'Has sido seleccionada para el proyecto "{project.nombre}". ¿Aceptas?',
                    project=project,
                )


class NotificationSerializer(serializers.ModelSerializer):
    project_id_display = serializers.CharField(
        source="project.project_id", read_only=True, default=None
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "project",
            "project_id_display",
            "read",
            "created_at",
        ]
        read_only_fields = ["notification_type", "title", "message", "project", "created_at"]
