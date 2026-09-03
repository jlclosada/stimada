from rest_framework import serializers

from apps.content_makers.models import ContentMakerProfile, PerformanceOption


class ContentMakerProjectSerializer(serializers.Serializer):
    """Lightweight project info for the CM detail view."""
    id = serializers.IntegerField()
    project_id = serializers.CharField()
    name = serializers.CharField()
    brand_name = serializers.CharField(allow_null=True)
    status_name = serializers.CharField(allow_null=True)
    service_date = serializers.DateField(allow_null=True)


class ContentMakerListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    has_account = serializers.BooleanField(read_only=True)
    user_email = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ContentMakerProfile
        fields = [
            "id", "stimada_id", "full_name", "first_name", "last_name",
            "type", "type_display",
            "cm_type", "status", "content_categories",
            "instagram_handle", "instagram_followers",
            "tiktok_handle", "tiktok_followers",
            "has_account", "user_email", "email",
        ]

    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None


class ContentMakerDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    has_account = serializers.BooleanField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True, allow_null=True)
    user_email = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    associated_projects = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    performance_options = serializers.PrimaryKeyRelatedField(
        many=True, queryset=PerformanceOption.objects.all(), required=False,
    )
    performance_options_display = serializers.SerializerMethodField()

    class Meta:
        model = ContentMakerProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]

    def get_user_email(self, obj):
        return obj.user.email if obj.user_id else None

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

    def get_performance_options_display(self, obj):
        return [{"id": o.id, "name": o.name} for o in obj.performance_options.all()]

    def update(self, instance, validated_data):
        performance_options = validated_data.pop("performance_options", None)
        instance = super().update(instance, validated_data)
        if performance_options is not None:
            instance.performance_options.set(performance_options)
        return instance

    def get_associated_projects(self, obj):
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
                "name": p.name,
                "brand_name": p.brand.name if p.brand else None,
                "status_name": p.status.name if p.status else None,
                "service_date": p.service_date,
            }
            for p in projects
        ], many=True).data


class CreateAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class ContentMakerPublicSerializer(serializers.ModelSerializer):
    """Limited view for clients — hides sensitive/internal data like fees, billing, status."""
    full_name = serializers.CharField(read_only=True)
    photo_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ContentMakerProfile
        fields = [
            "id", "stimada_id", "first_name", "last_name", "full_name",
            "type", "type_display",
            "cm_type", "gender", "content_categories",
            "is_mother",
            "instagram_handle", "instagram_link",
            "instagram_followers", "instagram_followers_category",
            "tiktok_handle", "tiktok_link",
            "tiktok_followers", "tiktok_followers_category",
            "top_size", "bottom_size", "shoe_size", "height_measurements",
            "photo_url",
        ]

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class ContentMakerCreateSerializer(serializers.ModelSerializer):
    performance_options = serializers.PrimaryKeyRelatedField(
        many=True, queryset=PerformanceOption.objects.all(), required=False,
    )

    class Meta:
        model = ContentMakerProfile
        exclude = ["user", "created_at", "updated_at"]
        extra_kwargs = {
            "stimada_id": {"required": False, "allow_blank": True},
            "dni_cif": {"required": True, "allow_blank": False},
            "billing_address": {"required": True, "allow_blank": False},
            "postal_code": {"required": True, "allow_blank": False},
            "province": {"required": True, "allow_blank": False},
            "country": {"required": True, "allow_blank": False},
            "iban": {"required": True, "allow_blank": False},
        }

    def create(self, validated_data):
        performance_options = validated_data.pop("performance_options", [])
        instance = super().create(validated_data)
        if performance_options:
            instance.performance_options.set(performance_options)
        return instance

    def validate_instagram_link(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value

    def validate_tiktok_link(self, value):
        if value and not value.startswith("http"):
            value = f"https://{value}"
        return value
