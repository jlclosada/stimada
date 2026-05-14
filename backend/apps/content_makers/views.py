import secrets
import string

from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminOrEmployee
from apps.content_makers.models import ContentMakerProfile, ContentMakerStatus, ContentMakerType
from apps.content_makers.serializers import (
    ContentMakerCreateSerializer,
    ContentMakerDetailSerializer,
    ContentMakerListSerializer,
    ContentMakerPublicSerializer,
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


# Fields a Content Maker can NOT edit on their own profile
CM_NON_EDITABLE_FIELDS = [
    "nombre", "apellidos", "stimada_id",
    "fee_instagram", "fee_tiktok",
    "status", "tipo_cm",
    "categorias_contenido",
    # Valoración interna (solo admin/empleados)
    "desempeno", "calidad_contenido", "apariencia",
    # Notas internas
    "comentarios",
    "user", "created_at", "updated_at",
]


class ContentMakerMeView(APIView):
    """Endpoint for content maker users to view and edit their own profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_content_maker:
            return Response(
                {"detail": "Solo content makers pueden acceder a este recurso."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not hasattr(request.user, "content_maker_profile") or not request.user.content_maker_profile:
            return Response(
                {"detail": "No tienes un perfil de content maker asociado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile = request.user.content_maker_profile
        return Response(ContentMakerDetailSerializer(profile, context={"request": request}).data)

    def patch(self, request):
        if not request.user.is_content_maker:
            return Response(
                {"detail": "Solo content makers pueden acceder a este recurso."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not hasattr(request.user, "content_maker_profile") or not request.user.content_maker_profile:
            return Response(
                {"detail": "No tienes un perfil de content maker asociado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile = request.user.content_maker_profile

        # Handle file uploads (foto)
        update_data = {}
        for k, v in request.data.items():
            if k not in CM_NON_EDITABLE_FIELDS:
                update_data[k] = v
        # Include uploaded files
        for k, v in request.FILES.items():
            if k not in CM_NON_EDITABLE_FIELDS:
                update_data[k] = v

        serializer = ContentMakerDetailSerializer(profile, data=update_data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContentMakerDetailSerializer(profile, context={"request": request}).data)


class ContentMakerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrEmployee]
    queryset = ContentMakerProfile.objects.select_related("user").order_by("stimada_id")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        # Allow clients read-only access to retrieve, list, and filters
        if self.action in ("retrieve", "list", "filters"):
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        # Clients see a limited public view
        if self.request.user.is_client:
            return ContentMakerPublicSerializer
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
        next_num = ContentMakerProfile.generate_next_id()
        return Response({"next_id": next_num})

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
            "tipos": distinct_values("tipo_cm"),
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
