from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "full_name", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "full_name"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Información personal", {"fields": ("email", "full_name", "avatar", "password")}),
        ("Rol y permisos", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Metadatos", {"fields": ("created_by", "last_login_ip", "created_at", "last_login")}),
    )
    readonly_fields = ["created_at", "last_login", "last_login_ip"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )
