# v2.1 DTO Ground Truth Reference

**Date**: 2025-11-16
**Status**: CANONICAL - All phase plans must match this table

---

## Purpose

This document defines the **single source of truth** for v2.1 DTO structure, naming, and access patterns. All phase plans (1-7) must align with this reference.

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

**DECISION**: `compile()` compiles **ONE LEVEL AT A TIME** (Phase 4 approach)

```python
# Single-level compilation
def compile(experiment_dir: Path, level_name: str | None = None) -> CompiledUniverse:
    """Compile one curriculum level from v2.1 hierarchical structure."""
    raw = RawConfigsV21.from_experiment_dir(experiment_dir)

    # Select level (first alphabetically if not specified)
    if level_name is None:
        level_name = sorted(raw.levels.keys())[0]

    level = raw.levels[level_name]

    # Run stages 2-7 for this level only
    ...

    # Return CompiledUniverse for this level
    return CompiledUniverse(...)
```

**Multi-level support**: Caller compiles each level separately if needed. Future enhancement could add `compile_all_levels()` that populates `CompiledUniverse.all_levels`.

**Rationale**:
- Simpler implementation (Phase 4)
- Clear separation of concerns
- Cache works per-level
- Multi-level runtime can be added later if needed

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

---

**ALL PHASE PLANS MUST MATCH THIS REFERENCE. ANY DEVIATIONS ARE BUGS.**
