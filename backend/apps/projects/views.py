from django.db import models as models
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    ServiceType,
)
from apps.projects.serializers import (
    NotificationSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectStatusSerializer,
    ServiceTypeSerializer,
)
from config.pagination import FlexiblePageNumberPagination


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FlexiblePageNumberPagination

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action == "list":
            return ProjectListSerializer
        return ProjectDetailSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), ]
        return super().get_permissions()

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # Only admin/employees can edit/delete projects
        if request.method in ("PUT", "PATCH", "DELETE"):
            if request.user.role not in ("admin", "stimada_employee"):
                self.permission_denied(request, message="No tienes permiso para modificar este proyecto.")

    def create(self, request, *args, **kwargs):
        if request.user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden crear proyectos."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        qs = Project.objects.select_related(
            "client", "brand", "status", "service_type", "content_maker", "created_by"
        ).prefetch_related("content_makers__content_maker")

        user = self.request.user
        # Clients only see their own projects
        if user.role == "client" and hasattr(user, "client_profile"):
            qs = qs.filter(client=user.client_profile)
        # Content makers only see projects they're assigned to (accepted)
        elif user.role == "content_maker" and hasattr(user, "content_maker_profile"):
            qs = qs.filter(
                models.Q(content_maker=user.content_maker_profile)
                | models.Q(
                    content_makers__content_maker=user.content_maker_profile,
                    content_makers__status__in=[
                        ProjectContentMaker.STATUS_ACCEPTED,
                        ProjectContentMaker.STATUS_PENDING,
                    ],
                )
            ).distinct()

        # Filtering
        params = self.request.query_params
        search = params.get("search", "").strip()
        if search:
            qs = qs.filter(
                models.Q(nombre__icontains=search)
                | models.Q(project_id__icontains=search)
                | models.Q(client__nombre_cliente__icontains=search)
            )

        status_filter = params.get("status")
        if status_filter:
            qs = qs.filter(status__nombre=status_filter)

        service_type_filter = params.get("service_type")
        if service_type_filter:
            qs = qs.filter(service_type__nombre=service_type_filter)

        client_filter = params.get("client")
        if client_filter:
            qs = qs.filter(client_id=client_filter)

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept_project(self, request, pk=None):
        project = self.get_object()
        user = request.user

        # Find the CM profile for this user
        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile

        # Update ProjectContentMaker status
        pcm = ProjectContentMaker.objects.filter(project=project, content_maker=cm_profile).first()
        if pcm:
            pcm.status = ProjectContentMaker.STATUS_ACCEPTED
            pcm.save()

        # Set as the definitive CM if not already set
        if not project.content_maker:
            project.content_maker = cm_profile
        project.save()

        # Notify the admin/creator
        if project.created_by:
            Notification.objects.create(
                recipient=project.created_by,
                notification_type=Notification.TYPE_PROJECT_CM_ACCEPTED,
                title="Content Maker aceptó el proyecto",
                message=f'{cm_profile.nombre} {cm_profile.apellidos} ha aceptado el proyecto "{project.nombre}".',
                project=project,
            )

        # Notify client
        if project.client.user:
            Notification.objects.create(
                recipient=project.client.user,
                notification_type=Notification.TYPE_PROJECT_CM_ACCEPTED,
                title="Content Maker confirmada",
                message=f'{cm_profile.nombre} {cm_profile.apellidos} ha aceptado participar en tu proyecto "{project.nombre}".',
                project=project,
            )

        return Response({"status": "accepted"})

    @action(detail=True, methods=["post"], url_path="reject")
    def reject_project(self, request, pk=None):
        project = self.get_object()
        user = request.user

        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile

        # Update ProjectContentMaker status
        pcm = ProjectContentMaker.objects.filter(project=project, content_maker=cm_profile).first()
        if pcm:
            pcm.status = ProjectContentMaker.STATUS_REJECTED
            pcm.save()

        # If this was the assigned CM, unassign
        if project.content_maker == cm_profile:
            project.content_maker = None
            project.save()

        # Notify the admin/creator
        if project.created_by:
            Notification.objects.create(
                recipient=project.created_by,
                notification_type=Notification.TYPE_PROJECT_CM_REJECTED,
                title="Content Maker rechazó el proyecto",
                message=f'{cm_profile.nombre} {cm_profile.apellidos} ha rechazado el proyecto "{project.nombre}".',
                project=project,
            )

        # Notify client — different message depending on mode
        if project.client.user:
            if project.cm_selection_mode in (
                Project.CM_SELECTION_CLIENT_CHOOSES,
                Project.CM_SELECTION_RECOMMENDED,
            ):
                Notification.objects.create(
                    recipient=project.client.user,
                    notification_type=Notification.TYPE_PROJECT_CM_SELECT,
                    title="Debes seleccionar otra Content Maker",
                    message=f'{cm_profile.nombre} {cm_profile.apellidos} no puede participar en "{project.nombre}". Por favor, elige otra Content Maker.',
                    project=project,
                )
            else:
                Notification.objects.create(
                    recipient=project.client.user,
                    notification_type=Notification.TYPE_PROJECT_CM_REJECTED,
                    title="Content Maker no disponible",
                    message=f'{cm_profile.nombre} {cm_profile.apellidos} no puede participar en el proyecto "{project.nombre}". Se buscará otra opción.',
                    project=project,
                )

        return Response({"status": "rejected"})

    @action(detail=True, methods=["post"], url_path="select_cm")
    def select_cm(self, request, pk=None):
        """Client selects a content maker for a project in 'client_chooses' mode."""
        project = self.get_object()
        user = request.user

        # Only clients who own this project (or admin/employee) can select a CM
        is_owner = (
            user.role == "client"
            and hasattr(user, "client_profile")
            and project.client == user.client_profile
        )
        is_staff = user.role in ("admin", "stimada_employee")
        if not is_owner and not is_staff:
            return Response(
                {"detail": "No tienes permiso para seleccionar una CM en este proyecto."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only allow in client_chooses or recommended mode with no definitive CM yet
        if project.content_maker:
            return Response(
                {"detail": "Este proyecto ya tiene una Content Maker asignada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cm_id = request.data.get("content_maker_id")
        if not cm_id:
            return Response(
                {"detail": "Debes indicar content_maker_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cm_profile = ContentMakerProfile.objects.get(id=cm_id)
        except ContentMakerProfile.DoesNotExist:
            return Response(
                {"detail": "Content Maker no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create or update the junction entry
        pcm, created = ProjectContentMaker.objects.get_or_create(
            project=project,
            content_maker=cm_profile,
            defaults={"status": ProjectContentMaker.STATUS_PENDING},
        )
        if not created:
            # If already existed but was rejected, reset to pending
            pcm.status = ProjectContentMaker.STATUS_PENDING
            pcm.save()

        # Notify the CM
        if cm_profile.user:
            Notification.objects.create(
                recipient=cm_profile.user,
                notification_type=Notification.TYPE_PROJECT_CM_REQUEST,
                title="Nuevo proyecto disponible",
                message=f'Has sido seleccionada para el proyecto "{project.nombre}". ¿Aceptas?',
                project=project,
            )

        return Response({"status": "cm_selected", "content_maker_id": cm_profile.id})

    @action(detail=False, methods=["get"], url_path="search_cms")
    def search_cms(self, request):
        """Lightweight CM search for clients selecting a content maker."""
        q = request.query_params.get("q", "").strip()
        qs = ContentMakerProfile.objects.all()
        if q:
            qs = qs.filter(
                models.Q(nombre__icontains=q)
                | models.Q(apellidos__icontains=q)
                | models.Q(instagram_handle__icontains=q)
            )
        qs = qs[:20]
        results = [
            {
                "id": cm.id,
                "nombre": f"{cm.nombre} {cm.apellidos}".strip(),
                "instagram_handle": cm.instagram_handle,
                "seguidores_instagram": cm.seguidores_instagram,
            }
            for cm in qs
        ]
        return Response(results)

    @action(detail=False, methods=["get"])
    def filters(self, request):
        statuses = list(ProjectStatus.objects.values("id", "nombre"))
        service_types = list(ServiceType.objects.values("id", "nombre"))
        return Response({"statuses": statuses, "service_types": service_types})


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return Response({"count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({"status": "ok"})

    @action(detail=True, methods=["patch"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)
