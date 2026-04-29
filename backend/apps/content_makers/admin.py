from django.contrib import admin

from apps.content_makers.models import ContentMakerProfile, ContentMakerStatus, ContentMakerType


@admin.register(ContentMakerStatus)
class ContentMakerStatusAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden"]
    list_editable = ["orden"]
    ordering = ["orden", "nombre"]


@admin.register(ContentMakerType)
class ContentMakerTypeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "orden"]
    list_editable = ["orden"]
    ordering = ["orden", "nombre"]


@admin.register(ContentMakerProfile)
class ContentMakerProfileAdmin(admin.ModelAdmin):
    list_display = ["stimada_id", "nombre", "apellidos", "tipo_cm", "status", "tiene_cuenta", "email"]
    list_filter = ["tipo_cm", "status", "contrato_firmado", "es_mama"]
    search_fields = ["nombre", "apellidos", "email", "stimada_id", "instagram_handle"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Identificación", {"fields": ("stimada_id", "user")}),
        ("Persona", {"fields": ("nombre", "apellidos", "sexo", "tipo_cm", "status")}),
        ("Valoración interna", {"fields": ("desempeno", "calidad_contenido", "apariencia", "es_mama", "categorias_contenido")}),
        ("Stimada", {"fields": ("sigue_stimada", "stimada_en_bio", "contrato_firmado")}),
        ("Instagram", {"fields": ("instagram_handle", "link_instagram", "seguidores_instagram", "categoria_seguidores_ig", "fee_instagram")}),
        ("TikTok", {"fields": ("tiktok_handle", "link_tiktok", "seguidores_tiktok", "categoria_seguidores_tt", "fee_tiktok")}),
        ("Tallaje", {"fields": ("talla_arriba", "talla_abajo", "talla_pie", "altura_medidas")}),
        ("Facturación", {"fields": ("email", "telefono", "direccion_facturacion", "codigo_postal", "provincia", "pais", "dni_cif", "iban")}),
        ("Notas", {"fields": ("comentarios",)}),
        ("Fechas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def tiene_cuenta(self, obj):
        return obj.user_id is not None
    tiene_cuenta.boolean = True
    tiene_cuenta.short_description = "Cuenta"
