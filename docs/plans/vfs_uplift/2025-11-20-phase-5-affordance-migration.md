# Phase 5: Affordance Migration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate affordances from EffectPipeline (opaque dict system) to Effects commands (declarative, unified system).

**Architecture:** Replace the 5-stage EffectPipeline (on_start, per_tick, on_completion, on_early_exit, on_failure) with Effects commands that integrate with the existing CommandExecutor. This unifies affordance interactions with the Items system, enabling future enhancements like conditional effects, VFS references, and expression-based logic.

**Tech Stack:** Pydantic DTOs, Effects system (CommandCompiler + CommandExecutor), PyTorch tensors, YAML configuration

**Timeline:** 3-4 days (Task 5.1: 1 day, Task 5.2: 1.5 days, Task 5.3: 0.5 days)

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

**Migration Path:**
1. **Preserve simple effects dict** (backward compatible during migration)
2. **Add new `interactions` field** with Effects commands
3. **Update affordance_engine** to execute Effects commands
4. **Migrate configs** from simple dicts to Effects commands
5. **Remove `effect_pipeline` and `effects` fields** (breaking change)
6. **Delete EffectPipeline code**

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

Update AffordanceParamConfig to add new field after `effect_pipeline`:
```python
    # Effect semantics -------------------------------------------------------
    effects: dict[str, float] = Field(
        default_factory=dict,
        description="Simple instant effects (meter: value). "
        "For advanced control, use effect_pipeline instead.",
    )
    effect_pipeline: EffectPipeline | None = Field(
        default=None,
        description=(
            "Optional multi-stage effect pipeline. "
            "When provided, takes precedence over simple effects for runtime behavior."
        ),
    )

    # NEW: Effects commands (unified with Items system)
    interactions: dict[str, list[CommandConfig]] | None = Field(
        default=None,
        description=(
            "Effects commands for affordance lifecycle stages. "
            "Replaces effect_pipeline with declarative command system. "
            "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure"
        ),
    )
```

Add validator after `validate_interaction_semantics`:
```python
    @model_validator(mode="after")
    def validate_effects_exclusivity(self) -> "AffordanceParamConfig":
        """Ensure only one effect system is used."""
        effects_count = sum([
            bool(self.effects),
            self.effect_pipeline is not None,
            self.interactions is not None,
        ])

        if effects_count > 1:
            raise ValueError(
                f"Affordance '{self.name}': Only one of [effects, effect_pipeline, interactions] "
                "may be specified. Use 'interactions' for new affordances (Effects system)."
            )

        if effects_count == 0:
            raise ValueError(
                f"Affordance '{self.name}': Must specify one of [effects, effect_pipeline, interactions]. "
                "Use 'interactions' for new affordances (Effects system)."
            )

        return self

    @model_validator(mode="after")
    def validate_interaction_stages(self) -> "AffordanceParamConfig":
        """Validate interactions have correct stages for interaction_type."""
        if self.interactions is None:
            return self

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
```

Update `__init__` to accept command_executor:
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

        # ... rest of existing __init__ code
```

Add helper method to execute Effects commands:
```python
    def _execute_affordance_effects(
        self,
        affordance: AffordanceParamConfig,
        stage: str,
        agent_mask: torch.Tensor,
        meters: torch.Tensor,
    ) -> torch.Tensor:
        """Execute Effects commands for affordance lifecycle stage.

        Args:
            affordance: Affordance configuration
            stage: Lifecycle stage (on_start, per_tick, on_completion, etc.)
            agent_mask: Boolean mask of agents interacting [batch]
            meters: Current meter values [batch, num_meters]

        Returns:
            Updated meters tensor [batch, num_meters]
        """
        if self.command_executor is None:
            return meters  # No Effects support, return unchanged

        if affordance.interactions is None:
            return meters  # No Effects commands, return unchanged

        commands = affordance.interactions.get(stage, [])
        if not commands:
            return meters  # No commands for this stage

        # Parse commands to CommandNode AST (if not already compiled)
        from townlet.effects.parser import CommandParser
        from townlet.effects.compiler import CommandCompiler

        parser = CommandParser()
        compiler = CommandCompiler(schema=self.env.effects_schema)

        command_configs = [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in commands]
        command_nodes = parser.parse_commands(command_configs)
        compiled_commands = compiler.compile_commands(command_nodes)

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

            self.command_executor.execute_commands(compiled_commands, context)

            # Sync meters from VFS back to tensor
            for meter_name, meter_idx in self.meter_name_to_idx.items():
                if meter_name in self.env.vfs_registry.storage:
                    updated_meters[agent_idx, meter_idx] = self.env.vfs_registry.storage[meter_name][agent_idx]

        return updated_meters
```

Update `execute_instant_affordance` to use Effects (after line ~200):
```python
    def execute_instant_affordance(
        self,
        affordance_name: str,
        meters: torch.Tensor,
        agent_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Execute instant affordance interaction."""
        affordance = self.affordances[affordance_name]
        updated_meters = meters.clone()

        # ... existing code for costs ...

        # Apply effects (THREE PATHS: interactions > effect_pipeline > effects dict)

        # PATH 1: New Effects commands (PREFERRED)
        if affordance.interactions is not None:
            updated_meters = self._execute_affordance_effects(
                affordance, "on_start", agent_mask, updated_meters
            )

        # PATH 2: EffectPipeline (LEGACY - to be removed)
        elif hasattr(affordance, "effect_pipeline") and affordance.effect_pipeline:
            # ... existing effect_pipeline code ...

        # PATH 3: Simple effects dict (LEGACY - to be removed)
        else:
            # ... existing effects dict code ...

        # Clamp meters to [0, 1]
        updated_meters = torch.clamp(updated_meters, 0.0, 1.0)

        return updated_meters
```

**Expected:** AffordanceEngine can execute Effects commands.

---

### Step 5: Run test to verify it passes

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/environment/test_affordance_engine.py::test_affordance_engine_executes_effects_commands -v
```

**Expected:** PASS

---

### Step 6: Commit schema migration

**Command:**
```bash
git add src/townlet/config/affordances_v2_config.py src/townlet/environment/affordance_engine.py tests/test_townlet/unit/environment/test_affordance_engine.py
git commit -m "feat(affordances): add Effects commands support via interactions field

- Add interactions field to AffordanceParamConfig with lifecycle stages
- Integrate CommandExecutor into AffordanceEngine
- Add _execute_affordance_effects helper method
- Backward compatible: interactions > effect_pipeline > effects dict
- Add test for Effects command execution in affordances

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
    """Migrate single affordance from effects dict to interactions commands."""
    # If already has interactions, skip
    if "interactions" in affordance:
        return affordance

    # Convert effects dict to on_start commands
    effects = affordance.get("effects", {})
    costs = affordance.get("costs", {})

    interactions = {
        "on_start": [],
        "per_tick": [],
        "on_completion": [],
        "on_early_exit": [],
        "on_failure": [],
    }

    # Convert effects to modify commands
    for meter, amount in effects.items():
        interactions["on_start"].append({
            "modify": f"target.bar.{meter}",
            "value": f"target.bar.{meter} + {amount}",
        })

    # Convert costs to modify commands (negative delta)
    for meter, cost in costs.items():
        interactions["on_start"].append({
            "modify": f"target.bar.{meter}",
            "value": f"target.bar.{meter} - {cost}",
        })

    # Remove old fields
    affordance.pop("effects", None)
    affordance.pop("costs", None)

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

**Expected:** Script can parse and migrate affordances.yaml files.

---

### Step 2: Test migration script (dry-run)

**Command:**
```bash
python scripts/migrate_affordances_to_effects.py configs/default_curriculum/levels/L0_0_minimal --dry-run
```

**Expected:** Output shows migrated YAML with `interactions` field replacing `effects` and `costs`.

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
git commit -m "feat(configs): migrate affordances to Effects commands

- Migrate all 5 curriculum levels from effects dict to interactions
- Add migration script: scripts/migrate_affordances_to_effects.py
- Convert effects/costs to modify commands with expressions
- All integration tests passing (verified backward compatibility)

Migrated levels:
- L0_0_minimal
- L0_5_dual_resource
- L1_full_observability
- L2_partial_observability
- L3_temporal_mechanics

Part of Phase 5: Affordance Migration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5.3: Code Cleanup & EffectPipeline Removal (0.5 days)

**Goal:** Delete deprecated EffectPipeline code and remove all references.

### Step 1: Remove effect_pipeline field from AffordanceParamConfig

**File:** `src/townlet/config/affordances_v2_config.py`

Remove import:
```python
from townlet.config.effect_pipeline import EffectPipeline  # DELETE THIS LINE
```

Remove field from AffordanceParamConfig:
```python
    # Effect semantics -------------------------------------------------------
    effects: dict[str, float] = Field(
        default_factory=dict,
        description="Simple instant effects (meter: value). "
        "DEPRECATED: Use interactions field instead.",
    )
    # DELETE effect_pipeline field entirely

    interactions: dict[str, list[CommandConfig]] | None = Field(
        default=None,
        description=(
            "Effects commands for affordance lifecycle stages. "
            "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure"
        ),
    )
```

Update validator to require interactions:
```python
    @model_validator(mode="after")
    def validate_effects_required(self) -> "AffordanceParamConfig":
        """Ensure interactions field is provided."""
        if self.interactions is None:
            raise ValueError(
                f"Affordance '{self.name}': interactions field is required. "
                "Simple effects dict is deprecated."
            )
        return self
```

**Expected:** AffordanceParamConfig no longer has effect_pipeline or effects fields.

---

### Step 2: Remove EffectPipeline code paths from affordance_engine

**File:** `src/townlet/environment/affordance_engine.py`

In `execute_instant_affordance`, remove PATH 2 and PATH 3:
```python
    def execute_instant_affordance(
        self,
        affordance_name: str,
        meters: torch.Tensor,
        agent_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Execute instant affordance interaction."""
        affordance = self.affordances[affordance_name]
        updated_meters = meters.clone()

        # Costs are now part of interactions (modify commands with negative delta)
        # No separate costs processing needed

        # Execute on_start Effects commands
        updated_meters = self._execute_affordance_effects(
            affordance, "on_start", agent_mask, updated_meters
        )

        # Clamp meters to [0, 1]
        updated_meters = torch.clamp(updated_meters, 0.0, 1.0)

        return updated_meters
```

Similarly update `execute_multi_tick_affordance_tick` and `execute_dual_mode_affordance_as_instant`.

**Expected:** Affordance engine only uses Effects commands.

---

### Step 3: Delete effect_pipeline.py

**Command:**
```bash
git rm src/townlet/config/effect_pipeline.py
```

**Expected:** File deleted from repository.

---

### Step 4: Remove EffectPipeline from tests

**File:** `tests/test_townlet/unit/environment/test_affordance_engine.py`

Remove all tests that reference EffectPipeline or effect_pipeline.

Update remaining tests to use `interactions` field.

**Expected:** All tests use new Effects system.

---

### Step 5: Verify no EffectPipeline references remain

**Command:**
```bash
grep -r "EffectPipeline\|effect_pipeline" src/ tests/ --include="*.py" | grep -v "__pycache__"
```

**Expected:** No matches (all references removed).

---

### Step 6: Run full test suite

**Command:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -v
```

**Expected:** All tests PASS.

---

### Step 7: Update reference config

**File:** `configs/reference_config/reference-config-v2.1-complete.yaml`

Remove all `effect_pipeline` examples and replace with `interactions` using Effects commands.

**Expected:** Reference config demonstrates Effects commands instead of EffectPipeline.

---

### Step 8: Commit cleanup

**Command:**
```bash
git add -A
git commit -m "refactor(affordances): remove EffectPipeline system

BREAKING CHANGE: effect_pipeline and effects dict removed from affordances

- Delete src/townlet/config/effect_pipeline.py
- Remove effect_pipeline field from AffordanceParamConfig
- Remove effects dict field (deprecated)
- Simplify affordance_engine to only use Effects commands
- Update tests to use interactions field
- Update reference config examples

All affordances now use unified Effects system (interactions field).
Migration complete - EffectPipeline code fully removed.

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
- ✅ All curriculum levels migrated
- ✅ EffectPipeline code deleted
- ✅ Zero regressions in existing tests
- ✅ Affordances use unified Effects system

---

## Troubleshooting

**Issue:** Migration script fails on multi_tick affordances

**Solution:** Extend migration script to handle `costs_per_tick` and map to `per_tick` stage:
```python
# In migrate_affordance():
costs_per_tick = affordance.get("costs_per_tick", {})
for meter, cost in costs_per_tick.items():
    interactions["per_tick"].append({
        "modify": f"target.bar.{meter}",
        "value": f"target.bar.{meter} - {cost}",
    })
```

---

**Issue:** Tests fail with "command_executor is None"

**Solution:** Update VectorizedHamletEnv to pass command_executor to AffordanceEngine:
```python
self.affordance_engine = AffordanceEngine(
    env=self,
    affordances=affordances_config.affordances,
    meter_names=self.meter_names,
    modulations=affordances_config.modulations,
    command_executor=self.command_executor,  # ADD THIS
)
```

---

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

1. **Compile affordance Effects at startup** (similar to ItemManager)
   - Pre-compile CommandNodes during affordance_engine initialization
   - Avoid parsing YAML strings on every interaction

2. **Add affordance self-reference support**
   - Enable affordances to have VFS state (like items)
   - Example: `self.vfs.door_locked` for door affordance

3. **Add conditional effects**
   - Example: "WORK pays more if mood > 0.5"
   - Use `if:` conditions in Effects commands

4. **Add multi-target effects**
   - Example: SOCIALIZE affects both agents
   - Use `modify: "agents[*].bar.social"` syntax

---

## End of Plan

**Estimated Timeline:** 3-4 days
- Task 5.1: Schema Migration (1 day)
- Task 5.2: Config Migration (1.5 days)
- Task 5.3: Code Cleanup (0.5 days)

**Total LOC Changes:**
- Added: ~300 lines (migration script, Effects integration)
- Modified: ~100 lines (affordance_engine, configs)
- Deleted: ~150 lines (effect_pipeline.py, legacy code paths)

**Net Change:** +150 lines, -1 legacy system, +1 unified architecture
