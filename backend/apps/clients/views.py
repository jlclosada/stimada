from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import CustomUser
from apps.accounts.permissions import IsAdminOrEmployee, IsClient
from apps.clients.models import Brand, ClientProfile, ClientType
from apps.clients.serializers import (
    BrandCreateSerializer,
    BrandDetailSerializer,
    BrandListSerializer,
    ClientProfileCreateSerializer,
    ClientProfileDetailSerializer,
    ClientProfileListSerializer,
    ClientTypeSerializer,
)


class ClientTypeListView(APIView):
    permission_classes = [IsAdminOrEmployee]

    def get(self, request):
        types = ClientType.objects.filter(is_active=True)
        return Response(ClientTypeSerializer(types, many=True).data)


class ClientMeView(APIView):
    """Endpoint for client users to view their own profile and brands."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_client:
            return Response(
                {"detail": "Solo usuarios de tipo cliente pueden acceder a este recurso."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not hasattr(request.user, "client_profile") or not request.user.client_profile:
            return Response(
                {"detail": "No tienes un perfil de cliente asociado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile = request.user.client_profile
        data = ClientProfileDetailSerializer(profile, context={"request": request}).data
        data["brands"] = [
            {"id": b.id, "brand_id": b.brand_id, "name": b.name, "status": b.status}
            for b in profile.brands.filter(status="activa")
        ]
        return Response(data)


class ClientProfileViewSet(ModelViewSet):
    permission_classes = [IsAdminOrEmployee]
    queryset = ClientProfile.objects.select_related("client_type", "created_by", "user").order_by("name")

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
        client_type = self.request.query_params.get("type", "").strip()
        contract = self.request.query_params.get("contract", "").strip()
        account = self.request.query_params.get("account", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()
        ordering = self.request.query_params.get("ordering", "").strip()

        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(client_id__icontains=q)
        if client_type:
            qs = qs.filter(client_type__slug=client_type)
        if contract == "firmado":
            qs = qs.filter(contract_signed=True)
        elif contract == "pendiente":
            qs = qs.filter(contract_signed=False)
        if account == "activa":
            qs = qs.filter(user__isnull=False)
        elif account == "sin_cuenta":
            qs = qs.filter(user__isnull=True)
        if status_filter in (ClientProfile.STATUS_ACTIVE, ClientProfile.STATUS_INACTIVE):
            qs = qs.filter(status=status_filter)

        # Ordering (whitelist + direction)
        allowed_ordering = {
            "name", "client_id", "city", "created_at",
            "contract_signed", "client_type__name",
        }
        if ordering:
            field = ordering.lstrip("-")
            if field in allowed_ordering:
                qs = qs.order_by(ordering)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            ClientProfileDetailSerializer(instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def next_id(self, request):
        next_num = ClientProfile.generate_next_id()
        return Response({"next_id": next_num})

    @action(detail=True, methods=["post"], url_path="create-account")
    def create_account(self, request, pk=None):
        client = self.get_object()

        if client.user:
            return Response(
                {"detail": "Este cliente ya tiene una cuenta de usuario asociada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.data.get("email", "").strip()
        full_name = request.data.get("full_name", "").strip() or client.name
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
        brand_list = Brand.objects.filter(client=client, status="activa")
        data = [{"id": b.id, "brand_id": b.brand_id, "name": b.name} for b in brand_list]
        return Response(data)


class ClientFavoriteCMsView(APIView):
    """Manage favorite content makers for the authenticated client."""
    permission_classes = [IsAuthenticated]

    def _get_client_profile(self, request):
        if not request.user.is_client:
            return None, Response(
                {"detail": "Solo clientes pueden acceder a este recurso."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not hasattr(request.user, "client_profile") or not request.user.client_profile:
            return None, Response(
                {"detail": "No tienes un perfil de cliente asociado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return request.user.client_profile, None

    def get(self, request):
        """List favorite content makers."""
        profile, err = self._get_client_profile(request)
        if err:
            return err
        favorites = profile.favorite_cms.all()
        data = []
        for cm in favorites:
            photo_url = None
            if cm.photo:
                photo_url = request.build_absolute_uri(cm.photo.url)
            data.append({
                "id": cm.id,
                "name": f"{cm.first_name} {cm.last_name}".strip(),
                "instagram_handle": cm.instagram_handle,
                "instagram_followers": cm.instagram_followers,
                "tiktok_handle": cm.tiktok_handle,
                "tiktok_followers": cm.tiktok_followers,
                "photo_url": photo_url,
            })
        return Response(data)

    def post(self, request):
        """Add a content maker to favorites."""
        from apps.content_makers.models import ContentMakerProfile

        profile, err = self._get_client_profile(request)
        if err:
            return err
        cm_id = request.data.get("content_maker_id")
        if not cm_id:
            return Response(
                {"detail": "content_maker_id es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            cm = ContentMakerProfile.objects.get(id=cm_id)
        except ContentMakerProfile.DoesNotExist:
            return Response(
                {"detail": "Content Maker no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile.favorite_cms.add(cm)
        return Response({"status": "added"})

    def delete(self, request):
        """Remove a content maker from favorites."""
        from apps.content_makers.models import ContentMakerProfile

        profile, err = self._get_client_profile(request)
        if err:
            return err
        cm_id = request.data.get("content_maker_id")
        if not cm_id:
            return Response(
                {"detail": "content_maker_id es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            cm = ContentMakerProfile.objects.get(id=cm_id)
        except ContentMakerProfile.DoesNotExist:
            return Response(
                {"detail": "Content Maker no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        profile.favorite_cms.remove(cm)
        return Response({"status": "removed"})


class BrandViewSet(ModelViewSet):
    permission_classes = [IsAdminOrEmployee]
    queryset = Brand.objects.select_related("client", "client__client_type", "brand_type").order_by("name")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BrandCreateSerializer
        if self.action == "retrieve":
            return BrandDetailSerializer
        return BrandListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        client_pk = self.request.query_params.get("client", "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        if client_pk:
            qs = qs.filter(client_id=client_pk)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            BrandDetailSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def next_id(self, request):
        return Response({"next_id": Brand.generate_next_id()})
