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

## Architecture

See [CLI_ARCHITECTURE_ROADMAP.md](ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md) for detailed architecture and Phase 2 implementation status.

## Installation

```bash
# Install entire ecosystem with all dependencies
pip install -e .

# With development tools
pip install -e ".[dev]"
```

## Using stackctl

This project is configured for [stackctl](https://github.com/jreese/stackctl) for coordinated multi-repo management:

```bash
# Initialize all sibling repositories
kistack init

# Install all dependencies
kistack install

# Update all projects
kistack update

# Deploy with current stack configuration
kistack deploy
```

## Development

See individual project READMEs for development setup:

- [ki-core/README.md](ki-core/README.md)
- [kicli-code-assist/README.md](kicli-code-assist/README.md)
- [ki-knowledge/README.md](ki-knowledge/README.md)
- [yaml-cfg-wizard/README.md](yaml_cfg_wizard/README.md)

## License

MIT
