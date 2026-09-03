from django.contrib import admin

from apps.clients.models import Brand, ClientProfile, ClientType


@admin.register(ClientType)
class ClientTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["brand_id", "name", "client", "brand_type", "status", "created_at"]
    list_filter = ["status", "brand_type"]
    search_fields = ["name", "brand_id", "client__name"]
    readonly_fields = ["brand_id", "created_at"]


class BrandInline(admin.TabularInline):
    model = Brand
    extra = 1
    fields = ["brand_id", "name", "brand_type", "web_instagram", "status"]
    readonly_fields = ["brand_id"]


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ["client_id", "name", "client_type", "is_agency", "status", "traffic_light", "city", "contract_signed", "created_at"]
    list_filter = ["client_type", "contract_signed", "is_agency", "status", "traffic_light", "country"]
    search_fields = ["name", "client_id", "cif", "billing_email", "contact_email"]
    readonly_fields = ["created_at", "updated_at", "created_by"]
    inlines = [BrandInline]

    fieldsets = (
        ("Identification", {"fields": ("client_id", "name", "client_type", "web_instagram", "is_agency")}),
        ("Contact", {"fields": ("contact_person", "contact_email", "phone")}),
        ("Billing", {"fields": ("billing_name", "cif", "billing_email", "billing_address", "postal_code", "city", "country")}),
        ("Contract", {"fields": ("contract_signed", "contract")}),
        ("Status and evaluation", {"fields": ("status", "traffic_light", "internal_notes")}),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
