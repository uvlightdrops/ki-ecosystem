---
project: ki-ecosystem
agent_project: ki-ecosystem
purpose: Ecosystem entry point
created: null # Unknown
updated: "2026-11-09 11"
update_reason: Add Wissenswiki projects
---

# KI Ecosystem

Unified stack control and deployment for all KI system components.

## Components

This ecosystem coordinates:

- **ki-core** - Shared orchestration and CLI base for all apps
- **kicli-code-assist** - Headless code assistant with TUI and diff preview
- **ki-knowledge** - Knowledge base system with graph and ingestion
- **yaml-cfg-wizard** - Reusable YAML config resolution and validation toolkit
- **widgetkit** - Framework-neutral widget rendering core
- **widgetkit-django** - Django integration for widgetkit
- **yaml-cfg-wizard-ui** - Web UI for YAML config management
- **wissenswiki-core** - Knowledge blocks, typed relations and standalone web app
- **wissenswiki-django** - Reusable Django app for Markdown knowledge blocks

## Architecture

See [CLI_ARCHITECTURE_ROADMAP.md](docs/CLI_ARCHITECTURE_ROADMAP.md) for
cross-project design context. Historical phase status must be checked against
current implementation in the owning repository.

## PyCharm / Copilot entry point

Use this repository as the central entry point for cross-project work.
[AGENTS.md](docs/AGENTS.md) contains the startup checklist, repository map and working
boundaries; [.github/copilot-instructions.md](.github/copilot-instructions.md)
points Copilot to those instructions. A single conversation helps continuity,
but fresh sessions should reconstruct context from these files and current code.

`[[tool.stackctl.siblings]]` in `pyproject.toml` is the repository registry.
Sibling checkouts normally sit beside this repository, not inside it.

## Installation

```bash
# Install entire ecosystem with all dependencies
pip install -e .

# With development tools
pip install -e ".[dev]"
```

## Using stackctl

This project is configured for the locally installed `stackctl` tool for
coordinated multi-repo management. See [STACKCTL.md](docs/STACKCTL.md) for path
resolution, verified command semantics and installation boundaries.

```bash
# Inspect supported commands
stackctl --help
# Fetch/prune remote-tracking refs and inspect status; no checkout or merge
stackctl repo-status
```

Clone, installation, synchronization and service operations are deliberate
follow-up actions, not automatic session initialization.

## Development

See individual project READMEs for development setup:

- [ki-core/README.md](../ki-core/README.md)
- [kicli-code-assist/README.md](../kicli-code-assist/README.md)
- [ki-knowledge/README.md](../ki-knowledge/README.md)
- [yaml-cfg-wizard/README.md](../yaml_cfg_wizard/README.md)

## License

MIT
