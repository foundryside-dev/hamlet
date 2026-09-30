# enabled_actions Configuration

> ⚠️ **Restored to the live tree 2026-08-26 — correct on action composition, wrong about WHERE the vocabulary lives.**
>
> Cited by `CLAUDE.md` §"Action Space" and `docs/architecture/STRATA.md` §5 as the reference for
> enabled actions and action labels.
>
> **Action vocabulary is pack-scoped.** `configs/default_curriculum/actions.yaml` is a
> conventional transport example; the compiler discovers its `actions:` declaration by
> content. All levels share that vocabulary. A separate global config directory is not a
> semantic authority.
>
> **Do not quote a per-substrate action count from this file.** The action space is *composed* —
> substrate movement actions (a function of substrate type *and* declared parameters such as
> `diagonals`) plus custom actions — under the ordering contract in `substrate/base.py`:
> movement, then `INTERACT` at `[-2]`, then `WAIT` at `[-1]`. Ask the compiled artifact.


**Purpose**: Control which actions from global vocabulary are available in this config.

**Location**: The required level-scope `training:` declaration → `training.enabled_actions`.
`training.yaml` and pack-scope `actions.yaml` are conventions; keep their existing wrappers in
arbitrarily named nested `.yaml`/`.yml` documents. See [declaration discovery](declarations.md).

**Pattern**: All curriculum levels share the same action vocabulary (same `action_dim`).
Disabled actions are masked out at runtime but still occupy action IDs, so checkpoints stay compatible.
Set `enabled_actions: null` (or omit the field) to enable the entire vocabulary, or use an explicit list to gate
actions per config. Passing an empty list intentionally disables every action (useful for curriculum tests).

## Example

### Pack-scope vocabulary (`actions:` declaration)

```yaml
custom_actions:
  - name: "REST"
  - name: "MEDITATE"
  - name: "TELEPORT_HOME"
  - name: "SPRINT"
```

Total actions: 6 substrate (Grid2D) + 4 custom = **10 actions**

### Occupancy writes (affordance contention)

A custom action in the pack's `actions.yaml` may bind an affordance and declare
VFS transition writes. Claim compositions (`claim_if_free`, `capacity_claim`)
target the bound affordance's registry row and resolve contention
deterministically in `resolve_affordance_access_and_occupancy` during
`env.step`:

```yaml
custom_actions:
  - name: "CLAIM_BED"
    description: "Claim the bed if it is free"
    enabled_by_default: true
    source_affordance: "SLEEP"        # must name a declared affordance
    writes:
      - variable_id: "occupied_by"    # affordance-scoped VFS variable
        expression: "agent_id"
        condition: null
        composition: "claim_if_free"
        phase: "resolve_affordance_access_and_occupancy"
        priority: 0
        clamp: null
        telemetry_label: "claim_bed_occupancy"
```

Compile-time guarantees: a claim write without `source_affordance` is rejected
at parse; an unknown affordance name or unknown write target is rejected at
compile. See `docs/architecture/VFS.md` §13.2 for the contention semantics.

### L0_0_minimal/training.yaml (excerpt)

```yaml
training:
  device: cuda
  max_episodes: 500
  # ... other hyperparameters ...
  enabled_actions:
    - "UP"
    - "DOWN"
    - "LEFT"
    - "RIGHT"
    - "INTERACT"
    - "WAIT"
    - "REST"
```

**Result**: 7 enabled, 3 disabled, action_dim = 10
**Live reference**: `configs/default_curriculum/levels/L0_0_minimal/training.yaml`

### L1_full_observability/training.yaml (excerpt)

```yaml
training:
  # ...
  enabled_actions:
    - "UP"
    - "DOWN"
    - "LEFT"
    - "RIGHT"
    - "INTERACT"
    - "WAIT"
    - "REST"
    - "MEDITATE"
```

**Result**: 10 enabled, 0 disabled, action_dim = 10
**Live reference**: `configs/default_curriculum/levels/L0_5_dual_resource/training.yaml`

## Checkpoint Transfer

Both L0 and L1 have **action_dim = 10**, so checkpoints transfer!

L0 Q-network outputs 10 Q-values (3 disabled actions get masked).
L1 Q-network outputs 10 Q-values (all actions available).

**Same architecture → checkpoint compatible.**

## Implementation

**Phase 1 (Current)**: No formal DTO validation. Configs manually specify enabled_actions.

**Phase 2 (TASK-004A)**: TrainingConfig Pydantic DTO validates `enabled_actions` (duplicates, empty entries) and the
compiler validates names against the global vocabulary.

## Best Practices

1. **Define the pack-scope action vocabulary first** (`actions:` declaration)
2. **Freeze vocabulary** before training starts (adding actions breaks checkpoint transfer)
3. **Enable progressively** across curriculum (L0 → L1 → L2 adds more actions)
4. **Test action_dim** matches across all configs (use integration tests)
5. **Document disabled actions** in comments (explain why not enabled yet)

## Validation (Future - TASK-004A)

TrainingConfig + Stage 1 validation enforce:
- Entries are non-empty, deduplicated strings (trimmed automatically)
- All listed names must exist in the combined substrate + pack-scope action vocabulary
- Compiler raises `[UAC-ACT-001]` with file/line context when a name is invalid

## Migration Checklist

1. Add an explicit `enabled_actions` list under each level's `training:` declaration (see `configs/default_curriculum/levels/L0_0_minimal/training.yaml`).
2. Keep the list ordered and documented (comments explain why certain custom actions stay disabled).
3. Run `uv run pytest tests/test_townlet/unit/universe/test_raw_configs.py` to ensure Stage 1 sees the new mask and that action metadata reflects the intended unlocks.
