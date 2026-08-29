# Affordances Configuration

> ⛔ **Restored to the live tree 2026-08-26 — this document describes a schema that IS NOT WIRED. Nothing here parses as written.**
>
> Verified 2026-08-26. The real DTO is `AffordanceParamConfig`
> (`src/townlet/config/affordances_v2_config.py`) and its **complete** field set is:
>
> `costs` · `costs_per_tick` · `deployment` · `duration_ticks` · `interaction_type` ·
> `interactions` · `name` · `opening_hours`
>
> Because the DTO uses `ConfigDict(extra="forbid")`, **every key this doc documents that is not
> in that list is refused at parse time.** In particular:
>
> - **`id:` is not a field — the identity field is `name:`.**
> - **`effect_pipeline:` is not a field — the real key is `interactions:`.**
> - **`capabilities:` is not a field.** `src/townlet/config/capability_config.py` defines six
>   Capability DTOs (`cooldown`, `meter_gated`, `prerequisite`, `probabilistic`,
>   `skill_scaling`, …) that **nothing imports** — grep finds zero importers outside the module
>   itself. It is dead declared surface, unreachable from any pack. Tracked as
>   `hamlet-6b24c0bd83`, which also notes that `effects.md` Example 8 documents an
>   affordance-scope `on_cooldown` pattern with no runtime gate consulting it.
> - **The error strings and codes quoted here are invented.** `UAC-VAL-010` / `-011` / `-012`
>   appear 3× in this document and **0×** anywhere in `src/`. Do not search for them.
>
> Tracked as `hamlet-8c2da322aa`. Use `configs/default_curriculum/levels/*/affordances.yaml` as
> the working reference until this
> is rewritten.


## Capability Validation Rules

The Universe Compiler validates affordance capabilities to ensure configuration correctness at compile time.

### Prerequisite Capabilities (UAC-VAL-010)

**Rule**: `PrerequisiteCapability.required_affordances` must only reference affordances that exist in `affordances.yaml`.

**Example - Valid**:
```yaml
affordances:
  - id: "Foundation"
    name: "Foundation Course"
    effect_pipeline:
      on_completion:
        - meter: energy
          amount: 0.1

  - id: "Advanced"
    name: "Advanced Course"
    capabilities:
      - type: prerequisite
        required_affordances: ["Foundation"]  # Valid - Foundation exists
    effect_pipeline:
      on_completion:
        - meter: energy
          amount: 0.2
```

**Example - Invalid**:
```yaml
affordances:
  - id: "Advanced"
    name: "Advanced Course"
    capabilities:
      - type: prerequisite
        required_affordances: ["NonExistent"]  # ERROR: NonExistent does not exist
    effect_pipeline:
      on_completion:
        - meter: energy
          amount: 0.2
```

**Error Message**: `Prerequisite affordance 'NonExistent' does not exist in affordances.yaml`

### Probabilistic Capabilities (UAC-VAL-011)

**Rule**: `ProbabilisticCapability` affordances must define both `on_completion` (success path) and `on_failure` (failure path) in their effect pipeline.

**Example - Valid**:
```yaml
affordances:
  - id: "Casino"
    name: "Slot Machine"
    capabilities:
      - type: probabilistic
        success_probability: 0.3
    effect_pipeline:
      on_completion:  # Success path
        - meter: money
          amount: 0.5
      on_failure:     # Failure path
        - meter: money
          amount: -0.1
```

**Example - Invalid**:
```yaml
affordances:
  - id: "Casino"
    name: "Slot Machine"
    capabilities:
      - type: probabilistic
        success_probability: 0.3
    effect_pipeline:
      on_completion:
        - meter: money
          amount: 0.5
      # ERROR: Missing on_failure - what happens when the 70% failure case occurs?
```

**Error Message**: `Probabilistic affordance 'Casino' should define both success and failure effects. Missing: on_failure (failure path)`

**Rationale**: Probabilistic affordances have two distinct outcomes. Both must be explicitly defined to avoid ambiguity and ensure reproducible behavior.

### Skill Scaling Capabilities (UAC-VAL-012)

**Rule**: `SkillScalingCapability.skill` must reference an existing meter defined in `bars.yaml`.

**Example - Valid**:
```yaml
# bars.yaml
bars:
  - name: fitness
    range: [0.0, 1.0]
    # ... other fields

# affordances.yaml
affordances:
  - id: "Training"
    name: "Gym Training"
    capabilities:
      - type: skill_scaling
        skill: fitness  # Valid - fitness meter exists
        base_multiplier: 0.5
        max_multiplier: 2.0
    effect_pipeline:
      on_completion:
        - meter: fitness
          amount: 0.1
```

**Example - Invalid**:
```yaml
affordances:
  - id: "Training"
    name: "Gym Training"
    capabilities:
      - type: skill_scaling
        skill: nonexistent_meter  # ERROR: No such meter
        base_multiplier: 0.5
        max_multiplier: 2.0
    effect_pipeline:
      on_completion:
        - meter: fitness
          amount: 0.1
```

**Error Message**: `Skill scaling capability references non-existent meter 'nonexistent_meter'. Valid meters: ['energy', 'fitness', 'health', ...]`

**Rationale**: Skill scaling modifies effects based on a meter's value. The meter must exist for the scaling to function.

## See Also

- [The Universe Compiler](../architecture/COMPILER.md) - Full compiler pipeline documentation (design history: `../architecture/archive/COMPILER_ARCHITECTURE.md`)
- [Training Configuration](./training.md) - Training hyperparameters and reward strategies
- [Variables Reference](./variables.md) - VFS configuration guide
