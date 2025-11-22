# P1-DOC-8: VFS Integration Guide Outdated (Phase 1 Schema)

**Priority:** P1 (Important - Should Fix)
**Category:** Documentation
**Estimated Effort:** 1 day
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The VFS integration guide (`docs/vfs-integration-guide.md`) still describes Phase 1 VFS with level-scoped `variables_reference.yaml`, not the current Phase 2 VFS profiles system with experiment-level `vfs_profiles.yaml`.

**Outdated Content:**
- Describes `variables_reference.yaml` at level scope ❌
- Shows inline item variables in variables_reference.yaml ❌
- Missing VFS profiles (global/agent/item) ❌
- Missing mark-and-sweep evaluation mode ❌
- Missing VFSEvaluator runtime integration ❌

**Impact:**
- Users following guide will create invalid configs
- Confusion about experiment vs level scoping
- Missing critical Phase 2 features (profiles, runtime evaluation)

**Evidence:**
- Agent 7 (Documentation) report, section DOC-8
- Agent 8 (Breaking Changes) noted outdated docs
- File: `docs/vfs-integration-guide.md` (last updated Phase 1)

---

## What Needs Updating

### 1. Schema Migration (Phase 1 → Phase 2)

**Old (Phase 1):**
```yaml
# configs/L1_example/variables_reference.yaml
variables:
  global:
    time_of_day:
      type: float
      default: 0.0
  agent:
    energy_efficiency:
      type: float
      default: 1.0
  item:  # ❌ Item scope was removed
    durability:
      type: float
      default: 1.0
```

**New (Phase 2):**
```yaml
# configs/default_curriculum/vfs_profiles.yaml
version: "2.1"

global_profile:
  time_of_day:
    expression: "(step % 24) / 24.0"
    observation: true

agent_profile:
  energy_efficiency:
    expression: "self.bar.energy / self.bar.max_energy"
    observation: true

item_profiles:
  sword:
    durability:
      initial_value: 1.0
      observation: true
```

### 2. Runtime Evaluation

**Add section:**
- VFSEvaluator class and mark-and-sweep mode
- How VFS variables are evaluated at runtime
- Dependency ordering (topological sort)
- Performance characteristics

### 3. VFS Profiles Concept

**Add section:**
- What are profiles (global/agent/item)
- Why experiment-level (reusable across levels)
- How items reference profiles by name
- Profile-driven item VFS allocation

---

## How to Fix

### Step 1: Restructure Document (4 hours)

**File:** `docs/vfs-integration-guide.md`

New structure:

```markdown
# VFS Integration Guide

## Overview

The Variable & Feature System (VFS) provides declarative state space configuration for HAMLET experiments.

**Key Concepts:**
- **Experiment-level**: `vfs_profiles.yaml` defines variables once, reused across curriculum
- **Profiles**: Global, agent, and item-specific variable definitions
- **Expression-based**: Variables computed via expressions (not static defaults)
- **Runtime evaluation**: Mark-and-sweep dependency resolution

## Phase 2 Architecture (Current)

### File Structure

```
configs/my_experiment/
├── vfs_profiles.yaml    # Experiment-level VFS definitions
├── items.yaml           # Items reference profiles by name
└── levels/
    └── L1_example/
        ├── substrate.yaml
        ├── bars.yaml
        └── ...
```

### VFS Profiles (`vfs_profiles.yaml`)

[Examples with global_profile, agent_profile, item_profiles]

### Runtime Evaluation

VFS variables are evaluated every environment step:

1. **Parse**: Expressions compiled to AST at compile time
2. **Order**: Topological sort resolves dependencies
3. **Evaluate**: Mark-and-sweep execution (or eager mode)
4. **Observe**: Values included in observations if `observation: true`

### Item VFS Integration

Items use `vfs_profile` field to reference profiles:

```yaml
# items.yaml
item_types:
  sword:
    vfs_profile: "sword"  # References item_profiles.sword in vfs_profiles.yaml
```

## Migration from Phase 1

[If you have old configs with level-scoped variables_reference.yaml...]

## Advanced Topics

- Dependency graphs and circular detection
- Performance tuning (eager vs mark-and-sweep)
- Observation management modes
- Type system integration
```

### Step 2: Add Code Examples (2 hours)

Show how to:
- Create vfs_profiles.yaml from scratch
- Reference item profiles in items.yaml
- Access VFS variables in effects (`target.vfs.durability`)
- Use VFS in DAC reward functions

### Step 3: Update Diagrams (1 hour)

If document has diagrams, update to show:
- New file structure (experiment vs level)
- VFS evaluation pipeline
- Profile-driven item allocation

### Step 4: Test Examples (1 hour)

Ensure all code examples in the guide actually work:

```bash
# Create test config from examples in guide
mkdir -p /tmp/vfs_guide_test/
# ... copy examples from guide ...

# Verify it compiles
python -m townlet.compiler compile /tmp/vfs_guide_test/
```

---

## Acceptance Criteria

- [ ] Document describes Phase 2 VFS (vfs_profiles.yaml, profiles)
- [ ] No references to level-scoped variables_reference.yaml
- [ ] Runtime evaluation section added (VFSEvaluator, mark-and-sweep)
- [ ] Item VFS profile integration documented
- [ ] Migration guide from Phase 1 included (optional)
- [ ] All code examples tested and working
- [ ] Diagrams updated (if present)

---

## Files to Modify

1. `docs/vfs-integration-guide.md` - Complete rewrite for Phase 2
2. `docs/diagrams/vfs-architecture.png` (optional) - Update if exists

---

## Optional Enhancements

### Add Troubleshooting Section

Common errors and solutions:
- "variables_reference.yaml not found" → Use vfs_profiles.yaml at experiment level
- "Item scope forbidden" → Use item_profiles instead
- "Circular dependency detected" → Show how to fix

### Add Best Practices

- When to use global vs agent vs item profiles
- Expression performance tips
- Observation management strategies

---

## Related Issues

- Related: P1-DOC-6 (reference config missing sections)
- Related: P1-DOC-10 (observation modes not documented)
- Blocks: User onboarding, Phase 2 VFS adoption

---

## Notes

- This is a user-facing doc, so clarity is critical
- Use realistic examples from actual curriculum levels
- Consider adding a "Quick Start" section at the top
- Link to schema docs for detailed field references
- May want to deprecate and archive old guide as `docs/old-plan/vfs-integration-guide-phase1.md`
