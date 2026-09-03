from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import CustomUser, PasswordResetRequest
from apps.accounts.permissions import CanCreateUsers, IsAdmin, IsAdminOrEmployee
from apps.accounts.serializers import (
    CreateUserSerializer,
    LoginSerializer,
    PasswordResetRequestDetailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetResolveSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)
from config.pagination import FlexiblePageNumberPagination


def get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class LoginView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/15m", method="POST", block=True))
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = CustomUser.objects.get(email=request.data["email"])
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login_ip"])

        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Se requiere el refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token inválido o ya expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshView(TokenRefreshView):
    pass


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")
        confirm_password = request.data.get("confirm_password", "")

        if not request.user.check_password(current_password):
            return Response(
                {"current_password": ["La contraseña actual es incorrecta."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 8:
            return Response(
                {"new_password": ["La contraseña debe tener al menos 8 caracteres."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != confirm_password:
            return Response(
                {"confirm_password": ["Las contraseñas no coinciden."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"detail": "Contraseña actualizada correctamente."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="3/15m", method="POST", block=True))
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.context["reset_user"]

        reset_req = PasswordResetRequest.objects.create(user=user)

        # Notify all active admins by email
        admin_emails = list(
            CustomUser.objects.filter(role=CustomUser.ADMIN, is_active=True).values_list("email", flat=True)
        )
        if admin_emails:
            send_mail(
                subject=f"[Stimada] Solicitud de nueva contraseña — {user.full_name}",
                message=(
                    f"El usuario {user.full_name} ({user.email}) ha solicitado una nueva contraseña.\n\n"
                    f"Rol: {user.get_role_display()}\n"
                    f"Fecha: {reset_req.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                    "Accede al panel de administración para resolver esta solicitud.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True,
            )

        return Response(
            {"detail": "Solicitud enviada. Un administrador te proporcionará acceso pronto."},
            status=status.HTTP_201_CREATED,
        )


class PasswordResetRequestListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        requests = PasswordResetRequest.objects.filter(status=PasswordResetRequest.PENDING).select_related("user")
        serializer = PasswordResetRequestDetailSerializer(requests, many=True)
        return Response(serializer.data)


class PasswordResetResolveView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            reset_req = PasswordResetRequest.objects.get(pk=pk, status=PasswordResetRequest.PENDING)
        except PasswordResetRequest.DoesNotExist:
            return Response({"detail": "Solicitud no encontrada o ya resuelta."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PasswordResetResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["new_password"]
        reset_req.user.set_password(new_password)
        reset_req.user.save(update_fields=["password"])

        reset_req.status = PasswordResetRequest.RESOLVED
        reset_req.resolved_by = request.user
        reset_req.resolved_at = timezone.now()
        reset_req.save()

        # Notify the user
        send_mail(
            subject="[Stimada] Tu contraseña ha sido restablecida",
            message=(
                f"Hola {reset_req.user.full_name},\n\n"
                "Un administrador ha restablecido tu contraseña de acceso a Stimada.\n\n"
                f"Email: {reset_req.user.email}\n"
                f"Nueva contraseña: {new_password}\n\n"
                "Te recomendamos cambiarla tras el primer acceso.\n\n"
                "Un saludo,\nEl equipo de Stimada"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reset_req.user.email],
            fail_silently=True,
        )

        return Response({"detail": "Contraseña restablecida y notificación enviada al usuario."})


class UserViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == "list":
            return [IsAdminOrEmployee()]
        if self.action == "create":
            return [CanCreateUsers()]
        if self.action == "retrieve":
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request):
        qs = CustomUser.objects.all().order_by("-created_at")
        if request.user.role == CustomUser.EMPLOYEE:
            qs = qs.filter(role__in=[CustomUser.CLIENT, CustomUser.CONTENT_MAKER])

        role = request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        status_filter = request.query_params.get("status")
        if status_filter == "active":
            qs = qs.filter(is_active=True)
        elif status_filter == "inactive":
            qs = qs.filter(is_active=False)

        paginator = FlexiblePageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = UserDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserDetailSerializer(user).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        if not (request.user.is_admin or request.user.is_employee or str(request.user.pk) == pk):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(UserDetailSerializer(user).data)

    def update(self, request, pk=None):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Admin can update anyone; employees can update clients/CMs; users can update themselves
        is_self = str(request.user.pk) == pk
        is_employee_managing = (
            request.user.is_employee
            and user.role in (CustomUser.CLIENT, CustomUser.CONTENT_MAKER)
        )
        if not (request.user.is_admin or is_employee_managing or is_self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(user).data)

    def destroy(self, request, pk=None):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GiveAccessCMView(APIView):
    """Admin/Employee creates a user account for a Content Maker."""
    permission_classes = [IsAdminOrEmployee]

    def post(self, request, cm_id):
        from apps.accounts.services import create_content_maker_account
        from apps.content_makers.models import ContentMakerProfile

        try:
            cm_profile = ContentMakerProfile.objects.get(id=cm_id)
        except ContentMakerProfile.DoesNotExist:
            return Response({"detail": "Content Maker no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = create_content_maker_account(cm_profile, created_by=request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Cuenta creada y email enviado.", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class GiveAccessClientView(APIView):
    """
    Admin/Employee creates a user account for a Client.
    Requires: contract_signed = True and contract file uploaded.
    """
    permission_classes = [IsAdminOrEmployee]

    def post(self, request, client_id):
        from apps.accounts.services import create_client_account
        from apps.clients.models import ClientProfile

        try:
            client_profile = ClientProfile.objects.get(id=client_id)
        except ClientProfile.DoesNotExist:
            return Response({"detail": "Cliente no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user = create_client_account(client_profile, created_by=request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Cuenta creada y email enviado.", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )
