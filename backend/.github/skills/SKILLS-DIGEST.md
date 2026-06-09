# Skills Digest

Index of all available skill guides for this Stimada Django backend project. Each skill provides detailed, topic-specific rules that complement the main `copilot-instructions.md`.

| Skill                          | Path                    | Summary                                                                                      |
| ------------------------------ | ----------------------- | -------------------------------------------------------------------------------------------- |
| **API Design**                 | `api-design/SKILL.md`   | ViewSets, serializers, permissions, pagination, URL routing                                  |
| **Django Testing**             | `testing/SKILL.md`      | Django TestCase, APIClient, endpoint/permission tests                                        |
| **Code Quality & Clean Code**  | `quality/SKILL.md`      | Naming, functions, constants, error handling, Python & Django best practices                 |
| **Services & Business Logic**  | `services/SKILL.md`     | Service functions, state machine, notifications, audit integration                           |
| **Database & Models**          | `database/SKILL.md`     | Models, QuerySets, ORM best practices, migrations                                            |
| **Architecture Documentation** | `architecture/SKILL.md` | Creating arc42 architecture documentation, analyzing workspace structure, documenting design |

## How to Use

- The **copilot-instructions.md** provides the high-level rules and project conventions
- **Skill files** go deeper into a specific topic — consult the relevant skill when working in that area
- When a task spans multiple concerns (e.g., creating a new endpoint with tests), combine guidance from multiple skills (api-design + testing + quality)

## Automatic Skill Routing

Use the following trigger matrix to make skill usage deterministic:

| Trigger words / intent                                                        | Required skill(s)                     |
| ----------------------------------------------------------------------------- | ------------------------------------- |
| ViewSet, serializer, permission, pagination, endpoint, URL, API               | `api-design/SKILL.md`                 |
| test, APIClient, coverage, TestCase                                           | `testing/SKILL.md`                    |
| refactor, readability, naming, clean code, error handling, review, type hints | `quality/SKILL.md`                    |
| service, state machine, notification, workflow, transition, audit             | `services/SKILL.md`                   |
| model, QuerySet, migration, ORM, annotate, aggregate, Q, F                    | `database/SKILL.md`                   |
| new feature touching API + DB + tests                                         | `api-design` + `database` + `testing` |
| refactor with tests                                                           | `quality` + `testing`                 |
| arc42, architecture documentation, architecture analysis, design decisions    | `architecture/SKILL.md`               |

### Enforcement

- For non-trivial tasks, at least one skill must be selected before implementation.
- If no trigger matches clearly, ask one concise clarification question.
- Every substantive response should include `Skill used: ...` for visibility.
