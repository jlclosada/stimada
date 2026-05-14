from rest_framework import serializers

from apps.clients.models import Brand, ClientProfile
from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Briefing,
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
    foto_url = serializers.SerializerMethodField()
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
            "foto_url",
            "instagram_handle",
            "seguidores_instagram",
            "status",
            "is_recommended",
            "note",
        ]

    def get_nombre(self, obj):
        cm = obj.content_maker
        return f"{cm.nombre} {cm.apellidos}".strip()

    def get_foto_url(self, obj):
        cm = obj.content_maker
        if cm.foto:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(cm.foto.url)
            return cm.foto.url
        return None


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True, default=None)
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
            "is_draft",
            "created_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.nombre} {obj.content_maker.apellidos}".strip()
        # Show accepted CMs from ProjectContentMaker
        accepted_cms = obj.content_makers.filter(status=ProjectContentMaker.STATUS_ACCEPTED)
        if accepted_cms.exists():
            names = [f"{pcm.content_maker.nombre} {pcm.content_maker.apellidos}".strip() for pcm in accepted_cms]
            return ", ".join(names)
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.nombre_cliente", read_only=True, default=None)
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
    briefings = serializers.SerializerMethodField()

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
            "briefings",
            "is_draft",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.nombre} {obj.content_maker.apellidos}".strip()
        return None

    def get_briefings(self, obj):
        from apps.projects.serializers import BriefingSerializer
        return BriefingSerializer(obj.briefings.all(), many=True).data


class ProjectCreateSerializer(serializers.ModelSerializer):
    recommended_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        default=[],
    )
    defined_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        default=[],
    )
    is_draft = serializers.BooleanField(required=False, default=False)

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
            "defined_cms",
            "is_draft",
        ]
        extra_kwargs = {
            "project_id": {"required": False, "allow_blank": True},
        }

    def get_fields(self):
        fields = super().get_fields()
        # project_id is always optional (auto-generated)
        if "project_id" in fields:
            fields["project_id"].required = False
            fields["project_id"].allow_blank = True
        # Check if this is a draft request
        request = self.context.get("request")
        is_draft = False
        if request and request.data:
            is_draft = request.data.get("is_draft", False)
        if is_draft:
            # Make required fields optional for drafts
            for field_name in ("nombre", "client"):
                if field_name in fields:
                    fields[field_name].required = False
                    fields[field_name].allow_null = True
                    if hasattr(fields[field_name], "allow_blank"):
                        fields[field_name].allow_blank = True
        return fields

    def validate(self, data):
        is_draft = data.get("is_draft", False)
        if is_draft:
            return data
        mode = data.get("cm_selection_mode", Project.CM_SELECTION_CLIENT_CHOOSES)
        if mode == Project.CM_SELECTION_DEFINED:
            has_single = data.get("content_maker")
            has_multiple = data.get("defined_cms")
            if not has_single and not has_multiple:
                raise serializers.ValidationError(
                    {"defined_cms": "Debes seleccionar al menos una content maker en modo 'definida'."}
                )
        if mode == Project.CM_SELECTION_RECOMMENDED and not data.get("recommended_cms"):
            raise serializers.ValidationError(
                {"recommended_cms": "Debes recomendar al menos una content maker."}
            )
        return data

    def create(self, validated_data):
        import uuid

        recommended_cms = validated_data.pop("recommended_cms", [])
        defined_cms = validated_data.pop("defined_cms", [])
        is_draft = validated_data.pop("is_draft", False)

        if is_draft:
            validated_data["is_draft"] = True
            # Generate placeholder project_id if not provided
            if not validated_data.get("project_id"):
                validated_data["project_id"] = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
            # Set a placeholder name if not provided
            if not validated_data.get("nombre"):
                validated_data["nombre"] = "Borrador sin título"
            # Assign "Borrador" status
            borrador_status = ProjectStatus.objects.filter(nombre="Borrador").first()
            if borrador_status:
                validated_data["status"] = borrador_status

        project = Project.objects.create(**validated_data)

        # Create recommended CM entries
        if recommended_cms:
            cms = ContentMakerProfile.objects.filter(id__in=recommended_cms)
            ProjectContentMaker.objects.bulk_create([
                ProjectContentMaker(
                    project=project,
                    content_maker=cm,
                    is_recommended=True,
                    status=ProjectContentMaker.STATUS_RECOMMENDED,
                )
                for cm in cms
            ])

        # Handle defined CMs (multiple)
        if defined_cms:
            cms = ContentMakerProfile.objects.filter(id__in=defined_cms)
            for cm in cms:
                ProjectContentMaker.objects.get_or_create(
                    project=project,
                    content_maker=cm,
                    defaults={"status": ProjectContentMaker.STATUS_PENDING},
                )
        # Legacy single CM support
        elif project.content_maker:
            ProjectContentMaker.objects.get_or_create(
                project=project,
                content_maker=project.content_maker,
                defaults={"status": ProjectContentMaker.STATUS_PENDING},
            )

        # Create notifications based on selection mode (skip for drafts)
        if not project.is_draft:
            self._create_notifications(project, defined_cms)

        return project

    def _create_notifications(self, project, defined_cms=None):
        mode = project.cm_selection_mode

        # Always notify the client about the new project (if they have an account)
        if project.client and project.client.user:
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
                    message=f'Se ha creado el proyecto "{project.nombre}" con Content Makers asignadas.',
                    project=project,
                )

        # Notify all defined CMs
        if mode == Project.CM_SELECTION_DEFINED:
            cm_ids = defined_cms or []
            if not cm_ids and project.content_maker:
                cm_ids = [project.content_maker.id]
            if cm_ids:
                cms = ContentMakerProfile.objects.filter(id__in=cm_ids)
                for cm in cms:
                    if cm.user:
                        Notification.objects.create(
                            recipient=cm.user,
                            notification_type=Notification.TYPE_PROJECT_CM_REQUEST,
                            title="Nuevo proyecto disponible",
                            message=f'Has sido seleccionada para el proyecto "{project.nombre}". ¿Aceptas?',
                            project=project,
                        )


class ProjectUpdateSerializer(serializers.ModelSerializer):
    recommended_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )
    defined_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Project
        fields = [
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
            "defined_cms",
            "is_draft",
        ]

    def validate(self, data):
        mode = data.get("cm_selection_mode", self.instance.cm_selection_mode if self.instance else None)
        if mode == Project.CM_SELECTION_DEFINED:
            has_defined = "defined_cms" in data and data["defined_cms"]
            has_existing = self.instance and self.instance.content_makers.filter(
                status__in=[ProjectContentMaker.STATUS_PENDING, ProjectContentMaker.STATUS_ACCEPTED]
            ).exists() if self.instance else False
            if "defined_cms" in data and not has_defined:
                raise serializers.ValidationError(
                    {"defined_cms": "Debes seleccionar al menos una content maker en modo 'definida'."}
                )
        if mode == Project.CM_SELECTION_RECOMMENDED:
            if "recommended_cms" in data and not data["recommended_cms"]:
                raise serializers.ValidationError(
                    {"recommended_cms": "Debes recomendar al menos una content maker."}
                )
        return data

    def update(self, instance, validated_data):
        recommended_cms = validated_data.pop("recommended_cms", None)
        defined_cms = validated_data.pop("defined_cms", None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle CM assignment changes
        if defined_cms is not None:
            # Remove old non-accepted CMs and replace with new defined ones
            instance.content_makers.filter(
                status__in=[
                    ProjectContentMaker.STATUS_PENDING,
                    ProjectContentMaker.STATUS_RECOMMENDED,
                    ProjectContentMaker.STATUS_REJECTED,
                ]
            ).delete()
            cms = ContentMakerProfile.objects.filter(id__in=defined_cms)
            existing_ids = set(
                instance.content_makers.values_list("content_maker_id", flat=True)
            )
            new_cms = []
            for cm in cms:
                if cm.id not in existing_ids:
                    new_cms.append(cm)
                    ProjectContentMaker.objects.create(
                        project=instance,
                        content_maker=cm,
                        status=ProjectContentMaker.STATUS_PENDING,
                    )
            # Notify newly added CMs
            for cm in new_cms:
                if cm.user:
                    Notification.objects.create(
                        recipient=cm.user,
                        notification_type=Notification.TYPE_PROJECT_CM_REQUEST,
                        title="Nuevo proyecto disponible",
                        message=f'Has sido seleccionada para el proyecto "{instance.nombre}". ¿Aceptas?',
                        project=instance,
                    )

        elif recommended_cms is not None:
            # Remove old recommended CMs and replace
            instance.content_makers.filter(
                status=ProjectContentMaker.STATUS_RECOMMENDED,
            ).delete()
            cms = ContentMakerProfile.objects.filter(id__in=recommended_cms)
            existing_ids = set(
                instance.content_makers.values_list("content_maker_id", flat=True)
            )
            for cm in cms:
                if cm.id not in existing_ids:
                    ProjectContentMaker.objects.create(
                        project=instance,
                        content_maker=cm,
                        is_recommended=True,
                        status=ProjectContentMaker.STATUS_RECOMMENDED,
                    )

        return instance


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


class BriefingSerializer(serializers.ModelSerializer):
    content_maker_name = serializers.SerializerMethodField()

    class Meta:
        model = Briefing
        fields = [
            "id",
            "project",
            "content_maker",
            "content_maker_name",
            "link_referencia",
            "comentarios",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_content_maker_name(self, obj):
        cm = obj.content_maker
        return f"{cm.nombre} {cm.apellidos}".strip()
