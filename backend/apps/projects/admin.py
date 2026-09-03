from django.contrib import admin

from apps.projects.models import (
    Briefing,
    BriefingLink,
    BriefingPhoto,
    Deliverable,
    EconomicModel,
    Format,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    ProductLogistics,
    ProductPickup,
    ServiceType,
    SocialNetwork,
    StatusChangeLog,
    WhoPublishes,
    WhoRecords,
    WhoReviews,
    WinStatus,
)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active", "available_on_creation"]
    list_editable = ["order", "is_active", "available_on_creation"]


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active", "requires_profiles"]
    list_editable = ["order", "is_active", "requires_profiles"]


@admin.register(SocialNetwork)
class SocialNetworkAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(EconomicModel)
class EconomicModelAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(ProductLogistics)
class ProductLogisticsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(ProductPickup)
class ProductPickupAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(WhoRecords)
class WhoRecordsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(WhoReviews)
class WhoReviewsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(WhoPublishes)
class WhoPublishesAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(WinStatus)
class WinStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_active"]
    list_editable = ["order", "is_active"]


class ProjectContentMakerInline(admin.TabularInline):
    model = ProjectContentMaker
    extra = 0
    raw_id_fields = ["content_maker"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["project_id", "name", "client", "status", "service_type", "win_status", "traffic_light", "sale_date", "created_at"]
    list_filter = ["status", "service_type", "economic_model", "win_status", "cm_selection_mode"]
    search_fields = ["project_id", "name", "client__name"]
    raw_id_fields = ["client", "brand", "content_maker", "created_by"]
    filter_horizontal = ["social_networks", "formats"]
    inlines = [ProjectContentMakerInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "notification_type", "title", "read", "created_at"]
    list_filter = ["notification_type", "read"]
    search_fields = ["title", "recipient__email"]


class BriefingLinkInline(admin.TabularInline):
    model = BriefingLink
    extra = 0


class BriefingPhotoInline(admin.TabularInline):
    model = BriefingPhoto
    extra = 0


@admin.register(Briefing)
class BriefingAdmin(admin.ModelAdmin):
    list_display = ["project", "content_maker", "created_by", "created_at"]
    list_filter = ["project__status"]
    search_fields = ["project__project_id", "project__name"]
    raw_id_fields = ["project", "content_maker", "created_by"]
    inlines = [BriefingLinkInline, BriefingPhotoInline]


@admin.register(Deliverable)
class DeliverableAdmin(admin.ModelAdmin):
    list_display = ["project", "content_maker", "status", "revision_round", "uploaded_at", "reviewed_at"]
    list_filter = ["status", "revision_round"]
    search_fields = ["project__project_id", "project__name"]
    raw_id_fields = ["project", "content_maker", "reviewed_by"]


@admin.register(StatusChangeLog)
class StatusChangeLogAdmin(admin.ModelAdmin):
    list_display = ["project", "from_status", "to_status", "is_manual", "changed_by", "timestamp"]
    list_filter = ["is_manual", "to_status"]
    search_fields = ["project__project_id", "project__name", "reason"]
    raw_id_fields = ["project", "changed_by"]
    readonly_fields = ["project", "from_status", "to_status", "is_manual", "reason", "changed_by", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
