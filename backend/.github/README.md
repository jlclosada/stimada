# .github/ — AI Assistant Configuration

This directory configures GitHub Copilot's behavior for this Stimada Backend repository. All files are auto-discovered by VS Code Copilot when the workspace root is opened.

## Structure

```
.github/
├── copilot-instructions.md          # Global rules loaded into every conversation
├── agents/                          # Specialized AI agents
│   ├── api.agent.md                 # DRF endpoint creation/editing
│   ├── model.agent.md               # Django model work
│   └── test.agent.md                # Django test writing
├── prompts/                         # Reusable prompt templates (via /prompt command)
│   ├── django-drf-review.prompt.md  # Code review template
│   ├── drf-endpoint-change.prompt.md# Endpoint change template
│   ├── history.prompt.md            # Conversation history tracking
│   ├── modelUsage.prompt.md         # Token usage analysis
│   ├── skills.prompt.md             # Quick skill listing
│   └── thought.prompt.md            # Quick thought capture
└── skills/                          # Deep-dive topic guides
    ├── SKILLS-DIGEST.md             # Index of all skills + routing matrix
    ├── api-design/SKILL.md          # ViewSets, serializers, permissions
    ├── architecture/SKILL.md        # ARC42 documentation generation
    ├── database/SKILL.md            # Models, QuerySets, migrations
    ├── quality/SKILL.md             # Clean code for Python/Django
    ├── services/SKILL.md            # Service functions, state machine, notifications
    └── testing/SKILL.md             # Django TestCase, APIClient
```

## How it works

| File type                 | Auto-loaded?                                  | Purpose                                     |
| ------------------------- | --------------------------------------------- | ------------------------------------------- |
| `copilot-instructions.md` | Yes — every conversation                      | Project conventions, tech stack, patterns   |
| `skills/*.md`             | On demand — when task matches a skill trigger | Detailed rules for a specific topic         |
| `agents/*.md`             | On demand — when invoked by name or routed    | Scoped AI agent with tool/file restrictions |
| `prompts/*.md`            | On demand — via `/prompt` in chat             | Reusable structured templates               |

## Quick reference

- **Need to create an endpoint?** → `api` agent + `api-design` skill
- **Need to write tests?** → `test` agent + `testing` skill
- **Need to add a model?** → `model` agent + `database` skill
- **Need service/workflow logic?** → `services` skill
- **Code review?** → Use `/prompt django-drf-review`
- **Endpoint change?** → Use `/prompt drf-endpoint-change`
