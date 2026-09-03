"""
Servicio de creación de cuentas con contraseña auto-generada y envío de email.
- Creación de cuenta de Content Maker (Admin pulsa "Dar acceso")
- Creación de cuenta de Cliente (Contrato firmado = Sí + archivo subido)
"""
import secrets
import string

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.accounts.models import CustomUser
from apps.audit.services import audit_user_lifecycle
from apps.projects.models import Notification


def generate_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_content_maker_account(cm_profile, created_by=None):
    """
    Create a user account for a Content Maker.
    Sends email with credentials to the CM.
    Returns the created user.
    """
    if cm_profile.user:
        raise ValueError("Esta Content Maker ya tiene una cuenta de usuario.")

    email = cm_profile.email
    if not email:
        raise ValueError("La Content Maker no tiene email registrado.")

    password = generate_password()
    full_name = f"{cm_profile.first_name} {cm_profile.last_name}".strip()

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role=CustomUser.CONTENT_MAKER,
        full_name=full_name,
    )

    # Link profile to user
    cm_profile.user = user
    cm_profile.save(update_fields=["user"])

    # Send email
    _send_account_email(
        email=email,
        full_name=full_name,
        password=password,
        role="Content Maker",
    )

    # Audit
    if created_by:
        audit_user_lifecycle(
            created_by, user, "create",
            f"Cuenta Content Maker creada para {full_name} ({email})"
        )

    # Notification to the CM
    Notification.objects.create(
        recipient=user,
        notification_type=Notification.TYPE_ACCOUNT_CREATED,
        title="Tu cuenta ha sido creada",
        message="Se ha creado tu cuenta en Stimada. Revisa tu email para las credenciales de acceso.",
    )

    return user


def create_client_account(client_profile, created_by=None):
    """
    Create a user account for a Client.
    Prerequisite: contract_signed = True and contract file uploaded.
    Returns the created user.
    """
    if client_profile.user:
        raise ValueError("Este cliente ya tiene una cuenta de usuario.")

    if not client_profile.contract_signed:
        raise ValueError("El contrato debe estar firmado antes de crear la cuenta.")

    if not client_profile.contract:
        raise ValueError("Debe subirse el archivo del contrato antes de crear la cuenta.")

    email = client_profile.contact_email
    if not email:
        raise ValueError("El cliente no tiene email de contacto registrado.")

    password = generate_password()
    full_name = client_profile.contact_person or client_profile.name

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        role=CustomUser.CLIENT,
        full_name=full_name,
    )

    # Link profile to user
    client_profile.user = user
    client_profile.save(update_fields=["user"])

    # Send email
    _send_account_email(
        email=email,
        full_name=full_name,
        password=password,
        role="Cliente",
    )

    # Audit
    if created_by:
        audit_user_lifecycle(
            created_by, user, "create",
            f"Cuenta Cliente creada para {full_name} ({email})"
        )

    return user


def _send_account_email(email: str, full_name: str, password: str, role: str):
    """Send account creation email with credentials."""
    subject = f"Tu cuenta en Stimada ha sido creada"
    message = (
        f"Hola {full_name},\n\n"
        f"Se ha creado tu cuenta de {role} en la plataforma Stimada.\n\n"
        f"Tus credenciales de acceso:\n"
        f"  Email: {email}\n"
        f"  Contraseña: {password}\n\n"
        f"Por seguridad, te recomendamos cambiar la contraseña tras tu primer acceso.\n\n"
        f"Accede a la plataforma en: {settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://app.stimada.com'}\n\n"
        f"Un saludo,\n"
        f"El equipo de Stimada"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
