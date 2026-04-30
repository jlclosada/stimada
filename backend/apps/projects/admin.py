from django.contrib import admin

from apps.projects.models import (
    Briefing,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    ServiceType,
)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden"]
    list_editable = ["orden"]


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden"]
    list_editable = ["orden"]


class ProjectContentMakerInline(admin.TabularInline):
    model = ProjectContentMaker
    extra = 0
    raw_id_fields = ["content_maker"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["project_id", "nombre", "client", "status", "service_type", "fecha_venta", "created_at"]
    list_filter = ["status", "service_type", "cm_selection_mode"]
    search_fields = ["project_id", "nombre", "client__nombre_cliente"]
    raw_id_fields = ["client", "brand", "content_maker", "created_by"]
    inlines = [ProjectContentMakerInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "notification_type", "title", "read", "created_at"]
    list_filter = ["notification_type", "read"]
    search_fields = ["title", "recipient__email"]


@admin.register(Briefing)
class BriefingAdmin(admin.ModelAdmin):
    list_display = ["project", "content_maker", "created_by", "created_at"]
    list_filter = ["project__status"]
    search_fields = ["project__project_id", "project__nombre"]
    raw_id_fields = ["project", "content_maker", "created_by"]
