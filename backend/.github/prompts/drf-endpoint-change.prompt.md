# DRF Endpoint Change

Use this prompt when implementing or modifying a Django REST Framework endpoint in this repository.

## Task

Describe the endpoint change in one sentence.

## Scope

- Modify only: `<apps/files>`
- Do not modify: `<apps/files>`

## Contract and behavior

- Request fields and validation:
- Response fields and status codes:
- Permission expectations (which roles can access):
- Backward-compatibility requirements:

## Implementation constraints

- Keep validation/normalization in serializers
- Keep viewsets focused on orchestration
- Keep business logic in `services.py`
- Reuse existing app modules and nearby patterns before creating new abstractions
- Use role-based filtering in `get_queryset()` for client/content_maker visibility

## Data/query constraints

- Prefer queryset/ORM expressions over Python loops
- Use `select_related`/`prefetch_related` where needed
- Keep query param filtering in `get_queryset()` method

## Testing constraints

- Add tests in `apps/<app>/tests/test_<feature>.py`
- Validate at least one happy path and one error/edge path
- Assert status codes and key payload fields
- Test role-based access (admin vs client vs content_maker)

## Output format

1. Short plan checklist
2. Files changed and why
3. Validation performed (commands/tests + status)
4. Risks, assumptions, and open questions
