# `transition_rules` declaration

> ✅ **Re-cut 2026-10-31 (VFS round 2, WP17 S8).** The family was `social_residue`; the rule
> carried a required `reads` list the compiler never checked and a three-valued `kind` that
> changed only a telemetry label. All three are gone: a rule's reads are **derived from its
> expression and condition**, a rule has no kind, and the family is named for what it is — the
> general declarative per-tick VFS dynamic. The old spellings fail at parse (see "Failure modes").
>
> One caveat, not a defect: the example variables `public_reputation`, `was_observed` and
> `chosen_action` are **not declared in any shipped pack**. Read them as illustrative names,
> and declare your own before copying an example. There is no `pair` scope (VFS WP15, owner
> ruling S1: the batch is N independent single-agent worlds), so no rule relates two agents.

---
## AI-Friendly Frontmatter

**Purpose**: Declarative per-tick transition rules — condition-gated writes to VFS variables — compiled into the VTC transition schedule

**When to Read**: Authoring any "state changes every tick when ..." mechanic — decay, accumulation, social traces (trust damage, reputation, sanctions), wear — or debugging why a rule does or does not fire

**AI-Friendly Summary**:
The pack-scope `transition_rules` declaration (conventionally `<config_pack>/transition_rules.yaml`) is the authoring surface for VTC transition rules. Each rule declares a `phase`, an optional `condition`, and one or more writes to `global`, `agent` or `affordance` VFS variables or to meters (`bar.<name>`), executed by `env.step` at the declared phase (canonically `apply_transition_rules`). The declaration is validated at load by a no-defaults DTO (`townlet.config.transition_rules_config.TransitionRulesConfig`, `extra="forbid"`): unknown or typo'd keys fail at parse, and the behavioural fields `condition`, `clamp`, `effect` must be set explicitly (`null` included). What a rule reads is derived from its ASTs at compile (`CompiledVTCTransitionRule.reads`); masking follows the target variable's declared scope, never an authored annotation; telemetry identifies a rule by its `id`.

**Reading Strategy**:
- **Quick Reference**: "Field Reference" below
- **Examples**: `docs/architecture/VFS.md` §14.3, §16.4, §20.7 (every example, and the one below, is compiled and stepped in a scratch copy of `configs/default_curriculum` by `tests/test_townlet/unit/config/test_vfs_doc_transition_rule_examples.py`, which checks that each write moves its target)

**Related Documents**:
- `docs/architecture/VFS.md` §16.3 (semantics, effect vocabulary)
- `docs/config-schemas/variables.md` - VFS variable scopes (`global`, `agent`, `affordance`) and the phase order
- `docs/config-schemas/expressions.md` - expression language used by `condition` / `expression`

---

**Scope**: Optional pack-scope declaration. Its bare shape is recognized by content — a document
whose root carries the `transition_rules` key — so the filename is transport; rule IDs are
unique across fragments in the scope, not merely within a file.
See [declaration discovery](declarations.md).

**Schema**: `townlet.config.transition_rules_config.TransitionRulesConfig`

**Compiled by**: `UniverseCompiler` → `compile_vtc_transition_rules` → `VTCTransitionSchedule.transition_rule_program`, executed by `VTCTransitionRunner` at each rule's phase inside `env.step`. The compiled program participates in `transition_graph_hash` (and therefore `vfs_hash`), so adding or editing a rule changes checkpoint provenance. The hash is over the rule's declared fields with `expression` and `condition` as canonical ASTs: a respelling that parses identically is the same rule; the derived `reads` are not hashed because the ASTs already are.

## File Structure

```yaml
version: "1.0"            # required, literal
transition_rules:         # required list (may be empty, but say so explicitly)
  - id: "seen_stealing_damages_reputation"
    phase: "apply_transition_rules"
    condition: "was_observed and chosen_action == STEAL"   # or null
    writes:
      - variable_id: "public_reputation"
        expression: "-0.15"
        composition: "additive_delta"
        condition: null                # combined (AND) with the rule condition when set
        clamp: [0.0, 1.0]              # or null
        effect: "reputation_delta"     # effect label, or null
```

The compiler derives this rule's reads as `("chosen_action", "was_observed")` — the
variables its condition names (the expression is a literal). A rule reads a variable by its
bare id and a meter as `bar.<name>` (one spelling per reference, VFS round-2 S5; a write's
`variable_id` naming a meter is `bar.<name>` too, and the rule commits to the meter exactly as
an action write does: masked by its world's activity, clamped by the write's `clamp`, then held
to the meter's declared bounds when its phase commits, so no later phase, cascade or effect reads
it out of bounds; `clamp_and_validate` re-asserts the bounds at the end of the transition); reads resolve to storage names through the
one resolver, an old spelling (`vfs.x`, `self.vfs.x`, `target.bar.m`, a bare meter name)
refuses naming the one to write, and an expression naming nothing declared refuses, so a rule
cannot claim to read what does not exist.
When a rule reads an *expression* variable, the compiler inlines that variable's expression
into the rule's AST first (WP17 S4), so the derived reads name the **stored** state the rule
actually reads — a condition `scaled_public > 0.0` over `scaled_public: public_state *
immutable_scale` derives `("immutable_scale", "public_state")`, not `("scaled_public",)`.

## Field Reference

### Rule (`transition_rules[]`)

| field | required | notes |
|---|---|---|
| `id` | yes | unique across pack-scope transition declarations; the telemetry label is `id:effect` (or `id:variable_id` when `effect` is null) |
| `phase` | yes | canonically `apply_transition_rules`; writes inherit it; any phase in the closed graph is admitted, except that a write to a meter must run at `clamp_and_validate` or earlier (a meter write is held to its bounds at its phase commit, and the end-of-transition bounds invariant runs there) |
| `condition` | yes, nullable | rule-level gate; `null` = unconditional |
| `writes` | yes, non-empty | see below |
| `priority` | no (computed) | defaults to declaration order |

### Write (`writes[]`)

| field | required | notes |
|---|---|---|
| `variable_id` | yes | a declared VFS variable by its bare id, or a meter as `bar.<name>` (compile-time checked) |
| `expression` | yes | `additive_delta` expressions are deltas, not post-update values |
| `composition` | yes | `WriteSpec`'s vocabulary minus the action-only occupancy claims: `overwrite`, `additive_delta`, `multiplicative_modifier`, `min`, `max`, `clamp`, `priority_write`, `last_write_wins`; `claim_if_free`/`capacity_claim` fail at parse |
| `condition` | yes, nullable | ANDed with the rule condition |
| `clamp` | yes, nullable | `[low, high]` post-write bounds; refused on a `bool` or reference target, which has no numeric value to bound |
| `effect` | yes, nullable | vocabulary label (see VFS.md §16.3 table); used in the derived telemetry label |
| `phase`, `priority`, `telemetry_label` | no (computed) | derived from the rule when omitted |

## Failure modes (by design)

- Unknown/typo'd key anywhere → load error naming the key (`extra="forbid"`), with the
  declaration's `file:line`.
- **`reads:` on a rule** → load error (`[LOAD_ERROR] Invalid transition_rules declaration
  (...reads): Extra inputs are not permitted`). Reads are derived; there is nothing to author.
- **`kind:` on a rule** → the same load error. There is one rule family.
- **A `social_residue:` document** (the old family name) → `[DECLARATION_UNKNOWN] Unknown
  declaration fields: ['social_residue', 'version']` at the document's `file:line`. It is not
  an alias.
- Omitting `condition`/`clamp`/`effect` → load error; write `null` to mean "none".
- `variable_id` naming no declared variable or meter → compile error (`UAC-STATIC-WRITE`, "... names no
  variable, meter or item state a transition write or rule can read"), at the rule's `file:line`.
- An expression or condition naming an undeclared variable → compile error (`VTC-WRITE-TYPE`,
  unknown identifier).
- The removed write-level `target` role annotation and `scope` masking annotation → load
  error as unknown keys. A write is masked by its target's declared scope: every scope has
  one row (or, for `affordance`, one row per affordance) per world, and a world's rows are
  written while that world's agent is active (S1).
- An expression or condition whose shape does not fit the target scope → compile error
  (`VTC-WRITE-TYPE`; rules in [variables.md](variables.md#transition-phases-and-evaluation-order)).
- A write to a variable that carries an `expression` → compile error (`UAC-STATIC-WRITE`),
  naming both the write and the declaration.
- A write to a meter (`bar.<name>`) scheduled after `clamp_and_validate` → compile error
  (`UAC-STATIC-WRITE`): the meter would escape its declared bounds. A write meant to end the
  episode this tick belongs at `apply_transition_rules`, which runs before
  `evaluate_terminal_conditions`.
- A `clamp` on a `bool`, `agent_ref`, `item_ref`, `affordance_ref` or `effect_ref` target →
  compile error (`VTC-WRITE-TYPE`): a clamp bounds a number, and a reference's number is a row.
- A value that reads state (a variable, a meter, `agent_id`) written into a vector or tensor
  target → compile error (`VTC-WRITE-TYPE`): it would spread one number over every element
  implicitly. A constant fills every element; action writes follow the same rule.
