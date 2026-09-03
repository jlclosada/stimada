from datetime import timedelta

from django.db import models as models
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Briefing,
    BriefingLink,
    BriefingPhoto,
    Deliverable,
    Format,
    ProductLogistics,
    EconomicModel,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    WhoRecords,
    WhoPublishes,
    WhoReviews,
    ProductPickup,
    SocialNetwork,
    ServiceType,
    StatusChangeLog,
    WinStatus,
)
from apps.projects.serializers import (
    BriefingSerializer,
    DeliverableSerializer,
    FormatSerializer,
    ProductLogisticsSerializer,
    EconomicModelSerializer,
    NotificationSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectStatusSerializer,
    ProjectUpdateSerializer,
    WhoRecordsSerializer,
    WhoPublishesSerializer,
    WhoReviewsSerializer,
    ProductPickupSerializer,
    SocialNetworkSerializer,
    ServiceTypeSerializer,
    StatusChangeLogSerializer,
    WinStatusSerializer,
)
from apps.projects.services import (
    handle_briefing_submitted,
    handle_cm_accept,
    handle_cm_reject,
    handle_deliverable_review,
    handle_deliverable_status_change,
    handle_deliverable_upload,
    override_project_status,
    transition_project_status,
)
from config.pagination import FlexiblePageNumberPagination


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FlexiblePageNumberPagination

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProjectUpdateSerializer
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
                models.Q(name__icontains=search)
                | models.Q(project_id__icontains=search)
                | models.Q(client__name__icontains=search)
            )

        status_filter = params.get("status")
        if status_filter:
            qs = qs.filter(status__name=status_filter)

        service_type_filter = params.get("service_type")
        if service_type_filter:
            qs = qs.filter(service_type__name=service_type_filter)

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

        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile
        success = handle_cm_accept(project, cm_profile, user=user)

        if not success:
            return Response(
                {"detail": "No estás asignada a este proyecto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"status": "accepted"})

    @action(detail=True, methods=["post"], url_path="reject")
    def reject_project(self, request, pk=None):
        project = self.get_object()
        user = request.user

        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile
        success = handle_cm_reject(project, cm_profile, user=user)

        if not success:
            return Response(
                {"detail": "No estás asignada a este proyecto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"status": "rejected"})

    @action(detail=True, methods=["post"], url_path="override_status")
    def override_status(self, request, pk=None):
        """Manual status override by Admin/Employee with mandatory reason."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden cambiar el estado manualmente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status_name = request.data.get("status")
        reason = request.data.get("reason", "").strip()

        if not new_status_name:
            return Response({"detail": "Debes indicar el estado destino."}, status=status.HTTP_400_BAD_REQUEST)
        if not reason:
            return Response({"detail": "El motivo del cambio es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = override_project_status(project, new_status_name, user, reason)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "overridden", "new_status": result})

    @action(detail=True, methods=["get"], url_path="status_history")
    def status_history(self, request, pk=None):
        """Get status change history for a project."""
        project = self.get_object()
        changes = StatusChangeLog.objects.filter(project=project).select_related(
            "from_status", "to_status", "changed_by"
        )
        data = StatusChangeLogSerializer(changes, many=True).data
        return Response(data)

    @action(detail=True, methods=["post"], url_path="upload_deliverable")
    def upload_deliverable(self, request, pk=None):
        """CM uploads a deliverable for the project."""
        project = self.get_object()
        user = request.user

        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile

        # Verify CM is accepted on this project
        pcm = ProjectContentMaker.objects.filter(
            project=project, content_maker=cm_profile, status=ProjectContentMaker.STATUS_ACCEPTED
        ).first()
        if not pcm:
            return Response({"detail": "No estás confirmada en este proyecto."}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Debes subir un archivo."}, status=status.HTTP_400_BAD_REQUEST)

        description = request.data.get("description", "")

        deliverable = Deliverable.objects.create(
            project=project,
            content_maker=cm_profile,
            file=file,
            description=description,
        )

        handle_deliverable_upload(project, deliverable)
        return Response(DeliverableSerializer(deliverable).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="reupload_deliverable")
    def reupload_deliverable(self, request, pk=None):
        """CM reuploads a deliverable after revision request."""
        project = self.get_object()
        user = request.user

        if not hasattr(user, "content_maker_profile"):
            return Response({"detail": "No eres una content maker."}, status=status.HTTP_403_FORBIDDEN)

        cm_profile = user.content_maker_profile

        deliverable_id = request.data.get("deliverable_id")
        if not deliverable_id:
            return Response({"detail": "Debes indicar deliverable_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deliverable = Deliverable.objects.get(id=deliverable_id, project=project, content_maker=cm_profile)
        except Deliverable.DoesNotExist:
            return Response({"detail": "Entregable no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if deliverable.status != Deliverable.STATUS_REVISION:
            return Response(
                {"detail": "Solo puedes resubir un entregable en estado de revisión."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Debes subir un archivo."}, status=status.HTTP_400_BAD_REQUEST)

        deliverable.file = file
        deliverable.status = Deliverable.STATUS_PENDING
        deliverable.revision_round += 1
        deliverable.reviewed_by = None
        deliverable.reviewed_at = None
        deliverable.save()

        handle_deliverable_upload(project, deliverable)
        return Response(DeliverableSerializer(deliverable).data)

    @action(detail=True, methods=["post"], url_path="review_deliverable")
    def review_deliverable(self, request, pk=None):
        """PM reviews a deliverable (approve or request revision)."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden revisar entregables."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deliverable_id = request.data.get("deliverable_id")
        approved = request.data.get("approved")
        notes = request.data.get("notes", "")

        if deliverable_id is None or approved is None:
            return Response(
                {"detail": "Debes indicar deliverable_id y approved (true/false)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deliverable = Deliverable.objects.get(id=deliverable_id, project=project)
        except Deliverable.DoesNotExist:
            return Response({"detail": "Entregable no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            handle_deliverable_review(deliverable, user, approved=bool(approved), notes=notes)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(DeliverableSerializer(deliverable).data)

    @action(detail=True, methods=["get"], url_path="deliverables")
    def list_deliverables(self, request, pk=None):
        """List all deliverables for a project."""
        project = self.get_object()
        deliverables = project.deliverables.select_related("content_maker", "reviewed_by")
        return Response(DeliverableSerializer(deliverables, many=True).data)

    @action(detail=True, methods=["post"], url_path="mark_published")
    def mark_published(self, request, pk=None):
        """Mark an approved deliverable as published (set published_at)."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden marcar como publicado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deliverable_id = request.data.get("deliverable_id")
        if not deliverable_id:
            return Response({"detail": "Debes indicar deliverable_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deliverable = Deliverable.objects.get(id=deliverable_id, project=project)
        except Deliverable.DoesNotExist:
            return Response({"detail": "Entregable no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if deliverable.status != Deliverable.STATUS_APPROVED:
            return Response(
                {"detail": "Solo se pueden marcar como publicados entregables aprobados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils import timezone as tz
        deliverable.published_at = tz.now()
        deliverable.save(update_fields=["published_at"])

        # Notify the CM that her content was published
        if deliverable.content_maker.user:
            Notification.objects.create(
                recipient=deliverable.content_maker.user,
                notification_type=Notification.TYPE_DELIVERY_APPROVED,
                title="Tu contenido ha sido publicado",
                message=f'Tu entregable para "{project.name}" ha sido publicado.',
                project=project,
            )

        # Notify client
        if project.client and project.client.user:
            Notification.objects.create(
                recipient=project.client.user,
                notification_type=Notification.TYPE_STATUS_CHANGED,
                title="Contenido publicado",
                message=f'Se ha publicado contenido en el proyecto "{project.name}".',
                project=project,
            )

        # Evaluate state transition (may move to Publicado → Finalizado)
        transition_project_status(project, user=user)

        return Response(DeliverableSerializer(deliverable).data)

    @action(detail=True, methods=["post"], url_path="delete_deliverable")
    def delete_deliverable(self, request, pk=None):
        """Admin/Employee can delete a deliverable."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden eliminar entregables."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deliverable_id = request.data.get("deliverable_id")
        if not deliverable_id:
            return Response({"detail": "Debes indicar deliverable_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deliverable = Deliverable.objects.get(id=deliverable_id, project=project)
        except Deliverable.DoesNotExist:
            return Response({"detail": "Entregable no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        deliverable.delete()
        return Response({"status": "deleted"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="change_deliverable_status")
    def change_deliverable_status(self, request, pk=None):
        """Admin/Employee can change a deliverable's status freely."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden cambiar el estado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deliverable_id = request.data.get("deliverable_id")
        new_status = request.data.get("status")

        if not deliverable_id or not new_status:
            return Response(
                {"detail": "Debes indicar deliverable_id y status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = [c[0] for c in Deliverable.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Estado no válido. Opciones: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deliverable = Deliverable.objects.get(id=deliverable_id, project=project)
        except Deliverable.DoesNotExist:
            return Response({"detail": "Entregable no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        notes = request.data.get("notes", "")
        handle_deliverable_status_change(deliverable, new_status, user=user, notes=notes)

        deliverable.refresh_from_db()
        return Response(DeliverableSerializer(deliverable).data)

    @action(detail=True, methods=["post"], url_path="confirm_pickup")
    def confirm_pickup(self, request, pk=None):
        """Confirm product has been picked up (for product_return=True projects)."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden confirmar la recogida."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not project.product_return:
            return Response(
                {"detail": "Este proyecto no requiere devolución de producto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Move to Proyecto Finalizado
        from apps.projects.models import ProjectStatus as PS
        finalizado = PS.objects.filter(name="Proyecto Finalizado").first()
        if finalizado and project.status != finalizado:
            old_status = project.status
            project.status = finalizado
            project.save(update_fields=["status", "updated_at"])
            StatusChangeLog.objects.create(
                project=project,
                from_status=old_status,
                to_status=finalizado,
                is_manual=False,
                reason="Recogida de producto confirmada.",
                changed_by=user,
            )

            # Notify all involved parties
            recipients = set()
            if project.created_by:
                recipients.add(project.created_by)
            if project.client and project.client.user:
                recipients.add(project.client.user)
            # Notify accepted CMs
            for pcm in project.content_makers.filter(status=ProjectContentMaker.STATUS_ACCEPTED).select_related("content_maker__user"):
                if pcm.content_maker.user:
                    recipients.add(pcm.content_maker.user)

            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    notification_type=Notification.TYPE_STATUS_CHANGED,
                    title="Proyecto finalizado",
                    message=f'El proyecto "{project.name}" ha sido finalizado. Producto recogido correctamente.',
                    project=project,
                )

        return Response({"status": "confirmed", "new_status": "Proyecto Finalizado"})

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
            # If already existed (recommended or rejected), set to pending
            pcm.status = ProjectContentMaker.STATUS_PENDING
            pcm.save()

        # Notify the CM
        if cm_profile.user:
            Notification.objects.create(
                recipient=cm_profile.user,
                notification_type=Notification.TYPE_PROJECT_CM_REQUEST,
                title="Nuevo proyecto disponible",
                message=f'Has sido seleccionada para el proyecto "{project.name}". ¿Aceptas?',
                project=project,
            )

        return Response({"status": "cm_selected", "content_maker_id": cm_profile.id})

    @action(detail=True, methods=["post"], url_path="unlink_cm")
    def unlink_cm(self, request, pk=None):
        """Admin/employee removes a content maker from a project, deleting associated briefings."""
        project = self.get_object()
        user = request.user

        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden desvincular content makers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        cm_id = request.data.get("content_maker_id")
        if not cm_id:
            return Response(
                {"detail": "Debes indicar content_maker_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Remove the ProjectContentMaker record
        pcm = ProjectContentMaker.objects.filter(project=project, content_maker_id=cm_id).first()
        if pcm:
            pcm.delete()

        # Delete associated briefings for this CM on this project
        Briefing.objects.filter(project=project, content_maker_id=cm_id).delete()

        # If this was the assigned content_maker FK, clear it
        if project.content_maker_id and project.content_maker_id == int(cm_id):
            project.content_maker = None
            project.save()

        return Response({"status": "unlinked"})

    @action(detail=False, methods=["get"], url_path="search_cms")
    def search_cms(self, request):
        """Lightweight CM search for clients selecting a content maker."""
        q = request.query_params.get("q", "").strip()
        qs = ContentMakerProfile.objects.all()
        if q:
            qs = qs.filter(
                models.Q(first_name__icontains=q)
                | models.Q(last_name__icontains=q)
                | models.Q(instagram_handle__icontains=q)
            )
        qs = qs[:20]
        results = []
        for cm in qs:
            photo_url = None
            if cm.photo:
                photo_url = request.build_absolute_uri(cm.photo.url)
            results.append({
                "id": cm.id,
                "name": f"{cm.first_name} {cm.last_name}".strip(),
                "instagram_handle": cm.instagram_handle,
                "instagram_followers": cm.instagram_followers,
                "photo_url": photo_url,
            })
        return Response(results)

    @action(detail=False, methods=["get"])
    def filters(self, request):
        statuses = ProjectStatusSerializer(ProjectStatus.objects.filter(is_active=True), many=True).data
        creation_statuses = ProjectStatusSerializer(
            ProjectStatus.objects.filter(is_active=True, available_on_creation=True), many=True
        ).data
        service_types = ServiceTypeSerializer(ServiceType.objects.filter(is_active=True), many=True).data
        economic_models = EconomicModelSerializer(EconomicModel.objects.filter(is_active=True), many=True).data
        social_networks = SocialNetworkSerializer(SocialNetwork.objects.filter(is_active=True), many=True).data
        formats = FormatSerializer(Format.objects.filter(is_active=True), many=True).data
        product_logistics = ProductLogisticsSerializer(ProductLogistics.objects.filter(is_active=True), many=True).data
        product_pickup = ProductPickupSerializer(ProductPickup.objects.filter(is_active=True), many=True).data
        who_records = WhoRecordsSerializer(WhoRecords.objects.filter(is_active=True), many=True).data
        who_reviews = WhoReviewsSerializer(WhoReviews.objects.filter(is_active=True), many=True).data
        who_publishes = WhoPublishesSerializer(WhoPublishes.objects.filter(is_active=True), many=True).data
        win_statuses = WinStatusSerializer(WinStatus.objects.filter(is_active=True), many=True).data
        return Response({
            "statuses": statuses,
            "creation_statuses": creation_statuses,
            "service_types": service_types,
            "economic_models": economic_models,
            "social_networks": social_networks,
            "formats": formats,
            "product_logistics": product_logistics,
            "product_pickup": product_pickup,
            "who_records": who_records,
            "who_reviews": who_reviews,
            "who_publishes": who_publishes,
            "win_statuses": win_statuses,
        })

    @action(detail=False, methods=["get"])
    def next_id(self, request):
        next_num = Project.generate_next_id()
        return Response({"next_id": next_num})

    @action(detail=False, methods=["get"], url_path="client_dashboard")
    def client_dashboard(self, request):
        """Dashboard metrics for the authenticated client."""
        user = request.user
        if user.role != "client" or not hasattr(user, "client_profile"):
            return Response(
                {"detail": "Solo disponible para clientes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        client_profile = user.client_profile
        projects = Project.objects.filter(client=client_profile).select_related("status", "service_type")

        total_projects = projects.count()
        active_projects = projects.exclude(
            status__name__in=["Finalizado", "Borrador"]
        ).count()
        completed_projects = projects.filter(status__name="Finalizado").count()

        # Financial metrics
        from django.db.models import Sum
        financial = projects.aggregate(
            total_base=Sum("tax_base"),
            total_impuestos=Sum("taxes"),
        )
        total_invertido = (financial["total_base"] or 0) + (financial["total_impuestos"] or 0)

        # Content makers associated (accepted in any project)
        cm_entries = ProjectContentMaker.objects.filter(
            project__client=client_profile,
            status=ProjectContentMaker.STATUS_ACCEPTED,
        ).select_related("content_maker")
        unique_cms = {}
        for entry in cm_entries:
            cm = entry.content_maker
            if cm.id not in unique_cms:
                photo_url = None
                if cm.photo:
                    photo_url = request.build_absolute_uri(cm.photo.url)
                unique_cms[cm.id] = {
                    "id": cm.id,
                    "name": f"{cm.first_name} {cm.last_name}".strip(),
                    "instagram_handle": cm.instagram_handle,
                    "photo_url": photo_url,
                    "projects_count": 0,
                }
            unique_cms[cm.id]["projects_count"] += 1
        content_makers = sorted(unique_cms.values(), key=lambda x: -x["projects_count"])

        # Projects by status
        status_breakdown = {}
        for p in projects:
            name = p.status.name if p.status else "Sin estado"
            status_breakdown[name] = status_breakdown.get(name, 0) + 1

        # Projects by service type
        service_breakdown = {}
        for p in projects:
            name = p.service_type.name if p.service_type else "Sin tipo"
            service_breakdown[name] = service_breakdown.get(name, 0) + 1

        # Calendar events (upcoming dates)
        from django.utils import timezone
        today = timezone.now().date()
        calendar_events = []
        for p in projects:
            if p.service_date and p.service_date >= today:
                calendar_events.append({
                    "id": p.id,
                    "name": p.name,
                    "project_id": p.project_id,
                    "date": str(p.service_date),
                    "type": "servicio",
                })
            if p.end_date and p.end_date >= today:
                calendar_events.append({
                    "id": p.id,
                    "name": p.name,
                    "project_id": p.project_id,
                    "date": str(p.end_date),
                    "type": "fin",
                })
        calendar_events.sort(key=lambda x: x["date"])

        # Project ranges for calendar visualization
        project_ranges = []
        for p in projects:
            if p.sale_date or p.service_date or p.end_date:
                project_ranges.append({
                    "id": p.id,
                    "name": p.name,
                    "project_id": p.project_id,
                    "start_date": str(p.sale_date) if p.sale_date else None,
                    "service_date": str(p.service_date) if p.service_date else None,
                    "end_date": str(p.end_date) if p.end_date else None,
                    "status_name": p.status.name if p.status else None,
                })

        # Recent projects
        recent = projects.order_by("-created_at")[:5]
        recent_projects = [
            {
                "id": p.id,
                "project_id": p.project_id,
                "name": p.name,
                "status_name": p.status.name if p.status else None,
                "service_date": str(p.service_date) if p.service_date else None,
                "end_date": str(p.end_date) if p.end_date else None,
                "total_price": str(p.tax_base + p.taxes),
            }
            for p in recent
        ]

        return Response({
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_invertido": str(total_invertido),
            "content_makers": content_makers,
            "total_content_makers": len(content_makers),
            "status_breakdown": status_breakdown,
            "service_breakdown": service_breakdown,
            "calendar_events": calendar_events,
            "project_ranges": project_ranges,
            "recent_projects": recent_projects,
        })

    @action(detail=False, methods=["get"], url_path="staff_dashboard")
    def staff_dashboard(self, request):
        """Comprehensive dashboard for admin and stimada_employee users."""
        user = request.user
        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo disponible para administradores y empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from apps.clients.models import ClientProfile

        today = timezone.now().date()

        # --- All projects ---
        projects = Project.objects.select_related(
            "client", "brand", "status", "service_type", "content_maker"
        ).prefetch_related("content_makers__content_maker")

        total_projects = projects.count()
        draft_projects = projects.filter(is_draft=True).count()
        active_projects = projects.filter(is_draft=False).exclude(
            status__name__in=["Finalizado", "Cancelado"]
        ).count()
        completed_projects = projects.filter(status__name="Finalizado").count()

        # --- Status breakdown ---
        status_breakdown = {}
        for entry in projects.exclude(is_draft=True).values("status__name").annotate(count=Count("id")):
            name = entry["status__name"] or "Sin estado"
            status_breakdown[name] = entry["count"]

        # --- Service type breakdown ---
        service_breakdown = {}
        for entry in projects.exclude(is_draft=True).values("service_type__name").annotate(count=Count("id")):
            name = entry["service_type__name"] or "Sin tipo"
            service_breakdown[name] = entry["count"]

        # --- Financial metrics ---
        financial = projects.filter(is_draft=False).aggregate(
            total_base=Sum("tax_base"),
            total_impuestos=Sum("taxes"),
        )
        total_facturado = (financial["total_base"] or 0) + (financial["total_impuestos"] or 0)

        # --- Clients ---
        total_clients = ClientProfile.objects.count()
        clients_with_active = ClientProfile.objects.filter(
            projects__is_draft=False
        ).exclude(projects__status__name__in=["Finalizado", "Cancelado"]).distinct().count()

        # --- Content Makers ---
        total_cms = ContentMakerProfile.objects.count()
        cms_active = ContentMakerProfile.objects.filter(
            Q(project_participations__status=ProjectContentMaker.STATUS_ACCEPTED)
        ).distinct().count()

        # --- Pending actions ---
        pending_cm_entries = ProjectContentMaker.objects.filter(
            status=ProjectContentMaker.STATUS_PENDING
        ).select_related("content_maker", "project", "project__client")
        pending_cm_responses = pending_cm_entries.count()

        projects_without_cm_qs = projects.filter(
            is_draft=False, content_maker__isnull=True
        ).exclude(
            content_makers__status=ProjectContentMaker.STATUS_ACCEPTED
        )
        projects_without_cm = projects_without_cm_qs.count()

        projects_pending_briefing_qs = projects.filter(
            status__name="Briefing"
        ).exclude(briefings__isnull=False)
        projects_pending_briefing = projects_pending_briefing_qs.count()

        pending_actions = []
        if pending_cm_responses:
            items = [
                {
                    "project_id": e.project.id,
                    "project_name": e.project.name,
                    "project_code": e.project.project_id,
                    "cm_name": f"{e.content_maker.first_name} {e.content_maker.last_name}".strip(),
                    "cm_id": e.content_maker.id,
                }
                for e in pending_cm_entries
            ]
            pending_actions.append({
                "type": "cm_pending",
                "label": f"{pending_cm_responses} CM pendientes de responder",
                "count": pending_cm_responses,
                "items": items,
            })
        if projects_without_cm:
            items = [
                {
                    "project_id": p.id,
                    "project_name": p.name,
                    "project_code": p.project_id,
                    "client_name": p.client.name if p.client else None,
                }
                for p in projects_without_cm_qs[:20]
            ]
            pending_actions.append({
                "type": "no_cm",
                "label": f"{projects_without_cm} proyectos sin content maker",
                "count": projects_without_cm,
                "items": items,
            })
        if projects_pending_briefing:
            items = [
                {
                    "project_id": p.id,
                    "project_name": p.name,
                    "project_code": p.project_id,
                    "client_name": p.client.name if p.client else None,
                }
                for p in projects_pending_briefing_qs[:20]
            ]
            pending_actions.append({
                "type": "briefing_pending",
                "label": f"{projects_pending_briefing} proyectos esperando briefing",
                "count": projects_pending_briefing,
                "items": items,
            })

        # --- Calendar: all project date ranges ---
        project_ranges = []
        for p in projects.filter(is_draft=False):
            if p.sale_date or p.service_date or p.end_date:
                cm_name = None
                if p.content_maker:
                    cm_name = f"{p.content_maker.first_name} {p.content_maker.last_name}".strip()
                project_ranges.append({
                    "id": p.id,
                    "name": p.name,
                    "project_id": p.project_id,
                    "client_name": p.client.name if p.client else None,
                    "cm_name": cm_name,
                    "start_date": str(p.sale_date) if p.sale_date else None,
                    "service_date": str(p.service_date) if p.service_date else None,
                    "end_date": str(p.end_date) if p.end_date else None,
                    "status_name": p.status.name if p.status else None,
                    "service_type": p.service_type.name if p.service_type else None,
                })

        # --- Today's tasks: projects with a date today ---
        todays_tasks = []
        for p in projects.filter(is_draft=False):
            if p.service_date == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "name": p.name,
                    "event": "Fecha de servicio",
                    "client_name": p.client.name if p.client else None,
                    "status_name": p.status.name if p.status else None,
                })
            if p.end_date == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "name": p.name,
                    "event": "Fecha de fin",
                    "client_name": p.client.name if p.client else None,
                    "status_name": p.status.name if p.status else None,
                })
            if p.sale_date == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "name": p.name,
                    "event": "Fecha de venta",
                    "client_name": p.client.name if p.client else None,
                    "status_name": p.status.name if p.status else None,
                })

        # --- Upcoming events (next 7 days) ---
        upcoming = []
        week_end = today + timedelta(days=7)
        for p in projects.filter(is_draft=False):
            if p.service_date and today < p.service_date <= week_end:
                upcoming.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "name": p.name,
                    "event": "Servicio",
                    "date": str(p.service_date),
                    "client_name": p.client.name if p.client else None,
                })
            if p.end_date and today < p.end_date <= week_end:
                upcoming.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "name": p.name,
                    "event": "Fin de proyecto",
                    "date": str(p.end_date),
                    "client_name": p.client.name if p.client else None,
                })
        upcoming.sort(key=lambda x: x["date"])

        # --- Recent projects ---
        recent = projects.filter(is_draft=False).order_by("-created_at")[:8]
        recent_projects = [
            {
                "id": p.id,
                "project_id": p.project_id,
                "name": p.name,
                "client_name": p.client.name if p.client else None,
                "status_name": p.status.name if p.status else None,
                "service_type": p.service_type.name if p.service_type else None,
                "service_date": str(p.service_date) if p.service_date else None,
                "created_at": str(p.created_at.date()),
            }
            for p in recent
        ]

        # --- Top content makers (by accepted projects) ---
        top_cms_qs = (
            ProjectContentMaker.objects.filter(status=ProjectContentMaker.STATUS_ACCEPTED)
            .values("content_maker__id", "content_maker__first_name", "content_maker__last_name", "content_maker__instagram_handle")
            .annotate(projects_count=Count("project", distinct=True))
            .order_by("-projects_count")[:10]
        )
        top_cms = [
            {
                "id": entry["content_maker__id"],
                "name": f'{entry["content_maker__first_name"]} {entry["content_maker__last_name"]}'.strip(),
                "instagram_handle": entry["content_maker__instagram_handle"],
                "projects_count": entry["projects_count"],
            }
            for entry in top_cms_qs
        ]

        # --- Top clients (by project count) ---
        top_clients_qs = (
            ClientProfile.objects.annotate(projects_count=Count("projects"))
            .filter(projects_count__gt=0)
            .order_by("-projects_count")[:10]
        )
        top_clients = [
            {
                "id": c.id,
                "name": c.name,
                "projects_count": c.projects_count,
            }
            for c in top_clients_qs
        ]

        return Response({
            # KPIs
            "total_projects": total_projects,
            "draft_projects": draft_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_facturado": str(total_facturado),
            "total_clients": total_clients,
            "clients_with_active": clients_with_active,
            "total_cms": total_cms,
            "cms_active": cms_active,
            # Breakdowns
            "status_breakdown": status_breakdown,
            "service_breakdown": service_breakdown,
            # Pending actions
            "pending_actions": pending_actions,
            # Calendar
            "project_ranges": project_ranges,
            # Today
            "todays_tasks": todays_tasks,
            # Upcoming 7 days
            "upcoming_events": upcoming,
            # Lists
            "recent_projects": recent_projects,
            "top_cms": top_cms,
            "top_clients": top_clients,
        })


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)

        # Filter by type
        notification_type = self.request.query_params.get("type")
        if notification_type:
            qs = qs.filter(notification_type=notification_type)

        # Filter by read status
        read_status = self.request.query_params.get("read")
        if read_status == "true":
            qs = qs.filter(read=True)
        elif read_status == "false":
            qs = qs.filter(read=False)

        # Search in title/message
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                models.Q(title__icontains=search) | models.Q(message__icontains=search)
            )

        return qs.order_by("-created_at")

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


class BriefingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BriefingSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        user = self.request.user
        qs = Briefing.objects.select_related("project", "content_maker").prefetch_related("links", "photos")

        # CMs only see their own briefings
        if user.role == "content_maker" and hasattr(user, "content_maker_profile"):
            qs = qs.filter(content_maker=user.content_maker_profile)
        # Clients only see briefings for their projects
        elif user.role == "client" and hasattr(user, "client_profile"):
            qs = qs.filter(project__client=user.client_profile)

        # Filter by project if provided
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        """Only clients (project owners) or admins can create briefings."""
        import json

        user = request.user
        project_id = request.data.get("project")

        if not project_id:
            return Response({"detail": "project es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Check permission: client must own the project, or be admin/employee
        is_owner = (
            user.role == "client"
            and hasattr(user, "client_profile")
            and project.client == user.client_profile
        )
        is_staff = user.role in ("admin", "stimada_employee")
        if not is_owner and not is_staff:
            return Response(
                {"detail": "No tienes permiso para crear un briefing en este proyecto."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        briefing = serializer.save(created_by=user)

        # Create links from JSON array
        links_raw = request.data.get("links", "[]")
        if isinstance(links_raw, str):
            try:
                links_data = json.loads(links_raw)
            except (json.JSONDecodeError, TypeError):
                links_data = []
        else:
            links_data = links_raw if isinstance(links_raw, list) else []

        for i, link in enumerate(links_data):
            if isinstance(link, dict) and link.get("url"):
                BriefingLink.objects.create(
                    briefing=briefing,
                    url=link["url"],
                    title=link.get("title", ""),
                    order=i,
                )

        # Create photos from uploaded files
        photos = request.FILES.getlist("photos")
        for i, photo in enumerate(photos):
            BriefingPhoto.objects.create(
                briefing=briefing,
                image=photo,
                description=request.data.get(f"photo_description_{i}", ""),
                order=i,
            )

        # Use service for notifications and state transitions
        handle_briefing_submitted(briefing)

        # Re-fetch to include nested data
        briefing.refresh_from_db()
        return Response(
            BriefingSerializer(briefing, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """Only admins/employees can modify an existing briefing."""
        import json

        user = request.user
        if user.role not in ("admin", "stimada_employee"):
            return Response(
                {"detail": "Solo administradores y empleados pueden modificar briefings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        briefing = self.get_object()

        # Update comments if provided
        if "comments" in request.data:
            briefing.comments = request.data["comments"]
            briefing.save(update_fields=["comments", "updated_at"])

        # Update links: replace all with new set
        links_raw = request.data.get("links")
        if links_raw is not None:
            if isinstance(links_raw, str):
                try:
                    links_data = json.loads(links_raw)
                except (json.JSONDecodeError, TypeError):
                    links_data = []
            else:
                links_data = links_raw if isinstance(links_raw, list) else []

            briefing.links.all().delete()
            for i, link in enumerate(links_data):
                if isinstance(link, dict) and link.get("url"):
                    BriefingLink.objects.create(
                        briefing=briefing,
                        url=link["url"],
                        title=link.get("title", ""),
                        order=i,
                    )

        # Add new photos (existing photos are kept unless explicitly removed)
        new_photos = request.FILES.getlist("photos")
        existing_count = briefing.photos.count()
        for i, photo in enumerate(new_photos):
            BriefingPhoto.objects.create(
                briefing=briefing,
                image=photo,
                description=request.data.get(f"photo_description_{i}", ""),
                order=existing_count + i,
            )

        # Remove specific photos by ID
        remove_photos_raw = request.data.get("remove_photos")
        if remove_photos_raw:
            if isinstance(remove_photos_raw, str):
                try:
                    remove_ids = json.loads(remove_photos_raw)
                except (json.JSONDecodeError, TypeError):
                    remove_ids = []
            else:
                remove_ids = remove_photos_raw if isinstance(remove_photos_raw, list) else []
            if remove_ids:
                briefing.photos.filter(id__in=remove_ids).delete()

        briefing.refresh_from_db()
        return Response(
            BriefingSerializer(briefing, context={"request": request}).data,
        )
