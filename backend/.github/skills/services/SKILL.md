# Services & Business Logic

Rules and patterns for service functions, state machines, notifications, and workflow orchestration in this Stimada project.

## Service Functions

### Location and purpose

All business logic lives in `apps/<app>/services.py`. Services are called from views and management commands.

### When to use services

| Scenario                                 | Use service? | Reason                                 |
| ---------------------------------------- | ------------ | -------------------------------------- |
| State machine transitions                | Yes          | Multi-step logic with side effects     |
| CM accept/reject with suplente promotion | Yes          | Complex workflow with notifications    |
| Briefing/deliverable status changes      | Yes          | Triggers state machine + notifications |
| Simple field update on PATCH             | No           | Serializer handles it                  |
| Creating a user account for CM/client    | Yes          | Password generation + email + audit    |
| Deadline checking and overdue detection  | Yes          | Scheduled via management command       |

### Service function rules

- **One function, one workflow** — each function handles a single business operation
- **Accept model instances** as primary arguments (not raw IDs when avoidable)
- **Accept `user`** parameter for audit trail attribution
- **Return None or raise** — services mutate state, they don't return serialized data
- **Type all parameters and returns**
- **Keep ≤ 30 lines** — extract helpers for sub-steps

### Example patterns from this project

```python
def transition_project_status(project: Project, user=None, reason: str = "") -> None:
    """Auto-advance project through workflow based on current state."""
    ...

def handle_cm_accept(project: Project, cm_profile, user) -> None:
    """Handle content maker accepting a project."""
    ...

def handle_entregable_upload(entregable: Entregable, user) -> None:
    """Process deliverable upload and trigger state evaluation."""
    ...

def override_project_status(project: Project, new_status: ProjectStatus, user, reason: str) -> None:
    """Manual admin override with audit logging."""
    ...
```

## State Machine Pattern

The project implements an automatic state machine for project lifecycle management:

### Status Order

```python
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
```

### State Machine Rules

- **Only advance forward** — never go backwards automatically
- **Data-driven evaluation** — check related model states (CM acceptance, briefing completion, deliverables)
- **Max iterations** — cap cascading transitions (12 max) to prevent infinite loops
- **Log all transitions** via `StatusChangeLog` model
- **Distinguish automatic vs manual** — `is_manual` flag on change logs

### Calling the State Machine

```python
# After any action that might advance the project
transition_project_status(project, user=request.user, reason="CM aceptó el proyecto")

# For manual admin override (skips automatic logic)
override_project_status(project, new_status, user=request.user, reason="Cliente solicitó adelantar")
```

## Notifications

Notifications are created in-app via the `Notification` model:

```python
Notification.objects.create(
    project=project,
    user=target_user,
    tipo="cm_aceptado",
    mensaje=f"{cm_profile.nombre} ha aceptado el proyecto {project.project_id}",
)
```

### Notification Types

The project defines 13+ notification types covering:

- CM selection, acceptance, rejection
- Briefing submission
- Deliverable uploads and reviews
- Deadline reminders
- Project status changes

## Audit Integration

Services that modify sensitive fields should call audit:

```python
from apps.audit.services import audit_changes

old_data = {"status": str(project.status), "content_maker": str(project.content_maker)}
# ... perform changes ...
new_data = {"status": str(project.status), "content_maker": str(project.content_maker)}
audit_changes(user, project, old_data, new_data)
```

## Management Commands for Scheduled Logic

For periodic tasks (no Celery in this project), use management commands:

```python
# apps/projects/management/commands/check_deadlines.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        check_deadline_reminders()
        check_overdue_deliveries()
```

Run via cron or scheduler:

```bash
python manage.py check_deadlines
```
