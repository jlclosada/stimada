"""
Servicio de lógica de negocio para proyectos.
Incluye:
- Máquina de estados automática (6.7)
- Selección y aceptación/rechazo de CMs con auto-promoción de suplentes (6.5)
- Reglas temporales (6.1)
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.projects.models import (
    Briefing,
    Entregable,
    Notification,
    Project,
    ProjectContentMaker,
    ProjectStatus,
    StatusChangeLog,
)


# ─── State Machine ─────────────────────────────────────────────────────────────

# Map status names to their order for reference.
# Any status NOT in this dict gets order 0 (treated as early/initial state).
STATUS_ORDER = {
    "Borrador": 0,
    "Negociación": 1,
    "Perfiles Propuestos": 2,
    "Perfiles Aprobados": 3,
    "Producto Enviado": 4,
    "Briefing": 5,
    "Producto Recibido": 6,
    "En producción": 7,
    "Revisión": 8,
    "Publicado": 9,
    "Producto a Recoger": 10,
    "Proyecto Finalizado": 11,
    "Cerrado": 12,
}


def _get_status(nombre: str):
    """Get a ProjectStatus by name, or None."""
    return ProjectStatus.objects.filter(nombre=nombre).first()


def transition_project_status(project: Project, user=None, reason: str = "", force: bool = False):
    """
    Evaluate and apply automatic state transitions for a project.
    Loops until no more transitions are possible (catches up multiple states).
    Returns the final new status name if any transition happened, else None.
    """
    if force:
        return None

    last_new_name = None
    max_iterations = 12  # safety: prevent infinite loops

    for _ in range(max_iterations):
        project.refresh_from_db()
        old_status = project.status
        new_status = _evaluate_correct_status(project)

        if new_status and new_status != old_status:
            _apply_transition(project, old_status, new_status, user=user, is_manual=False)
            last_new_name = new_status.nombre
        else:
            break

    return last_new_name


def override_project_status(project: Project, new_status_name: str, user, reason: str):
    """
    Manual status override by Admin/Employee.
    Requires reason for audit trail.
    """
    if not reason.strip():
        raise ValueError("El motivo del cambio es obligatorio para un override manual.")

    old_status = project.status
    new_status = _get_status(new_status_name)
    if not new_status:
        raise ValueError(f"Estado '{new_status_name}' no encontrado.")

    _apply_transition(project, old_status, new_status, user=user, is_manual=True, reason=reason)

    # Audit the override
    from apps.audit.services import audit_status_override
    old_name = old_status.nombre if old_status else "—"
    audit_status_override(user, project, old_name, new_status_name, reason)

    return new_status.nombre


def _apply_transition(project: Project, from_status, to_status, user=None, is_manual=False, reason=""):
    """Apply a status transition and log it."""
    project.status = to_status
    project.save(update_fields=["status", "updated_at"])

    StatusChangeLog.objects.create(
        project=project,
        from_status=from_status,
        to_status=to_status,
        is_manual=is_manual,
        reason=reason,
        changed_by=user,
    )

    # Notify project creator about status change
    if project.created_by:
        from_name = from_status.nombre if from_status else "—"
        to_name = to_status.nombre if to_status else "—"
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_STATUS_CHANGED,
            title=f"Proyecto actualizado: {to_name}",
            message=f'El proyecto "{project.nombre}" ha pasado de "{from_name}" a "{to_name}".',
            project=project,
        )


def _evaluate_correct_status(project: Project):
    """
    Data-driven state evaluation.
    Determines the CORRECT state based on the project's current data,
    regardless of its current status. Only advances forward (never goes back).
    Returns a ProjectStatus instance if the project should move forward, else None.
    """
    current_name = project.status.nombre if project.status else ""
    current_order = STATUS_ORDER.get(current_name, 0)

    # Helper: only return a status if it's higher than current
    def _advance_to(name):
        target_order = STATUS_ORDER.get(name, 0)
        if target_order > current_order:
            return _get_status(name)
        return None

    # Gather data
    principal_cms = project.content_makers.filter(is_suplente=False)
    accepted_principals = principal_cms.filter(status=ProjectContentMaker.STATUS_ACCEPTED)
    pending_principals = principal_cms.filter(status=ProjectContentMaker.STATUS_PENDING)

    has_principals = principal_cms.exists()
    all_principals_accepted = has_principals and not principal_cms.exclude(
        status=ProjectContentMaker.STATUS_ACCEPTED
    ).exists()

    confirmed_count = accepted_principals.count()
    briefings_count = project.briefings.count()
    all_briefings_done = confirmed_count > 0 and briefings_count >= confirmed_count

    has_shipping_logistics = False
    if project.logistica_producto:
        logistica_name = project.logistica_producto.nombre.lower()
        has_shipping_logistics = "envío" in logistica_name or "envio" in logistica_name

    has_entregables = project.entregables.exists()
    entregables = project.entregables.all() if has_entregables else None

    # ─── Evaluate from highest to lowest (find the highest valid state) ───

    # 11. Proyecto Finalizado
    if has_entregables and entregables is not None:
        all_approved = not entregables.exclude(status=Entregable.STATUS_APPROVED).exists()
        all_published = not entregables.filter(published_at__isnull=True).exists()
        if all_approved and all_published:
            if project.devolucion_producto:
                # Need manual confirmation for pickup → stop at "Producto a Recoger"
                result = _advance_to("Producto a Recoger")
                if result:
                    return result
            else:
                result = _advance_to("Proyecto Finalizado")
                if result:
                    return result

    # 9. Publicado
    if has_entregables and entregables is not None:
        all_approved = not entregables.exclude(status=Entregable.STATUS_APPROVED).exists()
        all_published = not entregables.filter(published_at__isnull=True).exists()
        if all_approved and all_published:
            result = _advance_to("Publicado")
            if result:
                return result

    # 8. Revisión: entregables uploaded
    if has_entregables:
        result = _advance_to("Revisión")
        if result:
            return result

    # 7. En producción: briefings done + (product received or no shipping)
    if all_briefings_done:
        if has_shipping_logistics:
            if project.fecha_llegada_producto:
                result = _advance_to("En producción")
                if result:
                    return result
        else:
            # No shipping → skip product states, go to production
            result = _advance_to("En producción")
            if result:
                return result

    # 6. Producto Recibido
    if has_shipping_logistics and project.fecha_llegada_producto and all_briefings_done:
        result = _advance_to("Producto Recibido")
        if result:
            return result

    # 5. Briefing: all briefings submitted
    if all_briefings_done:
        result = _advance_to("Briefing")
        if result:
            return result

    # 4. Producto Enviado: shipping logistics + fecha_servicio (fecha envío)
    if has_shipping_logistics and project.fecha_servicio and all_principals_accepted:
        result = _advance_to("Producto Enviado")
        if result:
            return result

    # 3. Perfiles Aprobados: all principal CMs accepted
    if all_principals_accepted:
        result = _advance_to("Perfiles Aprobados")
        if result:
            return result

    # 2. Perfiles Propuestos: has principals with pending status
    if has_principals and (pending_principals.exists() or accepted_principals.exists()):
        result = _advance_to("Perfiles Propuestos")
        if result:
            return result

    return None


# ─── CM Acceptance & Promotion ──────────────────────────────────────────────────

def handle_cm_accept(project: Project, cm_profile, user=None):
    """
    Handle when a CM accepts a project.
    Updates status, notifies, and evaluates state transition.
    """
    pcm = ProjectContentMaker.objects.filter(
        project=project, content_maker=cm_profile
    ).first()
    if not pcm:
        return False

    pcm.status = ProjectContentMaker.STATUS_ACCEPTED
    pcm.responded_at = timezone.now()
    pcm.save(update_fields=["status", "responded_at"])

    # Notify project creator
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_PROJECT_CM_ACCEPTED,
            title="Content Maker aceptó el proyecto",
            message=f'{cm_profile.nombre} {cm_profile.apellidos} ha aceptado el proyecto "{project.nombre}".',
            project=project,
        )

    # Notify client to fill briefing
    if project.client and project.client.user:
        Notification.objects.create(
            recipient=project.client.user,
            notification_type=Notification.TYPE_BRIEFING_SUBMITTED,
            title="Content Maker confirmada — Completa el briefing",
            message=f'{cm_profile.nombre} {cm_profile.apellidos} ha aceptado "{project.nombre}". Por favor, completa el briefing.',
            project=project,
        )

    # Evaluate state transition
    transition_project_status(project, user=user)
    return True


def handle_cm_reject(project: Project, cm_profile, user=None):
    """
    Handle when a CM rejects a project.
    Auto-promotes the next suplente if available.
    """
    pcm = ProjectContentMaker.objects.filter(
        project=project, content_maker=cm_profile
    ).first()
    if not pcm:
        return False

    pcm.status = ProjectContentMaker.STATUS_REJECTED
    pcm.responded_at = timezone.now()
    pcm.save(update_fields=["status", "responded_at"])

    # If was assigned as primary content_maker, unassign
    if project.content_maker == cm_profile:
        project.content_maker = None
        project.save(update_fields=["content_maker", "updated_at"])

    # Notify project creator
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_PROJECT_CM_REJECTED,
            title="Content Maker rechazó el proyecto",
            message=f'{cm_profile.nombre} {cm_profile.apellidos} ha rechazado "{project.nombre}".',
            project=project,
        )

    # Auto-promote next suplente
    promoted = _promote_next_suplente(project, pcm)

    if not promoted:
        # No more suplentes — notify admin
        if project.created_by:
            Notification.objects.create(
                recipient=project.created_by,
                notification_type=Notification.TYPE_PROJECT_CM_REJECTED,
                title="Sin suplentes disponibles",
                message=f'Todas las Content Makers han rechazado "{project.nombre}". Se requiere acción manual.',
                project=project,
            )

    return True


def _promote_next_suplente(project: Project, rejected_pcm):
    """
    Promote the next available suplente to principal.
    Returns True if a suplente was promoted, False otherwise.
    """
    # Find next suplente that hasn't been rejected
    next_suplente = ProjectContentMaker.objects.filter(
        project=project,
        is_suplente=True,
        status=ProjectContentMaker.STATUS_PENDING,
    ).order_by("created_at").first()

    if not next_suplente:
        return False

    # Promote: mark as principal
    next_suplente.is_suplente = False
    next_suplente.status = ProjectContentMaker.STATUS_PENDING
    next_suplente.save(update_fields=["is_suplente", "status"])

    # Send notification to the promoted CM
    cm = next_suplente.content_maker
    if cm.user:
        Notification.objects.create(
            recipient=cm.user,
            notification_type=Notification.TYPE_CM_PROMOTED,
            title="Has sido seleccionada para un proyecto",
            message=f'Has sido promovida como Content Maker principal para "{project.nombre}". ¿Aceptas?',
            project=project,
        )

    # Notify project creator
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_CM_PROMOTED,
            title="Suplente promovida automáticamente",
            message=f'{cm.nombre} {cm.apellidos} ha sido promovida a principal en "{project.nombre}".',
            project=project,
        )

    return True


# ─── Deadline Logic (6.1) ───────────────────────────────────────────────────────

def check_deadline_reminders():
    """
    Check all projects for deadline reminders (3 days before fecha_limite_entrega).
    Should be called daily via management command or cron.
    """
    today = timezone.now().date()
    reminder_date = today + timedelta(days=3)

    projects = Project.objects.filter(
        fecha_limite_entrega=reminder_date,
        retrasado=False,
    ).select_related("status", "created_by", "content_maker")

    for project in projects:
        # Notify all accepted CMs
        accepted_cms = project.content_makers.filter(
            status=ProjectContentMaker.STATUS_ACCEPTED
        ).select_related("content_maker__user")

        for pcm in accepted_cms:
            if pcm.content_maker.user:
                Notification.objects.create(
                    recipient=pcm.content_maker.user,
                    notification_type=Notification.TYPE_DEADLINE_REMINDER,
                    title="Recordatorio: entrega en 3 días",
                    message=f'Tu entrega para "{project.nombre}" vence el {project.fecha_limite_entrega}.',
                    project=project,
                )

        # Notify PM (creator)
        if project.created_by:
            Notification.objects.create(
                recipient=project.created_by,
                notification_type=Notification.TYPE_DEADLINE_REMINDER,
                title=f"Recordatorio: entrega en 3 días ({project.project_id})",
                message=f'El proyecto "{project.nombre}" tiene fecha límite el {project.fecha_limite_entrega}.',
                project=project,
            )


def check_overdue_deliveries():
    """
    Check all projects for overdue deliveries (fecha_limite_entrega = today, no deliverables).
    Should be called daily. Activates the 'retrasado' flag.
    """
    today = timezone.now().date()

    projects = Project.objects.filter(
        fecha_limite_entrega__lte=today,
        retrasado=False,
    ).exclude(
        entregables__status__in=[Entregable.STATUS_APPROVED, Entregable.STATUS_PENDING]
    ).select_related("status", "created_by")

    for project in projects:
        # Check if ANY entregable has been uploaded
        has_any_entregable = project.entregables.exists()
        if not has_any_entregable:
            # Activate retrasado flag
            project.retrasado = True
            project.save(update_fields=["retrasado", "updated_at"])

            # Notify PM
            if project.created_by:
                Notification.objects.create(
                    recipient=project.created_by,
                    notification_type=Notification.TYPE_DEADLINE_OVERDUE,
                    title=f"Entrega vencida: {project.project_id}",
                    message=f'El proyecto "{project.nombre}" ha superado la fecha límite sin entregable.',
                    project=project,
                )


# ─── Deliverable Logic ──────────────────────────────────────────────────────────

def handle_entregable_upload(project: Project, entregable):
    """Handle a new deliverable upload. Evaluates state transition."""
    # Clear retrasado flag if it was set
    if project.retrasado:
        project.retrasado = False
        project.save(update_fields=["retrasado", "updated_at"])

    # Notify PM that a deliverable was uploaded
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_DELIVERY_UPLOADED,
            title="Nuevo entregable recibido",
            message=f'{entregable.content_maker} ha subido un entregable para "{project.nombre}".',
            project=project,
        )

    # Transition to Revisión
    transition_project_status(project)


def handle_entregable_review(entregable, reviewer, approved: bool, notes: str = ""):
    """
    Handle review of a deliverable.
    approved=True → mark as approved
    approved=False → request revision (if within max rounds)
    """
    entregable.reviewed_by = reviewer
    entregable.reviewed_at = timezone.now()

    if approved:
        entregable.status = Entregable.STATUS_APPROVED
        entregable.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        # Notify CM
        if entregable.content_maker.user:
            Notification.objects.create(
                recipient=entregable.content_maker.user,
                notification_type=Notification.TYPE_DELIVERY_APPROVED,
                title="Entregable aprobado",
                message=f'Tu entregable para "{entregable.project.nombre}" ha sido aprobado.',
                project=entregable.project,
            )

        # Check if all entregables are approved → transition
        transition_project_status(entregable.project)
    else:
        if not entregable.can_request_revision:
            raise ValueError(
                f"Se han alcanzado las {Entregable.MAX_REVISION_ROUNDS} rondas máximas de revisión."
            )
        entregable.status = Entregable.STATUS_REVISION
        entregable.revision_notes = notes
        entregable.revision_round += 1
        entregable.save(update_fields=[
            "status", "revision_notes", "revision_round", "reviewed_by", "reviewed_at"
        ])

        # Notify CM to revise
        if entregable.content_maker.user:
            Notification.objects.create(
                recipient=entregable.content_maker.user,
                notification_type=Notification.TYPE_REVISION_REQUESTED,
                title="Se requieren cambios en tu entregable",
                message=f'El PM ha solicitado cambios en tu entrega para "{entregable.project.nombre}": {notes}',
                project=entregable.project,
            )


# ─── Briefing Logic (6.6) ──────────────────────────────────────────────────────

def handle_briefing_submitted(briefing):
    """Called after a briefing is created. Evaluates state transition."""
    project = briefing.project

    # Notify CM that briefing is ready
    if briefing.content_maker.user:
        Notification.objects.create(
            recipient=briefing.content_maker.user,
            notification_type=Notification.TYPE_BRIEFING_SUBMITTED,
            title="Tienes un nuevo briefing",
            message=f'El cliente ha completado tu briefing para el proyecto "{project.nombre}".',
            project=project,
        )

    # Evaluate state transition
    transition_project_status(project)
