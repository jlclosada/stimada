# Django DRF Code Review

Use this prompt for code review tasks. Focus on bugs, regressions, and missing tests.

## Review scope

- Files/area under review:
- Expected behavior and API contracts:

## Review checklist

- Correct module placement (`serializers`, `views`, `services`, `permissions`)
- API contract safety (request/response/status code compatibility)
- Query correctness and performance (ORM-first logic, N+1 risks, `select_related`/`prefetch_related`)
- Permissions and role-based access (admin, stimada_employee, client, content_maker)
- State machine integration (does the change trigger `transition_project_status` when needed?)
- Audit logging for sensitive fields (via `apps.audit.services.audit_changes`)
- Test quality (happy path + edge/error coverage)
- Type hints on all function signatures
- Clean code (no dead code, no magic values, descriptive names)

## Findings format

List findings first, ordered by severity:

- `[High|Medium|Low] <file>:<line or symbol> - issue and risk`

Then include:

1. Open questions/assumptions
2. Brief change summary
3. Validation gaps or residual risks

## Review constraints

- Prioritize concrete defects over style preferences
- Keep recommendations scoped and backward-compatible unless explicitly requested otherwise
