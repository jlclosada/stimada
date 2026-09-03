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
    Deliverable,
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


def _get_status(name: str):
    """Get a ProjectStatus by name, or None."""
    return ProjectStatus.objects.filter(name=name).first()


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
            last_new_name = new_status.name
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
    old_name = old_status.name if old_status else "—"
    audit_status_override(user, project, old_name, new_status_name, reason)

    return new_status.name


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
        from_name = from_status.name if from_status else "—"
        to_name = to_status.name if to_status else "—"
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_STATUS_CHANGED,
            title=f"Proyecto actualizado: {to_name}",
            message=f'El proyecto "{project.name}" ha pasado de "{from_name}" a "{to_name}".',
            project=project,
        )


def _evaluate_correct_status(project: Project):
    """
    Data-driven state evaluation.
    Determines the CORRECT state based on the project's current data,
    regardless of its current status. Only advances forward (never goes back).
    Returns a ProjectStatus instance if the project should move forward, else None.
    """
    current_name = project.status.name if project.status else ""
    current_order = STATUS_ORDER.get(current_name, 0)

    # Helper: only return a status if it's higher than current
    def _advance_to(name):
        target_order = STATUS_ORDER.get(name, 0)
        if target_order > current_order:
            return _get_status(name)
        return None

    # Gather data
    principal_cms = project.content_makers.filter(is_substitute=False)
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
    if project.product_logistics:
        logistics_name = project.product_logistics.name.lower()
        has_shipping_logistics = "envío" in logistics_name or "envio" in logistics_name

    has_deliverables = project.deliverables.exists()
    deliverables = project.deliverables.all() if has_deliverables else None

    # ─── Evaluate from highest to lowest (find the highest valid state) ───

    # 11. Proyecto Finalizado
    if has_deliverables and deliverables is not None:
        all_approved = not deliverables.exclude(status=Deliverable.STATUS_APPROVED).exists()
        all_published = not deliverables.filter(published_at__isnull=True).exists()
        if all_approved and all_published:
            if project.product_return:
                # Need manual confirmation for pickup → stop at "Producto a Recoger"
                result = _advance_to("Producto a Recoger")
                if result:
                    return result
            else:
                result = _advance_to("Proyecto Finalizado")
                if result:
                    return result

    # 9. Publicado
    if has_deliverables and deliverables is not None:
        all_approved = not deliverables.exclude(status=Deliverable.STATUS_APPROVED).exists()
        all_published = not deliverables.filter(published_at__isnull=True).exists()
        if all_approved and all_published:
            result = _advance_to("Publicado")
            if result:
                return result

    # 8. Revisión: deliverables uploaded
    if has_deliverables:
        result = _advance_to("Revisión")
        if result:
            return result

    # 7. En producción: briefings done + (product received or no shipping)
    if all_briefings_done:
        if has_shipping_logistics:
            if project.product_arrival_date:
                result = _advance_to("En producción")
                if result:
                    return result
        else:
            # No shipping → skip product states, go to production
            result = _advance_to("En producción")
            if result:
                return result

    # 6. Producto Recibido
    if has_shipping_logistics and project.product_arrival_date and all_briefings_done:
        result = _advance_to("Producto Recibido")
        if result:
            return result

    # 5. Briefing: all briefings submitted
    if all_briefings_done:
        result = _advance_to("Briefing")
        if result:
            return result

    # 4. Producto Enviado: shipping logistics + service_date (fecha envío)
    if has_shipping_logistics and project.service_date and all_principals_accepted:
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
            message=f'{cm_profile.first_name} {cm_profile.last_name} ha aceptado el proyecto "{project.name}".',
            project=project,
        )

    # Notify client to fill briefing
    if project.client and project.client.user:
        Notification.objects.create(
            recipient=project.client.user,
            notification_type=Notification.TYPE_BRIEFING_SUBMITTED,
            title="Content Maker confirmada — Completa el briefing",
            message=f'{cm_profile.first_name} {cm_profile.last_name} ha aceptado "{project.name}". Por favor, completa el briefing.',
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
            message=f'{cm_profile.first_name} {cm_profile.last_name} ha rechazado "{project.name}".',
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
                message=f'Todas las Content Makers han rechazado "{project.name}". Se requiere acción manual.',
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
        is_substitute=True,
        status=ProjectContentMaker.STATUS_PENDING,
    ).order_by("created_at").first()

    if not next_suplente:
        return False

    # Promote: mark as principal
    next_suplente.is_substitute = False
    next_suplente.status = ProjectContentMaker.STATUS_PENDING
    next_suplente.save(update_fields=["is_substitute", "status"])

    # Send notification to the promoted CM
    cm = next_suplente.content_maker
    if cm.user:
        Notification.objects.create(
            recipient=cm.user,
            notification_type=Notification.TYPE_CM_PROMOTED,
            title="Has sido seleccionada para un proyecto",
            message=f'Has sido promovida como Content Maker principal para "{project.name}". ¿Aceptas?',
            project=project,
        )

    # Notify project creator
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_CM_PROMOTED,
            title="Suplente promovida automáticamente",
            message=f'{cm.first_name} {cm.last_name} ha sido promovida a principal en "{project.name}".',
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
        delivery_deadline=reminder_date,
        delayed=False,
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
                    message=f'Tu entrega para "{project.name}" vence el {project.delivery_deadline}.',
                    project=project,
                )

        # Notify PM (creator)
        if project.created_by:
            Notification.objects.create(
                recipient=project.created_by,
                notification_type=Notification.TYPE_DEADLINE_REMINDER,
                title=f"Recordatorio: entrega en 3 días ({project.project_id})",
                message=f'El proyecto "{project.name}" tiene fecha límite el {project.delivery_deadline}.',
                project=project,
            )


def check_overdue_deliveries():
    """
    Check all projects for overdue deliveries (fecha_limite_entrega = today, no deliverables).
    Should be called daily. Activates the 'retrasado' flag.
    """
    today = timezone.now().date()

    projects = Project.objects.filter(
        delivery_deadline__lte=today,
        delayed=False,
    ).exclude(
        deliverables__status__in=[Deliverable.STATUS_APPROVED, Deliverable.STATUS_PENDING]
    ).select_related("status", "created_by")

    for project in projects:
        # Check if ANY deliverable has been uploaded
        has_any_entregable = project.deliverables.exists()
        if not has_any_entregable:
            # Activate delayed flag
            project.delayed = True
            project.save(update_fields=["delayed", "updated_at"])

            # Notify PM
            if project.created_by:
                Notification.objects.create(
                    recipient=project.created_by,
                    notification_type=Notification.TYPE_DEADLINE_OVERDUE,
                    title=f"Entrega vencida: {project.project_id}",
                    message=f'El proyecto "{project.name}" ha superado la fecha límite sin entregable.',
                    project=project,
                )


# ─── Deliverable Logic ──────────────────────────────────────────────────────────

def handle_deliverable_upload(project: Project, deliverable):
    """Handle a new deliverable upload. Evaluates state transition."""
    # Clear delayed flag if it was set
    if project.delayed:
        project.delayed = False
        project.save(update_fields=["delayed", "updated_at"])

    # Notify PM that a deliverable was uploaded
    if project.created_by:
        Notification.objects.create(
            recipient=project.created_by,
            notification_type=Notification.TYPE_DELIVERY_UPLOADED,
            title="Nuevo entregable recibido",
            message=f'{deliverable.content_maker} ha subido un entregable para "{project.name}".',
            project=project,
        )

    # Transition to Revisión
    transition_project_status(project)


def handle_deliverable_review(deliverable, reviewer, approved: bool, notes: str = ""):
    """
    Handle review of a deliverable.
    approved=True → mark as approved
    approved=False → request revision (if within max rounds)
    """
    deliverable.reviewed_by = reviewer
    deliverable.reviewed_at = timezone.now()

    if approved:
        deliverable.status = Deliverable.STATUS_APPROVED
        deliverable.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        # Notify CM
        if deliverable.content_maker.user:
            Notification.objects.create(
                recipient=deliverable.content_maker.user,
                notification_type=Notification.TYPE_DELIVERY_APPROVED,
                title="Entregable aprobado",
                message=f'Tu entregable para "{deliverable.project.name}" ha sido aprobado.',
                project=deliverable.project,
            )

        # Check if all deliverables are approved → transition
        transition_project_status(deliverable.project)
    else:
        if not deliverable.can_request_revision:
            raise ValueError(
                f"Se han alcanzado las {Deliverable.MAX_REVISION_ROUNDS} rondas máximas de revisión."
            )
        deliverable.status = Deliverable.STATUS_REVISION
        deliverable.revision_notes = notes
        deliverable.revision_round += 1
        deliverable.save(update_fields=[
            "status", "revision_notes", "revision_round", "reviewed_by", "reviewed_at"
        ])

        # Notify CM to revise
        if deliverable.content_maker.user:
            Notification.objects.create(
                recipient=deliverable.content_maker.user,
                notification_type=Notification.TYPE_REVISION_REQUESTED,
                title="Se requieren cambios en tu entregable",
                message=f'El PM ha solicitado cambios en tu entrega para "{deliverable.project.name}": {notes}',
                project=deliverable.project,
            )


def handle_deliverable_status_change(deliverable, new_status: str, user=None, notes: str = ""):
    """
    Handle a manual deliverable status change by admin/employee.
    Updates the deliverable, sends appropriate notifications, and
    re-evaluates the project state (including going backwards if needed).
    """
    old_status = deliverable.status
    project = deliverable.project

    deliverable.status = new_status
    if new_status == Deliverable.STATUS_APPROVED:
        deliverable.reviewed_by = user
        deliverable.reviewed_at = timezone.now()
    elif new_status == Deliverable.STATUS_REVISION:
        deliverable.reviewed_by = user
        deliverable.reviewed_at = timezone.now()
        if notes:
            deliverable.revision_notes = notes
    deliverable.save()

    # ─── Notifications based on the new status ───
    cm_user = deliverable.content_maker.user if deliverable.content_maker else None

    if new_status == Deliverable.STATUS_REVISION and cm_user:
        Notification.objects.create(
            recipient=cm_user,
            notification_type=Notification.TYPE_REVISION_REQUESTED,
            title="Se requieren cambios en tu entregable",
            message=f'Se han solicitado cambios en tu entrega para "{project.name}".{" Motivo: " + deliverable.revision_notes if deliverable.revision_notes else ""}',
            project=project,
        )
    elif new_status == Deliverable.STATUS_APPROVED and cm_user:
        Notification.objects.create(
            recipient=cm_user,
            notification_type=Notification.TYPE_DELIVERY_APPROVED,
            title="Entregable aprobado",
            message=f'Tu entregable para "{project.name}" ha sido aprobado.',
            project=project,
        )
    elif new_status == Deliverable.STATUS_REJECTED and cm_user:
        Notification.objects.create(
            recipient=cm_user,
            notification_type=Notification.TYPE_REVISION_REQUESTED,
            title="Entregable rechazado",
            message=f'Tu entregable para "{project.name}" ha sido rechazado.',
            project=project,
        )
    elif new_status == Deliverable.STATUS_PENDING and cm_user:
        Notification.objects.create(
            recipient=cm_user,
            notification_type=Notification.TYPE_STATUS_CHANGED,
            title="Entregable pendiente de revisión",
            message=f'Tu entregable para "{project.name}" ha sido marcado como pendiente de revisión.',
            project=project,
        )

    # ─── Re-evaluate the project status (bidirectional) ───
    _reevaluate_project_from_deliverables(project, user=user)


def _reevaluate_project_from_deliverables(project: Project, user=None):
    """
    Re-evaluate the project status based on deliverable states.
    Unlike `transition_project_status`, this can move the project BACKWARDS
    when deliverables are no longer in a higher state (e.g., approved → revision).

    Logic:
    - All deliverables approved + published → Publicado / Proyecto Finalizado / Producto a Recoger
    - All deliverables approved (not all published) → Publicado
    - Any deliverable pending or in revision → Revisión (content uploaded, under review)
    - No deliverables → don't touch status
    """
    deliverables = project.deliverables.all()
    if not deliverables.exists():
        return

    all_approved = not deliverables.exclude(status=Deliverable.STATUS_APPROVED).exists()
    all_published = all_approved and not deliverables.filter(published_at__isnull=True).exists()
    any_revision = deliverables.filter(status=Deliverable.STATUS_REVISION).exists()
    any_pending = deliverables.filter(status=Deliverable.STATUS_PENDING).exists()

    current_name = project.status.name if project.status else ""

    # Determine the correct deliverable-related status
    target_name = None

    if all_published:
        if project.product_return:
            if current_name == "Proyecto Finalizado":
                return  # Already finalized, don't go back
            target_name = "Producto a Recoger"
        else:
            target_name = "Proyecto Finalizado"
    elif all_approved:
        target_name = "Publicado"
    elif any_revision or any_pending:
        # Deliverables exist but not all approved → project is in review phase
        target_name = "Revisión"

    if not target_name or target_name == current_name:
        return

    new_status = _get_status(target_name)
    if not new_status:
        return

    old_status = project.status
    _apply_transition(project, old_status, new_status, user=user, is_manual=False)


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
            message=f'El cliente ha completado tu briefing para el proyecto "{project.name}".',
            project=project,
        )

    # Evaluate state transition
    transition_project_status(project)
