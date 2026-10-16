# Stackctl Integration for KI Ecosystem

This project uses [stackctl](https://github.com/jreese/stackctl) for coordinated multi-repository management across all ecosystem components.

## Setup

### Prerequisites

```bash
# Install stackctl (if not already installed)
pip install stackctl
```

### Initialize All Repositories

```bash
# Clone/setup all sibling repositories defined in pyproject.toml
stackctl init

# Or if you already have the repos locally:
# stackctl init --verbose  # to see what it's doing
```

## Workflow

### Install All Dependencies

```bash
# Install main project and all siblings
stackctl install

# With optional dev tools
stackctl install --extras dev
```

### Update All Projects

```bash
# Pull latest from all siblings
stackctl update
```

### Deploy Stack

```bash
# Deploy using current configuration
stackctl deploy
```

### Run Commands in All Repos

```bash
# Run same command across all siblings
stackctl run pytest  # run tests in all projects
stackctl run ruff check  # lint all projects
```

## Configuration

The `[tool.stackctl]` section in `pyproject.toml` defines:

1. **config_loader**: How to load deployment configuration
   ```toml
   config_loader = "ki_core:load_config"
   ```
   This tells stackctl to use `ki_core.load_config()` to load stack configuration.

2. **config_key**: Which config section defines the stack
   ```toml
   config_key = "stack"
   ```
   Looks for `config["stack"]` to find deployment targets.

3. **siblings**: All related repositories
   ```toml
   [[tool.stackctl.siblings]]
   name = "ki-core"
   path = "ki-core"
   url = "https://github.com/uvlightdrops/ki-core.git"
   ```

## Example: Full Deployment Workflow

```bash
# 1. Initialize all repos
cd ki-ecosystem
stackctl init

# 2. Install dependencies
stackctl install --extras dev

# 3. Run tests across all projects
stackctl run pytest

# 4. Lint code
stackctl run ruff check

# 5. Deploy to production
stackctl deploy
```

## Troubleshooting

### Stackctl can't find siblings

Ensure all paths in `[[tool.stackctl.siblings]]` are correct relative to `ki-ecosystem/`.

```bash
# Check if repos are properly cloned
ls -la ki-core kicli-code-assist ki-knowledge yaml_cfg_wizard
```

### Config loader error

If stackctl can't load config, verify:

```bash
# 1. ki-core is installed
python -c "from ki_core import load_config; print(load_config.__doc__)"

# 2. Stack configuration exists
# (typically at config/defaults/stack.yaml or via active stage)
ki config resolve
```

### Dependency conflicts

If siblings have conflicting dependencies, use virtual environments per repo:

```bash
# Instead of global install
stackctl install --venv

# This creates .venv in each repo
```

## Architecture Context

See the following for architectural details:

- **Phase 2 Implementation**: [`kicli-code-assist/docs/PHASE_2_SUMMARY.md`](../kicli-code-assist/docs/PHASE_2_SUMMARY.md)
- **CLI Architecture Roadmap**: [`ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md`](../ki-core/docs/CLI_ARCHITECTURE_ROADMAP.md)
- **Implementation Status**: [`ki-core/docs/IMPLEMENTATION_STATUS.md`](../ki-core/docs/IMPLEMENTATION_STATUS.md)

## Next Steps

1. **Phase 2 Testing**: Verify all commands work across ecosystem after Phase 2 implementation
2. **Phase 3 Planning**: Design unified "ki" CLI namespace (currently deferred)
3. **CI/CD Integration**: Use stackctl commands in GitHub Actions workflows
