# Database — Models, QuerySets & Migrations

Rules and patterns for Django models, ORM best practices, migrations, and fixtures in this Stimada project.

## Models

### Model definition

```python
from django.db import models


class Project(models.Model):
    project_id = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=255, blank=True, default="")
    status = models.ForeignKey("ProjectStatus", on_delete=models.PROTECT, related_name="projects")
    client = models.ForeignKey("clients.ClientProfile", on_delete=models.PROTECT, related_name="projects")
    content_maker = models.ForeignKey(
        "content_makers.ContentMakerProfile", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_projects"
    )
    base_imponible = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_servicio = models.DateField(null=True, blank=True)
    is_draft = models.BooleanField(default=False)
    created_by = models.ForeignKey("accounts.CustomUser", on_delete=models.PROTECT, related_name="created_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.project_id} - {self.nombre}"
```

### Model rules

- **Use `on_delete=models.PROTECT`** for foreign keys unless deletion cascading is explicitly required
- **Use `related_name`** on all ForeignKey/ManyToMany fields — be descriptive
- **Use `null=True, blank=True`** for optional fields (not just `blank=True` for non-string fields)
- **Use `auto_now_add=True`** for `created_at`, **`auto_now=True`** for `updated_at`
- **Keep models focused** — business logic goes in services, not model methods
- **Define `__str__`** for admin and debugging readability
- **Define `class Meta`** with `ordering` when a default sort makes sense
- **Spanish domain terms** for field names representing business concepts (e.g., `estado`, `nombre`, `fecha_servicio`)

### Field naming conventions

- **Foreign keys**: `<related_model>` or `<role>` — `client`, `content_maker`, `created_by`, `status`
- **Foreign key ID**: Django adds `_id` automatically — access `project.client_id` (no extra query)
- **Booleans**: `is_<adjective>` or `has_<noun>` — `is_active`, `is_draft`, `es_agencia`
- **Dates**: `fecha_<noun>` (Spanish) — `fecha_servicio`, `fecha_venta`, `fecha_fin`
- **Amounts**: descriptive — `base_imponible`, `fee_instagram`, not `amount`

## ORM Best Practices

### Avoid N+1 queries

```python
# Bad — N+1: 1 query for projects + N queries for clients
projects = Project.objects.all()
for p in projects:
    print(p.client.nombre_empresa)  # Extra query per iteration

# Good — eager loading with select_related (ForeignKey)
contracts = Contract.objects.select_related('contract_owner').all()

# Good — prefetch_related for ManyToMany or reverse ForeignKey
projects = Project.objects.prefetch_related('sbus', 'gates').all()
```

### When to use which

| Relationship type    | Use                  |
| -------------------- | -------------------- |
| ForeignKey (forward) | `select_related()`   |
| OneToOneField        | `select_related()`   |
| ManyToManyField      | `prefetch_related()` |
| Reverse ForeignKey   | `prefetch_related()` |

### Use bulk operations

```python
# Bad — N individual INSERT statements
for item in items:
    Notification(user_id=item.user_id, message=item.msg).save()

# Good — single INSERT
notifications = [Notification(user_id=i.user_id, message=i.msg) for i in items]
Notification.objects.bulk_create(notifications)

# Bulk update
Contract.objects.filter(status='draft').update(status='active')

# Bulk update with different values per object
contracts[0].status = 'active'
contracts[1].status = 'closed'
Contract.objects.bulk_update(contracts, ['status'])
```

### Use F() expressions for database-level operations

```python
from django.db.models import F

# Bad — fetches to Python, modifies, saves back
contract = Contract.objects.get(id=1)
contract.view_count = contract.view_count + 1
contract.save()

# Good — single UPDATE query at database level
Contract.objects.filter(id=1).update(view_count=F('view_count') + 1)
```

### Use Q() for complex filters

```python
from django.db.models import Q

# OR conditions
contracts = Contract.objects.filter(
    Q(contract_owner=user) | Q(contract_owner_deputy=user)
)

# NOT conditions
active_contracts = Contract.objects.filter(~Q(status='cancelled'))

# Complex combinations
contracts = Contract.objects.filter(
    Q(status='active') & (Q(contract_owner=user) | Q(is_public=True))
)
```

### Aggregations and annotations

```python
from django.db.models import Count, Sum, Avg, Max, Min

# Aggregate over entire queryset
totals = Contract.objects.aggregate(
    total_amount=Sum('total_financial_obligation'),
    contract_count=Count('id'),
)

# Annotate each object
contracts = Contract.objects.annotate(
    payment_count=Count('payments'),
    total_paid=Sum('payments__amount'),
)
```

### Use `.exists()` and `.count()` efficiently

```python
# Bad — loads all objects
if len(Contract.objects.filter(status='draft')) > 0: ...

# Good — single COUNT query
if Contract.objects.filter(status='draft').exists(): ...

# Bad — loads all objects
total = len(Contract.objects.all())

# Good — single COUNT query
total = Contract.objects.count()
```

### Use `.values()` and `.values_list()` for projections

```python
# Only need IDs — avoid loading full objects
contract_ids = Contract.objects.filter(status='active').values_list('id', flat=True)

# Only need specific fields
contract_data = Contract.objects.values('id', 'contract_title', 'status__name')
```

### Null-safe annotations and aggregations

Handle null/empty aggregation pitfalls intentionally:

```python
from django.db.models.functions import Coalesce

# Bad — Sum returns None when no rows match
total = Contract.objects.filter(status='active').aggregate(total=Sum('amount'))
# total = {'total': None}  ← can break downstream code

# Good — null-safe with Coalesce
total = Contract.objects.filter(status='active').aggregate(
    total=Coalesce(Sum('amount'), 0)
)
```

When using `Subquery`, `Exists`, or `Case/When`, keep result types explicit:

```python
is_open = Subquery(
    CostCenter.objects.filter(project_no=OuterRef('project_no')).values('is_open')[:1],
    output_field=BooleanField()  # Always specify output_field
)
```

### Generic relations

For generic relations, follow `content_type` + `object_id` patterns used in the codebase:

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    text = models.TextField()
```

## Migrations

### Creating migrations

```bash
just makemigrations        # Auto-detect model changes
just makemigrations APP    # For a specific app
just migrate               # Apply all pending migrations
```

### Migration rules

- **Always create migrations** when models change — never modify the database manually
- **Review auto-generated migrations** before committing — check field names, defaults, constraints
- **Avoid data migrations in schema migrations** — use separate `RunPython` migrations for data
- **Keep migrations reversible** — provide `reverse_code` in `RunPython` operations
- **Never edit applied migrations** — create new migrations to fix issues
- **Squash old migrations** when the count becomes unwieldy: `python manage.py squashmigrations app 0001 0050`

### Data migrations

```python
from django.db import migrations

def populate_status(apps, schema_editor):
    Status = apps.get_model('contracts', 'Status')
    Status.objects.bulk_create([
        Status(name='Draft'),
        Status(name='Active'),
        Status(name='Closed'),
    ])

def reverse_populate_status(apps, schema_editor):
    Status = apps.get_model('contracts', 'Status')
    Status.objects.filter(name__in=['Draft', 'Active', 'Closed']).delete()

class Migration(migrations.Migration):
    dependencies = [('contracts', '0001_initial')]

    operations = [
        migrations.RunPython(populate_status, reverse_populate_status),
    ]
```

## Fixtures

### Structure

Fixtures are JSON files in `<app>/fixtures/tests/`:

```json
[
  {
    "model": "contracts.contract",
    "pk": 1,
    "fields": {
      "contract_title": "Test Contract",
      "status": 1,
      "type": 1,
      "contract_owner": 1,
      "created_by": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
]
```

### Fixture rules

- **Keep test fixtures minimal** — only the records needed for each test scenario
- **Include all FK dependencies** — if a contract references a status, include the status fixture
- **Use stable PKs** — fixtures reference PKs directly, so keep them deterministic
- **Generate from real data**: `python manage.py dumpdata app.Model --indent 2 > fixture.json`
- **Naming**: `test_<feature>.json` (e.g., `test_contracts.json`, `test_project_gates.json`)
- **Location**: `<app>/fixtures/tests/` directory

### Fixture conventions for configuration/data models

- When adding fixture entries, add them for **all operational divisions**: `PM`, `RG`, and `RGQCS`
- New fixture entries must use the **next ID** for that model: check the latest existing ID in related fixture files and increment by one
- Fixture file name **prefixes** represent load order by dependency (e.g., `1_`, `2_`, `3_`); follow existing convention
- Models without dependency constraints should not use a numeric prefix
- Fixture file **suffixes** represent order within the same type/group when multiple files are needed
- Once a fixture file is already loaded, adding new values to the same file will **not** insert those new entries — create a new file (e.g., `Model_2.json`)
- For new dumpable config-related models, consider adding them to `rdcp.management.commands.dump_models` (`models_to_dump`) — ask before proceeding

### Loading in tests

```python
class TestContractEndpoints(ApiTestCase):
    fixtures = [
        'tests/test_contracts',     # contracts/fixtures/tests/test_contracts.json
        'tests/test_projects',       # projects/fixtures/tests/test_projects.json
    ]
```

## Checklist

- [ ] Models use `on_delete=models.PROTECT` and explicit `related_name`
- [ ] Choices defined in `choices.py` using `TextChoices` / `IntegerChoices`
- [ ] Complex queries encapsulated in query objects (`queries.py`)
- [ ] QuerySets use `select_related` / `prefetch_related` appropriately
- [ ] Bulk operations used instead of loops with `.save()`
- [ ] `F()` expressions used for database-level updates
- [ ] `Q()` objects used for complex filter logic
- [ ] `.exists()` and `.count()` used instead of `len(queryset)`
- [ ] Migrations are reviewed, reversible, and committed
- [ ] Fixtures are minimal, have stable PKs, and include FK dependencies
- [ ] Config fixtures cover all operational divisions (PM, RG, RGQCS)
- [ ] Fixture IDs are sequential and don't conflict with existing entries
- [ ] No raw SQL unless Django ORM cannot express the query
- [ ] Query object properties/methods are ≤ 15 lines; each ORM expression (`ArraySubquery`, `JSONObject`, `ArrayAgg`) is extracted into its own named method

## General code rules (apply here too)

These are reinforced in `quality/SKILL.md` but apply strictly to query objects, handlers, and any DB-touching code:

- **No imports inside methods** — keep all imports at the top of the module.
- **No negative `if not …: return` guard clauses** — write the positive condition (`if cond:`) with the logic inside the block, and a single explicit `return None` (or ap## General code rules (apply here too)
  Thesgrep -E '"pk"|"username"|"model"' /Users/AnguloM/PycharmProjects/RDCP-backend/django/users/fixtures/tests/test_user_for_tasks.json | head -30
  echo done
