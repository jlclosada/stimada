import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=255)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Administrador"),
                            ("stimada_employee", "Empleado Stimada"),
                            ("client", "Cliente"),
                            ("content_maker", "Content Maker"),
                        ],
                        max_length=30,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("avatar", models.ImageField(blank=True, null=True, upload_to="avatars/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_login_ip", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_users",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("groups", models.ManyToManyField(blank=True, related_name="customuser_set", to="auth.group")),
                (
                    "user_permissions",
                    models.ManyToManyField(blank=True, related_name="customuser_set", to="auth.permission"),
                ),
            ],
            options={
                "verbose_name": "Usuario",
                "verbose_name_plural": "Usuarios",
            },
        ),
        migrations.AddIndex(
            model_name="customuser",
            index=models.Index(fields=["role"], name="accounts_cu_role_idx"),
        ),
        migrations.AddIndex(
            model_name="customuser",
            index=models.Index(fields=["is_active"], name="accounts_cu_is_acti_idx"),
        ),
    ]
