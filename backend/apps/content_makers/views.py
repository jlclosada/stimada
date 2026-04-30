import secrets
import string

from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminOrEmployee
from apps.content_makers.models import ContentMakerProfile, ContentMakerStatus, ContentMakerType
from apps.content_makers.serializers import (
    ContentMakerCreateSerializer,
    ContentMakerDetailSerializer,
    ContentMakerListSerializer,
)


def _generate_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure at least one of each category
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
        ):
            return pwd


class ContentMakerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrEmployee]
    queryset = ContentMakerProfile.objects.select_related("user").order_by("stimada_id")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        # Allow clients read-only access to retrieve and list
        if self.action in ("retrieve", "list"):
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ("create", "retrieve", "update", "partial_update"):
            return ContentMakerDetailSerializer
        return ContentMakerListSerializer

    def create(self, request, *args, **kwargs):
        serializer = ContentMakerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            ContentMakerDetailSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def next_id(self, request):
        import re
        ids = ContentMakerProfile.objects.values_list("stimada_id", flat=True)
        nums = [int(m.group()) for sid in ids if (m := re.search(r"\d+", sid))]
        next_num = (max(nums) if nums else 0) + 1
        return Response({"next_id": f"[CM] - {next_num:05d}"})

    @action(detail=False, methods=["get"])
    def filters(self, request):
        def distinct_values(field):
            return list(
                ContentMakerProfile.objects.exclude(**{field: ""})
                .values_list(field, flat=True)
                .distinct()
                .order_by(field)
            )

        return Response({
            "statuses": list(ContentMakerStatus.objects.values_list("nombre", flat=True)),
            "tipos": list(ContentMakerType.objects.values_list("nombre", flat=True)),
            "sexos": distinct_values("sexo"),
            "calidad_contenido": distinct_values("calidad_contenido"),
            "apariencia": distinct_values("apariencia"),
            "categoria_seguidores_ig": distinct_values("categoria_seguidores_ig"),
            "categoria_seguidores_tt": distinct_values("categoria_seguidores_tt"),
        })

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()
        tipo_filter = self.request.query_params.get("tipo", "").strip()
        tiene_cuenta = self.request.query_params.get("tiene_cuenta", "").strip()

        if search:
            qs = qs.filter(nombre__icontains=search) | qs.filter(apellidos__icontains=search) | qs.filter(email__icontains=search)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if tipo_filter:
            qs = qs.filter(tipo_cm=tipo_filter)
        if tiene_cuenta == "true":
            qs = qs.filter(user__isnull=False)
        elif tiene_cuenta == "false":
            qs = qs.filter(user__isnull=True)

        return qs

    @action(detail=True, methods=["post"])
    def create_account(self, request, pk=None):
        profile = self.get_object()

        if profile.user_id:
            return Response(
                {"detail": "Esta content maker ya tiene cuenta de acceso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.data.get("email", profile.email).strip()
        if not email:
            return Response(
                {"detail": "Es necesario un email para crear la cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {"detail": f"Ya existe una cuenta con el email '{email}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = _generate_password()
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            role=CustomUser.CONTENT_MAKER,
            full_name=profile.nombre_completo or profile.nombre,
            created_by=request.user,
        )
        profile.user = user
        profile.save(update_fields=["user"])

        return Response(
            {
                "user_id": user.id,
                "email": email,
                "password": password,
                "detail": "Cuenta creada correctamente.",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def send_credentials(self, request, pk=None):
        profile = self.get_object()

        if not profile.user_id:
            return Response(
                {"detail": "Esta content maker no tiene cuenta aún."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient = request.data.get("email", profile.email).strip()
        password = request.data.get("password", "").strip()

        if not recipient:
            return Response({"detail": "Email destinatario requerido."}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"detail": "Contraseña requerida para enviar."}, status=status.HTTP_400_BAD_REQUEST)

        send_mail(
            subject="Bienvenida a Stimada — Tus credenciales de acceso",
            message=(
                f"Hola {profile.nombre},\n\n"
                "Tu cuenta en la plataforma Stimada ha sido creada.\n\n"
                f"Email: {profile.user.email}\n"
                f"Contraseña: {password}\n\n"
                "Accede en la plataforma con estas credenciales.\n"
                "Te recomendamos cambiar tu contraseña tras el primer acceso.\n\n"
                "Un saludo,\n"
                "El equipo de Stimada"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )

        return Response({"detail": f"Credenciales enviadas a {recipient}."})
