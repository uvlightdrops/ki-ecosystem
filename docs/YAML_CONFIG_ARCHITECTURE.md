# YAML Config Architecture: Libs and UI Tiers

**Status:** Conceptual Architecture (Foundation for Phase 3)  
**Audience:** Developers integrating config systems across ki-ecosystem

---

## Overview

YAML config management across ki-ecosystem is organized into **three tiers**:

```
┌─────────────────────────────────────────────────────────────┐
│  UI Tier (Interactive Presentation)                         │
├──────────────────┬──────────────────┬──────────────────────┤
│  CLI             │  TUI              │  Web UI              │
│  (typer/click)   │  (textual)        │  (React/Next.js)     │
│  Simple args     │  Terminal app     │  Browser forms       │
│  yaml-cfg set    │  kicli-assist     │  yaml-cfg-wizard-ui  │
└────────┬─────────┴──────────┬────────┴──────────────┬───────┘
         │                    │                       │
         └────────────────────┼───────────────────────┘
                              │ (all delegate to lib tier)
┌─────────────────────────────┴───────────────────────────────┐
│  Library Tier (Domain Logic)                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  yaml-cfg (Foundation)                                      │
│  • YAML file I/O (load, save, merge)                        │
│  • JSON Schema validation                                   │
│  • Type coercion and defaults                               │
│  • Path resolution (config file location)                   │
│  • Used in EVERY config operation                           │
│                                                              │
│  yaml-cfg-wizard (Guided Overlay)                           │
│  • Sequenced prompts (step-by-step config creation)         │
│  • Interactive validation feedback                          │
│  • Layered prompting (skip sections, optional fields)       │
│  • Used for NEW deployments or interactive setup            │
│  • Builds ON TOP of yaml-cfg                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Library Tier: Two Concerns

### 1. **yaml-cfg** (Always-On Foundation)

**Responsibility:** Technical YAML operations

```python
from yaml_cfg.core import ConfigResolver, deep_merge

# These happen on EVERY config access
resolver = ConfigResolver(schema_path="schema/ki.schema.yaml")
config = resolver.resolve("ki.yaml")  # load + validate + coerce
resolver.save(config, path="ki.yaml")  # merge + write
```

**Invoked by:**
- CLI tools (direct `yaml-cfg` commands)
- TUI apps (load config on startup, save on Ctrl+S)
- Web UIs (backend API endpoints)
- Django apps (AppConfig initialization)
- Any program needing validated YAML

**Key exports:**
- `load_yaml_file()` - Basic file I/O
- `ConfigResolver` - Schema-aware loading + validation
- `deep_merge()` - Layer merging logic
- `scaffold_skeleton_from_schema()` - Generate empty config template

---

### 2. **yaml-cfg-wizard** (Optional Enhancement)

**Responsibility:** Guided configuration processes

```python
from yaml_cfg_wizard.editor import edit_field, apply_changes

# Called ONLY when building/modifying config interactively
changes = apply_changes(
    config_dict=existing_config,
    dotted_path="llm.model",
    new_value="gpt-4",
    schema=schema_dict
)
```

**Invoked by:**
- Interactive setup flows (first-time deployment)
- TUI settings panel (Ctrl+O edit)
- Web wizard UI (step-by-step forms)
- CLI with `--wizard` flag (guided mode)

**Key exports:**
- `edit_field()` - Type-aware field editing
- `apply_changes()` - Validate + merge changes
- `FieldValidator` - Schema-based field validation
- `PrompterSequence` - Define multi-step guided flows

**Does NOT import yaml-cfg directly** - receives `config_dict` and `schema` as parameters, keeps logic pure.

---

## UI Tier: Three Front-Ends (Parallel, Independent)

### 1. **CLI** (Command-line interface)

**Tech:** `typer` or `click`  
**Entry point:** `yaml-cfg` command  
**Use case:** Scripting, direct args, CI/CD

```bash
# Simple operations (direct yaml-cfg)
yaml-cfg set ki.yaml llm.model gpt-4
yaml-cfg resolve ki.yaml

# Wizard mode (yaml-cfg-wizard overlay)
yaml-cfg setup --wizard
```

**Code pattern:**
```python
import typer
from yaml_cfg_wizard.cli import setup_wizard

app = typer.Typer()

@app.command()
def setup(wizard: bool = False):
    if wizard:
        setup_wizard()  # yaml-cfg-wizard lib
    else:
        # direct yaml-cfg lib
```

---

### 2. **TUI** (Terminal User Interface)

**Tech:** `textual`  
**Entry point:** `kicli-assist` app → Ctrl+O settings panel  
**Use case:** Interactive terminal apps, remote servers

**Code pattern:**
```python
# kicli_code_assist/ui/settings_panel.py
from yaml_cfg_wizard.editor import apply_changes
from textual.widgets import Input, Button

class SettingsPanel(Screen):
    def on_button_pressed(self, event: Button.Pressed):
        # User edited a field, save it
        changes = apply_changes(
            config_dict=self.app_config.raw,
            dotted_path="llm.model",
            new_value=self.model_input.value,
            schema=self.schema
        )
        # Write back to file (yaml-cfg)
        resolver.save(changes, path=config_path)
```

**Always uses yaml-cfg for I/O, yaml-cfg-wizard for editing logic.**

---

### 3. **Web UI** (Browser interface)

**Tech:** React/Next.js  
**Entry point:** `yaml-cfg-wizard-ui` standalone service  
**Use case:** Admin dashboards, centralized config management

**Code pattern:**
```javascript
// pages/config/edit.tsx
import { applyChanges } from '@/lib/config';

export default function EditPage() {
  const handleFieldChange = async (dotted_path, value) => {
    // Backend API calls yaml-cfg-wizard lib
    const response = await fetch('/api/config/apply', {
      method: 'POST',
      body: JSON.stringify({
        config: currentConfig,
        dotted_path,
        value,
        schema
      })
    });
  };
}
```

**Backend always uses yaml-cfg for I/O, yaml-cfg-wizard for editing.**

---

## Dependency Flow

```
┌─ CLI command                 ┐
├─ TUI panel (kicli-assist)    ├─→ yaml-cfg-wizard lib (if guided mode)
├─ Web form (wizard-ui)        │       ↓
└─ Django app                  ┘   yaml-cfg lib (core I/O + validation)
```

**Important invariant:**
- **yaml-cfg is always used** for file I/O and validation
- **yaml-cfg-wizard is optional** for enhanced guidance/sequencing
- **No circular dependencies** - wizard imports yaml-cfg, not vice versa

---

## Schema Ownership: One Per Domain

Each application/domain owns its schema, not each tool:

```
kicli-assist/schema/
  └─ kicli.schema.yaml    ← Describes kicli-assist config structure

ki-knowledge/schema/
  └─ ki-knowledge.schema.yaml  ← Describes ki-knowledge config

yaml-cfg-wizard/
  └─ (NO schema - it reads others' schemas)

yaml-cfg-wizard-ui/
  └─ (NO schema - it reads others' schemas)
```

When a schema changes, ALL UIs automatically use the new schema (because they all read from it).

---

## Refactoring: Settings Panel Unification

**Current state:** `kicli-assist/ui/settings_panel.py` reimplements field editing logic

**Target state:**
```python
# Before: duplicate logic
def edit_field_custom_logic(value, type_hint, schema):
    # custom type coercion, validation ...
    
# After: use shared lib
from yaml_cfg_wizard.editor import apply_changes
changes = apply_changes(config, path, new_value, schema)
```

**Benefits:**
- Single source of truth for validation
- TUI, CLI, Web UI all use same logic
- Schema changes don't require UI updates

---

## Deployment: CLI vs Wizard vs Direct

**Simple config change (script/automation):**
```bash
yaml-cfg set config.yaml llm.model gpt-4
```

**Interactive setup (first deployment):**
```bash
yaml-cfg setup --wizard
# OR
kicli-assist
# (Ctrl+O in TUI)
```

**Web dashboard:**
```bash
yaml-cfg-wizard-ui --port 8080
# (Browse to localhost:8080)
```

All three paths ultimately use the same `yaml-cfg` and `yaml-cfg-wizard` libraries.

---

## Next Steps

1. **Refactor kicli-assist settings** to import from yaml-cfg-wizard.editor
2. **Extract wizard CLI** into separate package if needed (currently in yaml-cfg-wizard)
3. **Standardize schema locations** across all projects
4. **Document each project's schema** in its own `docs/CONFIG_SCHEMA.md`
