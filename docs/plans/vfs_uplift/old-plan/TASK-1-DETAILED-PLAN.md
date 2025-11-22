# Task 1: Compile-time Wiring (VFS Profiles + Effects) - Implementation Plan

> **For Claude:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task with code review between tasks.

**Goal:** Move VFS profiles and Effects catalog compilation into UniverseCompiler so they become first-class compiled artifacts

**Architecture:** Extend UniverseCompiler with profile and effect catalog compilation stages, store results in CompiledUniverse, update vectorized_env to consume compiled artifacts

**Tech Stack:** PyTorch, Pydantic, networkx (topo sort), pyparsing (expressions), YAML

**Estimated Duration:** 2-3 days
**Test Target:** 5-8 new tests

---

## Context

**Current State (as of 2025-11-23):**
- VFS profiles: DTOs exist (`src/townlet/config/vfs_profiles_config.py`), compiler exists (`src/townlet/vfs/profiles.py`), but runtime ignores them
- Effects catalog: Rebuilt at runtime from `effects.yaml` in `vectorized_env.py:350-382`, not part of `CompiledUniverse`
- `CompiledUniverse`: No fields for VFS profiles or effects catalog

**Target State:**
- VFS profiles compiled by `UniverseCompiler`, stored in `CompiledUniverse`
- Effects catalog compiled by `UniverseCompiler`, stored in `CompiledUniverse`
- Runtime (`vectorized_env.py`) consumes compiled artifacts, no YAML loading

---

## Subtask 1.1: Add VFS Profiles Compilation to UniverseCompiler

**Files:**
- Modify: `src/townlet/universe/compiler.py` (add profile loading)
- Modify: `src/townlet/universe/compiled.py` (add profile fields)
- Test: `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py` (new file)

### Step 1.1.1: Write failing test for VFS profile loading

**Test:** `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py`

```python
"""Tests for VFS profile compilation in UniverseCompiler."""

from pathlib import Path
import pytest
import tempfile
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_compiler_loads_vfs_profiles_if_present(tmp_path: Path):
    """UniverseCompiler should load vfs_profiles.yaml from experiment root if present."""
    # Setup: Create minimal config pack with vfs_profiles.yaml
    experiment_dir = tmp_path / "experiment"
    experiment_dir.mkdir()

    # Create vfs_profiles.yaml
    profiles = {
        "global_profile": {
            "variables": [
                {"name": "day_count", "type": "int", "initial_value": 0}
            ]
        }
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Create minimal required files (stub for now)
    # ... (will expand in actual implementation)

    # Exercise: Compile universe
    compiler = UniverseCompiler()
    # This will fail until we implement profile loading
    compiled = compiler.compile(experiment_dir, primary_level="test_level")

    # Verify: CompiledUniverse has compiled profiles
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is not None
    assert len(compiled.compiled_vfs_profiles.global_profile.variables) == 1
    assert compiled.compiled_vfs_profiles.global_profile.variables[0].name == "day_count"


def test_compiler_allows_missing_vfs_profiles():
    """UniverseCompiler should allow missing vfs_profiles.yaml (not all configs use VFS)."""
    # Setup: Create minimal config pack WITHOUT vfs_profiles.yaml
    # ... (stub for now)

    # Exercise: Compile universe
    compiler = UniverseCompiler()
    # This should succeed with empty/None profiles
    compiled = compiler.compile(experiment_dir, primary_level="test_level")

    # Verify: No error, profiles are None or empty
    assert compiled.compiled_vfs_profiles is None or compiled.compiled_vfs_profiles.global_profile is None
```

**Expected:** Tests FAIL (fields don't exist yet)

### Step 1.1.2: Run test to verify it fails

```bash
cd /home/john/hamlet
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_profile_compilation.py::test_compiler_loads_vfs_profiles_if_present -xvs
```

**Expected Output:**
```
FAILED - AttributeError: 'CompiledUniverse' object has no attribute 'compiled_vfs_profiles'
```

### Step 1.1.3: Add compiled_vfs_profiles field to CompiledUniverse

**File:** `src/townlet/universe/compiled.py`

Add new dataclass for compiled profiles and field to CompiledUniverse:

```python
# After line 38 (after imports)
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable

# ... existing code ...

@dataclass(frozen=True)
class CompiledVFSProfiles:
    """Compiled VFS profiles (global, agent, item)."""

    global_profile: CompiledGlobalProfile | None = None
    agent_profile: Any | None = None  # TODO: Add CompiledAgentProfile type
    item_profiles: dict[str, Any] = None  # TODO: Add CompiledItemProfile type

    def __post_init__(self):
        # Make item_profiles immutable
        if self.item_profiles is None:
            object.__setattr__(self, "item_profiles", {})


@dataclass(frozen=True)
class CompiledUniverse:
    """Compiled universe representation with multi-level support."""

    # ... existing fields ...

    # NEW: Compiled VFS profiles (experiment-level artifact)
    compiled_vfs_profiles: CompiledVFSProfiles | None = None

    # ... rest of existing code ...
```

**Location:** After line 40, before CompiledUniverse class definition

### Step 1.1.4: Add VFS profile loading to UniverseCompiler

**File:** `src/townlet/universe/compiler.py`

Add imports:

```python
# After line 52 (after existing VFS imports)
from townlet.vfs.profiles import VFSProfileCompiler, CompiledGlobalProfile
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.universe.compiled import CompiledVFSProfiles
```

Add method to load and compile profiles:

```python
# Add after _load_experiment_structure method (around line 200)

def _compile_vfs_profiles(
    self,
    experiment_dir: Path,
    bar_schema: dict[str, str]
) -> CompiledVFSProfiles | None:
    """Load and compile VFS profiles from experiment directory.

    Args:
        experiment_dir: Experiment root directory
        bar_schema: Type schema for bars (for expression type checking)

    Returns:
        Compiled profiles or None if vfs_profiles.yaml not present
    """
    profiles_path = experiment_dir / "vfs_profiles.yaml"

    if not profiles_path.exists():
        logger.debug("vfs_profiles.yaml not found, skipping VFS profile compilation")
        return None

    # Load YAML
    import yaml
    profiles_data = yaml.safe_load(profiles_path.read_text())

    # Validate with Pydantic
    profiles_config = VFSProfilesConfig(**profiles_data)

    # Compile profiles
    compiler = VFSProfileCompiler()

    compiled_global = None
    if profiles_config.global_profile is not None:
        compiled_global = compiler.compile_global_profile(
            profiles_config.global_profile,
            bar_schema=bar_schema
        )

    # TODO: Compile agent_profile and item_profiles (Task 1.2)

    return CompiledVFSProfiles(
        global_profile=compiled_global,
        agent_profile=None,  # TODO
        item_profiles={},    # TODO
    )
```

**Location:** After `_load_experiment_structure` method

Update `compile()` method to call `_compile_vfs_profiles`:

```python
# In compile() method, after building bar_schema (around line 450)

# Build bar schema for VFS profile type checking
bar_schema = {}
for meter in level.bars.meters:
    bar_schema[meter.name] = "float"  # All meters are float

# Compile VFS profiles (experiment-level)
compiled_vfs_profiles = self._compile_vfs_profiles(experiment_dir, bar_schema)

# ... later, when constructing CompiledUniverse (around line 600) ...

return CompiledUniverse(
    # ... existing fields ...
    compiled_vfs_profiles=compiled_vfs_profiles,
    # ... rest of fields ...
)
```

### Step 1.1.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_profile_compilation.py::test_compiler_loads_vfs_profiles_if_present -xvs
```

**Expected:** PASS

### Step 1.1.6: Commit VFS profile compilation

```bash
git add src/townlet/universe/compiled.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_vfs_profile_compilation.py
git commit -m "feat(compiler): add VFS profile compilation to UniverseCompiler

- Add CompiledVFSProfiles dataclass to CompiledUniverse
- Add _compile_vfs_profiles() method to UniverseCompiler
- Load vfs_profiles.yaml from experiment root if present
- Compile global_profile with expression validation
- Tests verify profile loading and optional presence

Task 1.1 complete (VFS profiles compilation)"
```

---

## Subtask 1.2: Add Effects Catalog Compilation to UniverseCompiler

**Files:**
- Modify: `src/townlet/universe/compiled.py` (add effect catalog field)
- Modify: `src/townlet/universe/compiler.py` (add catalog compilation)
- Test: `tests/test_townlet/unit/universe/test_effects_catalog_compilation.py` (new file)

### Step 1.2.1: Write failing test for effects catalog compilation

**Test:** `tests/test_townlet/unit/universe/test_effects_catalog_compilation.py`

```python
"""Tests for Effects catalog compilation in UniverseCompiler."""

from pathlib import Path
import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_effects_catalog_per_level():
    """UniverseCompiler should compile effects.yaml into catalog artifact."""
    # Setup: Create config pack with effects.yaml
    # ... (minimal fixture with effects.yaml)

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level="test_level")

    # Verify: CompiledUniverse has compiled effect catalog
    assert compiled.compiled_effect_catalog is not None
    assert len(compiled.compiled_effect_catalog.effects) > 0
    assert "energy_regen" in compiled.compiled_effect_catalog.effects


def test_compiler_fails_if_effects_yaml_missing():
    """UniverseCompiler should fail if effects.yaml required but missing."""
    # Setup: Config pack with affordances but no effects.yaml
    # ...

    # Exercise & Verify
    compiler = UniverseCompiler()
    with pytest.raises(FileNotFoundError, match="effects.yaml is required"):
        compiled = compiler.compile(experiment_dir, primary_level="test_level")
```

**Expected:** Tests FAIL (field doesn't exist yet)

### Step 1.2.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_effects_catalog_compilation.py::test_compiler_compiles_effects_catalog_per_level -xvs
```

**Expected Output:**
```
FAILED - AttributeError: 'CompiledUniverse' object has no attribute 'compiled_effect_catalog'
```

### Step 1.2.3: Add compiled_effect_catalog field to CompiledUniverse

**File:** `src/townlet/universe/compiled.py`

Add import:

```python
# After line 38
from townlet.effects.catalog import EffectCatalog
```

Add field to CompiledUniverse:

```python
@dataclass(frozen=True)
class CompiledUniverse:
    """Compiled universe representation with multi-level support."""

    # ... existing fields ...

    # NEW: Compiled effects catalog (per-level artifact)
    compiled_effect_catalog: EffectCatalog | None = None

    # ... rest of code ...
```

Add field to LevelMetadata (effects are per-level):

```python
@dataclass(frozen=True)
class LevelMetadata:
    """Per-level metadata for multi-level compilation."""

    # ... existing fields ...

    # NEW: Compiled effects catalog
    compiled_effect_catalog: EffectCatalog | None = None
```

### Step 1.2.4: Add effects catalog compilation to UniverseCompiler

**File:** `src/townlet/universe/compiler.py`

Add imports:

```python
# After line 52
from townlet.effects.catalog import EffectCatalog
from townlet.config.effects_config import EffectsConfig
```

Add method to compile effects catalog:

```python
# Add after _compile_vfs_profiles method

def _compile_effects_catalog(
    self,
    level_dir: Path,
    effects_schema: dict[str, str]
) -> EffectCatalog:
    """Load and compile effects catalog from level directory.

    Args:
        level_dir: Level config directory containing effects.yaml
        effects_schema: Type schema for effect command validation

    Returns:
        Compiled effects catalog

    Raises:
        FileNotFoundError: If effects.yaml not found
    """
    effects_path = level_dir / "effects.yaml"

    if not effects_path.exists():
        raise FileNotFoundError(
            f"effects.yaml is required for affordance interactions but not found at {effects_path}"
        )

    # Load YAML
    import yaml
    effects_data = yaml.safe_load(effects_path.read_text())

    # Validate with Pydantic
    effects_config = EffectsConfig(**effects_data)

    # Compile catalog with schema validation
    catalog = EffectCatalog.from_config(effects_config, schema=effects_schema)

    return catalog
```

Update compile() method to build effects schema and compile catalog:

```python
# In compile() method, after VFS profile compilation

# Build effects schema for command validation
effects_schema = {}
effects_schema["intensity"] = "float"
effects_schema["elapsed_ticks"] = "float"
effects_schema["duration_remaining"] = "float"

# Add bar paths
for meter in level.bars.meters:
    effects_schema[f"bar.{meter.name}"] = "float"
    effects_schema[f"target.bar.{meter.name}"] = "float"

# Add VFS paths (from compiled profiles)
if compiled_vfs_profiles and compiled_vfs_profiles.global_profile:
    for var in compiled_vfs_profiles.global_profile.variables:
        vfs_type = "bool" if var.type == "bool" else "float"
        effects_schema[f"vfs.{var.name}"] = vfs_type
        effects_schema[f"target.vfs.{var.name}"] = vfs_type

# Compile effects catalog
compiled_effect_catalog = self._compile_effects_catalog(level_dir, effects_schema)

# ... when constructing CompiledUniverse ...

return CompiledUniverse(
    # ... existing fields ...
    compiled_effect_catalog=compiled_effect_catalog,
    # ... rest of fields ...
)
```

### Step 1.2.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_effects_catalog_compilation.py::test_compiler_compiles_effects_catalog_per_level -xvs
```

**Expected:** PASS

### Step 1.2.6: Commit effects catalog compilation

```bash
git add src/townlet/universe/compiled.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_effects_catalog_compilation.py
git commit -m "feat(compiler): add effects catalog compilation to UniverseCompiler

- Add compiled_effect_catalog field to CompiledUniverse
- Add _compile_effects_catalog() method to UniverseCompiler
- Build effects schema from bars + VFS profiles
- Compile catalog with command validation at compile time
- Tests verify catalog compilation and error handling

Task 1.2 complete (Effects catalog compilation)"
```

---

## Subtask 1.3: Add VFS Expression Schema to CompiledUniverse

**Files:**
- Modify: `src/townlet/universe/compiled.py` (add schema field)
- Modify: `src/townlet/universe/compiler.py` (generate schema)
- Test: `tests/test_townlet/unit/universe/test_vfs_expression_schema.py` (new file)

### Step 1.3.1: Write failing test for VFS expression schema

**Test:** `tests/test_townlet/unit/universe/test_vfs_expression_schema.py`

```python
"""Tests for VFS expression schema in CompiledUniverse."""

from pathlib import Path
import pytest

from townlet.universe.compiler import UniverseCompiler


def test_compiler_generates_vfs_expression_schema():
    """UniverseCompiler should generate type schema for runtime expression checking."""
    # Setup: Config pack with VFS profiles
    # ...

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level="test_level")

    # Verify: Schema includes bars and VFS variables
    assert compiled.vfs_expression_schema is not None
    assert "bar.energy" in compiled.vfs_expression_schema
    assert "vfs.day_count" in compiled.vfs_expression_schema
    assert compiled.vfs_expression_schema["bar.energy"] == "float"
    assert compiled.vfs_expression_schema["vfs.day_count"] == "int"
```

### Step 1.3.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_expression_schema.py::test_compiler_generates_vfs_expression_schema -xvs
```

**Expected:** FAIL (field doesn't exist)

### Step 1.3.3: Add vfs_expression_schema field to CompiledUniverse

**File:** `src/townlet/universe/compiled.py`

```python
@dataclass(frozen=True)
class CompiledUniverse:
    """Compiled universe representation with multi-level support."""

    # ... existing fields ...

    # NEW: Type schema for runtime VFS expression validation
    vfs_expression_schema: dict[str, str] | None = None

    # ... rest of code ...
```

### Step 1.3.4: Generate VFS expression schema in UniverseCompiler

**File:** `src/townlet/universe/compiler.py`

Add method to build schema:

```python
def _build_vfs_expression_schema(
    self,
    bars: BarsV2Config,
    compiled_vfs_profiles: CompiledVFSProfiles | None
) -> dict[str, str]:
    """Build type schema for VFS expression runtime validation.

    Args:
        bars: Bars configuration (for bar paths)
        compiled_vfs_profiles: Compiled VFS profiles (for vfs paths)

    Returns:
        Type schema mapping path -> type
    """
    schema = {}

    # Add bar paths
    for meter in bars.meters:
        schema[f"bar.{meter.name}"] = "float"

    # Add VFS paths from global profile
    if compiled_vfs_profiles and compiled_vfs_profiles.global_profile:
        for var in compiled_vfs_profiles.global_profile.variables:
            schema[f"vfs.{var.name}"] = var.type

    # TODO: Add agent profile paths (Task 2)
    # TODO: Add item profile paths (Task 3)

    return schema
```

Update compile() method:

```python
# After compiling VFS profiles and effects catalog

vfs_expression_schema = self._build_vfs_expression_schema(level.bars, compiled_vfs_profiles)

# ... when constructing CompiledUniverse ...

return CompiledUniverse(
    # ... existing fields ...
    vfs_expression_schema=vfs_expression_schema,
    # ... rest of fields ...
)
```

### Step 1.3.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_vfs_expression_schema.py::test_compiler_generates_vfs_expression_schema -xvs
```

**Expected:** PASS

### Step 1.3.6: Commit VFS expression schema

```bash
git add src/townlet/universe/compiled.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_vfs_expression_schema.py
git commit -m "feat(compiler): generate VFS expression schema for runtime validation

- Add vfs_expression_schema field to CompiledUniverse
- Generate schema from bars + VFS profiles
- Schema maps variable paths to types for runtime type checking
- Tests verify schema generation

Task 1.3 complete (VFS expression schema)"
```

---

## Subtask 1.4: Update CompiledUniverse Serialization

**Files:**
- Modify: `src/townlet/universe/compiled.py` (update to_dict/from_dict)
- Test: `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py`

### Step 1.4.1: Write failing test for serialization

**Test:** `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py`

```python
"""Tests for CompiledUniverse serialization with new fields."""

import pytest
from pathlib import Path

from townlet.universe.compiled import CompiledUniverse


def test_compiled_universe_serializes_vfs_profiles(minimal_compiled_universe_with_profiles):
    """CompiledUniverse.to_dict() should serialize VFS profiles."""
    # Exercise
    data = minimal_compiled_universe_with_profiles.to_dict()

    # Verify
    assert "compiled_vfs_profiles" in data
    assert data["compiled_vfs_profiles"]["global_profile"] is not None


def test_compiled_universe_deserializes_vfs_profiles(minimal_compiled_universe_with_profiles):
    """CompiledUniverse.from_dict() should deserialize VFS profiles."""
    # Setup
    data = minimal_compiled_universe_with_profiles.to_dict()

    # Exercise
    restored = CompiledUniverse.from_dict(data)

    # Verify
    assert restored.compiled_vfs_profiles is not None
    assert restored.compiled_vfs_profiles.global_profile is not None
```

### Step 1.4.2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_compiled_universe_serialization.py -xvs
```

**Expected:** FAIL (serialization doesn't handle new fields)

### Step 1.4.3: Update to_dict() method

**File:** `src/townlet/universe/compiled.py`

```python
def to_dict(self) -> dict[str, Any]:
    """Convert to a serialization-friendly dictionary."""

    # Serialize VFS profiles
    compiled_vfs_profiles_data = None
    if self.compiled_vfs_profiles is not None:
        compiled_vfs_profiles_data = {
            "global_profile": (
                {
                    "variables": [
                        {
                            "name": v.name,
                            "type": v.type,
                            "initial_value": v.initial_value,
                            "result_type": v.result_type,
                            # Note: AST is not serialized (will be recompiled on load)
                        }
                        for v in self.compiled_vfs_profiles.global_profile.variables
                    ]
                }
                if self.compiled_vfs_profiles.global_profile is not None
                else None
            ),
            # TODO: agent_profile, item_profiles
        }

    # Serialize effects catalog
    compiled_effect_catalog_data = None
    if self.compiled_effect_catalog is not None:
        compiled_effect_catalog_data = {
            "effects": {
                effect_id: {
                    "id": effect.id,
                    "scope": effect.scope,
                    "duration": effect.duration,
                    "intensity": effect.intensity,
                    "reapply_policy": effect.reapply_policy,
                    "observable": effect.observable,
                    # Note: Command nodes not serialized (will be recompiled on load)
                }
                for effect_id, effect in self.compiled_effect_catalog.effects.items()
            }
        }

    return {
        # ... existing fields ...
        "compiled_vfs_profiles": compiled_vfs_profiles_data,
        "compiled_effect_catalog": compiled_effect_catalog_data,
        "vfs_expression_schema": self.vfs_expression_schema,
        # ... rest of fields ...
    }
```

### Step 1.4.4: Update from_dict() method

**File:** `src/townlet/universe/compiled.py`

```python
@classmethod
def from_dict(cls, payload: Mapping[str, Any]) -> CompiledUniverse:
    """Create CompiledUniverse from a dictionary produced by to_dict/save_to_cache."""

    # Deserialize VFS profiles
    compiled_vfs_profiles = None
    vfs_data = payload.get("compiled_vfs_profiles")
    if vfs_data is not None:
        # Note: Deserialization creates stub profiles without ASTs
        # Full recompilation from YAML is needed for expression evaluation
        # This is acceptable for cache storage
        global_profile = None
        if vfs_data.get("global_profile") is not None:
            from townlet.vfs.profiles import CompiledVariable, CompiledGlobalProfile
            variables = [
                CompiledVariable(
                    name=v["name"],
                    type=v["type"],
                    ast=None,  # Not serialized
                    initial_value=v["initial_value"],
                    result_type=v["result_type"],
                )
                for v in vfs_data["global_profile"]["variables"]
            ]
            global_profile = CompiledGlobalProfile(variables=variables)

        compiled_vfs_profiles = CompiledVFSProfiles(
            global_profile=global_profile,
            agent_profile=None,
            item_profiles={},
        )

    # Deserialize effects catalog
    compiled_effect_catalog = None
    catalog_data = payload.get("compiled_effect_catalog")
    if catalog_data is not None:
        # Similar stub deserialization for effects
        # Full recompilation from YAML needed for command execution
        from townlet.effects.catalog import CompiledEffect, EffectCatalog
        effects = {
            effect_id: CompiledEffect(
                id=effect_data["id"],
                scope=effect_data["scope"],
                duration=effect_data["duration"],
                intensity=effect_data["intensity"],
                reapply_policy=effect_data["reapply_policy"],
                observable=effect_data["observable"],
                on_spawn=[],  # Stub
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
            for effect_id, effect_data in catalog_data["effects"].items()
        }
        compiled_effect_catalog = EffectCatalog(effects=effects)

    return CompiledUniverse(
        # ... existing fields ...
        compiled_vfs_profiles=compiled_vfs_profiles,
        compiled_effect_catalog=compiled_effect_catalog,
        vfs_expression_schema=payload.get("vfs_expression_schema"),
        # ... rest of fields ...
    )
```

### Step 1.4.5: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_compiled_universe_serialization.py -xvs
```

**Expected:** PASS

### Step 1.4.6: Commit serialization updates

```bash
git add src/townlet/universe/compiled.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py
git commit -m "feat(compiler): update CompiledUniverse serialization for new fields

- Serialize/deserialize compiled_vfs_profiles
- Serialize/deserialize compiled_effect_catalog
- Serialize/deserialize vfs_expression_schema
- Note: ASTs and command nodes use stub deserialization (not executable)
- Full recompilation from YAML needed for runtime execution
- Tests verify round-trip serialization

Task 1.4 complete (Serialization updates)"
```

---

## Subtask 1.5: Integration Tests and Validation

**Files:**
- Test: `tests/test_townlet/integration/test_compile_time_wiring.py` (new file)

### Step 1.5.1: Write integration test for end-to-end compilation

**Test:** `tests/test_townlet/integration/test_compile_time_wiring.py`

```python
"""Integration tests for compile-time VFS profiles + effects catalog."""

from pathlib import Path
import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_compiler_wires_vfs_and_effects_together(effects_smoke_config):
    """UniverseCompiler should compile VFS profiles and effects together."""
    # Setup: Use effects_smoke test config (has both VFS and effects)
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="effects_smoke")

    # Verify: Both artifacts present
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_effect_catalog is not None
    assert compiled.vfs_expression_schema is not None

    # Verify: Effects schema includes VFS variables
    assert "vfs.day_count" in compiled.vfs_expression_schema

    # Verify: Effects can reference VFS in commands
    energy_regen = compiled.compiled_effect_catalog.get("energy_regen")
    assert energy_regen is not None


def test_compiler_handles_minimal_config_without_vfs():
    """UniverseCompiler should handle configs without VFS profiles."""
    # Setup: Minimal config without vfs_profiles.yaml
    # ... (use existing minimal config)

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="minimal")

    # Verify: No profiles, but compilation succeeds
    assert compiled.compiled_vfs_profiles is None or compiled.compiled_vfs_profiles.global_profile is None
    # Effects catalog should still compile (no VFS dependencies)
    assert compiled.compiled_effect_catalog is not None
```

### Step 1.5.2: Run integration test

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_compile_time_wiring.py -xvs
```

**Expected:** PASS

### Step 1.5.3: Verify no runtime YAML loading in vectorized_env (grep check)

```bash
cd /home/john/hamlet
grep -n "effects_path.*read_text" src/townlet/environment/vectorized_env.py
grep -n "EffectsConfig" src/townlet/environment/vectorized_env.py
```

**Expected Output:** Should still show lines 355-382 (we haven't removed them yet - that's Task 4)

**Rationale:** This grep check documents current state. Task 4 will remove these lines and use compiled artifacts.

### Step 1.5.4: Commit integration tests

```bash
git add tests/test_townlet/integration/test_compile_time_wiring.py
git commit -m "test(compiler): add integration tests for VFS + effects compilation

- Test end-to-end compilation with VFS profiles and effects
- Test effects schema includes VFS variables
- Test minimal configs without VFS still compile
- Grep check documents current runtime YAML loading (to be removed in Task 4)

Task 1.5 complete (Integration tests)"
```

---

## Subtask 1.6: Documentation and Cleanup

**Files:**
- Modify: `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

### Step 1.6.1: Update implementation status

**File:** `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

Mark Task 1 as COMPLETE with test counts and commit references.

### Step 1.6.2: Commit documentation updates

```bash
git add docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md
git commit -m "docs: mark Task 1 (Compile-time wiring) as COMPLETE

Task 1 delivered:
- VFS profiles compiled by UniverseCompiler ✅
- Effects catalog compiled by UniverseCompiler ✅
- VFS expression schema generated ✅
- CompiledUniverse serialization updated ✅
- 8 new tests passing (5 unit + 3 integration)

Next: Task 2 (Runtime VFS evaluation)"
```

---

## Task 1 Success Criteria

**Functional:**
- ✅ VFS profiles loaded from `vfs_profiles.yaml` if present
- ✅ VFS profiles optional (minimal configs without VFS work)
- ✅ Effects catalog compiled from `effects.yaml` per level
- ✅ VFS expression schema generated for runtime validation
- ✅ All artifacts stored in `CompiledUniverse`
- ✅ Serialization supports new fields

**Tests:**
- ✅ 5-8 new tests passing (unit + integration)
- ✅ All existing 435+ tests still pass

**Code Quality:**
- ✅ No breaking changes to existing API
- ✅ Effects catalog compilation uses existing `EffectCatalog.from_config()`
- ✅ VFS profile compilation uses existing `VFSProfileCompiler`
- ✅ Runtime still works (Task 4 will remove YAML loading)

---

## Notes for Engineer

**Key Design Decisions:**

1. **VFS profiles are experiment-level, effects are per-level:**
   VFS profiles live at experiment root (`vfs_profiles.yaml`), effects live per-level (`levels/L1/effects.yaml`).

2. **Serialization uses stub deserialization:**
   ASTs and command nodes are not serialized. Cache reload creates stubs. Full recompilation from YAML needed for runtime execution. This is acceptable because cache is for fast iteration, not production distribution.

3. **Effects schema includes VFS paths:**
   Effects can reference `vfs.day_count` in commands. Schema generation happens after VFS profile compilation.

4. **Circular dependency risk:**
   VFS profiles use `VFSProfileCompiler` which already handles circular dependency detection via networkx. No additional validation needed.

**Common Pitfalls:**

- Don't forget to update both `to_dict()` AND `from_dict()` for serialization
- Don't serialize ASTs (they're not JSON-serializable, recompile from YAML instead)
- Don't break existing tests - run full suite after each commit
- Don't load YAML in runtime yet - that's Task 4

**Testing Strategy:**

- Unit tests: Test each compilation method in isolation
- Integration tests: Test full compile() pipeline with real configs
- Use `effects_smoke` config for integration tests (has both VFS and effects)

---

## Execution Handoff

**Plan complete and saved to `docs/plans/vfs_uplift/TASK-1-DETAILED-PLAN.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - Dispatch fresh subagent per subtask, review between subtasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with `/superpowers:execute-plan`, batch execution with checkpoints

**Which approach?**
