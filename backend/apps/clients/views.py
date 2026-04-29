from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminOrEmployee
from apps.clients.models import Brand, ClientProfile, ClientType
from apps.clients.serializers import (
    ClientProfileCreateSerializer,
    ClientProfileDetailSerializer,
    ClientProfileListSerializer,
    ClientTypeSerializer,
)


class ClientTypeListView(APIView):
    permission_classes = [IsAdminOrEmployee]

    def get(self, request):
        types = ClientType.objects.filter(activo=True)
        return Response(ClientTypeSerializer(types, many=True).data)


class ClientProfileViewSet(ModelViewSet):
    permission_classes = [IsAdminOrEmployee]
    queryset = ClientProfile.objects.select_related("tipo_cliente", "created_by", "user").order_by("nombre_cliente")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ClientProfileCreateSerializer
        if self.action == "retrieve":
            return ClientProfileDetailSerializer
        return ClientProfileListSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()
        if q:
            qs = qs.filter(nombre_cliente__icontains=q) | qs.filter(cliente_id__icontains=q)
        if tipo:
            qs = qs.filter(tipo_cliente__slug=tipo)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            ClientProfileDetailSerializer(instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="create-account")
    def create_account(self, request, pk=None):
        client = self.get_object()

        if client.user:
            return Response(
                {"detail": "Este cliente ya tiene una cuenta de usuario asociada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.data.get("email", "").strip()
        full_name = request.data.get("full_name", "").strip() or client.nombre_cliente
        password = request.data.get("password", "").strip() or get_random_string(12)

        if not email:
            return Response(
                {"detail": "El campo email es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {"detail": "Ya existe un usuario con ese email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            role=CustomUser.CLIENT,
            full_name=full_name,
        )
        user.created_by = request.user
        user.save(update_fields=["created_by"])

        client.user = user
        client.save(update_fields=["user"])

        return Response(
            {
                "detail": "Cuenta creada correctamente.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "password": password,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def brands(self, request, pk=None):
        client = self.get_object()
        brand_list = Brand.objects.filter(client=client, activo=True)
        data = [{"id": b.id, "nombre": b.nombre} for b in brand_list]
        return Response(data)
