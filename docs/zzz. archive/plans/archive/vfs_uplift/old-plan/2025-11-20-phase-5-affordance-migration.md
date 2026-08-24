# Phase 5: Affordance Migration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate affordances from EffectPipeline (opaque dict system) to Effects commands (declarative, unified system).

**Architecture:** Replace the 5-stage EffectPipeline (on_start, per_tick, on_completion, on_early_exit, on_failure) with Effects commands that integrate with the existing CommandExecutor. This unifies affordance interactions with the Items system, enabling future enhancements like conditional effects, VFS references, and expression-based logic.

**Tech Stack:** Pydantic DTOs, Effects system (CommandCompiler + CommandExecutor), PyTorch tensors, YAML configuration

**Timeline:** 4-5 days (Task 5.1: 1.5 days, Task 5.2: 2 days, Task 5.3: 0.5 days, Task 5.4: 0.5 days)

**CRITICAL FIXES APPLIED:**
1. ✅ Compile affordance Effects at startup (performance)
2. ✅ Wire command_executor in VectorizedHamletEnv (integration)
3. ✅ Extend migration script for multi_tick and effect_pipeline (completeness)
4. ✅ Preserve costs/costs_per_tick as affordability gates (design correction)

---

## Context: What is EffectPipeline?

**Current System** (`effect_pipeline.py`):
```python
class AffordanceEffect:
    meter: str  # Meter name
    amount: float  # Delta (positive or negative)

class EffectPipeline:
    on_start: list[AffordanceEffect]  # Applied when interaction starts
    per_tick: list[AffordanceEffect]  # Applied each tick (multi_tick/dual only)
    on_completion: list[AffordanceEffect]  # Applied when interaction completes
    on_early_exit: list[AffordanceEffect]  # Applied if agent leaves early
    on_failure: list[AffordanceEffect]  # Applied if interaction fails
```

**Example Usage** (reference-config-v2.1-complete.yaml):
```yaml
effect_pipeline:
  on_start:
    - meter: satiation
      amount: 0.4
    - meter: mood
      amount: 0.05
  per_tick: []
  on_completion: []
  on_early_exit: []
  on_failure: []
```

**Target System** (Effects commands, like Items use):
```yaml
interactions:
  on_start:
    - modify: "target.bar.satiation"
      value: "target.bar.satiation + 0.4"
    - modify: "target.bar.mood"
      value: "target.bar.mood + 0.05"
  per_tick: []
  on_completion: []
  on_early_exit: []
  on_failure: []
```

**Why Migrate?**
- **Unified System**: Affordances and Items use the same Effects architecture
- **Extensibility**: Effects support conditions, VFS references, complex expressions
- **Maintainability**: Single command execution pipeline instead of dual systems
- **Future-Proof**: Enables affordances to read/write VFS variables, reference items, etc.

---

## Migration Strategy

**Scope:** 5 curriculum levels need migration:
- L0_0_minimal
- L0_5_dual_resource
- L1_full_observability
- L2_partial_observability
- L3_temporal_mechanics

**Current State:**
- All production configs use simple `effects` dict (instant deltas only)
- Only reference config uses `effect_pipeline` (example/documentation)
- Affordance engine applies effects directly via tensor operations

**Migration Path (BREAKING CHANGE - No Backwards Compatibility):**
1. **Add `interactions` field** to AffordanceParamConfig (REQUIRED)
2. **Integrate CommandExecutor** into AffordanceEngine (Effects-only path)
3. **Migrate all configs** in single batch (migration script)
4. **Delete `effect_pipeline` and `effects` fields** immediately
5. **Delete EffectPipeline code** (no fallback paths)

---

## Task 5.1: Schema Migration & Effects Integration (1 day)

**Goal:** Update affordance DTOs to support Effects commands and integrate CommandExecutor into affordance_engine.

### Files

**Create:**
- None (reusing existing Effects system)

**Modify:**
- `src/townlet/config/affordances_v2_config.py` - Add `interactions` field
- `src/townlet/environment/affordance_engine.py` - Integrate CommandExecutor
- `tests/test_townlet/unit/environment/test_affordance_engine.py` - Add Effects tests

---

### Step 1: Add `interactions` field to AffordanceParamConfig

**File:** `src/townlet/config/affordances_v2_config.py`

Add import at top of file:
```python
from townlet.config.effects_config import CommandConfig
```

**BREAKING CHANGE**: Remove `effects` and `effect_pipeline` fields, add REQUIRED `interactions` field, KEEP `costs`:

```python
    # Affordability gates (checked BEFORE execution) -------------------------
    costs: dict[str, float] = Field(
        default_factory=dict,
        description="Resource costs required to use this affordance (affordability check). "
        "Example: {'energy': 0.2} means agent needs energy >= 0.2 to interact."
    )
    costs_per_tick: dict[str, float] = Field(
        default_factory=dict,
        description="Resource costs per tick for multi_tick affordances (affordability check)."
    )

    # Effect outcomes (applied AFTER affordability check passes) -------------
    # REMOVED: effects dict and effect_pipeline (legacy systems deleted)

    # NEW: Effects commands (unified with Items system) - REQUIRED
    interactions: dict[str, list[CommandConfig]] = Field(
        description=(
            "Effects commands for affordance lifecycle stages. "
            "Unified with Items system (declarative Effects). "
            "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure. "
            "NOTE: Use costs/costs_per_tick for affordability gates, interactions for outcomes."
        ),
    )
```

**Design Rationale:**
- **costs/costs_per_tick**: Gating mechanism (pre-check) - "Can agent afford this?"
- **interactions**: Outcomes (post-check) - "What happens when affordance succeeds?"
- Separation preserves affordability semantics while unifying outcome logic with Effects

Add validator after `validate_interaction_semantics`:
```python
    @model_validator(mode="after")
    def validate_interaction_stages(self) -> "AffordanceParamConfig":
        """Validate interactions have correct stages for interaction_type."""
        valid_stages = {"on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"}
        provided_stages = set(self.interactions.keys())

        invalid = provided_stages - valid_stages
        if invalid:
            raise ValueError(
                f"Affordance '{self.name}': Invalid interaction stages: {invalid}. "
                f"Valid stages: {valid_stages}"
            )

        interaction_type = self.interaction_type or "instant"

        # Instant affordances shouldn't have per_tick effects
        if interaction_type == "instant" and self.interactions.get("per_tick"):
            raise ValueError(
                f"Affordance '{self.name}': instant affordances cannot have per_tick effects. "
                "Use multi_tick or dual interaction_type."
            )

        return self
```

**Expected:** Config loads with `interactions` field validated.

---

### Step 2: Write failing test for Effects execution in affordance_engine

**File:** `tests/test_townlet/unit/environment/test_affordance_engine.py`

Add import at top:
```python
from townlet.config.effects_config import CommandConfig
from townlet.effects.executor import CommandExecutor
from townlet.vfs.registry import VariableRegistry
```

Add test after existing tests:
```python
def test_affordance_engine_executes_effects_commands():
    """Affordances with interactions field execute Effects commands."""
    # Setup: Create affordance with Effects commands instead of simple effects
    from unittest.mock import Mock
    from townlet.config.affordances_v2_config import AffordanceParamConfig, OpeningHoursConfig, DeploymentConfig

    # Create affordance with interactions (Effects commands)
    affordance = AffordanceParamConfig(
        name="TEST_AFFORDANCE",
        interaction_type="instant",
        costs={},
        effects={},  # Empty - using interactions instead
        interactions={
            "on_start": [
                {"modify": "target.bar.energy", "value": "target.bar.energy + 0.5"}
            ],
        },
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="random"),
    )

    # Create mock environment with VFS registry and command executor
    env = Mock()
    env.num_agents = 2
    env.vfs_registry = VariableRegistry(num_agents=2, device="cpu")
    env.command_executor = CommandExecutor(registry=env.vfs_registry, device="cpu")

    # Register energy bar in VFS
    from townlet.vfs.schema import VariableDef, VariableScope, Reader, Writer
    env.vfs_registry.register_variable(
        VariableDef(
            name="energy",
            scope=VariableScope.AGENT,
            dtype="scalar",
            readers=[Reader.AGENT],
            writers=[Writer.ENGINE],
        )
    )

    # Initialize meters tensor
    meters = torch.tensor([[0.2, 0.5], [0.3, 0.6]], dtype=torch.float32)  # [batch, meters]
    env.vfs_registry.storage["energy"] = meters[:, 0]  # Store energy in VFS

    # Create affordance engine
    engine = AffordanceEngine(
        env=env,
        affordances=[affordance],
        meter_names=["energy", "health"],
        modulations=[],
    )

    # Execute instant affordance
    agent_mask = torch.tensor([True, False])  # Only agent 0 interacts
    updated_meters = engine.execute_instant_affordance("TEST_AFFORDANCE", meters, agent_mask)

    # Verify: Agent 0's energy increased by 0.5, agent 1 unchanged
    assert updated_meters[0, 0] == pytest.approx(0.7)  # 0.2 + 0.5
    assert updated_meters[1, 0] == pytest.approx(0.3)  # Unchanged
```

---

### Step 3: Run test to verify it fails

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/test_affordance_engine.py::test_affordance_engine_executes_effects_commands -v
```

**Expected:** FAIL - `AttributeError: 'Mock' object has no attribute 'vfs_registry'` or similar (affordance_engine doesn't use Effects yet)

---

### Step 4: Integrate CommandExecutor into AffordanceEngine

**File:** `src/townlet/environment/affordance_engine.py`

Add imports at top:
```python
from townlet.effects.executor import CommandExecutor, ExecutionContext
from townlet.effects.parser import CommandParser
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode
from dataclasses import dataclass
```

Add dataclass for compiled affordances:
```python
@dataclass
class CompiledAffordance:
    """Pre-compiled Effects commands for affordance lifecycle stages."""
    on_start: list[CommandNode]
    per_tick: list[CommandNode]
    on_completion: list[CommandNode]
    on_early_exit: list[CommandNode]
    on_failure: list[CommandNode]
```

Update `__init__` to compile affordance Effects at startup:
```python
    def __init__(
        self,
        env,  # VectorizedHamletEnv instance
        affordances: list[AffordanceParamConfig],
        meter_names: list[str],
        modulations: list[ModulationParamConfig],
        command_executor: CommandExecutor | None = None,  # NEW
    ) -> None:
        """Initialize affordance engine.

        Args:
            env: Environment instance
            affordances: List of affordance configurations
            meter_names: List of meter names (for indexing)
            modulations: List of modulation configurations
            command_executor: Effects command executor (optional for backward compat)
        """
        self.env = env
        self.affordances_list = affordances
        self.meter_names = meter_names
        self.modulations_list = modulations
        self.command_executor = command_executor  # NEW

        # Compile affordance Effects commands at startup (CRITICAL: Performance)
        self.compiled_affordances: dict[str, CompiledAffordance] = {}

        if command_executor is not None:
            parser = CommandParser()
            compiler = CommandCompiler(schema=env.effects_schema)

            for affordance in affordances:
                if affordance.interactions is not None:
                    compiled = CompiledAffordance(
                        on_start=[],
                        per_tick=[],
                        on_completion=[],
                        on_early_exit=[],
                        on_failure=[],
                    )

                    for stage in ["on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"]:
                        commands = affordance.interactions.get(stage, [])
                        if commands:
                            command_configs = [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in commands]
                            command_nodes = parser.parse_commands(command_configs)
                            compiled_commands = compiler.compile_commands(command_nodes)
                            setattr(compiled, stage, compiled_commands)

                    self.compiled_affordances[affordance.name] = compiled

        # ... rest of existing __init__ code
```

Add helper method to execute Effects commands (using pre-compiled commands):
```python
    def _execute_affordance_effects(
        self,
        affordance_name: str,
        stage: str,
        agent_mask: torch.Tensor,
        meters: torch.Tensor,
    ) -> torch.Tensor:
        """Execute pre-compiled Effects commands for affordance lifecycle stage.

        Args:
            affordance_name: Affordance name
            stage: Lifecycle stage (on_start, per_tick, on_completion, etc.)
            agent_mask: Boolean mask of agents interacting [batch]
            meters: Current meter values [batch, num_meters]

        Returns:
            Updated meters tensor [batch, num_meters]
        """
        if self.command_executor is None:
            return meters  # No Effects support, return unchanged

        if affordance_name not in self.compiled_affordances:
            return meters  # No compiled Effects, return unchanged

        compiled = self.compiled_affordances[affordance_name]
        commands = getattr(compiled, stage)

        if not commands:
            return meters  # No commands for this stage

        # Execute commands for each agent in mask
        updated_meters = meters.clone()

        for agent_idx in torch.where(agent_mask)[0]:
            context = ExecutionContext(
                target_index=agent_idx.item(),
                self_index=None,  # Affordances don't have self yet
                registry=self.env.vfs_registry,
                meters=updated_meters,
                meter_name_to_idx=self.meter_name_to_idx,
            )

            for command in commands:
                self.command_executor.execute(command, context)

            # Sync meters from VFS back to tensor
            for meter_name, meter_idx in self.meter_name_to_idx.items():
                if meter_name in self.env.vfs_registry.storage:
                    updated_meters[agent_idx, meter_idx] = self.env.vfs_registry.storage[meter_name][agent_idx]

        return updated_meters
```

Update `execute_instant_affordance` to use Effects (replace existing effects logic):
```python
    def execute_instant_affordance(
        self,
        affordance_name: str,
        meters: torch.Tensor,
        agent_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Execute instant affordance interaction."""
        updated_meters = meters.clone()

        # Execute on_start Effects commands (costs integrated as negative deltas)
        updated_meters = self._execute_affordance_effects(
            affordance_name, "on_start", agent_mask, updated_meters
        )

        # Clamp meters to [0, 1]
        updated_meters = torch.clamp(updated_meters, 0.0, 1.0)

        return updated_meters
```

**Expected:** AffordanceEngine compiles Effects at startup and reuses compiled commands (no per-execution parsing).

---

### Step 5: Wire command_executor in VectorizedHamletEnv

**File:** `src/townlet/environment/vectorized_env.py`

Find AffordanceEngine initialization (around line 500-600) and add `command_executor` parameter:

```python
# Before (old code):
self.affordance_engine = AffordanceEngine(
    env=self,
    affordances=affordances_config.affordances,
    meter_names=self.meter_names,
    modulations=affordances_config.modulations,
)

# After (with command_executor):
self.affordance_engine = AffordanceEngine(
    env=self,
    affordances=affordances_config.affordances,
    meter_names=self.meter_names,
    modulations=affordances_config.modulations,
    command_executor=self.command_executor,  # NEW: Wire Effects system
)
```

**Expected:** VectorizedHamletEnv passes command_executor to AffordanceEngine for Effects compilation.

---

### Step 6: Run test to verify it passes

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/test_affordance_engine.py::test_affordance_engine_executes_effects_commands -v
```

**Expected:** PASS

---

### Step 7: Commit schema migration

**Command:**
```bash
git add src/townlet/config/affordances_v2_config.py src/townlet/environment/affordance_engine.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/environment/test_affordance_engine.py
git commit -m "feat(affordances)!: migrate to Effects commands via interactions field

BREAKING CHANGE: effects dict and effect_pipeline removed from affordances

All affordances now use unified Effects system (interactions field):
- Add REQUIRED interactions field to AffordanceParamConfig
- Compile Effects commands at AffordanceEngine startup (performance)
- Add CompiledAffordance dataclass for pre-compiled command storage
- Integrate CommandExecutor into AffordanceEngine
- Wire command_executor in VectorizedHamletEnv
- Add _execute_affordance_effects helper using pre-compiled commands
- Remove all legacy code paths (effects dict, effect_pipeline)
- Add test for Effects command execution

Effects compiled once at startup (not per-execution) for optimal performance.
Follows ItemManager pattern.

Part of Phase 5: Affordance Migration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5.2: Config Migration & Testing (1.5 days)

**Goal:** Migrate all curriculum level affordances.yaml files from simple effects dict to Effects commands.

### Step 1: Write migration script

**File:** `scripts/migrate_affordances_to_effects.py`

```python
"""Migrate affordances.yaml from effects dict to Effects commands.

Usage:
    python scripts/migrate_affordances_to_effects.py configs/default_curriculum/levels/L0_0_minimal
    python scripts/migrate_affordances_to_effects.py --all  # Migrate all levels
"""

import argparse
import yaml
from pathlib import Path


def migrate_affordance(affordance: dict) -> dict:
    """Migrate single affordance from effects dict to interactions commands.

    Supports three input formats:
    1. Simple effects dict → interactions.on_start (costs PRESERVED)
    2. effect_pipeline → interactions (all stages)
    3. Multi-tick affordances (costs_per_tick PRESERVED)

    NOTE: costs and costs_per_tick fields are PRESERVED as affordability gates.
    Only effects/effect_pipeline are migrated to interactions.
    """
    # If already has interactions, skip
    if "interactions" in affordance:
        return affordance

    interactions = {
        "on_start": [],
        "per_tick": [],
        "on_completion": [],
        "on_early_exit": [],
        "on_failure": [],
    }

    # PATH 1: Migrate effect_pipeline (if present)
    if "effect_pipeline" in affordance:
        pipeline = affordance["effect_pipeline"]
        for stage in ["on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"]:
            for effect in pipeline.get(stage, []):
                interactions[stage].append({
                    "modify": f"target.bar.{effect['meter']}",
                    "value": f"target.bar.{effect['meter']} + {effect['amount']}",
                })

        affordance.pop("effect_pipeline")

    # PATH 2: Migrate simple effects dict (on_start only)
    else:
        effects = affordance.get("effects", {})

        # Convert effects to modify commands (on_start)
        for meter, amount in effects.items():
            interactions["on_start"].append({
                "modify": f"target.bar.{meter}",
                "value": f"target.bar.{meter} + {amount}",
            })

        # Remove effects field (migrated to interactions)
        affordance.pop("effects", None)

        # PRESERVE costs and costs_per_tick fields (affordability gates)
        # These are NOT migrated - they remain as separate pre-check mechanism

    # Add interactions
    affordance["interactions"] = interactions

    return affordance


def migrate_file(config_path: Path, dry_run: bool = False) -> None:
    """Migrate affordances.yaml file."""
    affordances_file = config_path / "affordances.yaml"

    if not affordances_file.exists():
        print(f"❌ Not found: {affordances_file}")
        return

    print(f"📝 Migrating: {affordances_file}")

    # Load YAML
    with open(affordances_file, "r") as f:
        data = yaml.safe_load(f)

    # Migrate each affordance
    affordances = data["affordances"]["affordances"]
    for aff in affordances:
        aff = migrate_affordance(aff)

    # Save (or show) result
    if dry_run:
        print(yaml.dump(data, default_flow_style=False, sort_keys=False))
    else:
        with open(affordances_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Migrated: {affordances_file}")


def main():
    parser = argparse.ArgumentParser(description="Migrate affordances to Effects commands")
    parser.add_argument("path", nargs="?", help="Path to config level directory")
    parser.add_argument("--all", action="store_true", help="Migrate all curriculum levels")
    parser.add_argument("--dry-run", action="store_true", help="Show output without writing")

    args = parser.parse_args()

    if args.all:
        levels_dir = Path("configs/default_curriculum/levels")
        for level_dir in sorted(levels_dir.iterdir()):
            if level_dir.is_dir():
                migrate_file(level_dir, dry_run=args.dry_run)
    elif args.path:
        migrate_file(Path(args.path), dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Expected:** Script can parse and migrate all three affordance formats:
- Simple effects dict → interactions.on_start
- effect_pipeline → interactions with all stages
- costs_per_tick → interactions.per_tick

---

### Step 2: Test migration script (dry-run)

**Command:**
```bash
python scripts/migrate_affordances_to_effects.py configs/default_curriculum/levels/L0_0_minimal --dry-run
```

**Expected:** Output shows migrated YAML with `interactions` field replacing `effects`. Note that `costs` and `costs_per_tick` fields are PRESERVED (not migrated).

---

### Step 3: Migrate L0_0_minimal (smallest level)

**Command:**
```bash
python scripts/migrate_affordances_to_effects.py configs/default_curriculum/levels/L0_0_minimal
```

**Expected:** `✅ Migrated: configs/default_curriculum/levels/L0_0_minimal/affordances.yaml`

---

### Step 4: Verify L0_0_minimal loads and validates

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "
from pathlib import Path
from townlet.config.affordances_v2_config import load_affordances_v2_config

config = load_affordances_v2_config(Path('configs/default_curriculum/levels/L0_0_minimal'))
print(f'✅ Loaded {len(config.affordances)} affordances')
for aff in config.affordances:
    print(f'  - {aff.name}: {len(aff.interactions.get(\"on_start\", []))} on_start commands')
"
```

**Expected:** `✅ Loaded N affordances` with command counts.

---

### Step 5: Run integration test with migrated L0_0_minimal

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_full_training_loop.py -k "L0_0" -v
```

**Expected:** PASS (L0_0_minimal training works with new Effects commands)

---

### Step 6: Migrate remaining levels

**Command:**
```bash
python scripts/migrate_affordances_to_effects.py --all
```

**Expected:** All 5 levels migrated.

---

### Step 7: Verify all levels load

**Command:**
```bash
for level in configs/default_curriculum/levels/*/; do
    echo "Testing: $level"
    UV_CACHE_DIR=.uv-cache uv run python -c "
from pathlib import Path
from townlet.config.affordances_v2_config import load_affordances_v2_config
config = load_affordances_v2_config(Path('$level'))
print(f'✅ {len(config.affordances)} affordances')
" || exit 1
done
```

**Expected:** All levels load successfully.

---

### Step 8: Run full integration test suite

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/ -v
```

**Expected:** All integration tests PASS (no regressions from migration).

---

### Step 9: Commit config migration

**Command:**
```bash
git add configs/default_curriculum/levels/*/affordances.yaml scripts/migrate_affordances_to_effects.py
git commit -m "feat(configs)!: migrate affordances to Effects commands

BREAKING CHANGE: All affordances now require interactions field

- Migrate all 5 curriculum levels to interactions (Effects commands)
- Add migration script: scripts/migrate_affordances_to_effects.py
- Convert effects/costs/costs_per_tick to modify commands
- Convert effect_pipeline to lifecycle stage commands
- All integration tests passing (clean migration)

Migrated levels:
- L0_0_minimal
- L0_5_dual_resource
- L1_full_observability
- L2_partial_observability
- L3_temporal_mechanics

Old configs with effects/effect_pipeline will fail validation.

Part of Phase 5: Affordance Migration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5.3: Delete Legacy EffectPipeline Code (0.5 days)

**Goal:** Delete effect_pipeline.py and verify all references removed.

**Note:** Fields were already removed in Task 5.1 (clean breaking change).

### Step 1: Delete effect_pipeline.py

**Command:**
```bash
git rm src/townlet/config/effect_pipeline.py
```

**Expected:** File deleted from repository.

---

### Step 2: Verify no EffectPipeline references remain

**Command:**
```bash
grep -r "EffectPipeline\|effect_pipeline" src/ tests/ --include="*.py" | grep -v "__pycache__"
```

**Expected:** No matches (all references removed).

---

### Step 3: Update reference config

**File:** `configs/reference_config/reference-config-v2.1-complete.yaml`

Remove all `effect_pipeline` examples and replace with `interactions` using Effects commands.

**Expected:** Reference config demonstrates Effects commands instead of EffectPipeline.

---

### Step 4: Run full test suite

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -v
```

**Expected:** All tests PASS.

---

### Step 5: Commit cleanup

**Command:**
```bash
git add -A
git commit -m "chore(affordances): delete legacy EffectPipeline code

- Delete src/townlet/config/effect_pipeline.py (legacy system)
- Update reference config to use interactions field
- Verify all EffectPipeline references removed

Migration complete - affordances fully unified with Effects system.

Part of Phase 5: Affordance Migration (COMPLETE)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5.4: Remove Backwards Compatibility Code (0.5 days)

**Goal:** Remove temporary backwards compatibility scaffolding added in Task 5.1 fix.

**Context:** Task 5.1 added backward compatibility (effects, effect_pipeline fields + validate_effects_exclusivity) to allow safe migration. After all configs migrated (Task 5.2) and legacy code deleted (Task 5.3), remove the compatibility layer.

### Step 1: Make interactions field REQUIRED

**File:** `src/townlet/config/affordances_v2_config.py`

Remove backward compatibility fields and make interactions required:

```python
# BEFORE (backward compatible):
effects: dict[str, float] = Field(
    default_factory=dict,
    description="[DEPRECATED] Simple instant effects (meter: value). Use interactions field instead.",
)
effect_pipeline: Any | None = Field(
    default=None,
    description="[DEPRECATED] Multi-stage effect pipeline. Use interactions field instead.",
)
interactions: dict[str, list[CommandConfig]] | None = Field(
    default=None,
    description=...
)

# AFTER (clean breaking change):
# REMOVED: effects and effect_pipeline fields

interactions: dict[str, list[CommandConfig]] = Field(
    description=(
        "Effects commands for affordance lifecycle stages. "
        "Unified with Items system (declarative Effects). "
        "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure. "
        "NOTE: Use costs/costs_per_tick for affordability gates, interactions for outcomes."
    ),
)
```

**Expected:** interactions field is REQUIRED, legacy fields deleted.

---

### Step 2: Remove validate_effects_exclusivity validator

**File:** `src/townlet/config/affordances_v2_config.py`

Delete the validator that checks for multiple effect systems:

```python
# DELETE THIS ENTIRE VALIDATOR:
@model_validator(mode="after")
def validate_effects_exclusivity(self) -> "AffordanceParamConfig":
    """Ensure only one effect system is used (legacy or new)."""
    effects_count = sum([
        bool(self.effects),
        self.effect_pipeline is not None,
        self.interactions is not None,
    ])
    # ... rest of validator ...
```

**Expected:** Validator removed (no longer needed - only one system exists).

---

### Step 3: Update validate_interaction_stages to remove legacy check

**File:** `src/townlet/config/affordances_v2_config.py`

Remove the backward compatibility skip:

```python
# BEFORE:
@model_validator(mode="after")
def validate_interaction_stages(self) -> "AffordanceParamConfig":
    """Validate interactions have correct stages for interaction_type."""
    # Skip validation if using legacy effect systems
    if self.interactions is None:
        return self
    # ... rest of validator ...

# AFTER:
@model_validator(mode="after")
def validate_interaction_stages(self) -> "AffordanceParamConfig":
    """Validate interactions have correct stages for interaction_type."""
    # interactions is always present now (required field)
    valid_stages = {"on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"}
    # ... rest of validator ...
```

**Expected:** No more legacy compatibility checks.

---

### Step 4: Verify all configs still load

**Command:**
```bash
for level in configs/default_curriculum/levels/*/; do
    echo "Testing: $level"
    UV_CACHE_DIR=.uv-cache uv run python -c "
from pathlib import Path
from townlet.config.affordances_v2_config import load_affordances_v2_config
config = load_affordances_v2_config(Path('$level'))
print(f'✅ {len(config.affordances)} affordances')
" || exit 1
done
```

**Expected:** All 5 levels load successfully (all using interactions field now).

---

### Step 5: Run full test suite

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -v
```

**Expected:** All tests PASS.

---

### Step 6: Commit cleanup

**Command:**
```bash
git add src/townlet/config/affordances_v2_config.py
git commit -m "chore(affordances)!: remove backwards compatibility scaffolding

BREAKING CHANGE: interactions field now REQUIRED, legacy fields removed

After config migration (Task 5.2) and legacy code deletion (Task 5.3),
remove temporary backwards compatibility added in Task 5.1:
- Make interactions field REQUIRED (remove Optional)
- Delete effects field (deprecated)
- Delete effect_pipeline field (deprecated)
- Delete validate_effects_exclusivity validator
- Remove legacy skip from validate_interaction_stages

All affordances now use interactions field exclusively.

Pre-release cleanup - no backwards compatibility needed (zero users).

Part of Phase 5: Affordance Migration (COMPLETE)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `src/townlet/config/effect_pipeline.py` deleted
- [ ] AffordanceParamConfig has `interactions` field (only)
- [ ] All 5 curriculum levels use `interactions` syntax
- [ ] Reference config uses `interactions` syntax
- [ ] AffordanceEngine uses CommandExecutor
- [ ] No `grep -r "EffectPipeline"` matches in src/tests
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Training loop works with L0_0_minimal
- [ ] Training loop works with L1_full_observability

**Success Criteria:**
- ✅ All curriculum levels migrated to interactions field
- ✅ EffectPipeline code completely deleted (no legacy paths)
- ✅ effects and effect_pipeline fields removed from schema
- ✅ Zero regressions in existing tests
- ✅ Affordances use unified Effects system (same as Items)
- ✅ Effects compiled at startup for optimal performance

---

## Troubleshooting

**Issue:** Effects modify wrong agent (batch indexing bug)

**Solution:** Ensure ExecutionContext uses correct target_index:
```python
context = ExecutionContext(
    target_index=agent_idx.item(),  # Convert tensor to int!
    self_index=None,
    registry=self.env.vfs_registry,
    meters=updated_meters,
    meter_name_to_idx=self.meter_name_to_idx,
)
```

---

## Post-Migration Cleanup

**Optional enhancements** (not required for Phase 5 completion):

1. **Add affordance self-reference support**
   - Enable affordances to have VFS state (like items)
   - Example: `self.vfs.door_locked` for door affordance

2. **Add conditional effects**
   - Example: "WORK pays more if mood > 0.5"
   - Use `if:` conditions in Effects commands

3. **Add multi-target effects**
   - Example: SOCIALIZE affects both agents
   - Use `modify: "agents[*].bar.social"` syntax

---

## End of Plan

**Estimated Timeline:** 4-5 days
- Task 5.1: Schema Migration (1.5 days) - includes compilation optimization + backward compat
- Task 5.2: Config Migration (2 days) - extended migration script
- Task 5.3: Legacy Code Deletion (0.5 days) - delete effect_pipeline.py
- Task 5.4: Remove Backward Compatibility (0.5 days) - clean breaking change

**Total LOC Changes:**
- Added: ~400 lines (migration script, Effects integration, compilation optimization)
- Modified: ~150 lines (affordance_engine, vectorized_env, configs)
- Deleted: ~150 lines (effect_pipeline.py, legacy code paths)

**Net Change:** +400 lines, -1 legacy system, +1 unified architecture

**Performance Impact:** ✅ Positive - Effects compiled once at startup vs per-execution
