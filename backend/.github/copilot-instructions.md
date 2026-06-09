# AI Agent Development Guidelines

This project is **Stimada Backend** — a content marketing platform for managing influencer/content creator campaigns, built with **Django 5.0**, **Django REST Framework 3.15**, **SimpleJWT**, and **PostgreSQL**. Follow Django/DRF conventions and project-specific patterns when adding models, views, serializers, and services.

> **Skills reference**: For in-depth guidance on specific topics, see `.github/skills/SKILLS-DIGEST.md`.

## Mandatory Skill Selection (Strict)

- Before proposing or writing code, always select at least one relevant skill from `.github/skills/SKILLS-DIGEST.md`.
- Skill selection is required for every non-trivial task (implementation, refactor, bug fix, tests).
- If multiple concerns are present, combine all relevant skills (for example: `quality` + `testing`).
- If no skill clearly applies, ask one clarification question before proceeding.
- In every substantive response, include a short line: `Skill used: <skill-name(s)>`.
- If the task is truly trivial and no skill is needed, explicitly state: `Skill used: none (trivial task)`.

### Skill Routing Rules

- **ViewSets/serializers/permissions/pagination/URLs** → use `.github/skills/api-design/SKILL.md`
- **Django tests/APIClient/mocking** → use `.github/skills/testing/SKILL.md`
- **Refactor/readability/naming/error handling/maintainability** → use `.github/skills/quality/SKILL.md`
- **Services/signals/notifications/state machine** → use `.github/skills/services/SKILL.md`
- **Models/QuerySets/migrations/choices** → use `.github/skills/database/SKILL.md`
- **Architecture documentation/design decisions** → use `.github/skills/architecture/SKILL.md`
- **Multi-concern work** → apply all matching skills in parallel

## Tech Stack

| Component        | Version/Tool                                  |
| ---------------- | --------------------------------------------- |
| Python           | 3.12                                          |
| Django           | 5.0+                                          |
| DRF              | 3.15+                                         |
| Database         | PostgreSQL 14+                                |
| Auth             | djangorestframework-simplejwt 5.3+ (JWT)      |
| CORS             | django-cors-headers 4.3+                      |
| Rate Limiting    | django-ratelimit 4.1+                         |
| Storage          | django-storages (Cloudflare R2) / local media |
| Images           | Pillow 10.3+                                  |
| Environment      | python-decouple 3.8+                          |
| Web Server       | Gunicorn 21.2+                                |
| Containerization | Docker                                        |
| Language         | Spanish (es-es), Timezone: Europe/Madrid      |

## Project Structure

```
backend/
├── config/                 # Django project configuration
│   ├── settings/           # base.py, local.py, production.py
│   ├── urls.py             # Root URL configuration
│   ├── pagination.py       # FlexiblePageNumberPagination
│   └── wsgi.py             # WSGI application
├── apps/                   # All Django apps
│   ├── accounts/           # User management, auth (JWT), roles
│   ├── audit/              # Immutable audit logging
│   ├── clients/            # Client/brand management
│   ├── content_makers/     # Content creator (influencer) profiles
│   └── projects/           # Core campaign/project lifecycle & state machine
├── data/                   # CSV imports and seed data
├── media/                  # Local file uploads
├── requirements/           # pip requirements (base.txt)
├── Dockerfile              # Container definition
└── manage.py               # Django management
```

## Python & Type Safety

- **Always use Python 3.12** features where appropriate (type hints, `|` union syntax, etc.)
- Use **type hints** on all function signatures (parameters and return types)
- Avoid using `Any` — use `object` or proper types instead
- Define model-level types through Django model fields and serializer definitions

## Import Conventions

- **Same app imports**: `from apps.app_name.models import ModelName`
- **Cross-app imports**: `from apps.other_app.models import ModelName`
- **Service imports**: `from apps.app_name.services import function_name`
- **Config imports**: `from config.pagination import FlexiblePageNumberPagination`

## Django App Architecture

### App Responsibilities

Each Django app owns a **single domain concern**. Key files per app:

| File             | Purpose                                                |
| ---------------- | ------------------------------------------------------ |
| `models.py`      | Data models, fields, relationships, model methods      |
| `serializers.py` | DRF serializers (list, detail, create/update variants) |
| `views.py`       | ViewSets and API views                                 |
| `urls.py`        | Router registration and URL patterns                   |
| `permissions.py` | DRF permission classes (role-based)                    |
| `services.py`    | Business logic, state machines, workflows              |
| `admin.py`       | Django admin configuration                             |
| `tests/`         | Test directory with test files                         |
| `migrations/`    | Database migrations                                    |

### Placement Rules

- `serializers.py`: request validation and input/output transformation
- `views.py` / viewsets: endpoint orchestration, permissions, and response flow
- `services.py`: domain logic, state transitions, multi-step workflows
- `permissions.py`: role-based access control (admin, employee, client, content_maker)
- `urls.py`: route and router wiring only

### When to Create What

- **Model**: Persistent data with database representation
- **Serializer**: API input/output transformation
- **ViewSet**: HTTP endpoint with CRUD operations
- **Service function** (`services.py`): Complex business logic with side effects
- **Permission class**: Role-based access control

### Anti-patterns to Avoid

- **Do not** place complex business logic directly in viewsets — delegate to services
- **Do not** duplicate logic across apps — centralize shared logic
- **Do not** create unnecessary abstractions for simple operations
- Reuse existing modules in the app before introducing new abstractions
- Follow existing nearby patterns before introducing new ones

## Code Patterns

### Multi-Serializer Pattern

Use different serializers for list/detail/create/update operations:

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

### Role-Based QuerySet Filtering

```python
def get_queryset(self):
    user = self.request.user
    qs = Project.objects.select_related("client", "status")
    if user.role == "client":
        return qs.filter(client__user=user)
    if user.role == "content_maker":
        return qs.filter(content_makers__content_maker__user=user)
    return qs  # admin/employee see all
```

### Service Pattern (Business Logic)

```python
# apps/projects/services.py
def transition_project_status(project: Project, user=None, reason: str = "") -> None:
    """Auto-advance project through workflow based on current state."""
    ...

def handle_cm_accept(project: Project, cm_profile, user) -> None:
    """Handle content maker accepting a project."""
    ...
```

### Permission Pattern (Role-Based)

```python
class IsAdminOrEmployee(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (CustomUser.ADMIN, CustomUser.EMPLOYEE)
        )
```

### Audit Trail Pattern

```python
# Track sensitive field changes via apps.audit.services
from apps.audit.services import audit_changes

old_data = {"status": old_status, "fee": old_fee}
new_data = {"status": new_status, "fee": new_fee}
audit_changes(user, instance, old_data, new_data)
```

## Authentication

- JWT tokens via **djangorestframework-simplejwt**
- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days, with rotation + blacklisting
- Rate-limited login (5 attempts per 15 minutes)
- Default: `rest_framework.permissions.IsAuthenticated`
- Four roles via `CustomUser.role`:
  - `admin` — full system access
  - `stimada_employee` — operational management
  - `client` — brand/agency user (sees own projects)
  - `content_maker` — influencer (sees assigned projects)

## URL Routing

- All apps use `rest_framework.routers.DefaultRouter` for automatic CRUD endpoints
- All app URLs are included under `/api/` prefix in `config/urls.py`
- Custom endpoints use explicit `APIView` classes with `@method_decorator(ratelimit(...))`
- Auth endpoints at `/api/auth/` (login, logout, refresh, me)

```python
router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
urlpatterns = [path("", include(router.urls))]
```

## Code Style & Documentation

- **No inline method comments** — method names and implementation must be self-documenting
- **Descriptive method names** — use clear names that explain intent (e.g., `transition_project_status()` not `process()`)
- **No docstrings for simple methods** — if a method's name and signature explain it, skip the docstring
- Use docstrings only for **complex logic** that cannot be made self-evident through naming
- **Spanish-language domain terms** in model fields/statuses (e.g., `estado`, `semaforo_cliente`, `fecha_servicio`)
- **English for code structure** (class names, method names, variable names)

- **Files**: snake_case (`my_helper.py`)
- **Classes**: PascalCase (`ProjectViewSet`, `ContentMakerProfile`)
- **Functions/methods**: snake_case (`get_active_projects`, `handle_cm_accept`)
- **Variables**: snake_case (`user_id`, `project_status`)
- **Constants**: UPPER_SNAKE_CASE (`STATUS_ORDER`, `CM_NON_EDITABLE_FIELDS`)
- **URLs**: kebab-case (`/projects/`, `/content-makers/`, `/client-types/`)
- **Test files**: `test_<feature>.py` (e.g., `test_project_endpoints.py`)

## Settings Structure

| File            | Purpose                                  |
| --------------- | ---------------------------------------- |
| `base.py`       | All base configuration                   |
| `local.py`      | Local development (DEBUG, console email) |
| `production.py` | Production (R2 storage, SMTP email)      |

## Testing

- Use **Django TestCase** with DRF's `APIClient`
- Tests live in `apps/<app>/tests/` directories
- Cover at least **one happy path and one error/edge path** for API changes
- Verify **status codes and key response fields**
- Use `self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")` for auth in tests

### Running Tests

```bash
python manage.py test                          # Run all tests
python manage.py test apps.projects            # Specific app
python manage.py test apps.projects.tests.test_views  # Specific module
```

## Docker & Development

- **Dockerfile**: Python 3.12-slim + PostgreSQL client + Gunicorn
- **Local development**: `docker-compose` or `python manage.py runserver`
- **Database**: PostgreSQL via `dj-database-url` from `.env`
- **Storage**: Cloudflare R2 (production) or local `media/` (development)

## Best Practices

1. **Type everything**: Function parameters, return types
2. **Query optimization**: Use `select_related()` / `prefetch_related()` in ViewSets
3. **Bulk operations**: Use `bulk_create()` / `bulk_update()` over individual saves in loops
4. **Business logic in services**: Multi-step logic goes in `services.py`, not in views
5. **Role-based access**: Use permission classes + queryset filtering by role
6. **Audit changes**: Use `apps.audit.services.audit_changes()` for sensitive field tracking
7. **State machine**: Use `transition_project_status()` for automatic project advancement
8. **Spanish domain terms**: Keep model field names in Spanish where they represent domain concepts
9. **Prefer ORM over Python loops**: Push data processing to database queries

## Safety Constraints

- Keep changes **strictly scoped** to the requested task — avoid unrelated file churn
- **Do not modify migrations** unless explicitly requested
- **Preserve backward compatibility** by default
- Do not refactor unrelated files while implementing a scoped task
- Prefer the **smallest change** that satisfies requirements
- If requirements are ambiguous, **pause and state assumptions** before proceeding
- Preserve existing API contracts (request/response fields and status codes) unless explicitly asked

## Code Quality & Clean Code

- Write **readable, self-documenting code** — meaningful names, small functions, single responsibility
- Key rules:
  - **Functions should do one thing** and be short (≤ 30 lines)
  - **Use descriptive names** — prefer `handle_cm_accept()` over `process()`
  - **Avoid magic numbers/strings** — extract to constants
  - **Prefer early returns** over deep nesting
  - **No dead code** — remove unused variables, imports, functions
  - **Handle errors explicitly** — never silently swallow exceptions
  - **Keep files focused** — one concern per module

## Code Review Checklist

Before considering code complete, verify:

- [ ] Type hints on all function signatures
- [ ] Query optimization (`select_related`, `prefetch_related`) applied
- [ ] Business logic in services, not views or serializers
- [ ] Permissions properly defined (role-based)
- [ ] Serializer validation handles edge cases
- [ ] No duplicate code
- [ ] Tests cover the change
- [ ] Code is clean: no dead code, no magic values, descriptive names
- [ ] Migrations are correct (if models changed)
- [ ] Code follows existing patterns in the codebase

## Expected Agent Output Style

1. Short plan checklist with the concrete steps taken
2. Files changed and why
3. Validation performed (commands/tests run, with pass/fail status)
4. Risks, assumptions, and open questions (if any)
