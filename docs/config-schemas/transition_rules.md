# transition_rules.yaml Configuration

> ✅ **Restored to the live tree 2026-08-26 — verified accurate. Its flagship example both parses AND compiles**, which is the bar the other schema docs fail.
>
> One caveat, not a defect: the example variables `trust`, `observer_mask` and `chosen_action`
> are **not declared in `configs/default_curriculum`**. Pair-scoped `trust` ships only in
> `configs/L5_multi_agent` and `configs/trial_o_bidding_blind`; `observer_mask` and
> `chosen_action` have no config hits anywhere. Read them as illustrative names, and declare
> your own before copying an example.


---
## AI-Friendly Frontmatter

**Purpose**: Declarative social-residue (relationship/norm) rules compiled into the VTC transition schedule

**When to Read**: Authoring "action leaves a social trace" mechanics — trust damage, obligations, reputation, sanctions — or debugging why a social-residue rule does or does not fire

**AI-Friendly Summary**:
`transition_rules.yaml` is the pack-root authoring surface for VTC social-residue rules. Three rule kinds (`visibility_effect`, `social_residue`, `institutional_rule`) declare condition-gated writes to VFS variables (typically pair-scope, e.g. `trust[i, j]`), executed in the `apply_social_residue_effects` phase inside `env.step`. The file is validated at load by a no-defaults DTO (`townlet.config.transition_rules_config.TransitionRulesConfig`, `extra="forbid"`): unknown or typo'd keys fail at parse, and the behavioural fields `condition`, `clamp`, `effect`, `scope` must be set explicitly (`null` included). Direction (observer→actor) is carried by declared pair-scope data in `condition`/`expression`, never by a role annotation.

**Reading Strategy**:
- **Quick Reference**: "Field Reference" below
- **Examples**: `docs/architecture/VFS.md` §14.3, §16.4 (pinned to the shipped grammar by `tests/test_townlet/unit/config/test_vfs_doc_social_residue_examples.py`)

**Related Documents**:
- `docs/architecture/VFS.md` §16.3 (semantics, effect vocabulary, directionality)
- `docs/config-schemas/variables.md` - VFS variable scopes (`pair`, `agent`, ...)
- `docs/config-schemas/expressions.md` - expression language used by `condition` / `expression`

---

**Location**: `<config_pack>/transition_rules.yaml` (experiment-level, optional file)

**Schema**: `townlet.config.transition_rules_config.TransitionRulesConfig`

**Compiled by**: `UniverseCompiler` → `compile_vtc_social_residue_rules` → `VTCTransitionSchedule.social_residue_program`, executed by `VTCTransitionRunner` in the `apply_social_residue_effects` phase of `env.step`. The compiled program participates in `transition_graph_hash` (and therefore `vfs_hash`), so adding or editing a rule changes checkpoint provenance.

## File Structure

```yaml
version: "1.0"            # required, literal
social_residue:           # required list (may be empty, but say so explicitly)
  - id: "seen_stealing_damages_trust"
    kind: "visibility_effect"          # visibility_effect | social_residue | institutional_rule
    phase: "apply_social_residue_effects"
    reads: ["chosen_action", "observer_mask", "trust"]
    condition: "observer_mask and chosen_action == STEAL"   # or null
    writes:
      - variable_id: "trust"
        expression: "-0.15"
        composition: "additive_delta"
        condition: null                # combined (AND) with the rule condition when set
        clamp: [0.0, 1.0]              # or null
        effect: "trust_delta"          # relationship-effect label, or null
        scope: "pair"                  # pair | agent | null (null = infer from tensor shape)
```

## Field Reference

### Rule (`social_residue[]`)

| field | required | notes |
|---|---|---|
| `id` | yes | unique across the file; appears in telemetry labels |
| `kind` | yes | `visibility_effect` \| `social_residue` \| `institutional_rule` |
| `phase` | yes | canonically `apply_social_residue_effects`; writes inherit it |
| `reads` | yes, non-empty | variables the rule reads; directionality lives here as pair-scope data |
| `condition` | yes, nullable | rule-level gate; `null` = unconditional |
| `writes` | yes, non-empty | see below |
| `priority` | no (computed) | defaults to declaration order |

### Write (`writes[]`)

| field | required | notes |
|---|---|---|
| `variable_id` | yes | must be a declared VFS variable (compile-time checked) |
| `expression` | yes | `additive_delta` expressions are deltas, not post-update values |
| `composition` | yes | same vocabulary as `WriteSpec` (`additive_delta`, `overwrite`, ...) |
| `condition` | yes, nullable | ANDed with the rule condition |
| `clamp` | yes, nullable | `[low, high]` post-write bounds |
| `effect` | yes, nullable | vocabulary label (see vfs.md §16.3 table); used in derived telemetry |
| `scope` | yes, nullable | `pair` masks by the symmetric active-agent mask; `agent` for agent vectors; `null` infers from shape |
| `phase`, `priority`, `telemetry_label` | no (computed) | derived from the rule when omitted |

## Failure modes (by design)

- Unknown/typo'd key anywhere → load error naming the key (`extra="forbid"`).
- Omitting `condition`/`clamp`/`effect`/`scope` → load error; write `null` to mean "none".
- `variable_id` not a declared VFS variable → compile error (`targets unknown VFS variable`).
- The removed write-level `target` role annotation → rejected with a pointer to vfs.md §16.3.
