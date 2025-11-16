# v2.1 DTO Ground Truth Reference

**Date**: 2025-11-16
**Status**: CANONICAL - All phase plans must match this table

---

## 🎯 HOW TO USE THIS DOCUMENT (For Subagents)

**If you are implementing Phase 1, 4, 5, or 7:**

1. **BEFORE writing any code**: Read the "DTO Structure Table" section below
2. **BEFORE accessing any config field**: Look up the correct pattern in "Field Access Patterns"
3. **WHEN in doubt**: Search this document for the DTO name (e.g., "BarsV2Config")
4. **VALIDATE your code**: Check "Common Mistakes to Avoid" at the bottom

**Key Rule**: EVERY config access MUST use the section field pattern:
- ✅ `config.section.field` (e.g., `raw.experiment.experiment.metadata`)
- ❌ `config.field` (missing section - THIS IS WRONG)

**If your code doesn't match this document, IT IS WRONG. Fix it before proceeding.**

---

## Purpose

This document defines the **single source of truth** for v2.1 DTO structure, naming, and access patterns.

**Referenced by:**
- Phase 1 (2025-11-16-v2.1-phase1-create-dtos.md) - Creates these DTOs
- Phase 4 (2025-11-16-v2.1-phase4-native-compiler.md) - Uses these DTOs in compiler
- Phase 5 (2025-11-16-v2.1-phase5-delete-legacy.md) - Validates only these DTOs remain
- Phase 7 (2025-11-16-v2.1-phase7-documentation.md) - Documents these DTOs

**All phase plans must align with this reference. Any deviations are bugs and must be fixed.**

---

## DTO Structure Table

| YAML File | DTO Class Name | File Location | Root Field | Access Pattern Example |
|-----------|---------------|---------------|------------|------------------------|
| `experiment.yaml` | `ExperimentConfig` | `src/townlet/config/experiment_config.py` | `experiment` | `raw.experiment.experiment.metadata.name` |
| `stratum.yaml` | `StratumConfig` | `src/townlet/config/stratum_config.py` | `stratum` | `raw.stratum.stratum.substrate.type` |
| `environment.yaml` | `EnvironmentConfig` | `src/townlet/config/environment_config.py` | `environment` | `raw.environment.environment.meters` |
| `actions.yaml` | `ActionsConfig` | `src/townlet/config/actions_config.py` | `actions` | `raw.actions.actions.custom_actions` |
| `agent.yaml` | `AgentConfig` | `src/townlet/config/agent_config.py` | `agent` | `raw.agent.agent.brain` |
| `curriculum.yaml` | `CurriculumConfig` | `src/townlet/config/curriculum_config.py` | `curriculum` | `level.curriculum.curriculum.active_vision` |
| `bars.yaml` | `BarsV2Config` | `src/townlet/config/bars_v2_config.py` | `bars` | `level.bars.bars.meters` |
| `affordances.yaml` | `AffordancesV2Config` | `src/townlet/config/affordances_v2_config.py` | `affordances` | `level.affordances.affordances.affordances` |
| `training.yaml` | `TrainingV2Config` | `src/townlet/config/training_v2_config.py` | `training` | `level.training.training.population` |

---

## Section-Root Pattern

**ALL DTOs follow this pattern:**

```python
class SomeSection(BaseModel):
    """The actual config data."""
    version: str
    field1: ...
    field2: ...

class SomeConfig(BaseModel):
    """Root config for some.yaml."""
    some: SomeSection  # Root field matches YAML root key
```

**Access pattern is ALWAYS: `config_instance.root_field.section_field`**

Examples:
- `ExperimentConfig.experiment.metadata` (not `ExperimentConfig.metadata`)
- `BarsV2Config.bars.meters` (not `BarsV2Config.meters`)
- `AffordancesV2Config.affordances.affordances` (not `AffordancesV2Config.affordances`)

---

## RawConfigsV21 Structure

**File Location**: `src/townlet/universe/raw_configs_v21.py` (NOT in config/)

```python
@dataclass(frozen=True)
class CurriculumLevel:
    """Per-level configs."""
    name: str
    curriculum: CurriculumConfig
    bars: BarsV2Config
    affordances: AffordancesV2Config
    training: TrainingV2Config

@dataclass(frozen=True)
class RawConfigsV21:
    """Container for all v2.1 configs."""
    # Shared experiment-level configs
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    agent: AgentConfig

    # Curriculum levels
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path
```

---

## Field Access Patterns

### Experiment-Level Access

```python
# Correct:
raw.experiment.experiment.metadata.name
raw.stratum.stratum.substrate.type
raw.environment.environment.meters
raw.actions.actions.custom_actions
raw.agent.agent.brain

# Wrong:
raw.experiment.metadata.name  # Missing .experiment section
raw.stratum.substrate.type    # Missing .stratum section
```

### Level-Specific Access

```python
level = raw.levels["L1_full_observability"]

# Correct:
level.curriculum.curriculum.active_vision
level.bars.bars.meters
level.affordances.affordances.affordances
level.training.training.population

# Wrong:
level.curriculum.active_vision      # Missing .curriculum section
level.bars.meters                    # Missing .bars section
level.affordances.affordances        # Only one .affordances (needs two!)
level.training.population            # Missing .training section
```

### Vocabulary Validation Pattern

```python
# Canonical vocabulary from environment.yaml
env_meter_names = {m.name for m in raw.environment.environment.meters}
env_affordance_names = {a.name for a in raw.environment.environment.affordances}

# Per-level vocabulary
for level_name, level in raw.levels.items():
    level_meter_names = {m.name for m in level.bars.bars.meters}
    level_affordance_names = {a.name for a in level.affordances.affordances.affordances}
    # Validate: level_meter_names == env_meter_names
```

---

## DTO Naming Convention

**V2 suffix for curriculum-level DTOs only:**
- ✅ `BarsV2Config` - v2.1 has different structure than legacy
- ✅ `AffordancesV2Config` - v2.1 has different structure than legacy
- ✅ `TrainingV2Config` - v2.1 has different structure than legacy

**No V2 suffix for experiment-level DTOs:**
- ✅ `ExperimentConfig` - new in v2.1 (no legacy equivalent)
- ✅ `StratumConfig` - new in v2.1 (no legacy equivalent)
- ✅ `EnvironmentConfig` - v2.1 vocabulary-only version
- ✅ `ActionsConfig` - new in v2.1
- ✅ `AgentConfig` - new in v2.1
- ✅ `CurriculumConfig` - new in v2.1

**Rationale**: V2 suffix marks DTOs that directly replace legacy versions with breaking changes.

---

## File Naming Convention

**Pattern**: `{snake_case}_config.py`

Examples:
- `experiment_config.py` (not `experiment.py`)
- `bars_v2_config.py` (not `bars.py` or `bars_config.py`)
- `affordances_v2_config.py`

---

## Import Patterns

```python
# Experiment-level DTOs
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.actions_config import ActionsConfig
from townlet.config.agent_config import AgentConfig

# Curriculum-level DTOs (note V2 suffix)
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.training_v2_config import TrainingV2Config

# Loader
from townlet.universe.raw_configs_v21 import RawConfigsV21, CurriculumLevel
```

---

## Test Snippets (Canonical)

### Loading All Configs

```python
from pathlib import Path
from townlet.universe.raw_configs_v21 import RawConfigsV21

raw = RawConfigsV21.from_experiment_dir(Path("configs/default_curriculum"))

# Experiment-level access
print(f"Experiment: {raw.experiment.experiment.metadata.name}")
print(f"Substrate: {raw.stratum.stratum.substrate.type}")
print(f"Meters: {[m.name for m in raw.environment.environment.meters]}")

# Level-specific access
l1 = raw.levels["L1_full_observability"]
print(f"Active vision: {l1.curriculum.curriculum.active_vision}")
print(f"Meters: {[m.name for m in l1.bars.bars.meters]}")
print(f"Affordances: {[a.name for a in l1.affordances.affordances.affordances]}")
print(f"Population size: {l1.training.training.population.size}")
```

### Vocabulary Validation

```python
# Get canonical vocabulary
env_meter_names = {m.name for m in raw.environment.environment.meters}
env_affordance_names = {a.name for a in raw.environment.environment.affordances}

# Validate each level
for level_name, level in raw.levels.items():
    level_meter_names = {m.name for m in level.bars.bars.meters}
    level_affordance_names = {a.name for a in level.affordances.affordances.affordances}

    assert level_meter_names == env_meter_names, f"{level_name}: meter mismatch"
    assert level_affordance_names == env_affordance_names, f"{level_name}: affordance mismatch"
```

---

## Multi-Level Compilation Decision

**DECISION**: `compile()` compiles **ALL LEVELS** in one pass (Option A / Multi-level)

```python
# Multi-level compilation
def compile(
    experiment_dir: Path,
    primary_level: str | None = None,
    use_cache: bool = True
) -> CompiledUniverse:
    """Compile all curriculum levels from v2.1 hierarchical structure.

    Args:
        experiment_dir: Path to experiment directory (e.g., configs/default_curriculum)
        primary_level: Which level to use for primary fields (default: first alphabetically)
        use_cache: Whether to use compilation cache

    Returns:
        CompiledUniverse with all_levels populated, primary fields from primary_level
    """
    # Stage 1: Load all configs
    raw = RawConfigsV21.from_experiment_dir(experiment_dir)

    # Select primary level (first alphabetically if not specified)
    if primary_level is None:
        primary_level = sorted(raw.levels.keys())[0]

    # Compile ALL levels
    all_levels_metadata = {}
    for level_name, level in raw.levels.items():
        # Run stages 2-6 for this level
        level_metadata = self._compile_one_level(raw, level, level_name)
        all_levels_metadata[level_name] = level_metadata

    # Stage 7: Emit single CompiledUniverse with all levels
    primary_metadata = all_levels_metadata[primary_level]
    return CompiledUniverse(
        # Primary level fields (for backwards compat)
        observation_spec=primary_metadata.observation_spec,
        action_metadata=primary_metadata.action_metadata,
        metadata=UniverseMetadata(..., level_name=primary_level),
        # ... other primary fields

        # Multi-level support
        experiment_dir=experiment_dir,
        all_levels=all_levels_metadata
    )
```

**Rationale**:
- Enables cross-level vocabulary validation (WHAT vs HOW enforcement)
- Supports runtime level switching via `compiled.get_level(level_name)`
- Enables transfer learning (same obs_dim across levels)
- Single compilation for all levels (efficient caching)
- Matches Phase 3, Phase 7, Phase 8 design

**Usage**:
```python
# Compile all levels, use L1 as primary
compiled = compiler.compile(
    Path("configs/default_curriculum"),
    primary_level="L1_full_observability"
)

# Access different levels at runtime
l1_env = compiled.create_environment(level_name="L1_full_observability")
l2_env = compiled.create_environment(level_name="L2_partial_observability")

# Or use primary level (defaults to L1)
primary_env = compiled.create_environment()
```

---

## Argument Naming Standard

**ALWAYS use `primary_level` in code, never `level_name` for compile()**

❌ **Wrong**: `compile(experiment_dir, level_name="L1")`
✅ **Correct**: `compile(experiment_dir, primary_level="L1")`

**Exception**: `create_environment(level_name=...)` uses `level_name` because it's selecting a level, not designating a primary.

**CLI**: Use `--level` flag (maps to `primary_level` internally)

```bash
# CLI usage
python -m townlet.compiler compile configs/default_curriculum --level L1_full_observability
```

---

## Common Mistakes to Avoid

❌ **Wrong**: `raw.experiment.metadata` (missing section field)
✅ **Correct**: `raw.experiment.experiment.metadata`

❌ **Wrong**: `level.bars.meters` (missing section field)
✅ **Correct**: `level.bars.bars.meters`

❌ **Wrong**: `level.affordances.affordances` (only one nesting)
✅ **Correct**: `level.affordances.affordances.affordances`

❌ **Wrong**: Using `BarsConfig` (legacy name)
✅ **Correct**: Using `BarsV2Config` (v2.1 name)

❌ **Wrong**: `raw_configs_v21.py` in `src/townlet/config/`
✅ **Correct**: `raw_configs_v21.py` in `src/townlet/universe/`

❌ **Wrong**: `compile(experiment_dir, level_name="L1")`
✅ **Correct**: `compile(experiment_dir, primary_level="L1")`

---

**ALL PHASE PLANS MUST MATCH THIS REFERENCE. ANY DEVIATIONS ARE BUGS.**
