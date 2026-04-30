from datetime import timedelta

from django.db import models as models
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.content_makers.models import ContentMakerProfile
from apps.projects.models import (
    Briefing,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    ServiceType,
)
from apps.projects.serializers import (
    BriefingSerializer,
    NotificationSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectStatusSerializer,
    ProjectUpdateSerializer,
    ServiceTypeSerializer,
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

        # Transition project to Briefing phase
        briefing_status = ProjectStatus.objects.filter(nombre="Briefing").first()
        if briefing_status:
            project.status = briefing_status
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

        # Notify client — tell them to fill in the briefing
        if project.client.user:
            Notification.objects.create(
                recipient=project.client.user,
                notification_type=Notification.TYPE_PROJECT_CM_ACCEPTED,
                title="Content Maker confirmada — Completa el briefing",
                message=f'{cm_profile.nombre} {cm_profile.apellidos} ha aceptado participar en "{project.nombre}". Por favor, completa el briefing.',
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
            # If already existed (recommended or rejected), set to pending
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
            status__nombre__in=["Finalizado", "Borrador"]
        ).count()
        completed_projects = projects.filter(status__nombre="Finalizado").count()

        # Financial metrics
        from django.db.models import Sum
        financial = projects.aggregate(
            total_base=Sum("base_imponible"),
            total_impuestos=Sum("impuestos"),
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
                unique_cms[cm.id] = {
                    "id": cm.id,
                    "nombre": f"{cm.nombre} {cm.apellidos}".strip(),
                    "instagram_handle": cm.instagram_handle,
                    "projects_count": 0,
                }
            unique_cms[cm.id]["projects_count"] += 1
        content_makers = sorted(unique_cms.values(), key=lambda x: -x["projects_count"])

        # Projects by status
        status_breakdown = {}
        for p in projects:
            name = p.status.nombre if p.status else "Sin estado"
            status_breakdown[name] = status_breakdown.get(name, 0) + 1

        # Projects by service type
        service_breakdown = {}
        for p in projects:
            name = p.service_type.nombre if p.service_type else "Sin tipo"
            service_breakdown[name] = service_breakdown.get(name, 0) + 1

        # Calendar events (upcoming dates)
        from django.utils import timezone
        today = timezone.now().date()
        calendar_events = []
        for p in projects:
            if p.fecha_servicio and p.fecha_servicio >= today:
                calendar_events.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "project_id": p.project_id,
                    "date": str(p.fecha_servicio),
                    "type": "servicio",
                })
            if p.fecha_fin and p.fecha_fin >= today:
                calendar_events.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "project_id": p.project_id,
                    "date": str(p.fecha_fin),
                    "type": "fin",
                })
        calendar_events.sort(key=lambda x: x["date"])

        # Project ranges for calendar visualization
        project_ranges = []
        for p in projects:
            if p.fecha_venta or p.fecha_servicio or p.fecha_fin:
                project_ranges.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "project_id": p.project_id,
                    "fecha_inicio": str(p.fecha_venta) if p.fecha_venta else None,
                    "fecha_servicio": str(p.fecha_servicio) if p.fecha_servicio else None,
                    "fecha_fin": str(p.fecha_fin) if p.fecha_fin else None,
                    "status_name": p.status.nombre if p.status else None,
                })

        # Recent projects
        recent = projects.order_by("-created_at")[:5]
        recent_projects = [
            {
                "id": p.id,
                "project_id": p.project_id,
                "nombre": p.nombre,
                "status_name": p.status.nombre if p.status else None,
                "fecha_servicio": str(p.fecha_servicio) if p.fecha_servicio else None,
                "fecha_fin": str(p.fecha_fin) if p.fecha_fin else None,
                "precio_total": str(p.base_imponible + p.impuestos),
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
            status__nombre__in=["Finalizado", "Cancelado"]
        ).count()
        completed_projects = projects.filter(status__nombre="Finalizado").count()

        # --- Status breakdown ---
        status_breakdown = {}
        for entry in projects.exclude(is_draft=True).values("status__nombre").annotate(count=Count("id")):
            name = entry["status__nombre"] or "Sin estado"
            status_breakdown[name] = entry["count"]

        # --- Service type breakdown ---
        service_breakdown = {}
        for entry in projects.exclude(is_draft=True).values("service_type__nombre").annotate(count=Count("id")):
            name = entry["service_type__nombre"] or "Sin tipo"
            service_breakdown[name] = entry["count"]

        # --- Financial metrics ---
        financial = projects.filter(is_draft=False).aggregate(
            total_base=Sum("base_imponible"),
            total_impuestos=Sum("impuestos"),
        )
        total_facturado = (financial["total_base"] or 0) + (financial["total_impuestos"] or 0)

        # --- Clients ---
        total_clients = ClientProfile.objects.count()
        clients_with_active = ClientProfile.objects.filter(
            projects__is_draft=False
        ).exclude(projects__status__nombre__in=["Finalizado", "Cancelado"]).distinct().count()

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
            status__nombre="Briefing"
        ).exclude(briefings__isnull=False)
        projects_pending_briefing = projects_pending_briefing_qs.count()

        pending_actions = []
        if pending_cm_responses:
            items = [
                {
                    "project_id": e.project.id,
                    "project_name": e.project.nombre,
                    "project_code": e.project.project_id,
                    "cm_name": f"{e.content_maker.nombre} {e.content_maker.apellidos}".strip(),
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
                    "project_name": p.nombre,
                    "project_code": p.project_id,
                    "client_name": p.client.nombre_cliente if p.client else None,
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
                    "project_name": p.nombre,
                    "project_code": p.project_id,
                    "client_name": p.client.nombre_cliente if p.client else None,
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
            if p.fecha_venta or p.fecha_servicio or p.fecha_fin:
                cm_name = None
                if p.content_maker:
                    cm_name = f"{p.content_maker.nombre} {p.content_maker.apellidos}".strip()
                project_ranges.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "project_id": p.project_id,
                    "client_name": p.client.nombre_cliente if p.client else None,
                    "cm_name": cm_name,
                    "fecha_inicio": str(p.fecha_venta) if p.fecha_venta else None,
                    "fecha_servicio": str(p.fecha_servicio) if p.fecha_servicio else None,
                    "fecha_fin": str(p.fecha_fin) if p.fecha_fin else None,
                    "status_name": p.status.nombre if p.status else None,
                    "service_type": p.service_type.nombre if p.service_type else None,
                })

        # --- Today's tasks: projects with a date today ---
        todays_tasks = []
        for p in projects.filter(is_draft=False):
            if p.fecha_servicio == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "nombre": p.nombre,
                    "event": "Fecha de servicio",
                    "client_name": p.client.nombre_cliente if p.client else None,
                    "status_name": p.status.nombre if p.status else None,
                })
            if p.fecha_fin == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "nombre": p.nombre,
                    "event": "Fecha de fin",
                    "client_name": p.client.nombre_cliente if p.client else None,
                    "status_name": p.status.nombre if p.status else None,
                })
            if p.fecha_venta == today:
                todays_tasks.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "nombre": p.nombre,
                    "event": "Fecha de venta",
                    "client_name": p.client.nombre_cliente if p.client else None,
                    "status_name": p.status.nombre if p.status else None,
                })

        # --- Upcoming events (next 7 days) ---
        upcoming = []
        week_end = today + timedelta(days=7)
        for p in projects.filter(is_draft=False):
            if p.fecha_servicio and today < p.fecha_servicio <= week_end:
                upcoming.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "nombre": p.nombre,
                    "event": "Servicio",
                    "date": str(p.fecha_servicio),
                    "client_name": p.client.nombre_cliente if p.client else None,
                })
            if p.fecha_fin and today < p.fecha_fin <= week_end:
                upcoming.append({
                    "id": p.id,
                    "project_id": p.project_id,
                    "nombre": p.nombre,
                    "event": "Fin de proyecto",
                    "date": str(p.fecha_fin),
                    "client_name": p.client.nombre_cliente if p.client else None,
                })
        upcoming.sort(key=lambda x: x["date"])

        # --- Recent projects ---
        recent = projects.filter(is_draft=False).order_by("-created_at")[:8]
        recent_projects = [
            {
                "id": p.id,
                "project_id": p.project_id,
                "nombre": p.nombre,
                "client_name": p.client.nombre_cliente if p.client else None,
                "status_name": p.status.nombre if p.status else None,
                "service_type": p.service_type.nombre if p.service_type else None,
                "fecha_servicio": str(p.fecha_servicio) if p.fecha_servicio else None,
                "created_at": str(p.created_at.date()),
            }
            for p in recent
        ]

        # --- Top content makers (by accepted projects) ---
        top_cms_qs = (
            ProjectContentMaker.objects.filter(status=ProjectContentMaker.STATUS_ACCEPTED)
            .values("content_maker__id", "content_maker__nombre", "content_maker__apellidos", "content_maker__instagram_handle")
            .annotate(projects_count=Count("project", distinct=True))
            .order_by("-projects_count")[:10]
        )
        top_cms = [
            {
                "id": entry["content_maker__id"],
                "nombre": f'{entry["content_maker__nombre"]} {entry["content_maker__apellidos"]}'.strip(),
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
                "nombre": c.nombre_cliente,
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
        qs = Briefing.objects.select_related("project", "content_maker")

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

    def create(self, request, *args, **kwargs):
        """Only clients (project owners) or admins can create briefings."""
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

        # Notify the content maker
        cm = briefing.content_maker
        if cm.user:
            Notification.objects.create(
                recipient=cm.user,
                notification_type=Notification.TYPE_BRIEFING_SUBMITTED,
                title="Nuevo briefing recibido",
                message=f'Has recibido el briefing para el proyecto "{project.nombre}".',
                project=project,
            )

        return Response(BriefingSerializer(briefing).data, status=status.HTTP_201_CREATED)
