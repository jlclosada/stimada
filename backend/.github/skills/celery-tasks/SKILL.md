# Celery Tasks, Signals, Handlers & Notifications

Rules and patterns for asynchronous task processing, Django signals, business logic handlers, change trackers, and the notification system in this project.

## Celery Tasks

### Task definition

All tasks use `@shared_task` and live in `<app>/tasks.py`:

```python
from celery import shared_task
from loguru import logger

@shared_task
def reminder_expected_payment_dates() -> str:
    logger.info("Sending reminder for expected payment dates...")

    for contract in queries.ContractsQuery.contracts_with_today_expected_payment_dates():
        values_to_replace = {
            'name': contract.contract_owner__first_name,
            'contract_title': contract.contract_title,
        }
        NotificationHandler(
            users_id=[contract.contract_owner_id],
            values_to_replace=values_to_replace,
            configuration_ids=[74],
        ).handle()

    return 'Success'
```

### When to use tasks

| Scenario                             | Use task? | Reason                                 |
| ------------------------------------ | --------- | -------------------------------------- |
| Sending email notifications          | Yes       | External I/O, can be slow              |
| PhaseGate data migration             | Yes       | Long-running, bulk processing          |
| User access permission recalculation | Yes       | Can involve many DB writes             |
| Simple model field update            | No        | Fast, synchronous is fine              |
| Validation during serializer save    | No        | Must be synchronous for error response |
| Loading data from external systems   | Yes       | External API calls, may fail/retry     |

### Task patterns

- **Return a string status** (`'Success'`, `'No data to process'`) for result tracking via `django-celery-results`
- **Use `logger`** for task progress (not `print()`)
- **Raise custom exceptions** (e.g., `PhaseGateMigrationError`) on failure — Celery marks the task as failed
- **Keep tasks thin** — delegate to handler/loader classes for business logic

```python
@shared_task
def bulk_insertion_for_all_projects(user_id: int, task_id: int, phasegate_token: str) -> str:
    issues = BulkInsertion(
        user_id=user_id, task_id=task_id, token=phasegate_token
    ).insertion()
    if issues:
        raise PhaseGateInsertionError("Bulk insertion failed")
    return 'Success'
```

### Calling tasks

```python
# Async — add to Celery queue
reminder_expected_payment_dates.delay()

# Async with arguments
bulk_insertion_for_all_projects.delay(user_id=1, task_id=42, phasegate_token='...')

# In tests — tasks execute synchronously via CELERY_TASK_ALWAYS_EAGER=True
```

### Celery configuration

- **Broker**: Redis (`CELERY_BROKER_URL`)
- **Result backend**: Django database (`CELERY_RESULT_BACKEND = "django-db"`)
- **Scheduler**: `django-celery-beat` with `DatabaseScheduler` for periodic tasks
- **Configuration**: `django/app/celery.py`

## Django Signals

### Signal location and purpose

Signals live in `<app>/signals.py` and are used for **automatic side effects** on model save/delete events.

### Common signal patterns

#### Pre-save — tracking changes

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Contract)
def track_contract_changes(sender, instance, **kwargs):
    ContractTracker(instance).track()
```

#### Post-save — triggering async tasks

```python
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=models.Gate)
@receiver(post_delete, sender=models.Gate)
def update_gate_access_rights(sender, instance, **kwargs):
    if instance.gatekeeper:
        users.tasks.update_project_access_for.delay(
            instance.gatekeeper_id, instance.project_id
        )
```

#### M2M changes

```python
from django.db.models.signals import m2m_changed

@receiver(m2m_changed, sender=models.Project.sbus.through)
def project_sbus_changed(sender, instance, action, pk_set, **kwargs):
    if action in ['post_add', 'post_remove']:
        for user_id in affected_user_ids:
            ProjectAccessUpdateQueue.objects.update_or_create(
                user_id=user_id, project_id=instance.id
            )
```

### Signal rules

- **pre_save**: Use for validation and change tracking (BEFORE database commit)
- **post_save**: Use for side effects that need the saved instance (notifications, async tasks)
- **post_delete**: Use for cleanup (cache invalidation, related data removal)
- **m2m_changed**: Use for many-to-many relationship changes — check `action` for `post_add`/`post_remove`
- **Never put business logic in signals** — delegate to handlers/trackers
- **Use custom decorators** to skip signals conditionally (e.g., `@skip_signal_if_project_status_is_extension`)

### Signal registration

Signals are auto-discovered via `<app>/apps.py`:

```python
class ContractsConfig(AppConfig):
    name = 'contracts'

    def ready(self):
        import contracts.signals  # noqa: F401
```

## Handlers

### Purpose

Handlers are **business logic orchestrators** in `<app>/handlers.py`. They encapsulate multi-step operations triggered by signals, views, or tasks.

### Handler pattern

```python
class NotificationHandler:
    def __init__(
        self,
        project_id: int | None = None,
        users_id: list[int] | None = None,
        values_to_replace: dict[str, str] | None = None,
        configuration_ids: list[int] | None = None,
        cc_users_id: list[int] | None = None,
    ):
        self.project_id = project_id
        self.configuration = self.get_configuration(configuration_ids)
        self.values_to_replace = self.get_values_to_replace(values_to_replace)

    def handle(self) -> None:
        """Main entry point — orchestrates the workflow."""
        for configuration in self.configuration:
            users_properties = self.get_user_properties(configuration)
            self.send_emails(configuration, users_properties)
            self.create_notifications(configuration, users_properties)

    def create_notifications(self, configuration, users) -> list[Notification]:
        notifications = [
            Notification(user_id=uid, configuration=configuration)
            for uid in users
        ]
        return Notification.objects.bulk_create(notifications)
```

### Handler rules

- **Single `handle()` entry point** — the public method that orchestrates all steps
- **`__init__` resolves dependencies** — queries, config lookups, parameter normalization
- **Private methods for each step** — `_validate()`, `_send_emails()`, `_create_notifications()`
- **Use bulk operations** — `bulk_create()`, `bulk_update()` instead of loops with `.save()`
- **Handlers don't query for data** — delegate complex queries to `queries.py`
- **One handler per operation** — `ContractCreationHandler`, `ProjectSubmitHandler`, etc.

### When to use handlers vs. other patterns

| Logic type                         | Pattern               |
| ---------------------------------- | --------------------- |
| Multi-step business workflow       | **Handler**           |
| Database write triggered by signal | **Tracker**           |
| Complex ORM query                  | **Query object**      |
| Single model save/update           | **Serializer**        |
| External API call                  | **Celery task**       |
| Validation before save             | **Serializer/Signal** |

## Trackers

### Purpose

Trackers in `<app>/tracker.py` record **model field changes** for audit trails. They compare previous and new values, then create change log entries.

### Simple tracker pattern (Contracts)

```python
class ContractTracker:
    def __init__(self, contract: Contract):
        self.contract = contract
        self.user = request_context.get_user()

    @property
    def trackable_fields(self) -> QuerySet:
        return Field.objects.filter(track_changes=True).values('name', 'label', 'id')

    def track(self) -> None:
        values_to_track = self.get_values_to_track()
        change_logs = self.get_contract_change_logs(values_to_track)
        if change_logs:
            ContractChangeLog.objects.bulk_create(change_logs)
```

### Advanced tracker pattern (Projects)

Uses a base `ChangeTracker` class with configuration:

```python
class ProjectChangeTracker(ChangeTracker):
    config = ChangeTracker.project  # Points to static config dict

class GateChangeTracker(ChangeTracker):
    config = ChangeTracker.gates
```

Configuration defines:

- `fields_in_tables` — related table fields to include
- `display_replace` — human-readable change message templates
- `fields_and_values_to_replace` — foreign key resolution for display names

### Tracker rules

- **Called from `pre_save` signals** — captures state before the save
- **Uses `bulk_create()`** for change log entries
- **Gets current user from thread-local context** (`app.models.request_context`)
- **Tracks only configured fields** — not every model field

## Notification System

### Architecture

The notification system is **configuration-driven** via `NotificationConfiguration` model:

```python
NotificationHandler(
    users_id=[user.id],
    cc_users_id=[cc_user.id],
    configuration_ids=[100],
    values_to_replace={'name': 'John', 'contract_title': 'R&D Contract #42'},
).handle()
```

### How it works

1. `NotificationConfiguration` defines: email template, subject, recipients, rules
2. `values_to_replace` are injected into the template via string replacement
3. Notifications are created as in-app DB records AND sent as emails
4. Rate limiting prevents duplicate notifications within a time window

### Rules

- **Never hardcode email templates** — use `NotificationConfiguration` entries
- **Always provide `values_to_replace`** with all required template variables
- **Use `configuration_ids`** to reference the notification config — these are stable IDs
- **Bulk notifications** use `bulk_create()` for efficiency

## Testing Async Code

In tests, Celery tasks execute **synchronously** thanks to `CELERY_TASK_ALWAYS_EAGER = True` in `app/settings/test.py`. This means:

```python
# This executes immediately in tests, no Celery worker needed
my_task.delay(arg1, arg2)
```

For signal-triggered logic, test via the API endpoint that triggers the signal:

```python
def test_signal_tracks_changes(self):
    response = self.client.patch(
        f'/contracts/{contract.id}/',
        {'contract_title': 'Updated'},
        format='json'
    )
    self.assertEqual(response.status_code, 200)
    # Signal should have created a change log
    self.assertTrue(ContractChangeLog.objects.filter(contract=contract).exists())
```

## Checklist

- [ ] Tasks use `@shared_task` and return status strings
- [ ] Tasks delegate to handler/loader classes — no inline business logic
- [ ] Signals are registered in `apps.py` via `ready()`
- [ ] Pre-save signals only do tracking/validation, post-save for side effects
- [ ] Handlers have a single `handle()` entry point
- [ ] Handlers use bulk operations where possible
- [ ] Trackers are called from pre_save signals
- [ ] Notifications use `NotificationConfiguration` — no hardcoded templates
- [ ] External services are mocked in tests
- [ ] Async tasks are tested synchronously via eager mode
