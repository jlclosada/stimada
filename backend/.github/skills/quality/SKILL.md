# Code Quality & Clean Code

Clean code principles adapted for **Python 3.12** and **Django/DRF** in this Stimada project.

## Naming

### Be descriptive and intentional

- **Variables**: describe what they hold — `active_projects`, `is_draft`, `selected_cm_ids`
- **Functions**: describe what they do — `transition_project_status()`, `handle_cm_accept()`
- **Booleans**: use `is_`, `has_`, `es_` prefixes — `is_active`, `has_account`, `es_agencia`
- **Constants**: UPPER_SNAKE_CASE — `STATUS_ORDER`, `CM_NON_EDITABLE_FIELDS`
- **Avoid generic names**: `data`, `info`, `temp`, `flag`, `result` — unless scope is very small

### Django-specific naming

- **Models**: singular nouns — `Project`, `ClientProfile`, `Notification`
- **Serializers**: `<Model>Serializer`, `<Model>ListSerializer`, `<Model>CreateSerializer`
- **ViewSets**: `<Model>ViewSet`
- **Permissions**: `Is<Role>` or `<Action>Permission` — `IsAdminOrEmployee`, `CanCreateUsers`
- **Services**: verb phrases — `transition_project_status`, `handle_cm_accept`, `audit_changes`

## Imports

- Use **absolute imports** — `from apps.app_name.models import ModelName`
- Group imports: stdlib → third-party → first-party, separated by blank lines
- Import from the app's own modules: `from apps.projects.models import Project`
- Cross-app: `from apps.accounts.models import CustomUser`

## Control flow

- **Prefer early returns** over deep nesting — bail early for error/invalid cases
- Wrap complex conditionals in well-named boolean variables
- Keep the "happy path" left-aligned (minimal indentation)

```python
# Good — early return for error case
def handle_cm_accept(project, cm_profile, user):
    if project.status.nombre != "Perfiles Propuestos":
        return
    # ... main logic at top indentation level

# Bad — unnecessary nesting
def handle_cm_accept(project, cm_profile, user):
    if project.status.nombre == "Perfiles Propuestos":
        if cm_profile:
            # deeply nested logic...
```

## Functions

### Single Responsibility

Every function should do **one thing**. If you can describe it with "and", split it.

```python
# Bad — does two things
def fetch_and_transform_contracts(user_id: int) -> list[dict]:
    raw = Contract.objects.filter(owner_id=user_id)
    return [serialize_contract(c) for c in raw]

# Good — separated concerns
def get_user_contracts(user_id: int) -> QuerySet[Contract]:
    return Contract.objects.filter(owner_id=user_id)

def serialize_contracts(contracts: QuerySet[Contract]) -> list[dict]:
    return [serialize_contract(c) for c in contracts]
```

### Keep functions short

Aim for **≤ 30 lines**. If a function grows beyond that, extract helper functions with descriptive names.

### Keep queryset properties clean

- The `queryset` property (or any main property) should only contain the return statement or the queryset construction — no intermediate variable assignments
- Extract reusable sub-expressions (subqueries, Case/When logic, annotations) into **separate properties or methods**
- If the same `Case(When(...))` pattern is repeated for multiple fields, create a **single reusable method** that accepts the varying parameter (e.g., field lookup) and returns the expression
- Never name a method starting with `_` (underscore) — use descriptive public names instead

### Limit parameters

- **≤ 3 parameters** is ideal
- If more are needed, group them into a dataclass or TypedDict

```python
# Bad
def create_notification(project_id: int, users_id: list[int], cc_users_id: list[int],
                        values: dict, config_ids: list[int], description_id: int) -> None: ...

# Good
@dataclass
class NotificationParams:
    project_id: int
    users_id: list[int]
    cc_users_id: list[int]
    values_to_replace: dict[str, str]
    configuration_ids: list[int]
    description_id: int | None = None

def create_notification(params: NotificationParams) -> None: ...
```

### Prefer positive `if` checks over `if not ... : return`

Always wrap the work in a positive `if <condition>:` block instead of guarding with `if not <condition>: return`. See the [Control flow](#control-flow) section above for the full rule and examples. This applies inside helpers, handlers, view methods and signal receivers alike.

### Pure functions when possible

Functions in utility modules should be **pure** — same input always produces same output, no side effects. This makes them easy to test and reason about.

## Constants & Magic Values

### No magic numbers or strings

Extract inline values to named constants or choices classes:

```python
# Bad
if status == 3: ...
queryset.filter(type_id=7)

# Good — use choices or constants
if status == ProjectStatus.APPROVED: ...
queryset.filter(type_id=ServiceType.UGC)
```

- Place shared constants at the module level or in a dedicated constants section
- Keep function-local constants at the top of the function

## Error Handling

### Never silently swallow errors

```python
# Bad
try:
    send_notification(user_id)
except Exception:
    pass

# Good
try:
    send_notification(user_id)
except NotificationError as e:
    logger.error("Failed to send notification to user %s: %s", user_id, e)
```

### Be specific about what you catch

Don't wrap large blocks in try/except. Wrap only the part that can fail and handle the specific exception.

```python
# Bad — catches everything, hides bugs
try:
    contract = Contract.objects.get(id=contract_id)
    tracker = ContractTracker(contract)
    tracker.track()
    contract.save()
except Exception:
    logger.error("Something went wrong")

# Good — specific exception handling
try:
    contract = Contract.objects.get(id=contract_id)
except Contract.DoesNotExist:
    logger.warning("Contract %s not found", contract_id)
    return

tracker = ContractTracker(contract)
tracker.track()
contract.save()
```

### Use Django/DRF exception patterns

- Raise `rest_framework.exceptions.ValidationError` in serializers
- Raise `Http404` or use `get_object_or_404()` in views
- Use DRF's built-in exception handler for consistent API responses
- Define custom exception classes in `errors.py` for domain-specific errors

## Code Organization

### One concern per file

- One domain per app — `contracts/` handles contracts, not also projects
- One model group per `models.py` — if it grows too large, split with a `models/` package
- One concern per query class — `ContractsQuery` handles contract queries, not also notification logic
- Handlers orchestrate, they don't contain ORM queries — delegate to `queries.py`

### Import order

Maintain a consistent import order (Ruff handles this automatically):

1. Standard library (`os`, `datetime`, `dataclasses`)
2. Third-party packages (`django`, `rest_framework`, `celery`)
3. Project imports (`from contracts.models import Contract`)
4. Relative imports (`from .models import Contract`)

### Never import inside functions

Always import at the **module level** (top of file). Importing inside functions hides dependencies, slows down repeated calls, and violates the principle of explicit imports.

```python
# Bad
def get_contracts(user_id: int) -> list[Contract]:
    from contracts.models import Contract
    return Contract.objects.filter(owner_id=user_id)

# Good
from contracts.models import Contract

def get_contracts(user_id: int) -> list[Contract]:
    return Contract.objects.filter(owner_id=user_id)
```

### Remove dead code

- Delete unused variables, functions, imports, and model methods
- Don't commit commented-out code — use version control to retrieve old code if needed
- Remove `print()` statements before committing (use `logger` instead)

## Python-Specific

### Avoid `Any`

```python
# Bad
def process(data: Any) -> Any: ...

# Good
def process(data: dict[str, str]) -> list[Contract]: ...
def process(data: object) -> None: ...
```

### Use type hints everywhere

```python
# Bad
def get_contracts(user_id, status=None):
    ...

# Good
def get_contracts(user_id: int, status: str | None = None) -> QuerySet[Contract]:
    ...
```

### Use Python 3.11 features

```python
# Use | union syntax instead of Optional/Union
def get_user(user_id: int) -> User | None: ...

# Use built-in generics
def get_ids(items: list[Item]) -> list[int]: ...
```

### Use list comprehensions and generator expressions

```python
# Bad
ids = []
for contract in contracts:
    ids.append(contract.id)

# Good
ids = [contract.id for contract in contracts]

# Use generators for large datasets
total = sum(c.amount for c in contracts)
```

### Use `f-strings` for formatting

```python
# Bad
message = "Contract %s owned by %s" % (title, owner)
message = "Contract {} owned by {}".format(title, owner)

# Good
message = f"Contract {title} owned by {owner}"
```

## Django-Specific

### QuerySet best practices

```python
# Bad — N+1 queries
contracts = Contract.objects.all()
for c in contracts:
    print(c.owner.username)  # DB query per iteration

# Good — eager loading
contracts = Contract.objects.select_related('owner').all()
for c in contracts:
    print(c.owner.username)  # No extra queries
```

### Use bulk operations

```python
# Bad — N individual INSERT statements
for item in items:
    Notification(user_id=item.user_id, message=item.message).save()

# Good — single INSERT
notifications = [Notification(user_id=item.user_id, message=item.message) for item in items]
Notification.objects.bulk_create(notifications)
```

### Serializer validation

- Validate at the serializer level, not in views
- Use `validate_<field>()` for single-field validation
- Use `validate()` for cross-field validation
- Raise `serializers.ValidationError` with descriptive messages

### Keep views thin

Views should only handle HTTP concerns. Delegate business logic:

```python
# Bad — business logic in view
class ContractViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        contract = serializer.save()
        # 50 lines of notification, tracking, permission logic...

# Good — delegate to handler
class ContractViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        contract = serializer.save()
        ContractCreationHandler(contract).handle()
```

### Keep query object methods focused and short

Properties and methods in query objects that build ORM expressions (`ArraySubquery`, `JSONObject`, `ArrayAgg`, `Subquery`, `Case`) must stay **≤ 15 lines**. Extract each named expression into its own method. **Never use a `_` prefix** — all helpers are named descriptively.

Choose the right method type:

- **`@property`** — use for any annotation expression that uses `self` and takes no external arguments. This is the default for subqueries and aggregates used as annotations.
- **`@staticmethod`** — when the expression needs no instance state at all (e.g., a fixed `JSONObject` of field refs).
- **Instance method** — only when external arguments are required (e.g., `scope`, `lookup_field`).
- **Never add a wrapper property just to call a method** — if it's a no-arg annotation, make it a `@property` directly.

When calling another method from within an instance method, **always use `self.method_name()` instead of `ClassName.method_name()`**. This preserves polymorphism, enables proper inheritance, and improves testability.

```python
# Bad — hardcodes class name; breaks polymorphism
def section_agg(self, date_from_field, date_to_field, percentage_field):
    entry = EffortChartQueries.section_entry(date_from_field, date_to_field, percentage_field)
    return ArrayAgg(entry, ...)

# Good — uses self; respects inheritance and overrides
def section_agg(self, date_from_field, date_to_field, percentage_field):
    entry = self.section_entry(date_from_field, date_to_field, percentage_field)
    return ArrayAgg(entry, ...)

@staticmethod
def section_entry(date_from_field, date_to_field, percentage_field) -> JSONObject:
    return JSONObject(date_from=F(date_from_field), date_to=F(date_to_field), ...)

# Property using self to call instance methods
@property
def projects(self) -> ArraySubquery:
    return ArraySubquery(
        ProjectTeamMember.objects.filter(...).annotate(
            effort_periods=self.effort_periods,      # @property — uses self
        ).values(entry=self.project_json_entry())    # @staticmethod — pure expression
    )
```

## Comments

### Code should be self-explanatory

Good naming and structure reduce the need for comments. Use comments only for:

- **Why**, not **what** — explain non-obvious business rules or workarounds
- **TODOs** — mark known technical debt with context: `# TODO: Refactor when PG API v2 is available`
- **Complex queries** — explain the intent of complex ORM annotations or subqueries

### Don't comment obvious code

```python
# Bad
# Get all contracts
contracts = Contract.objects.all()

# Good — no comment needed, the code speaks for itself
contracts = Contract.objects.all()
```

## Checklist

Before considering code clean:

- [ ] All names are descriptive and consistent with project conventions
- [ ] Functions are short, focused, and have ≤ 3 parameters
- [ ] No magic numbers or strings — constants and choices classes are used
- [ ] No deep nesting — positive `if` checks are used (no `if not ... : return` guard clauses)
- [ ] No dead code, no commented-out code, no stray `print()` statements
- [ ] Errors are handled explicitly, never silently swallowed
- [ ] `Any` is not used — proper types are in place
- [ ] Type hints on all function signatures (parameters + return type)
- [ ] QuerySets use `select_related` / `prefetch_related` where needed
- [ ] Bulk operations used instead of loops with `.save()`
- [ ] Business logic is in handlers, not in views or serializers
- [ ] Comments explain "why", not "what"
- [ ] Query object properties/methods building ORM expressions are ≤ 15 lines; each `ArraySubquery`, `JSONObject`, `ArrayAgg` etc. is extracted into its own named method
