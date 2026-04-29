from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, role, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", CustomUser.ADMIN)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ADMIN = "admin"
    EMPLOYEE = "stimada_employee"
    CLIENT = "client"
    CONTENT_MAKER = "content_maker"

    ROLE_CHOICES = [
        (ADMIN, "Administrador"),
        (EMPLOYEE, "Empleado Stimada"),
        (CLIENT, "Cliente"),
        (CONTENT_MAKER, "Content Maker"),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    @property
    def is_employee(self):
        return self.role == self.EMPLOYEE

    @property
    def is_client(self):
        return self.role == self.CLIENT

    @property
    def is_content_maker(self):
        return self.role == self.CONTENT_MAKER

    @property
    def can_create_users(self):
        return self.role in (self.ADMIN, self.EMPLOYEE)


class PasswordResetRequest(models.Model):
    PENDING = "pending"
    RESOLVED = "resolved"

    STATUS_CHOICES = [
        (PENDING, "Pendiente"),
        (RESOLVED, "Resuelto"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reset_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_resets",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Solicitud de contraseña"
        verbose_name_plural = "Solicitudes de contraseña"

    def __str__(self):
        return f"Reset {self.user.email} — {self.status}"
