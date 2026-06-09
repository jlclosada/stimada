from django.contrib import admin

from apps.projects.models import (
    Briefing,
    BriefingLink,
    BriefingPhoto,
    Entregable,
    LogisticaProducto,
    ModalidadEconomica,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    QuienGraba,
    QuienPublica,
    QuienRevisa,
    RecogidaProducto,
    ServiceType,
    StatusChangeLog,
    WinStatus,
)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(ModalidadEconomica)
class ModalidadEconomicaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(LogisticaProducto)
class LogisticaProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(RecogidaProducto)
class RecogidaProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(QuienGraba)
class QuienGrabaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(QuienRevisa)
class QuienRevisaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(QuienPublica)
class QuienPublicaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


@admin.register(WinStatus)
class WinStatusAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden", "activo"]
    list_editable = ["orden", "activo"]


class ProjectContentMakerInline(admin.TabularInline):
    model = ProjectContentMaker
    extra = 0
    raw_id_fields = ["content_maker"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["project_id", "nombre", "client", "status", "service_type", "win_status", "semaforo_proyecto", "fecha_venta", "created_at"]
    list_filter = ["status", "service_type", "modalidad_economica", "win_status", "cm_selection_mode"]
    search_fields = ["project_id", "nombre", "client__nombre_cliente"]
    raw_id_fields = ["client", "brand", "content_maker", "created_by"]
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
    search_fields = ["project__project_id", "project__nombre"]
    raw_id_fields = ["project", "content_maker", "created_by"]
    inlines = [BriefingLinkInline, BriefingPhotoInline]


@admin.register(Entregable)
class EntregableAdmin(admin.ModelAdmin):
    list_display = ["project", "content_maker", "status", "revision_round", "uploaded_at", "reviewed_at"]
    list_filter = ["status", "revision_round"]
    search_fields = ["project__project_id", "project__nombre"]
    raw_id_fields = ["project", "content_maker", "reviewed_by"]


@admin.register(StatusChangeLog)
class StatusChangeLogAdmin(admin.ModelAdmin):
    list_display = ["project", "from_status", "to_status", "is_manual", "changed_by", "timestamp"]
    list_filter = ["is_manual", "to_status"]
    search_fields = ["project__project_id", "project__nombre", "reason"]
    raw_id_fields = ["project", "changed_by"]
    readonly_fields = ["project", "from_status", "to_status", "is_manual", "reason", "changed_by", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
