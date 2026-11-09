# Repository instructions

Read and follow [`docs/AGENTS.md`](../docs/AGENTS.md) before starting work. It contains the
ecosystem map, startup checklist, stackctl path rules and operational boundaries.

This repository coordinates independent sibling Git repositories through
`pyproject.toml`. When working in a sibling, also read and follow that
repository's own agent instructions. Use current code and `stackctl --help` as
evidence; do not assume that historical roadmap status or prior chat context is
still accurate.

## Shared skills

The versioned `.github/skills` symlink points to the central `dev_doc/skills`
collection. Before starting a task, review the skill descriptions in
`.github/skills/*/*/SKILL.md` and load every relevant skill. For documentation
work, review all descriptions in `.github/skills/documentation/*/SKILL.md`,
then apply every relevant documentation skill.

If the client does not discover the category-nested skills or cannot load a
skill, read its `SKILL.md` directly before editing. If the link is broken,
report the missing central checkout; do not silently skip the standards or
copy skill definitions into this repository.
