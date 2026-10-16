# KI Ecosystem Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ki-ecosystem (this project)                  │
│                      Meta-project for stackctl                  │
│  Coordinates: init, install, update, deploy across all repos    │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌──────────────┐  ┌──────────┐  ┌──────────────┐
        │  ki-core     │  │yaml-cfg  │  │   widgetkit  │
        │(shared base) │  │(config   │  │(framework-   │
        │              │  │toolkit)  │  │ neutral UI)  │
        └──────────────┘  └──────────┘  └──────────────┘
           │      │           │              │
           │      └───────────┼──────────────┤
           │                  ▼              ▼
           │         ┌────────────────┐  ┌───────────┐
           │         │ yaml-cfg-wizard│  │ widgetkit-│
           │         │    (CLI)       │  │  django   │
           │         └────────────────┘  └───────────┘
           │
           └─────────────────────┬─────────────────────────┐
                                 │                         │
                    ┌────────────▼──────────────┬─────────▼──────────┐
                    │                           │                    │
                    ▼                           ▼                    ▼
          ┌──────────────────┐      ┌──────────────────┐  ┌──────────────┐
          │ kicli-code-assist│      │  ki-knowledge    │  │yaml-cfg-     │
          │ (TUI code assist)│      │(knowledge base)  │  │wizard-ui     │
          │                  │      │                  │  │(web UI)      │
          └──────────────────┘      └──────────────────┘  └──────────────┘


## Dependency Directions

All dependencies follow this hierarchy:

1. **Independent Layer**
   - yaml-cfg: Pure YAML config toolkit (no KI dependencies)
   - widgetkit: Framework-neutral widget rendering

2. **Orchestration Layer**
   - ki-core: Uses yaml-cfg for config management
   - Exports shared commands (config, profile, stage, doctor)

3. **Application Layer**
   - Each app (kicli-assist, ki-knowledge, ki-chat) uses ki-core
   - Apps delegate config commands to ki-core for consistency
   - Optional: yaml-cfg-wizard-ui provides web management layer

```

## Dependency Flow

```
Apps:
  kicli-assist ──────┐
  ki-knowledge ──────┤──> ki-core ──> yaml-cfg
  ki-chat ───────────┤
  yaml-cfg (cli) ────┘ (optional delegation)

Web UI:
  yaml-cfg-wizard-ui ──> widgetkit-django ──> widgetkit
                         │
                         └──> yaml-cfg (optionally, for API)
```

## Command Architecture (Phase 2)

Each app has these command groups (all delegate to ki-core):

```
App CLI
  ├─ config
  │   ├─ resolve      → ki_core.commands.config.run_config()
  │   ├─ skeleton     → ki_core.commands.config.run_skeleton()
  │   ├─ show         → ki_core.commands.config.run_show()
  │   └─ verify       → ki_core.commands.config.run_verify()
  ├─ profile
  │   ├─ list         → ki_core.commands.profile.run_list()
  │   ├─ active       → ki_core.commands.profile.run_active()
  │   └─ set <name>   → ki_core.commands.profile.run_set()
  └─ stage
      ├─ list         → ki_core.commands.stage.run_list()
      ├─ active       → ki_core.commands.stage.run_active()
      └─ set <name>   → ki_core.commands.stage.run_set()
```

All commands are cli-agnostic (accept `echo_fn` parameter) so they work across:
- Typer apps (kicli-assist, yaml-cfg)
- Click apps (ki-knowledge, ki-chat)
- Raw argv apps

## Stackctl Integration

Stackctl configuration in `pyproject.toml`:

```toml
[tool.stackctl]
config_loader = "ki_core:load_config"      # How to load deployment config
config_key = "stack"                        # Which config section has deployment targets

[[tool.stackctl.siblings]]                  # All related repos
name = "ki-core"
path = "ki-core"
url = "https://github.com/uvlightdrops/ki-core.git"
# ... etc for all siblings
```

This enables:
- `stackctl init` - Clone all siblings
- `stackctl install` - Install all with dependencies
- `stackctl update` - Pull latest from all
- `stackctl deploy` - Deploy stack based on config
- `stackctl run <cmd>` - Execute command in all repos

## Installation Scenarios

### Scenario 1: Full Ecosystem

```bash
cd ki-ecosystem
pip install -e ".[dev]"
# Installs: ki-core, yaml-cfg, kicli-assist, ki-knowledge, widgetkit*
```

### Scenario 2: Minimal (just config management)

```bash
pip install yaml-cfg-wizard
# Standalone YAML tool, zero KI dependencies
```

### Scenario 3: Single App

```bash
cd kicli-code-assist
pip install -e ".[dev]"
# Installs: kicli-assist + ki-core + yaml-cfg + dependencies
```

### Scenario 4: Development (all repos locally)

```bash
cd ki-ecosystem
stackctl init
stackctl install --venv --extras dev
# Creates .venv in each repo, installs with dev tools
```

## Configuration Management

Stack configuration hierarchy (from ki-core):

```
config/
  ├─ defaults/
  │   ├─ stack.yaml        (base deployment targets)
  │   ├─ config.yaml       (default config structure)
  │   └─ logging.yaml      (log settings)
  ├─ profiles/
  │   ├─ dev.yaml          (development overrides)
  │   ├─ prod.yaml         (production overrides)
  │   └─ .active_profile   (currently active: "dev" or "prod")
  └─ stages/
      ├─ local.yaml        (local machine overrides)
      ├─ test.yaml         (test environment)
      └─ .active_stage     (currently active: "local", "test", etc)

Resolution order:
  defaults/stack.yaml
  + profiles/<active>.yaml
  + stages/<active>.yaml
  = final stack configuration
```

## Phase 2 Status

✅ **Complete**
- ki-core: config, profile, stage, doctor commands (cli-agnostic)
- kicli-assist: delegates to ki-core
- ki-knowledge: delegates to ki-core
- yaml-cfg: optional delegation (standalone fallback)

📋 **Next: Phase 3 (Deferred)**
- Unified "ki" CLI with app namespaces (e.g., `ki assist tui`, `ki config resolve`)
- Complexity: breaking changes, requires testing across all apps
- Timeline: 2-3 weeks after Phase 2 is stable

## See Also

- [STACKCTL.md](STACKCTL.md) - Stackctl usage guide
- [ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md](../ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md) - Detailed CLI design
- [kicli-code-assist/docs/PHASE_2_SUMMARY.md](../kicli-code-assist/docs/PHASE_2_SUMMARY.md) - Phase 2 completion summary
- [ki-core/docs/IMPLEMENTATION_STATUS.md](../ki-core/docs/IMPLEMENTATION_STATUS.md) - Per-project status
