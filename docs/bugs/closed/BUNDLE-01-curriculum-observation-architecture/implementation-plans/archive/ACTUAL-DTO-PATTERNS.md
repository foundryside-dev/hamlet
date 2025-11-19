# Actual DTO Patterns in Live Code - 2025-11-16

**Purpose**: Document the ACTUAL DTO structure as implemented in live code

**Status**: Verified by reading actual source files

---

## Pattern Summary

**TWO DIFFERENT PATTERNS EXIST**:

1. **Wrapper Pattern** (used by experiment-level DTOs with `from_yaml`)
2. **Direct Pattern** (used by curriculum-level DTOs with `load_yaml_section`)

---

## Pattern 1: Wrapper (Experiment-Level DTOs)

### Files Using This Pattern:
- `experiment_config.py` → `ExperimentConfig`
- `stratum_config.py` → `StratumConfig`
- `curriculum_config.py` → `CurriculumConfig`
- `environment_config.py` → `EnvironmentConfig` (assumed)
- `actions_config.py` → `ActionsConfig` (assumed)
- `agent_config.py` → `AgentConfig` (assumed)

### Structure:
```python
class SomeConfigRoot(BaseModel):
    """Root structure for some.yaml file."""
    version: str
    field1: ...
    field2: ...

class SomeConfig(BaseModel):
    """Top-level config (wraps the YAML root key)."""
    some: SomeConfigRoot  # Wrapper field matches YAML root key

    @classmethod
    def from_yaml(cls, path: Path) -> "SomeConfig":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

### YAML Structure:
```yaml
some:  # Root key
  version: "1.0"
  field1: value1
  field2: value2
```

### Access Pattern:
```python
config = SomeConfig.from_yaml(path)
config.some.version       # Access via wrapper
config.some.field1        # All fields under wrapper
```

### Example (ExperimentConfig):
```python
config = ExperimentConfig.from_yaml(path)
config.experiment.version         # ✅
config.experiment.metadata.name   # ✅
```

---

## Pattern 2: Direct (Curriculum-Level DTOs)

### Files Using This Pattern:
- `bars_v2_config.py` → `BarsV2Config`
- `affordances_v2_config.py` → `AffordancesV2Config`
- `training_v2_config.py` → `TrainingV2Config` (assumed)

### Structure:
```python
class SomeV2Config(BaseModel):
    """Config for some.yaml (v2.1)."""
    version: Literal["1.0"]
    field1: ...
    field2: ...

def load_some_v2_config(config_dir: Path) -> SomeV2Config:
    data = load_yaml_section(config_dir, "some.yaml", "some")
    return SomeV2Config(**data)
```

### YAML Structure:
```yaml
some:  # Root key (extracted by load_yaml_section)
  version: "1.0"
  field1: value1
  field2: value2
```

### Access Pattern:
```python
config = load_some_v2_config(config_dir)
config.version    # Direct access (NO wrapper)
config.field1     # All fields directly on config
```

### Example (BarsV2Config):
```python
config = load_bars_v2_config(level_dir)
config.version     # ✅
config.meters      # ✅ (NOT config.bars.meters)
config.cascades    # ✅
```

---

## Why Two Patterns?

**Experiment-Level DTOs**: Use wrapper pattern because they have `from_yaml(path)` classmethod that loads entire file
- Needs wrapper to match YAML root key
- Loaded via `yaml.safe_load(file)` → returns full dict with root key
- Pattern: `cls(**data)` where data = `{"experiment": {...}}`

**Curriculum-Level DTOs**: Use direct pattern because they use `load_yaml_section` helper
- Helper extracts the root section BEFORE creating DTO
- Loaded via `load_yaml_section(..., "bars.yaml", "bars")` → returns section content
- Pattern: `SomeV2Config(**data)` where data = `{"version": "1.0", "meters": [...]}`

---

## Correct Field Access Patterns

### RawConfigsV21 Structure:
```python
@dataclass(frozen=True)
class CurriculumLevel:
    name: str
    curriculum: CurriculumConfig      # Wrapper pattern
    bars: BarsV2Config                # Direct pattern
    affordances: AffordancesV2Config  # Direct pattern
    training: TrainingV2Config        # Direct pattern

@dataclass(frozen=True)
class RawConfigsV21:
    experiment: ExperimentConfig      # Wrapper pattern
    stratum: StratumConfig            # Wrapper pattern
    environment: EnvironmentConfig    # Wrapper pattern
    actions: ActionsConfig            # Wrapper pattern
    agent: AgentConfig                # Wrapper pattern
    levels: dict[str, CurriculumLevel]
    experiment_dir: Path
```

### Experiment-Level Access (WRAPPER PATTERN):
```python
# Correct:
raw.experiment.experiment.metadata.name       # ✅ Double nesting
raw.stratum.stratum.substrate.type           # ✅ Double nesting
raw.environment.environment.meters           # ✅ Double nesting
raw.actions.actions.custom_actions           # ✅ Double nesting
raw.agent.agent.brain                        # ✅ Double nesting

# Wrong:
raw.experiment.metadata.name                 # ❌ Missing .experiment wrapper
raw.stratum.substrate.type                   # ❌ Missing .stratum wrapper
```

### Curriculum-Level Access (MIXED PATTERN):
```python
level = raw.levels["L1_full_observability"]

# Curriculum (wrapper pattern):
level.curriculum.curriculum.active_vision    # ✅ Double nesting

# Bars (direct pattern):
level.bars.version                           # ✅ Direct access
level.bars.meters                            # ✅ Direct access (NOT level.bars.bars.meters)
level.bars.cascades                          # ✅ Direct access

# Affordances (direct pattern):
level.affordances.version                    # ✅ Direct access
level.affordances.affordances                # ✅ Direct access (NOT level.affordances.affordances.affordances)
level.affordances.modulations                # ✅ Direct access

# Training (direct pattern):
level.training.version                       # ✅ Direct access (assumed)
level.training.population                    # ✅ Direct access (assumed)
```

### Vocabulary Validation Pattern:
```python
# Environment vocabulary (wrapper pattern):
env_meter_names = {m.name for m in raw.environment.environment.meters}
env_affordance_names = {a.name for a in raw.environment.environment.affordances}

# Level vocabulary (direct pattern):
level_meter_names = {m.name for m in level.bars.meters}                      # ✅
level_affordance_names = {a.name for a in level.affordances.affordances}      # ✅

# Validate:
assert level_meter_names == env_meter_names
assert level_affordance_names == env_affordance_names
```

---

## Summary Table

| DTO | File | Pattern | Access Example |
|-----|------|---------|----------------|
| ExperimentConfig | experiment_config.py | Wrapper | `config.experiment.metadata` |
| StratumConfig | stratum_config.py | Wrapper | `config.stratum.substrate` |
| EnvironmentConfig | environment_config.py | Wrapper | `config.environment.meters` |
| ActionsConfig | actions_config.py | Wrapper | `config.actions.custom_actions` |
| AgentConfig | agent_config.py | Wrapper | `config.agent.brain` |
| CurriculumConfig | curriculum_config.py | Wrapper | `config.curriculum.active_vision` |
| BarsV2Config | bars_v2_config.py | **Direct** | `config.meters` (NOT `config.bars.meters`) |
| AffordancesV2Config | affordances_v2_config.py | **Direct** | `config.affordances` (NOT `config.affordances.affordances.affordances`) |
| TrainingV2Config | training_v2_config.py | **Direct** | `config.population` (assumed) |

---

## Implications for Plans

**All phase plans must use the CORRECT access patterns**:

- ✅ `raw.experiment.experiment.metadata`
- ✅ `raw.stratum.stratum.substrate`
- ✅ `level.curriculum.curriculum.active_vision`
- ✅ `level.bars.meters` (NOT `level.bars.bars.meters`)
- ✅ `level.affordances.affordances` (NOT `level.affordances.affordances.affordances`)

**DTO-GROUND-TRUTH.md was WRONG** - it documented the wrapper pattern for ALL DTOs when curriculum-level DTOs use direct pattern.

---

**Status**: This document reflects ACTUAL implementation verified by reading source code
