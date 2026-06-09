# API Design — Django REST Framework

Rules and patterns for building API endpoints with **Django REST Framework 3.15** in this Stimada project. Covers ViewSets, serializers, permissions, pagination, and URL routing.

## ViewSets

### Use `ModelViewSet` for standard CRUD

```python
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrEmployee
from config.pagination import FlexiblePageNumberPagination


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FlexiblePageNumberPagination
```

### Multi-serializer pattern

Use different serializers for list vs. detail vs. create/update operations:

```python
class ProjectViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProjectUpdateSerializer
        if self.action == "list":
            return ProjectListSerializer
        return ProjectDetailSerializer
```

### Query optimization per action

Override `get_queryset()` to optimize based on the action:

```python
class ProjectViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        qs = Project.objects.select_related("client", "brand", "status", "service_type")

        if self.action == "retrieve":
            qs = qs.prefetch_related("content_makers__content_maker")

        user = self.request.user
        if user.role == "client":
            return qs.filter(client__user=user)
        if user.role == "content_maker":
            return qs.filter(content_makers__content_maker__user=user)
        return qs
```

### Custom actions

Use `@action` for non-CRUD operations:

```python
@action(detail=True, methods=["post"], url_path="accept")
def accept_project(self, request, pk=None):
    project = self.get_object()
    handle_cm_accept(project, request.user.cm_profile, request.user)
    return Response(self.get_serializer(project).data)
```

### Keep views thin

Views handle HTTP concerns only. Business logic belongs in services:

```python
# Good — view delegates to service
def perform_create(self, serializer):
    project = serializer.save(created_by=self.request.user)
    transition_project_status(project, user=self.request.user)

# Bad — business logic in view
def perform_create(self, serializer):
    project = serializer.save(created_by=self.request.user)
    # 50 lines of notification, state machine, audit logic...
```

## Serializers

### Structure

Each app typically has multiple serializers per model:

| Serializer                 | Purpose                              |
| -------------------------- | ------------------------------------ |
| `ContractListSerializer`   | Minimal fields for list endpoints    |
| `ContractSerializer`       | Full fields for detail/create/update |
| `ContractCreateSerializer` | Create-specific with write fields    |

### Nested vs. flat serializers

- Use **nested serializers** for read operations (GET) to reduce frontend round-trips
- Use **PrimaryKeyRelatedField** or **SlugRelatedField** for write operations (POST/PATCH)

```python
class ContractSerializer(serializers.ModelSerializer):
    # Read: nested user data
    contract_owner = UserSlugFieldSerializer(slug_field='username', read_only=True)
    # Write: accept user ID
    contract_owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='contract_owner', write_only=True
    )

    class Meta:
        model = Contract
        fields = ['id', 'contract_title', 'contract_owner', 'contract_owner_id', ...]
```

### Validation

Validate in serializers, not in views:

```python
class ContractSerializer(serializers.ModelSerializer):
    # Single-field validation
    def validate_contract_title(self, value: str) -> str:
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value

    # Cross-field validation
    def validate(self, attrs: dict) -> dict:
        if attrs.get('end_date') and attrs.get('start_date'):
            if attrs['end_date'] < attrs['start_date']:
                raise serializers.ValidationError("End date must be after start date.")
        return attrs
```

### List serializers should be lightweight

Avoid nested relations, heavy annotations, or method fields in list serializers:

```python
# List — fast, minimal
class ContractListSerializer(serializers.ModelSerializer):
    contract_owner_name = serializers.CharField(source='contract_owner.get_full_name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = Contract
        fields = ['id', 'contract_title', 'contract_owner_name', 'status_name', 'total_amount']

# Detail — full data
class ContractSerializer(serializers.ModelSerializer):
    contract_owner = UserSerializer(read_only=True)
    execution_units = ExecutionUnitSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    history = ContractChangeLogSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'
```

## Filters

### Use `django-filter` FilterSets

```python
import django_filters

class ContractFilter(django_filters.FilterSet):
    # Exact match
    status = django_filters.NumberFilter(field_name='status_id')

    # Range filters
    total_amount_min = django_filters.NumberFilter(field_name='total_financial_obligation', lookup_expr='gte')
    total_amount_max = django_filters.NumberFilter(field_name='total_financial_obligation', lookup_expr='lte')

    # Text search
    title = django_filters.CharFilter(field_name='contract_title', lookup_expr='icontains')

    # Custom filter methods
    i_am_owner = django_filters.BooleanFilter(method='filter_by_owner')

    class Meta:
        model = Contract
        fields = {
            'id': ['exact', 'in'],
            'contract_title': ['exact', 'icontains'],
            'status': ['exact', 'in'],
        }

    def filter_by_owner(self, queryset, name, value):
        if value:
            return queryset.filter(contract_owner=self.request.user)
        return queryset
```

### Dropdown filters pattern

For UI-driven dropdowns, provide separate endpoints or serializer methods that return available filter options:

```python
@action(detail=False, methods=['get'], url_path='dropdown-filters')
def dropdown_filters(self, request):
    return Response({
        'statuses': StatusSerializer(Status.objects.all(), many=True).data,
        'types': TypeSerializer(Type.objects.all(), many=True).data,
    })
```

## Permissions

### Two-tier permission system

Every endpoint should have both view-level and object-level permissions:

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS

class ContractPermissions(BasePermission):
    """
    View-level: authenticated users can read and create.
    Object-level: only owner/deputy can modify.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS or request.method == 'POST':
            return request.user and request.user.is_authenticated
        return True  # Defer to object-level

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return (
            obj.contract_owner == request.user
            or obj.contract_owner_deputy == request.user
        )
```

### Permission patterns in this project

| Pattern             | When to use                                  |
| ------------------- | -------------------------------------------- |
| `IsAuthenticated`   | Default for all endpoints                    |
| Owner/deputy check  | Object-level write permissions               |
| Role/group check    | Feature-level access (admin, reviewer, etc.) |
| Org code check      | Multi-tenant data isolation                  |
| URL-path extraction | Complex permission mapping via regex on path |

### Filtering via `get_queryset()`

For data isolation, filter the queryset instead of checking object permissions one by one:

```python
def get_queryset(self):
    user = self.request.user
    if user.is_superuser:
        return Contract.objects.all()
    return Contract.objects.filter(
        Q(contract_owner=user) | Q(contract_owner_deputy=user)
    )
```

## Pagination

Use the project's `CustomPagination` class:

```python
class ContractViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
```

Response format:

```json
{
    "count": 150,
    "next": "http://api/contracts/?page=2",
    "previous": null,
    "results": [...]
}
```

- Default page size is configured globally in settings
- Override per-ViewSet with `pagination_class`
- For unpaginated endpoints, set `pagination_class = None`

### Pagination inside `@action`

For custom action endpoints that paginate data, follow this exact flow:

1. Set `pagination_class` on the action when pagination behavior must be explicit.
2. Call `self.paginate_queryset(...)` on the sequence being paginated.
3. Build/serialize only the paginated slice when possible (for example, paginate IDs first, then fetch heavy queryset).
4. Return `self.get_paginated_response(serializer.data)` for paginated paths.
5. Do not return manual empty payloads like `Response([])` for paginated paths; let paginator own response envelope.

```python
# Good
@action(detail=False, methods=['get'], url_path='effort-chart', pagination_class=CustomPagination)
def effort_chart(self, request):
    user_ids = list(base_queryset.values_list('user_id', flat=True).distinct())
    page_user_ids = self.paginate_queryset(user_ids)
    queryset = effort_query.get_queryset(paginated_user_ids=page_user_ids)
    serializer = EffortChartSerializer(queryset, many=True)
    return self.get_paginated_response(serializer.data)
```

## URL Routing

### Standard pattern

Each app uses `DefaultRouter` and registers its ViewSets:

```python
# contracts/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'contracts', views.ContractViewSet)
router.register(r'contract-payments', views.ContractPaymentViewSet)

urlpatterns = router.urls
```

### URL naming conventions

- **Resource names**: kebab-case, plural nouns (`/contracts/`, `/steering-meetings/`)
- **Custom actions**: kebab-case verbs or descriptors (`/contracts/{id}/submit/`, `/contracts/my-contracts/`)
- **No app prefixes**: all registered at root level in `app/urls.py`

### Root URL registration

All app URLs are included with no prefix:

```python
# app/urls.py
urlpatterns = [
    path("", include("contracts.urls")),
    path("", include("projects.urls")),
    path("", include("controlling.urls")),
    # ...
]
```

## Response Patterns

### Consistent response structure

- **List**: paginated response with `count`, `next`, `previous`, `results`
- **Create**: return the created object with status `201`
- **Update**: return the updated object with status `200`
- **Delete**: return no body with status `204`
- **Custom actions**: return appropriate data with descriptive status codes

### Error responses

Use DRF's built-in exception handling for consistent error format:

```json
{
  "detail": "Not found."
}
```

```json
{
  "contract_title": ["This field may not be blank."],
  "end_date": ["End date must be after start date."]
}
```

## API Documentation

The project uses `drf-spectacular` for OpenAPI schema generation. When adding endpoints:

- Use descriptive `help_text` on serializer fields
- Add `@extend_schema()` decorator for complex or non-standard endpoints
- Ensure response serializers are correctly specified for custom actions

## Data & Query Conventions

- For list query params, follow existing app patterns and split utilities (e.g., `split_param_for_list_query`) before implementing custom parsing
- Be explicit with relation names and `related_name` values to avoid reverse accessor conflicts
- For generic relations, follow `content_type` + `object_id` patterns used in the codebase
- When using annotations, subqueries, or exists clauses, prefer deterministic and null-safe expressions with explicit result types
- Prefer queryset/ORM expressions over Python `for` loops for data processing

## Safety Rules

- Keep changes scoped to the requested endpoint; avoid unrelated file churn
- **Preserve existing API contracts** (request/response fields and status codes) unless explicitly asked to change them
- Prefer minimal backward-compatible diffs
- If adding or changing endpoints, ensure serializer, router/action wiring, permissions, and response format match existing conventions
- If requirements are ambiguous or imply broad impact, pause and state assumptions before proceeding

## Checklist

Before considering an API endpoint complete:

- [ ] ViewSet uses appropriate serializer(s) per action (list vs. detail)
- [ ] QuerySet is optimized with `select_related` / `prefetch_related` per action
- [ ] FilterSet covers all user-facing filter needs
- [ ] Permissions enforce both view-level and object-level access
- [ ] Serializer validation handles edge cases and provides clear error messages
- [ ] URL follows naming conventions (kebab-case, plural, no prefix)
- [ ] Pagination is configured (or explicitly disabled with `pagination_class = None`)
- [ ] Paginated `@action` endpoints return `self.get_paginated_response(...)` and preserve envelope fields (`count`, `next`, `previous`, `results`)
- [ ] Custom actions use `@action` with correct `detail`, `methods`, and `url_path`
- [ ] Business logic is delegated to handlers, not embedded in views
- [ ] Tests cover CRUD operations, permissions, and edge cases

## General code rules (apply here too)

These are reinforced in `quality/SKILL.md` but apply strictly to view/serializer/handler code as well:

- **No imports inside methods** — keep all imports at the top of the module.
- **No negative `if not …: return` guard clauses** — write the positive condition (`if cond:`) with the logic inside the block, and a single explicit `return None` (or appropriate value) at the end.
