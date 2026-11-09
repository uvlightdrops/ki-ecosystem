---
project: ki-ecosystem
agent_project: ki-ecosystem
purpose: Stackctl operation
created: null # Unknown
updated: "2026-11-09 01"
update_reason: Local service and port audit
---

# Stackctl Integration for KI Ecosystem

This repository is the central manifest for coordinated multi-repository work.
Start here in PyCharm/Copilot; application implementations remain in independent
sibling Git repositories. See [AGENTS.md](AGENTS.md) for the startup checklist and
agent boundaries. Keeping one conversation is convenient, not required: the
versioned instructions should also support a fresh session.

## Sources of truth

| Concern | Source |
|---------|--------|
| Sibling names, paths and clone URLs | `pyproject.toml`, `[[tool.stackctl.siblings]]` |
| Python package dependencies | `pyproject.toml`, `[project.dependencies]` |
| Stack configuration loader | `[tool.stackctl].config_loader = "ki_ecosystem:load_config"` |
| Stack section | `[tool.stackctl].config_key = "stack"` |
| Hub configuration | `ki_ecosystem/config.py` reads `config/defaults/stack.yaml` |
| Commands and flags | The installed `stackctl --help` and implementation |

This hub's loader does not use ki-core's profile/stage resolution. Its YAML
contains coordination/reference data, not complete service launch definitions.
Deploy and operate applications using their own stack specifications.

## Orientation without changing working files

Run from the ecosystem root:

```bash
git status --short --branch
command -v stackctl
stackctl --help
# Network operation: fetches/prunes remote-tracking refs in all repositories
stackctl repo-status
```

`repo-status` includes this repository and all manifest siblings. Its
implementation runs `git fetch --all --prune` before computing ahead/behind.
It updates Git metadata and needs network access, but does not merge or change
checked-out files. For offline orientation, use local `git status` per repository.

`stackctl projects --json` has a different meaning: it lists locally registered
runtime projects, registered by start/run/restart operations. It is not a listing
of `[[tool.stackctl.siblings]]` and should not be used to infer ecosystem membership.

## Path resolution

The installed implementation resolves the source directory in this order:

1. Environment variable `STACKCTL_SRC_DIR`.
2. `[tool.stackctl].src_dir`.
3. The parent of the ecosystem repository.

A sibling is located at `source_directory / (path or name)`. Thus `path = "ki-core"`
normally means `../ki-core`, not `ki-ecosystem/ki-core`.
`yaml-cfg-wizard` explicitly uses `yaml_cfg_wizard`. The UI currently omits `path`
and therefore uses `yaml-cfg-wizard-ui`; its commented `yaml_cfg_wizard_ui` path
is inactive. The reference list in `config/defaults/stack.yaml` still uses the
underscore UI spelling and is not authoritative for Git checkout discovery.

When investigating a missing checkout, check the environment, manifest and
resolved directory before changing paths or cloning anything.

## Verified command semantics

The following reflects the installed local tool inspected on 2026-11-01.
Check `stackctl --help` again after tool updates.

| Command | Meaning |
|---------|---------|
| `repo-status` | Inspect the hub and manifest siblings |
| `clone` | Clone missing siblings; preserve existing Git checkouts |
| `checkout BRANCH` | Attempt branch switching across the hub and siblings |
| `pull` / `push` | Synchronize repositories with their configured upstreams |
| `install` | Editable-install siblings and hub into the tool's running virtualenv |
| `normalize` | Rewrite dependency paths in project manifests |
| `projects` | List the local runtime-project registry |
| `spec` | Resolve and display the selected project's stack specification |
| `status` / `logs` | Inspect services for the selected project/target |
| `start` / `stop` / `restart` | Operate services |
| `run SERVICE` | Run exactly one local service, not an arbitrary shell command |
| `delete` | Delete services on minikube/k8s targets only |

For preview without starting services, use `.venv/bin/python -m stackctl spec`
from the application root. It runs the loader and displays the resolved services,
not a start execution plan or stage-file provenance. There is no `start --dry-run`.
The output may contain confidential environment/Kubernetes values.
Stage-selection checks and preview limits:
[stackctl preview guide](../../stackctl/doc/README.md#vorschau-ohne-dienststart).

Targets are selected with `--target local|minikube|k8s`. `--json` supports
`status`, `logs` without follow, and `projects`; JSON status/logs are local-only.

There is no installed `kistack` entry point here. Do not use the old examples
`kistack init`, `stackctl init`, `stackctl update`, `stackctl deploy`,
`stackctl run pytest`, `--venv` or `--extras`: they are not this tool's interface.
Run tests directly in the owning project's environment.

## Installation and synchronization boundaries

Use stackctl from the selected project's virtualenv, not a central
`~/.local/bin/stackctl`. Prefer `.venv/bin/python -m stackctl` for automation;
with the correct venv active, its `bin/stackctl` is equivalent. This hub uses
`venv/` rather than `.venv/`. The tool is not installed in every project venv.
Canonical guidance and the current integration gaps:
[`stackctl/doc/README.md`](../../stackctl/doc/README.md).

Installation is not a startup/orientation step. When explicitly requested:

```bash
stackctl clone
stackctl install
```

`install` requires the Python environment running stackctl to be a virtualenv.
Activating a project virtualenv does not override an executable's fixed shebang;
check the selected executable/interpreter first. Installation can clone missing
repositories, upgrades pip, installs editable packages and then normalizes
dependency paths across repositories.

The existing polling script still searches PATH/global locations and its
systemd service does not put a project venv on PATH. Removing the central
entry point therefore requires a separate launcher/polling migration;
documentation changes alone do not make automated pulls work.

Development extras are selected through `STACKCTL_EXTRAS=dev` or
`[tool.stackctl].extras`, not a command-line `--extras` flag. Do not change the
installation environment merely to orient yourself.

Inspect each repository's branch, dirty state and upstream before synchronization.
Bulk commands can affect unrelated work and can succeed only partially.
Commit deliberately per repository; do not automatically stage or push all repos.

## Polling and deployment

The supplied systemd timer schedules `scripts/deploy-polling.sh` approximately
every five minutes, with a randomized delay. That script runs `stackctl pull`
from this hub. The checked-in service and script contain host-specific absolute
paths; installation on another host requires reviewing them.

Check actual timer state and logs on the target rather than assuming polling is
installed or active. See [DEPLOYMENT.md](DEPLOYMENT.md) and `scripts/`.
Git synchronization alone does not verify application reload or deployment health.

## Architecture context

- [CLI Architecture Roadmap](CLI_ARCHITECTURE_ROADMAP.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [YAML Configuration Architecture](YAML_CONFIG_ARCHITECTURE.md)

These documents capture design and historical phase status. Verify current
implementation in the owning repository before treating planned work as complete.

## Local service and port audit [local-service-audit]

`scripts/service_audit.py` combines stackctl's local JSON status with Linux
`ss` TCP/UDP socket owners. It visits the hub and every manifest sibling using
stackctl's path resolution. Run it with the hub interpreter, which must have
stackctl installed; stackctl resolves application configuration through each
project's own interpreter.

```bash
venv/bin/python scripts/service_audit.py
# Include unrelated/unknown host listeners as well:
venv/bin/python scripts/service_audit.py --all-ports
# Preview a specific PID from the report:
venv/bin/python scripts/service_audit.py --cleanup-pid <PID>
# Explicitly send SIGTERM to that selected, eligible PID:
venv/bin/python scripts/service_audit.py --cleanup-pid <PID> --apply
```

The report shows configured service addresses, stackctl status, actual listener
PIDs and working directories. A port shared by incompatible service definitions
is not fixed by killing its healthy owner. An unassigned listener or an
`unhealthy` status is only a review candidate, not proof of a hung process.
Ports without visible owners cannot be cleaned up; `--all-ports` also exposes
listeners that cannot be associated with the ecosystem.

Cleanup is restricted to explicitly selected PIDs owned by the current user
whose working directory is inside a manifest checkout. Healthy services,
external/Compose services, detected systemd/Supervisor services and projects
with unknown status are protected. Before each cleanup, status and sockets
are rescanned. Linux pidfds prevent signaling a reused PID; only SIGTERM is
sent, without process-group termination or automatic SIGKILL. The script
checks whether the previous listener addresses disappear, including cases
where another process shares or reopens the socket. Use the owning project's
normal `stackctl stop SERVICE` for intentional shutdown of healthy services.

This is a local-host audit, not a remote cluster or all-stage inventory. Missing
stack definitions and failed configuration loaders are reported per project;
exit code 1 means an incomplete audit or unsuccessful cleanup, and 2 means
an overall execution error. No source configuration is rewritten and no
services are started. The underlying stackctl status command can remove stale
local PID records as part of its existing status inspection.
