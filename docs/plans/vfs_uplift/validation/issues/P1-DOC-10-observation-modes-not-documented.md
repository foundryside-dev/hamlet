# P1-DOC-10: Observation Management Modes Not in User Documentation

**Priority:** P1 (Important - Should Fix)
**Category:** Documentation
**Estimated Effort:** 4 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

VFS observation management modes (`full_auto`, `max_compact`, `full_manual`) are implemented in code but not documented in user-facing guides, making it difficult for users to understand how to control observation space.

**Missing Documentation:**
- What are the three observation modes?
- When to use each mode?
- How to configure them?
- Impact on observation dimensions?
- Examples of each mode in practice?

**Impact:**
- Users don't know these modes exist
- Cannot make informed decisions about observation space control
- May inadvertently create inefficient observation spaces
- Pedagogical value of modes not realized

**Evidence:**
- Agent 7 (Documentation) report, section DOC-10
- Modes implemented in code but only documented in internal design docs
- No user guide or config schema doc mentions them

---

## Current Implementation

**Observation modes control how VFS variables appear in observations:**

### Mode 1: `full_auto` (Default)

**Behavior:**
- ALL VFS variables with `observation: true` are included in observations
- No manual filtering needed
- Observation dim = sum of all observable VFS variables

**Use case:** Quick prototyping, when you want all VFS state visible

**Example:**
```yaml
# vfs_profiles.yaml
agent_profile:
  var1:
    expression: "self.bar.energy"
    observation: true    # ✅ Included
  var2:
    expression: "self.bar.health"
    observation: false   # ❌ Excluded
```

### Mode 2: `max_compact`

**Behavior:**
- Only includes VFS variables that are NOT derivable from other observations
- Removes redundancy (e.g., if `energy_ratio = energy / max_energy`, only include raw meters)
- Minimizes observation space for sample efficiency

**Use case:** Training efficiency, when observation space is a bottleneck

**Example:**
```yaml
# Automatically excludes derived variables if base variables observable
agent_profile:
  energy:
    expression: "self.bar.energy"
    observation: true    # ✅ Included (base variable)
  energy_ratio:
    expression: "self.bar.energy / self.bar.max_energy"
    observation: true    # ❌ Excluded (derivable from energy)
```

### Mode 3: `full_manual`

**Behavior:**
- User explicitly lists which VFS variables to include in observations
- Fine-grained control, no automatic filtering
- Observation dim = only manually specified variables

**Use case:** Advanced users, when you want precise control over observation space

**Example:**
```yaml
# substrate.yaml or training.yaml
observation_config:
  mode: full_manual
  include_vfs:
    - time_of_day         # Only include specific variables
    - energy_efficiency
```

---

## Where to Document

### 1. Config Schema Reference

**File:** `docs/config-schemas/vfs-profiles.md`

Add section:

```markdown
## Observation Management

VFS provides three modes for controlling which variables appear in observations:

| Mode | Description | Use Case |
|------|-------------|----------|
| `full_auto` | All `observation: true` variables included | Quick prototyping |
| `max_compact` | Removes derivable variables | Sample efficiency |
| `full_manual` | User specifies exact variables | Advanced control |

### Configuration

Set mode in `substrate.yaml`:

```yaml
observation_config:
  vfs_mode: full_auto  # or max_compact, full_manual

  # If full_manual, specify variables:
  include_vfs:
    - time_of_day
    - energy_efficiency
```

### Impact on Observation Dimensions

[Table showing how modes affect obs_dim for different configs]
```

### 2. User Guide

**File:** `docs/guides/observation-space-design.md` (NEW)

Create comprehensive guide:

```markdown
# Observation Space Design Guide

## Understanding VFS Observation Modes

When designing your observation space, you have three strategies for including VFS variables...

## Choosing the Right Mode

**Use `full_auto` when:**
- Prototyping a new environment
- You want all VFS state visible to the agent
- Observation space size is not a concern

**Use `max_compact` when:**
- Training is slow due to large observation space
- You want to remove redundant features
- Sample efficiency is critical

**Use `full_manual` when:**
- You need precise control over what agent observes
- Implementing partial observability (POMDP)
- Testing specific ablations

## Examples

### Example 1: Full Auto (L1 - Full Observability)

[Complete config example]

### Example 2: Max Compact (L2 - Efficient Training)

[Complete config example]

### Example 3: Full Manual (L2 - Partial Observability)

[Complete config example]

## Performance Implications

[Table showing obs_dim and training time for each mode]

## FAQ

**Q: Does mode affect what VFS variables are computed?**
A: No. All VFS variables are always computed. Mode only controls which ones appear in observations.

**Q: Can I change mode between curriculum levels?**
A: Yes. Mode is level-specific configuration.
```

### 3. Tutorial / Quick Start

**File:** `docs/tutorials/vfs-observations.md` (NEW)

Step-by-step tutorial:

```markdown
# Tutorial: Controlling VFS Observations

In this tutorial, you'll learn how to control which VFS variables your agent observes.

## Step 1: Define VFS Variables

[Create vfs_profiles.yaml with examples]

## Step 2: Choose Observation Mode

[Configure mode in substrate.yaml]

## Step 3: Verify Observation Dimensions

[Run compiler and check obs_dim]

## Step 4: Experiment with Different Modes

[Switch between modes and observe impact]
```

---

## How to Fix

### Step 1: Add to Config Schema Docs (2 hours)

Update `docs/config-schemas/vfs-profiles.md` with observation modes section.

### Step 2: Create User Guide (1.5 hours)

Write `docs/guides/observation-space-design.md` with comprehensive examples.

### Step 3: Add Examples to Reference Configs (0.5 hours)

Show mode configuration in `docs/config-schemas/reference-config-complete.md`.

---

## Acceptance Criteria

- [ ] Observation modes documented in `vfs-profiles.md`
- [ ] User guide created: `observation-space-design.md`
- [ ] Examples for all three modes included
- [ ] Reference config shows mode configuration
- [ ] Tutorial added (optional but recommended)
- [ ] FAQ section addresses common questions

---

## Files to Create/Modify

1. `docs/config-schemas/vfs-profiles.md` - Add observation modes section
2. `docs/guides/observation-space-design.md` (NEW) - Comprehensive guide
3. `docs/config-schemas/reference-config-complete.md` - Add mode examples
4. `docs/tutorials/vfs-observations.md` (OPTIONAL) - Tutorial

---

## Related Issues

- Related: P1-DOC-6 (reference config missing sections)
- Related: P1-DOC-8 (VFS integration guide outdated)

---

## Notes

- Modes are already implemented in code, just not documented
- This is purely a documentation task, no code changes needed
- Focus on user-facing guides, not internal implementation details
- Include performance implications (obs_dim impact on sample efficiency)
- Consider adding mode selection flowchart/decision tree
