---
project: ki-ecosystem
agent_project: ki-ecosystem
purpose: Reproducible session startup
created: 2026-11-01
updated: "2026-11-09 11"
update_reason: Register Wissenswiki and ki-knowledge-next repositories
---

# Agent entry point: KI Ecosystem

## Purpose and scope

This repository is the coordination hub for the KI ecosystem, not the home of
every application's implementation. Start cross-project work here; make
application changes in the owning sibling repository.

`pyproject.toml` is the source of truth for repository membership:
`[[tool.stackctl.siblings]]` defines names, checkout paths and clone URLs.
Python package dependencies in `[project.dependencies]` are a separate concern;
being a registered sibling does not imply being a package dependency.

One PyCharm/Copilot conversation is useful for continuity, but is not a
technical requirement. A new session must be able to reconstruct context from
these versioned instructions and the repositories. Never rely on remembered
chat state for paths, branches, implementation status or deployment status.

## Startup checklist

1. Read this file, the root `pyproject.toml` and `docs/STACKCTL.md`.
   Run all commands below from the repository root, not from `docs/`.
2. Inspect the local state without changing it:

   ```bash
   pwd
   git status --short --branch
   command -v stackctl
   stackctl --help
   ```

   For an ecosystem-wide view, use `stackctl repo-status` when network access is
   appropriate. It runs `git fetch --all --prune` in the hub and siblings,
   updating remote-tracking refs but not checking out or merging files.

3. Identify the owning repository from the manifest. Resolve its actual path
   using the rules below, then read its `AGENTS.md` and
   `.github/copilot-instructions.md` if present, its `pyproject.toml`, README
   and the documentation relevant to the task.
4. Check that repository's current branch, worktree and upstream before editing.
   Repositories can be on different branches; never assume they are synchronized.
5. Establish the relevant implementation and smallest existing validation
   command from current code. Historical roadmap checkmarks are not proof that
   functionality exists today.

Do not run `pull`, `push`, `checkout`, `clone`, `install`, `normalize`, service
commands or setup scripts merely to orient yourself. These change repositories,
environments or running systems. `repo-status` is not offline/read-only Git
metadata inspection: its fetch operations can fail and prune remote-tracking refs.

## Repository map

Paths below are relative to stackctl's source directory, not to this repository.
Re-read the manifest before using them.

| Manifest name | Checkout path | Responsibility |
|---------------|---------------|----------------|
| `ki-core` | `ki-core` | Shared orchestration and CLI base |
| `kicli-code-assist` | `kicli-code-assist` | Code assistant application |
| `ki-knowledge` | `ki-knowledge` | Knowledge application |
| `ki-knowledge-next` | `ki-knowledge-next` | Django rebuild of ki-knowledge using Wissenswiki |
| `yaml-cfg-wizard` | `yaml_cfg_wizard` | Standalone YAML configuration toolkit |
| `widgetkit` | `widgetkit` | Framework-neutral widget rendering |
| `widgetkit-django` | `widgetkit-django` | Django widget integration |
| `yaml-cfg-wizard-ui` | `yaml-cfg-wizard-ui` | Configuration web UI |
| `wissenswiki-core` | `wissenswiki-core` | Knowledge blocks and standalone web app |
| `wissenswiki-django` | `wissenswiki-django` | Reusable Django knowledge-block app |

Both Wissenswiki projects are Git repositories with HTTPS clone URLs configured
in the sibling manifest.

The installed tool currently resolves its source directory in this order:
`STACKCTL_SRC_DIR`, `[tool.stackctl].src_dir`, the parent of the ecosystem root.
An omitted or empty sibling `path` uses its `name`. In particular, the UI's
commented-out path is not a setting: its manifest currently resolves to
`yaml-cfg-wizard-ui`, not `yaml_cfg_wizard_ui`.

The local stackctl implementation was found at `../stackctl/src/stackctl/`.
It is tooling, not a sibling registered by this manifest. If tool behavior is
in question, locate the currently installed entry point again before relying
on that path. Do not substitute instructions for an unrelated upstream tool.

## Configuration and documentation

- `[tool.stackctl]` selects `ki_ecosystem:load_config` and config key `stack`.
- `ki_ecosystem/config.py` reads `config/defaults/stack.yaml` directly. This hub
  does not currently resolve ki-core profiles or stages.
- `stack.yaml` contains coordination/reference data, not complete application
  launch definitions. Its `ecosystem` list duplicates manifest information;
  it does not replace the manifest for sibling discovery.
- `docs/STACKCTL.md` documents verified tool behavior and operational boundaries.
- `docs/CLI_ARCHITECTURE_ROADMAP.md`, `docs/IMPLEMENTATION_STATUS.md` and
  `docs/YAML_CONFIG_ARCHITECTURE.md` provide cross-project design context.
  Treat phase/status claims as historical until verified in the owning code.
- `docs/ARCHITECTURE.md` contains historical architecture context;
  `docs/DEPLOYMENT.md` describes the polling setup. Verify operational claims against
  `scripts/` and the actual target system.
- Keep only `README.md` as Markdown in the repository root. Put shared ecosystem
  documentation in `docs/` and implementation details in the owning project's
  `docs/`. The discovery file `.github/copilot-instructions.md` stays at its
  standard path and points here. Keep this entry point short and link detailed docs.
- Start Markdown files with YAML front matter (`---`), not metadata tables.
  Use `project`, `agent_project`, `purpose`, `created` and `updated`; keep values
  and comments short. Use `created: null` for unknown dates and `first_tracked`
  for Git evidence. Use `update_reason` for later changes, not as initial purpose.
- Keep reports short and lookup-oriented, preferably a compact table of reason,
  decision, evidence and remaining uncertainty. Link implementation details;
  do not repeat them or add narrative progress logs.

## Change and deployment boundaries

Preserve existing uncommitted work. Scope edits and commits per repository.
Do not bulk-switch branches, install packages, commit or push all siblings as a
side effect of working on one project. Never commit secrets or `.env` files;
check ignore rules before adding configuration files. Do not rewrite Git history
to conceal leaked credentials; revoke them instead.

After code changes, use the owning repository's existing tests/linter/build.
Documentation-only changes do not require application tests.

Deployment uses Git push/pull. The provided systemd timer invokes
`scripts/deploy-polling.sh`, which runs `stackctl pull`; pulling source does not
prove that a service restarted, reloaded successfully or is healthy. Check the
target's timer, logs and application health when deployment is requested.
Do not activate/reconfigure polling or restart services without task scope.
Report whether changes are only local, pushed, or verified live; never imply
that a local edit was deployed.
