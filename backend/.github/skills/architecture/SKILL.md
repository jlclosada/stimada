---
name: Creating ARC42 architecture documentation
description: Creation of complete architecture documentation following the ARC42 template for a Django backend project
when_to_use: When your human partner asks you to create architecture documentation following "arc42" best-practices and templates. When asked on analyzing code or a workspace for architecture principles and to document them. When a workspace is complex and no architecture documentation exists, but you find it to be valuable for both the human partner and yourself.
version: 0.0.2
---

# Creating architecture documentation following arc42

## Your role

You are an expert software architect and technical writer. Your task is to analyze the current Django project repository and produce an overall architecture overview document following the arc42 template (https://arc42.org/overview/). Prepare everything so that documentation is written into the repository, but do not change or modify any source code or configuration files.
Add a startup page with a management summary (Executive Summary) and an overview (Architecture Documentation Structure) of all stakeholders and their view on the document (see https://arc42.org/overview/)

## Project context

This is a **Django 5.0 REST API** project (Stimada Backend) with the following key architectural patterns:

- **Django REST Framework** for API endpoints (ViewSets, Serializers, Permissions)
- **PostgreSQL** as the primary database
- **SimpleJWT** for JWT-based authentication with role-based access
- **Service functions** (`services.py`) for orchestrating multi-step business logic
- **State machine** for project lifecycle management (12 statuses)
- **Audit logging** via `apps.audit` for sensitive field changes
- **Notification system** via in-app `Notification` model
- **Cloudflare R2** for production file storage

## Primary goal

Create a concise, high quality overall architecture document (not implementation details) using the arc42 structure and place it under /docs/architecture in the repository. The document should provide a clear, traceable overview suitable for stakeholders and new developers.

## Django-specific analysis focus

When exploring the codebase, pay special attention to:

1. **App boundaries**: Each Django app (`contracts/`, `projects/`, `controlling/`, etc.) represents a bounded context. Map their responsibilities and inter-dependencies.
2. **Data flow**: Follow the request → view → serializer → model → signal → handler/tracker → notification chain.
3. **External integrations**: BASF Auth, PhaseGate API, LDAP, Databricks, Azure Blob Storage, Email Service.
4. **Settings architecture**: `app/settings/` with base, environment, local, test, logs, otel modules.
5. **URL structure**: All apps mounted at root level via `app/urls.py` using DRF routers.
6. **Async architecture**: Celery workers, beat scheduler, Redis broker, database result backend.

## Workflow and constraints

- Do not change source code or configuration files; produce only documentation files (Markdown).
- If technical operational details are required (runbooks, deployment scripts, configuration specifics, CI/CD, container images, operational steps), create separate documents under /docs/operations and reference them from the architecture document.
- Work iteratively: first produce a todo.md inside a hidden folder .tasks in the repository root (create .tasks/todo.md). After your human partner reviews and confirms, you will proceed to create the arc42 documents step by step.
- At every step beyond the initial todo.md, stop and ask for explicit confirmation before continuing.

### Deliverables 1 (initial): ToDo list

- Create .tasks/todo.md: an actionable checklist that lists all arc42 sections to produce, with substeps, estimated effort (low/medium/high), priority, and verification steps. End the todo.md with the line: "Ready to start: please confirm to analyze 'Introduction and Goals'."
- Include tasks to: locate entry points, identify Django apps/modules, map responsibilities to files/paths, identify external dependencies, produce Mermaid diagrams (system context, building blocks, runtime scenarios, deployment), list open questions requiring manual verification, and create /docs/operations placeholders if needed.

### Deliverables 2 (after confirmation only): Stepwise arc42 creation

- Produce the arc42 documentation under /docs/architecture using Markdown files. You may use a single arc42.md or split by section files (e.g., /docs/architecture/01_introduction.md), but keep the structure discoverable.
- For diagrams, use Mermaid code blocks exclusively (mermaid ... ). Include comments that map diagram entities to specific repository artifacts (file paths, scripts, Docker/Helm configs).
- Each arc42 section must:
  - Contain content derived from repository evidence (file paths, README snippets, package definitions, Dockerfiles, CI files). Quote or cite the exact file path or small code snippets as evidence.
  - Clearly state any assumptions and mark them as TODOs/questions for manual verification.
  - Avoid implementation-level details; if such details are necessary, create them under /docs/operations and reference them.
  - Use bullet lists, tables for mappings (component → files), and concise prose.

arc42 sections to cover (minimum)

- Introduction and Goals
- Constraints and Context
- System Scope and Context (with a Mermaid system context diagram)
- Solution Strategy
- Building Block View (with Mermaid component/block diagram and mapping to Django apps/source files)
- Runtime View / Scenarios (with Mermaid sequence/activity diagrams for key flows: authentication, project creation, notification, PhaseGate sync)
- Deployment View (with Mermaid deployment diagram showing Docker services, PostgreSQL, Redis, Celery)
- Cross-cutting Concepts (authentication, permissions, audit logging, signal-driven tracking, error handling, configuration-driven notifications)
- Architecture Decisions (ADR style: decision, context, alternatives, consequences)
- Quality Requirements and Tactics
- Risks and Technical Debt
- Glossary and References

## Documentation style and traceability

- Use professional, neutral English.
- For every architectural statement include a trace reference (file path and optionally a short excerpt). E.g., "The contracts domain is implemented in `django/contracts/` (see `django/contracts/models.py` for the data model)".
- Where exact mapping is unclear, include a TODO with suggested files to inspect.
- Use Mermaid diagrams with concise labels and include inline comments mapping nodes to repository artifacts.

## Interaction protocol

- Start by creating .tasks/todo.md and stop. Wait for review of your human partner.
- After each subsequent step (each arc42 section), present the generated file(s) and ask: "I have completed [SECTION NAME]. Do you want me to proceed to [NEXT SECTION NAME]? (yes/no)"
- If your human partner reply "yes", proceed to the next section. If "no", stop and wait.

## Output constraints

- Only create or update Markdown files under .tasks, /docs/architecture, or /docs/operations.
- Do not output any other artifacts (no images, no binary files).
- All diagrams must be Mermaid blocks.
- Keep commit-friendly, git-rebase friendly diffs (concise files).
- Never commit automatically code to git.

## Initial action (what to produce now)

- Create .tasks/todo.md as specified above. Provide it here as the first output so your human partner can review. Do not produce any other files or sections until your human partner confirms.

## Tone and emphasis

- Be precise, concise, and pragmatic.
- Prioritize traceability to repository artifacts.
- Flag open questions clearly for later manual verification.
