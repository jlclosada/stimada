from django.contrib import admin

from apps.content_makers.models import ContentMakerProfile, ContentMakerStatus, ContentMakerType, PerformanceOption, SizingCategory, SizingOption


@admin.register(ContentMakerStatus)
class ContentMakerStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    ordering = ["order", "name"]


@admin.register(ContentMakerType)
class ContentMakerTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    ordering = ["order", "name"]


@admin.register(PerformanceOption)
class PerformanceOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    ordering = ["order", "name"]


@admin.register(SizingCategory)
class SizingCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    ordering = ["order", "name"]


@admin.register(SizingOption)
class SizingOptionAdmin(admin.ModelAdmin):
    list_display = ["category", "value", "order"]
    list_editable = ["order"]
    list_filter = ["category"]
    ordering = ["category", "order"]


@admin.register(ContentMakerProfile)
class ContentMakerProfileAdmin(admin.ModelAdmin):
    list_display = ["stimada_id", "first_name", "last_name", "type", "cm_type", "status", "has_account", "email"]
    list_filter = ["type", "cm_type", "status", "contract_signed", "is_mother"]
    search_fields = ["first_name", "last_name", "email", "stimada_id", "instagram_handle"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["performance_options"]

    fieldsets = (
        ("Identificación", {"fields": ("stimada_id", "user")}),
        ("Persona", {"fields": ("first_name", "last_name", "gender", "type", "cm_type", "status")}),
        ("Valoración interna", {"fields": ("content_quality", "performance_options", "comments", "is_mother", "content_categories", "appearance", "performance")}),
        ("Stimada", {"fields": ("follows_stimada", "stimada_in_bio", "contract_signed")}),
        ("Instagram", {"fields": ("instagram_handle", "instagram_link", "instagram_followers", "instagram_followers_category", "fee_instagram")}),
        ("TikTok", {"fields": ("tiktok_handle", "tiktok_link", "tiktok_followers", "tiktok_followers_category", "fee_tiktok")}),
        ("Tallaje", {"fields": ("top_size", "bottom_size", "shoe_size", "height_measurements")}),
        ("Facturación", {"fields": ("email", "phone", "billing_address", "postal_code", "province", "country", "dni_cif", "iban")}),
        ("Fechas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_account(self, obj):
        return obj.user_id is not None
    has_account.boolean = True
    has_account.short_description = "Cuenta"
