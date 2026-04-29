from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsAdminOrEmployee
from apps.clients.models import ClientProfile, ClientType
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
    queryset = ClientProfile.objects.select_related("tipo_cliente", "created_by").order_by("nombre_cliente")

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
