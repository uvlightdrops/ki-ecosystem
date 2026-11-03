---
project: ki-ecosystem
scope: architecture
purpose: Architecture decision for stackctl deployment and access strategy
created: 2026-11-02T10:18:00+01:00
updated: 2026-11-02T10:18:00+01:00
status: in-decision
agent_project: ki-ecosystem
keywords: [stackctl, orchestration, multi-repo, architecture]
---

# Architecture Decision: stackctl Deployment Strategy

## Current Situation

### What Exists
- **stackctl**: Orchestration tool at `/home/flow/dev_flow/stackctl/`
- **Installed via**: Project's venv or Python module
- **Access**: Currently requires `cd` to specific project + `.venv/bin/python -m stackctl`
- **Symlink**: Was in `~/.local/bin/stackctl` (temporarily deleted)
- **Multi-repo need**: Want to coordinate kicli-code-assist, ki-knowledge, ki-ecosystem, etc.

### Current Access Pattern
```bash
# Per-project (current method)
cd /home/flow/dev_flow/kicli-code-assist
.venv/bin/python -m stackctl -t local start

# Global (before symlink deletion)
stackctl -t local start  # from any directory
```

---

## Three Options

### Option A: Global ~/.local/bin Symlink (Current Approach)

**What it does:**
```bash
# ~/.local/bin/stackctl → /home/flow/dev_flow/stackctl/src/stackctl/cli.py
ln -s /home/flow/dev_flow/stackctl/src/stackctl/cli.py ~/.local/bin/stackctl
chmod +x ~/.local/bin/stackctl
```

**Pros:**
- ✅ Works from any directory
- ✅ Simple for single-developer workflow
- ✅ No venv needed
- ✅ Familiar (how it was working)

**Cons:**
- ❌ Brittle: Symlink can break if paths change
- ❌ Not version-controlled (manual setup step)
- ❌ Doesn't scale to multiple developers/machines
- ❌ No dependency management (doesn't ensure stackctl deps installed)
- ❌ cli.py is entry point, but not meant to be executable directly

---

### Option B: Entry Point via Setup.py (Recommended)

**What it does:**
```bash
# In stackctl/setup.py or pyproject.toml
[project.scripts]
stackctl = "stackctl.cli:main"

# Install globally or locally
pip install -e /home/flow/dev_flow/stackctl
# Now available: stackctl (from anywhere)
```

**Pros:**
- ✅ Proper Python packaging (installable)
- ✅ Entry point is explicit and versioned
- ✅ Works across all directories
- ✅ Dependency management automatic
- ✅ Can be distributed/replicated
- ✅ Industry standard (like `pip`, `poetry`, etc.)

**Cons:**
- ⚠️ Requires setup.py update (one-time)
- ⚠️ Installation step needed on new machines
- ⚠️ Need to reinstall on code changes (unless `-e` editable mode)

---

### Option C: ki-ecosystem Central Wrapper

**What it does:**
```bash
# ki-ecosystem provides unified entry point
# ~/.local/bin/kicli → /home/flow/dev_flow/ki-ecosystem/bin/kicli
# Inside: routes to correct tool (stackctl, or others)

kicli stack start          # → stackctl
kicli repo pull            # → git orchestration
kicli deploy production    # → deployment
```

**Pros:**
- ✅ Single unified CLI for all multi-repo operations
- ✅ Central place to manage dependencies
- ✅ Extensible to other tools
- ✅ Makes ki-ecosystem the "hub"
- ✅ Better UX (one command, not project-specific)

**Cons:**
- ⚠️ More complex (wrapper layer)
- ⚠️ Requires coordination between ki-ecosystem and stackctl
- ⚠️ Longer implementation
- ❌ Could add latency (wrapper overhead)

---

## Architecture Implications

### Dependency Model Currently

```
kicli-code-assist/
  ├── venv/ → stackctl (installed as dependency? or external?)
  ├── .venv/bin/python -m stackctl
  └── config/stack.yaml

ki-ecosystem/
  ├── venv/
  └── (doesn't know about stackctl?)
```

### What Should Happen

**Goal**: "stackctl orchestrates all repos under ki-ecosystem"

```
ki-ecosystem/              (the orchestrator hub)
  ├── bin/
  │   ├── kicli           (unified CLI)
  │   └── stackctl        (or symlink/wrapper)
  ├── config/
  │   ├── ecosystem.yaml  (all repos config)
  │   └── stages/
  ├── venv/
  │   └── stackctl dependency installed
  └── stack.yaml          (ecosystem-wide config)

kicli-code-assist/         (one project)
  ├── stack.yaml          (local override)
  └── (calls ki-ecosystem stackctl)

ki-knowledge/              (another project)
  ├── stack.yaml          (local override)
  └── (calls ki-ecosystem stackctl)
```

---

## Recommendation

### Short Term (What You Should Do Now)

**Use Option B**: Proper Python entry point via setup.py

1. **Why**: Solves your immediate problem (global access) without complexity
2. **Setup** (15 minutes):
   ```bash
   cd /home/flow/dev_flow/stackctl
   cat setup.py  # or setup.cfg / pyproject.toml
   # Add entry point if missing:
   # [project.scripts]
   # stackctl = "stackctl.cli:main"
   
   pip install -e .
   stackctl --version  # Test
   ```

3. **Result**: `stackctl` works from any directory

### Medium Term (After This Works)

**Plan for Option C** (ki-ecosystem wrapper) but don't implement yet:

- Document required changes
- Coordinate with ki-ecosystem structure
- Plan integration with ki-knowledge, ki-core, etc.

---

## Decision Matrix

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| **Works from any dir?** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Reproducible?** | ❌ No | ✅ Yes | ✅ Yes |
| **Scalable?** | ❌ No | ✅ Yes | ✅ Yes |
| **Effort** | 5 min | 15 min | 2-3 hours |
| **Right now** | ❌ Brittle | ✅ Solid | ⏳ Future |
| **For ki-ecosystem** | ❌ No | ⚠️ Partial | ✅ Yes |

---

## Immediate Action Plan

### If You Choose Option B (Recommended Now)

1. **Check stackctl structure**
   ```bash
   cd /home/flow/dev_flow/stackctl
   ls -la
   cat setup.py 2>/dev/null || cat pyproject.toml | grep -A 10 "\[project\]"
   ```

2. **Add entry point if needed**
   ```python
   # In setup.py or pyproject.toml
   entry_points={
       "console_scripts": [
           "stackctl=stackctl.cli:main",
       ]
   }
   ```

3. **Install editable**
   ```bash
   cd /home/flow/dev_flow/stackctl
   pip install -e .
   stackctl --help  # Test
   ```

4. **Verify it works**
   ```bash
   cd /tmp  # Any directory
   stackctl -t local status  # Should work
   ```

### If You Want Option A (Quick Workaround, Not Recommended)

```bash
ln -s /home/flow/dev_flow/stackctl/src/stackctl/cli.py ~/.local/bin/stackctl
chmod +x ~/.local/bin/stackctl
stackctl --help  # Test
```

But then document: "TODO: Replace with Option B (proper entry point)"

---

## Future: ki-ecosystem Integration

Once Option B works, plan:

```
ki-ecosystem/
  ├── bin/
  │   └── kicli              ← Unified entry point
  ├── python/
  │   ├── ecosystem.py       ← Main CLI logic
  │   └── commands/
  │       ├── stack.py       ← Delegates to stackctl
  │       ├── repo.py        ← Git orchestration
  │       └── deploy.py      ← Deployment logic
  └── stack.yaml             ← Ecosystem-wide config

Usage:
  kicli stack start              # → stackctl start
  kicli stack status             # → stackctl status
  kicli repo pull                # → ki-ecosystem sync
  kicli deploy [env]             # → deployment orchestration
```

---

## Questions to Answer Before Deciding

1. **Does stackctl have setup.py/pyproject.toml already?**
   - If yes → Option B is 5 minutes
   - If no → Option B is 20 minutes

2. **Is stackctl meant to coordinate all repos or just local?**
   - If all repos → Lean toward Option C long-term
   - If local only → Option B is sufficient

3. **Will other developers need this?**
   - If yes → Option B/C required
   - If just you → Option A works

4. **How many repos will stackctl coordinate?**
   - Current: kicli-code-assist (1)
   - Future: kicli-code-assist + ki-knowledge + ki-core + ki-ecosystem (4+)
   - More repos → Stronger case for Option C

---

## My Recommendation Summary

🎯 **For You Right Now**:
- **Do**: Implement Option B (15 min setup)
- **Result**: `stackctl` works from anywhere, properly installed
- **Next**: Document for next developer

🚀 **For ki-ecosystem Long-term**:
- **Plan**: Option C (unified CLI wrapper)
- **Timeline**: After stackctl stabilized (Phase 2-3)
- **Benefit**: Single entry point for all multi-repo operations

---

**Status**: Ready for decision  
**Next Step**: Choose option, implement, test  
**Effort**: 15 minutes (Option B) or 5 minutes (Option A workaround)

Tell me which option you prefer and I'll implement it!
