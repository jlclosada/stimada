from rest_framework import serializers

from apps.clients.models import Brand, ClientProfile
from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Briefing,
    BriefingLink,
    BriefingPhoto,
    Deliverable,
    Format,
    ProductLogistics,
    EconomicModel,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    WhoRecords,
    WhoPublishes,
    WhoReviews,
    ProductPickup,
    SocialNetwork,
    ServiceType,
    StatusChangeLog,
    WinStatus,
)


class ProjectStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStatus
        fields = ["id", "name", "available_on_creation"]


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ["id", "name", "requires_profiles"]


class SocialNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialNetwork
        fields = ["id", "name"]


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = ["id", "name"]


class EconomicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomicModel
        fields = ["id", "name"]


class ProductLogisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLogistics
        fields = ["id", "name"]


class ProductPickupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPickup
        fields = ["id", "name"]


class WhoRecordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhoRecords
        fields = ["id", "name"]


class WhoReviewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhoReviews
        fields = ["id", "name"]


class WhoPublishesSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhoPublishes
        fields = ["id", "name"]


class WinStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WinStatus
        fields = ["id", "name"]


class ProjectContentMakerSerializer(serializers.ModelSerializer):
    content_maker_id = serializers.IntegerField(source="content_maker.id", read_only=True)
    user_id = serializers.IntegerField(source="content_maker.user_id", read_only=True)
    name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    instagram_handle = serializers.CharField(
        source="content_maker.instagram_handle", read_only=True
    )
    instagram_followers = serializers.IntegerField(
        source="content_maker.instagram_followers", read_only=True
    )

    class Meta:
        model = ProjectContentMaker
        fields = [
            "id",
            "content_maker_id",
            "user_id",
            "name",
            "photo_url",
            "instagram_handle",
            "instagram_followers",
            "status",
            "is_recommended",
            "is_substitute",
            "note",
            "responded_at",
        ]

    def get_name(self, obj):
        cm = obj.content_maker
        return f"{cm.first_name} {cm.last_name}".strip()

    def get_photo_url(self, obj):
        cm = obj.content_maker
        if cm.photo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(cm.photo.url)
            return cm.photo.url
        return None


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    status_name = serializers.CharField(source="status.name", read_only=True, default=None)
    service_type_name = serializers.CharField(
        source="service_type.name", read_only=True, default=None
    )
    economic_model_name = serializers.CharField(
        source="economic_model.name", read_only=True, default=None
    )
    win_status_name = serializers.CharField(
        source="win_status.name", read_only=True, default=None
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    content_maker_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "project_id",
            "name",
            "client_name",
            "brand_name",
            "status_name",
            "service_type_name",
            "economic_model_name",
            "win_status_name",
            "traffic_light",
            "tax_base",
            "taxes",
            "total_price",
            "sale_date",
            "service_date",
            "end_date",
            "cm_selection_mode",
            "content_maker_name",
            "delayed",
            "is_draft",
            "is_active",
            "created_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.first_name} {obj.content_maker.last_name}".strip()
        # Show accepted CMs from ProjectContentMaker
        accepted_cms = obj.content_makers.filter(status=ProjectContentMaker.STATUS_ACCEPTED)
        if accepted_cms.exists():
            names = [f"{pcm.content_maker.first_name} {pcm.content_maker.last_name}".strip() for pcm in accepted_cms]
            return ", ".join(names)
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True, default=None)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    status_name = serializers.CharField(source="status.name", read_only=True, default=None)
    service_type_name = serializers.CharField(
        source="service_type.name", read_only=True, default=None
    )
    economic_model_name = serializers.CharField(
        source="economic_model.name", read_only=True, default=None
    )
    product_logistics_name = serializers.CharField(
        source="product_logistics.name", read_only=True, default=None
    )
    product_pickup_name = serializers.CharField(
        source="product_pickup.name", read_only=True, default=None
    )
    who_records_name = serializers.CharField(
        source="who_records.name", read_only=True, default=None
    )
    who_reviews_name = serializers.CharField(
        source="who_reviews.name", read_only=True, default=None
    )
    who_publishes_name = serializers.CharField(
        source="who_publishes.name", read_only=True, default=None
    )
    win_status_name = serializers.CharField(
        source="win_status.name", read_only=True, default=None
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    gross_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    social_networks = SocialNetworkSerializer(many=True, read_only=True)
    formats = FormatSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    content_maker_name = serializers.SerializerMethodField()
    content_makers = ProjectContentMakerSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True, default=None
    )
    briefings = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "project_id",
            "name",
            "description",
            "client",
            "client_name",
            "brand",
            "brand_name",
            "status",
            "status_name",
            "service_type",
            "service_type_name",
            # Servicio: red social y formato
            "social_networks",
            "formats",
            # Modalidad operativa
            "economic_model",
            "economic_model_name",
            "product_logistics",
            "product_logistics_name",
            "product_pickup",
            "product_pickup_name",
            "who_records",
            "who_records_name",
            "who_reviews",
            "who_reviews_name",
            "who_publishes",
            "who_publishes_name",
            "product_return",
            # Estado y pipeline
            "win_status",
            "win_status_name",
            "traffic_light",
            "delayed",
            "is_active",
            # Económica
            "fee",
            "num_contents",
            "num_profiles",
            "gifting",
            "discount_active",
            "discount_percentage",
            "tax_base",
            "taxes",
            "gross_price",
            "final_price",
            "total_price",
            # Fechas
            "sale_date",
            "service_date",
            "product_arrival_date",
            "delivery_deadline",
            "end_date",
            # CMs
            "cm_selection_mode",
            "content_maker",
            "content_maker_name",
            "content_makers",
            "briefings",
            # Meta
            "comments",
            "is_draft",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def get_content_maker_name(self, obj):
        if obj.content_maker:
            return f"{obj.content_maker.first_name} {obj.content_maker.last_name}".strip()
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
    substitute_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        default=[],
    )
    social_networks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=SocialNetwork.objects.all(), required=False, default=[]
    )
    formats = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Format.objects.all(), required=False, default=[]
    )
    is_draft = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Project
        fields = [
            "project_id",
            "name",
            "description",
            "client",
            "brand",
            "status",
            "service_type",
            # Servicio: red social y formato
            "social_networks",
            "formats",
            # Modalidad operativa
            "economic_model",
            "product_logistics",
            "product_pickup",
            "who_records",
            "who_reviews",
            "who_publishes",
            "product_return",
            # Estado y pipeline
            "win_status",
            "traffic_light",
            "comments",
            # Económica
            "fee",
            "num_contents",
            "num_profiles",
            "gifting",
            "discount_active",
            "discount_percentage",
            "tax_base",
            "taxes",
            # Fechas
            "sale_date",
            "service_date",
            "product_arrival_date",
            "delivery_deadline",
            "end_date",
            # CM
            "cm_selection_mode",
            "content_maker",
            "recommended_cms",
            "defined_cms",
            "substitute_cms",
            "is_draft",
        ]
        extra_kwargs = {
            "project_id": {"required": False, "allow_blank": True},
            "client": {"required": False, "allow_null": True},
            "brand": {"required": True},
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
            for field_name in ("name", "brand"):
                if field_name in fields:
                    fields[field_name].required = False
                    fields[field_name].allow_null = True
                    if hasattr(fields[field_name], "allow_blank"):
                        fields[field_name].allow_blank = True
        return fields

    def validate(self, data):
        is_draft = data.get("is_draft", False)
        if is_draft:
            # Auto-inherit client from brand even for drafts
            brand = data.get("brand")
            if brand:
                data["client"] = brand.client
            return data
        # Auto-inherit client from brand (always)
        brand = data.get("brand")
        if brand:
            data["client"] = brand.client
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
        substitute_cms = validated_data.pop("substitute_cms", [])
        social_networks = validated_data.pop("social_networks", [])
        formats = validated_data.pop("formats", [])
        is_draft = validated_data.pop("is_draft", False)

        if is_draft:
            validated_data["is_draft"] = True
            # Generate placeholder project_id if not provided
            if not validated_data.get("project_id"):
                validated_data["project_id"] = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
            # Set a placeholder name if not provided
            if not validated_data.get("name"):
                validated_data["name"] = "Borrador sin título"
            # Assign "Borrador" status
            borrador_status = ProjectStatus.objects.filter(name="Borrador").first()
            if borrador_status:
                validated_data["status"] = borrador_status

        project = Project.objects.create(**validated_data)

        # Assign many-to-many service options
        if social_networks:
            project.social_networks.set(social_networks)
        if formats:
            project.formats.set(formats)

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

        # Handle defined CMs (multiple) - Principales
        if defined_cms:
            cms = ContentMakerProfile.objects.filter(id__in=defined_cms)
            for cm in cms:
                ProjectContentMaker.objects.get_or_create(
                    project=project,
                    content_maker=cm,
                    defaults={"status": ProjectContentMaker.STATUS_PENDING, "is_substitute": False},
                )
        # Legacy single CM support
        elif project.content_maker:
            ProjectContentMaker.objects.get_or_create(
                project=project,
                content_maker=project.content_maker,
                defaults={"status": ProjectContentMaker.STATUS_PENDING},
            )

        # Handle substitute CMs
        if substitute_cms:
            cms = ContentMakerProfile.objects.filter(id__in=substitute_cms)
            for cm in cms:
                ProjectContentMaker.objects.get_or_create(
                    project=project,
                    content_maker=cm,
                    defaults={
                        "status": ProjectContentMaker.STATUS_PENDING,
                        "is_substitute": True,
                    },
                )

        # Create notifications based on selection mode (skip for drafts)
        if not project.is_draft:
            self._create_notifications(project, defined_cms)

            # Evaluate automatic state transition based on assigned CMs
            from apps.projects.services import transition_project_status
            transition_project_status(project)

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
                    message=f'El proyecto "{project.name}" necesita que elijas una Content Maker.',
                    project=project,
                )
            else:
                Notification.objects.create(
                    recipient=project.client.user,
                    notification_type=Notification.TYPE_PROJECT_CM_SELECT,
                    title="Nuevo proyecto creado",
                    message=f'Se ha creado el proyecto "{project.name}" con Content Makers asignadas.',
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
                            message=f'Has sido seleccionada para el proyecto "{project.name}". ¿Aceptas?',
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
    substitute_cms = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )
    social_networks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=SocialNetwork.objects.all(), required=False
    )
    formats = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Format.objects.all(), required=False
    )

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "brand",
            "status",
            "service_type",
            # Servicio: red social y formato
            "social_networks",
            "formats",
            # Modalidad operativa
            "economic_model",
            "product_logistics",
            "product_pickup",
            "who_records",
            "who_reviews",
            "who_publishes",
            "product_return",
            # Estado y pipeline
            "win_status",
            "traffic_light",
            "comments",
            # Económica
            "fee",
            "num_contents",
            "num_profiles",
            "gifting",
            "discount_active",
            "discount_percentage",
            "tax_base",
            "taxes",
            # Fechas
            "sale_date",
            "service_date",
            "product_arrival_date",
            "delivery_deadline",
            "end_date",
            # CM
            "cm_selection_mode",
            "content_maker",
            "recommended_cms",
            "defined_cms",
            "substitute_cms",
            "is_draft",
        ]

    def validate(self, data):
        # Auto-inherit client from brand
        brand = data.get("brand")
        if brand:
            data["client"] = brand.client
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
        social_networks = validated_data.pop("social_networks", None)
        formats = validated_data.pop("formats", None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update many-to-many service options
        if social_networks is not None:
            instance.social_networks.set(social_networks)
        if formats is not None:
            instance.formats.set(formats)

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
                        message=f'Has sido seleccionada para el proyecto "{instance.name}". ¿Aceptas?',
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


class BriefingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BriefingLink
        fields = ["id", "url", "title", "order"]


class BriefingPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BriefingPhoto
        fields = ["id", "image", "image_url", "description", "order"]
        extra_kwargs = {"image": {"write_only": True}}

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class BriefingSerializer(serializers.ModelSerializer):
    content_maker_name = serializers.SerializerMethodField()
    links = BriefingLinkSerializer(many=True, read_only=True)
    photos = BriefingPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Briefing
        fields = [
            "id",
            "project",
            "content_maker",
            "content_maker_name",
            "comments",
            "links",
            "photos",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_content_maker_name(self, obj):
        cm = obj.content_maker
        return f"{cm.first_name} {cm.last_name}".strip()


class DeliverableSerializer(serializers.ModelSerializer):
    content_maker_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    can_request_revision = serializers.BooleanField(read_only=True)

    class Meta:
        model = Deliverable
        fields = [
            "id",
            "project",
            "content_maker",
            "content_maker_name",
            "file",
            "description",
            "status",
            "revision_round",
            "revision_notes",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "published_at",
            "uploaded_at",
            "can_request_revision",
        ]
        read_only_fields = [
            "uploaded_at", "reviewed_at", "reviewed_by",
            "revision_round", "can_request_revision",
        ]

    def get_content_maker_name(self, obj):
        cm = obj.content_maker
        return f"{cm.first_name} {cm.last_name}".strip()

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.full_name
        return None


class StatusChangeLogSerializer(serializers.ModelSerializer):
    from_status_name = serializers.SerializerMethodField()
    to_status_name = serializers.SerializerMethodField()
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StatusChangeLog
        fields = [
            "id",
            "from_status",
            "from_status_name",
            "to_status",
            "to_status_name",
            "is_manual",
            "reason",
            "changed_by",
            "changed_by_name",
            "timestamp",
        ]

    def get_from_status_name(self, obj):
        return obj.from_status.name if obj.from_status else None

    def get_to_status_name(self, obj):
        return obj.to_status.name if obj.to_status else None

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.full_name
        return "Sistema"
