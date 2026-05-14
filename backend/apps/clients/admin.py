from django.contrib import admin

from apps.clients.models import Brand, ClientProfile, ClientType


@admin.register(ClientType)
class ClientTypeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "slug", "orden", "activo"]
    list_editable = ["orden", "activo"]
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ["orden"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["brand_id", "nombre", "client", "tipo_marca", "estado", "created_at"]
    list_filter = ["estado", "tipo_marca"]
    search_fields = ["nombre", "brand_id", "client__nombre_cliente"]
    readonly_fields = ["brand_id", "created_at"]


class BrandInline(admin.TabularInline):
    model = Brand
    extra = 1
    fields = ["brand_id", "nombre", "tipo_marca", "web_instagram", "estado"]
    readonly_fields = ["brand_id"]


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ["cliente_id", "nombre_cliente", "tipo_cliente", "es_agencia", "estado", "semaforo_cliente", "ciudad", "contrato_firmado", "created_at"]
    list_filter = ["tipo_cliente", "contrato_firmado", "es_agencia", "estado", "semaforo_cliente", "pais"]
    search_fields = ["nombre_cliente", "cliente_id", "cif", "email_facturacion", "email_contacto"]
    readonly_fields = ["created_at", "updated_at", "created_by"]
    inlines = [BrandInline]

    fieldsets = (
        ("Identificación", {"fields": ("cliente_id", "nombre_cliente", "tipo_cliente", "web_instagram", "es_agencia")}),
        ("Contacto", {"fields": ("persona_contacto", "email_contacto", "telefono")}),
        ("Facturación", {"fields": ("nombre_facturacion", "cif", "email_facturacion", "direccion_facturacion", "codigo_postal", "ciudad", "pais")}),
        ("Contrato", {"fields": ("contrato_firmado", "contrato")}),
        ("Estado y evaluación", {"fields": ("estado", "semaforo_cliente", "notas_internas")}),
        ("Metadatos", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )
