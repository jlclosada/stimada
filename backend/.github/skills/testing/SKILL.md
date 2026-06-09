# Django Testing

## Overview

The project uses **Django TestCase** with DRF's **APIClient** for integration/unit testing. Tests are located in `apps/<app>/tests/` directories. Authentication is handled via SimpleJWT tokens.

## When to Write Tests

### Always test

- **API endpoints** — every ViewSet action (list, create, retrieve, update, delete, custom actions)
- **Permissions** — role-based access control (admin, employee, client, content_maker)
- **Business logic** — service functions, state machine transitions
- **Serializer validation** — field validation, cross-field validation, edge cases

### Test when non-trivial

- **State machine** — transition logic with multiple paths
- **Notifications** — when they trigger on specific conditions
- **Custom model methods** — when they contain logic beyond simple field access

### Skip tests for

- Auto-generated migrations
- Django admin configuration (unless customized)
- Simple model definitions with no custom methods

## Test Structure

- One test class per feature/endpoint group
- Multiple `test_*` methods for different scenarios
- Use `setUp()` for common setup (user creation, auth)

```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser


class TestProjectEndpoints(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = CustomUser.objects.create_user(
            email="admin@stimada.com",
            password="testpass123",
            role=CustomUser.ADMIN,
            full_name="Admin User",
        )
        self.authenticate_as(self.admin)
        self.endpoint = "/api/projects/"

    def authenticate_as(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_list_projects(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

    def test_create_project_as_admin(self):
        data = {"nombre": "Test", "client": 1}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_client_cannot_create_project(self):
        client_user = CustomUser.objects.create_user(
            email="client@test.com", password="test123", role=CustomUser.CLIENT
        )
        self.authenticate_as(client_user)
        response = self.client.post(self.endpoint, {}, format="json")
        self.assertEqual(response.status_code, 403)
```

## File Naming & Location

| Source file               | Test file                                   |
| ------------------------- | ------------------------------------------- |
| `projects/views.py`       | `projects/tests/test_project_endpoints.py`  |
| `projects/services.py`    | `projects/tests/test_project_services.py`   |
| `accounts/views.py`       | `accounts/tests/test_auth.py`               |
| `clients/views.py`        | `clients/tests/test_client_endpoints.py`    |
| `content_makers/views.py` | `content_makers/tests/test_cm_endpoints.py` |

## Permission Test Pattern

```python
class TestProjectPermissions(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = CustomUser.objects.create_user(
            email="admin@test.com", password="test", role=CustomUser.ADMIN
        )
        self.cm_user = CustomUser.objects.create_user(
            email="cm@test.com", password="test", role=CustomUser.CONTENT_MAKER
        )

    def test_admin_can_delete_project(self):
        self.authenticate_as(self.admin)
        response = self.client.delete(f"/api/projects/{self.project.id}/")
        self.assertEqual(response.status_code, 204)

    def test_content_maker_cannot_delete_project(self):
        self.authenticate_as(self.cm_user)
        response = self.client.delete(f"/api/projects/{self.project.id}/")
        self.assertIn(response.status_code, [403, 404])

    def authenticate_as(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
```

## Service Test Pattern

```python
class TestProjectStateMachine(TestCase):
    def setUp(self):
        # Create required lookup data and a project
        ...

    def test_transition_advances_from_borrador(self):
        self.assertEqual(self.project.status.nombre, "Borrador")
        transition_project_status(self.project)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status.nombre, "Negociación")

    def test_transition_does_not_go_backwards(self):
        # Set project to a later status and verify no regression
        ...
```

## Running Tests

```bash
python manage.py test                        # Run all tests
python manage.py test apps.projects          # Specific app
python manage.py test apps.projects.tests.test_project_endpoints  # Specific module
```

## Fixtures

### Structure

Fixtures are JSON files following Django's fixture format:

```json
[
  {
    "model": "projects.projectstatus",
    "pk": 1,
    "fields": {
      "nombre": "Borrador",
      "orden": 0,
      "activo": true
    }
  }
]
```

### Creating fixtures

- Use `python manage.py dumpdata <app>.<Model> --indent 2 > fixture.json` to export existing data
- For test fixtures, keep them minimal — only the records needed for the test
- Include all required foreign key dependencies in fixture ordering

## Mocking

### Mocking external services

```python
from unittest.mock import patch, MagicMock

class TestAccountServices(TestCase):
    @patch("apps.accounts.services.send_mail")
    def test_create_cm_account_sends_email(self, mock_send):
        # ... trigger account creation logic
        mock_send.assert_called_once()
```

### Mocking time-dependent tests

```python
from unittest.mock import patch
from datetime import date

class TestDeadlineChecks(TestCase):
    @patch("apps.projects.services.timezone.now")
    def test_overdue_detection(self, mock_now):
        mock_now.return_value = timezone.make_aware(datetime(2024, 6, 15))
        # ... trigger deadline check and assert
```

## Test Assertions Reference

```python
# Status code checks
self.assertEqual(response.status_code, 200)
self.assertEqual(response.status_code, 201)  # Created
self.assertEqual(response.status_code, 204)  # No Content (delete)
self.assertEqual(response.status_code, 400)  # Bad Request
self.assertEqual(response.status_code, 403)  # Forbidden
self.assertEqual(response.status_code, 404)  # Not Found

# Data checks
self.assertEqual(response.data["field"], expected_value)
self.assertIn("field", response.data)
self.assertGreater(len(response.data["results"]), 0)

# Database checks
self.assertTrue(Model.objects.filter(id=pk).exists())
self.assertEqual(Model.objects.count(), expected_count)
```

## Checklist for Test Quality

- [ ] Every endpoint has tests for CRUD operations
- [ ] Permission tests verify both allowed and denied access by role
- [ ] Service logic tests cover state transitions and edge cases
- [ ] External services (email) are mocked
- [ ] Tests use `format="json"` for POST/PATCH requests
- [ ] Edge cases are covered (empty, null, boundary values, invalid data)
- [ ] Tests are descriptive: `test_<action>_<context>` clearly states the scenario
- [ ] `setUp()` calls `super().setUp()` and uses `authenticate_as()` for auth
- [ ] No test interdependencies — each test can run independently
- [ ] Handler and query object logic has dedicated test coverage
- [ ] Existing orchestrator-style tests are extended before creating new standalone tests
- [ ] Prefer unifying related assertions into a single test method with helper methods for each step, rather than creating separate test methods — this reduces test overhead and keeps related flows together
- [ ] Status codes AND key response fields are asserted (not only object counts)
