from django.contrib import admin

from apps.clients.models import Brand, ClientProfile, ClientType


@admin.register(ClientType)
class ClientTypeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "slug", "orden", "activo"]
    list_editable = ["orden", "activo"]
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ["orden"]


class BrandInline(admin.TabularInline):
    model = Brand
    extra = 1


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ["cliente_id", "nombre_cliente", "tipo_cliente", "es_agencia", "ciudad", "contrato_firmado", "created_at"]
    list_filter = ["tipo_cliente", "contrato_firmado", "es_agencia", "pais"]
    search_fields = ["nombre_cliente", "cliente_id", "cif", "email_facturacion"]
    readonly_fields = ["created_at", "updated_at", "created_by"]
    inlines = [BrandInline]

    fieldsets = (
        ("Identificación", {"fields": ("cliente_id", "nombre_cliente", "tipo_cliente", "es_agencia")}),
        ("Facturación", {"fields": ("nombre_facturacion", "cif", "email_facturacion", "direccion_facturacion", "codigo_postal", "ciudad", "pais")}),
        ("Contrato", {"fields": ("contrato_firmado", "contrato")}),
        ("Metadatos", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
