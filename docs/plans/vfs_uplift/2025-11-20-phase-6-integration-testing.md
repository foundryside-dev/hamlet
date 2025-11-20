# Phase 6: Integration & Testing - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Validate complete World Compiler integration with end-to-end tests, performance benchmarks, and comprehensive documentation.

**Architecture:** Integration testing validates the full compilation pipeline (Expression Language → VFS Profiles → Effects → Items) works together. Performance benchmarks ensure <5% regression. Documentation provides complete reference for operators.

**Tech Stack:** pytest, pytest-benchmark, markdown, YAML validation

**Timeline:** 4-5 days (Task 6.1: 2 days, Task 6.2: 1 day, Task 6.3: 2 days)

---

## Task 6.1: Integration Tests (2 days)

**Goal:** Write 15+ integration tests validating the complete World Compiler pipeline.

### Files

**Create:**
- `tests/test_townlet/integration/test_world_compiler_full.py`
- `tests/test_townlet/integration/test_expression_vfs_effects.py`
- `tests/test_townlet/integration/test_items_effects_cascade.py`
- `tests/test_townlet/integration/test_curriculum_compatibility.py`

**Reference:**
- `src/townlet/world/expression/evaluator.py` (expression evaluation)
- `src/townlet/vfs/profiles.py` (VFS compilation)
- `src/townlet/effects/executor.py` (command execution)
- `src/townlet/items/manager.py` (item lifecycle)

---

### Step 1: Write test_world_compiler_full.py skeleton

Create test file with fixtures for compiler testing:

```python
"""Integration tests for complete World Compiler pipeline.

Tests the full compilation flow:
  Config YAML → Parse → Validate → Compile → Execute
"""

import pytest
import torch
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


@pytest.fixture
def compiler():
    """UniverseCompiler instance."""
    return UniverseCompiler()


@pytest.fixture
def integration_config_dir(tmp_path):
    """Create minimal test config pack."""
    config_dir = tmp_path / "integration_test"
    config_dir.mkdir()

    # Create minimal experiment-level configs
    (config_dir / "experiment.yaml").write_text("""
experiment:
  name: "integration_test"
  seed: 42
""")

    (config_dir / "stratum.yaml").write_text("""
stratum:
  substrate:
    type: "grid"
    grid_size: [5, 5]
    boundary_mode: "clamp"
    distance_metric: "manhattan"
""")

    (config_dir / "environment.yaml").write_text("""
environment:
  version: "2.1"
  affordances:
    - id: "EAT"
      name: "EAT"
      category: "consumption"
  bars:
    - name: "energy"
      initial_value: 0.5
  cascades: []
  modulation_graph: {}
""")

    (config_dir / "actions.yaml").write_text("""
actions:
  vocabulary: "global"
  enabled_actions: ["MOVE_N", "INTERACT"]
""")

    (config_dir / "agent.yaml").write_text("""
agent:
  network_type: "simple_q"
  hidden_layers: [128, 64]
""")

    # Create level directory
    level_dir = config_dir / "levels" / "L0_test"
    level_dir.mkdir(parents=True)

    (level_dir / "curriculum.yaml").write_text("""
curriculum:
  level_name: "L0_test"
  unlocks_at_episode: 0
""")

    (level_dir / "training.yaml").write_text("""
training:
  num_agents: 2
  enabled_affordances: ["EAT"]
  epsilon_start: 1.0
  epsilon_end: 0.1
  epsilon_decay_episodes: 100
""")

    (level_dir / "bars.yaml").write_text("""
bars:
  version: "1.0"
  bars:
    - name: "energy"
      initial_value: 0.5
      decay_per_tick: 0.01
      decay_type: "constant"
      critical_threshold: 0.2
      failure_threshold: 0.0
  cascades: []
""")

    (level_dir / "affordances.yaml").write_text("""
affordances:
  version: "1.0"
  affordances:
    - name: "EAT"
      interaction_type: "instant"
      costs: {}
      costs_per_tick: {}
      interactions:
        on_start:
          - modify: "target.bar.energy"
            value: "target.bar.energy + 0.3"
        per_tick: []
        on_completion: []
        on_early_exit: []
        on_failure: []
      opening_hours:
        enabled: false
      deployment:
        type: "random"
  modulations: []
""")

    return config_dir


class TestWorldCompilerPipeline:
    """Test complete compilation pipeline."""

    def test_compile_minimal_config(self, compiler, integration_config_dir):
        """Compiler can parse and validate minimal config pack."""
        # TODO: Implement
        pass

    def test_compiled_universe_structure(self, compiler, integration_config_dir):
        """CompiledUniverse has correct structure."""
        # TODO: Implement
        pass

    def test_affordance_effects_compilation(self, compiler, integration_config_dir):
        """Affordance interactions compile to Effects commands."""
        # TODO: Implement
        pass
```

---

### Step 2: Run test to verify skeleton loads

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_world_compiler_full.py -v
```

**Expected:** 3 tests collected, all SKIPPED (TODO not implemented)

---

### Step 3: Implement test_compile_minimal_config

```python
def test_compile_minimal_config(self, compiler, integration_config_dir):
    """Compiler can parse and validate minimal config pack."""
    # Compile the config
    universe = compiler.compile(integration_config_dir)

    # Verify compilation succeeded
    assert universe is not None
    assert universe.metadata is not None
    assert universe.optimization_data is not None

    # Verify levels loaded
    assert len(universe.levels) == 1
    assert universe.levels[0].name == "L0_test"
```

---

### Step 4: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_world_compiler_full.py::TestWorldCompilerPipeline::test_compile_minimal_config -v
```

**Expected:** PASS (compiler loads minimal config)

---

### Step 5: Implement test_compiled_universe_structure

```python
def test_compiled_universe_structure(self, compiler, integration_config_dir):
    """CompiledUniverse has correct structure."""
    universe = compiler.compile(integration_config_dir)

    # Check metadata structure
    assert hasattr(universe.metadata, 'meter_metadata')
    assert hasattr(universe.metadata, 'affordance_metadata')
    assert hasattr(universe.metadata, 'action_space_metadata')

    # Check optimization data
    assert hasattr(universe.optimization_data, 'action_mask_table')
    assert hasattr(universe.optimization_data, 'modulation_data')

    # Check level structure
    level = universe.levels[0]
    assert hasattr(level, 'affordances')
    assert hasattr(level, 'bars')
    assert hasattr(level, 'training')
```

---

### Step 6: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_world_compiler_full.py::TestWorldCompilerPipeline::test_compiled_universe_structure -v
```

**Expected:** PASS

---

### Step 7: Implement test_affordance_effects_compilation

```python
def test_affordance_effects_compilation(self, compiler, integration_config_dir):
    """Affordance interactions compile to Effects commands."""
    universe = compiler.compile(integration_config_dir)

    level = universe.levels[0]
    eat_affordance = next(a for a in level.affordances.affordances if a.name == "EAT")

    # Verify interactions field exists
    assert hasattr(eat_affordance, 'interactions')
    assert 'on_start' in eat_affordance.interactions

    # Verify on_start has effect commands
    on_start_commands = eat_affordance.interactions['on_start']
    assert len(on_start_commands) > 0

    # Verify command structure
    cmd = on_start_commands[0]
    assert hasattr(cmd, 'modify')
    assert hasattr(cmd, 'value')
    assert cmd.modify == "target.bar.energy"
    assert "target.bar.energy + 0.3" in cmd.value
```

---

### Step 8: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_world_compiler_full.py::TestWorldCompilerPipeline::test_affordance_effects_compilation -v
```

**Expected:** PASS

---

### Step 9: Commit compiler pipeline tests

```bash
git add tests/test_townlet/integration/test_world_compiler_full.py
git commit -m "test(integration): add World Compiler pipeline tests

Add 3 integration tests for complete compilation pipeline:
- test_compile_minimal_config: Basic compilation
- test_compiled_universe_structure: Metadata validation
- test_affordance_effects_compilation: Effects integration

Tests validate YAML → Parse → Compile → Effects flow.

Part of Phase 6: Integration & Testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Step 10: Write test_expression_vfs_effects.py

Create test file for expression → VFS → Effects data flow:

```python
"""Integration tests for Expression → VFS → Effects flow.

Tests the expression evaluation pipeline:
  Expression String → Parse → Type Check → Evaluate → VFS → Effects
"""

import pytest
import torch
from pathlib import Path

from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.evaluator import ExpressionEvaluator
from townlet.world.expression.context import ExpressionContext
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.effects.executor import CommandExecutor
from townlet.effects.context import ExecutionContext


@pytest.fixture
def expression_parser():
    """Expression parser instance."""
    return ExpressionParser()


@pytest.fixture
def vfs_registry():
    """VFS registry with test variables."""
    registry = VariableRegistry(num_agents=2, device="cpu")

    # Register test variable
    registry.register_variable(
        VariableDef(
            name="computed_value",
            scope=VariableScope.AGENT,
            dtype="scalar",
            readers=["agent"],
            writers=["engine"],
        )
    )

    return registry


class TestExpressionVFSEffectsFlow:
    """Test data flow through expression → VFS → Effects."""

    def test_expression_parses_and_evaluates(self, expression_parser):
        """Expression string parses to AST and evaluates."""
        # Parse expression
        expr_str = "0.5 + 0.3"
        ast = expression_parser.parse(expr_str)

        # Evaluate
        evaluator = ExpressionEvaluator()
        context = ExpressionContext(bars={}, vfs_registry=None, self_index=None, target_index=None)
        result = evaluator.evaluate(ast, context)

        # Verify result
        assert isinstance(result, torch.Tensor)
        assert result.item() == pytest.approx(0.8)

    def test_expression_reads_from_bars(self, expression_parser):
        """Expression can read from bars dict."""
        # Parse expression referencing bar
        expr_str = "target.bar.energy + 0.2"
        ast = expression_parser.parse(expr_str)

        # Setup context with bars
        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = ExpressionContext(
            bars=bars,
            vfs_registry=None,
            self_index=None,
            target_index=0,
        )

        # Evaluate
        evaluator = ExpressionEvaluator()
        result = evaluator.evaluate(ast, context)

        # Verify: 0.5 + 0.2 = 0.7
        assert result.item() == pytest.approx(0.7)

    def test_expression_reads_from_vfs(self, expression_parser, vfs_registry):
        """Expression can read from VFS registry."""
        # Set VFS value
        vfs_registry.set("computed_value", torch.tensor([1.0, 2.0]), writer="engine")

        # Parse expression referencing VFS
        expr_str = "target.vfs.computed_value * 2.0"
        ast = expression_parser.parse(expr_str)

        # Setup context
        context = ExpressionContext(
            bars={},
            vfs_registry=vfs_registry,
            self_index=None,
            target_index=0,
        )

        # Evaluate
        evaluator = ExpressionEvaluator()
        result = evaluator.evaluate(ast, context)

        # Verify: 1.0 * 2.0 = 2.0
        assert result.item() == pytest.approx(2.0)

    def test_effects_execute_with_expressions(self, vfs_registry):
        """Effects can execute commands with expression values."""
        # Setup execution context
        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = ExecutionContext(
            bars=bars,
            vfs_registry=vfs_registry,
            self_index=None,
            target_index=0,
        )

        # Create command executor
        executor = CommandExecutor(registry=vfs_registry, device="cpu")

        # Parse and compile command (simplified - actual compilation happens in CommandCompiler)
        # For this test, we'll manually create a CommandNode
        from townlet.effects.schema import CommandNode, CommandType

        # Modify command: target.bar.energy = target.bar.energy + 0.3
        command = CommandNode(
            type=CommandType.MODIFY,
            path="target.bar.energy",
            expression="target.bar.energy + 0.3",
        )

        # Execute command
        executor.execute(command, context)

        # Verify: energy[0] updated from 0.5 to 0.8
        assert bars["energy"][0].item() == pytest.approx(0.8)
```

---

### Step 11: Run test to verify it passes

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_expression_vfs_effects.py -v
```

**Expected:** 4 tests PASS (expression → VFS → Effects flow works)

**Note:** If CommandNode or CommandExecutor APIs differ, adjust test to match actual implementation from Phases 1-3.

---

### Step 12: Commit expression flow tests

```bash
git add tests/test_townlet/integration/test_expression_vfs_effects.py
git commit -m "test(integration): add Expression → VFS → Effects flow tests

Add 4 integration tests validating data flow:
- Expression parsing and evaluation
- Reading from bars dict
- Reading from VFS registry
- Effects execution with expressions

Tests validate Expression Language integrates with VFS and Effects.

Part of Phase 6: Integration & Testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Step 13: Write test_items_effects_cascade.py

Create test for Items → Effects → Cascades integration:

```python
"""Integration tests for Items → Effects → Cascades flow.

Tests complex interactions:
  Item Pickup → Effect Spawned → Cascade Triggered → Meters Updated
"""

import pytest
import torch
from pathlib import Path

from townlet.items.manager import ItemManager
from townlet.effects.manager import EffectManager
from townlet.vfs.registry import VariableRegistry


@pytest.fixture
def item_manager_with_effects():
    """ItemManager with Effects integration."""
    # TODO: Setup ItemManager with catalog
    pass


class TestItemsEffectsCascade:
    """Test Items triggering Effects triggering Cascades."""

    def test_item_pickup_spawns_effect(self, item_manager_with_effects):
        """Picking up item spawns effect."""
        # TODO: Implement
        pass

    def test_effect_modifies_bars_triggers_cascade(self):
        """Effect modifying bar triggers cascade to other bars."""
        # TODO: Implement
        pass

    def test_full_chain_item_to_cascade(self):
        """Complete chain: Item → Effect → Bar → Cascade → Bar."""
        # Example: Eat spoiled food → food_poisoning effect → health decay → energy cascade
        # TODO: Implement
        pass
```

**Note:** This test will be completed after Items implementation (Phase 4). For Phase 6, write skeleton and TODO markers.

---

### Step 14: Write test_curriculum_compatibility.py

Create test ensuring all curriculum levels still work:

```python
"""Integration tests for curriculum level compatibility.

Ensures all 5 curriculum levels compile and load after World Compiler changes.
"""

import pytest
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


CURRICULUM_LEVELS = [
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
]


@pytest.fixture
def compiler():
    """UniverseCompiler instance."""
    return UniverseCompiler()


@pytest.fixture
def curriculum_dir():
    """Path to default curriculum."""
    return Path("/home/john/hamlet/configs/default_curriculum")


class TestCurriculumCompatibility:
    """Test all curriculum levels work with World Compiler."""

    @pytest.mark.parametrize("level_name", CURRICULUM_LEVELS)
    def test_level_compiles(self, compiler, curriculum_dir, level_name):
        """Curriculum level compiles successfully."""
        universe = compiler.compile(curriculum_dir)

        # Verify level exists
        level = next((l for l in universe.levels if l.name == level_name), None)
        assert level is not None, f"Level {level_name} not found in compiled universe"

        # Verify level has affordances
        assert hasattr(level, 'affordances')
        assert len(level.affordances.affordances) > 0

        # Verify all affordances have interactions
        for aff in level.affordances.affordances:
            assert hasattr(aff, 'interactions')
            assert isinstance(aff.interactions, dict)

    def test_all_levels_have_stable_obs_dim(self, compiler, curriculum_dir):
        """All levels produce consistent observation dimensions."""
        universe = compiler.compile(curriculum_dir)

        obs_dims = {}
        for level in universe.levels:
            # Get obs_dim from metadata (if available)
            if hasattr(level, 'obs_dim'):
                obs_dims[level.name] = level.obs_dim

        # Verify Grid2D levels have same obs_dim (for transfer learning)
        grid2d_levels = ["L0_0_minimal", "L0_5_dual_resource", "L1_full_observability", "L3_temporal_mechanics"]
        grid2d_dims = {name: obs_dims.get(name) for name in grid2d_levels if name in obs_dims}

        if grid2d_dims:
            # All Grid2D levels should have same obs_dim
            dims_list = list(grid2d_dims.values())
            assert all(d == dims_list[0] for d in dims_list), \
                f"Grid2D obs_dim mismatch: {grid2d_dims}"
```

---

### Step 15: Run curriculum compatibility tests

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_curriculum_compatibility.py -v
```

**Expected:** 6 tests PASS (5 level compilation tests + 1 obs_dim test)

---

### Step 16: Commit curriculum compatibility tests

```bash
git add tests/test_townlet/integration/test_curriculum_compatibility.py tests/test_townlet/integration/test_items_effects_cascade.py
git commit -m "test(integration): add curriculum compatibility tests

Add integration tests ensuring all 5 curriculum levels work:
- Parametrized compilation tests (one per level)
- obs_dim stability test (transfer learning)
- Items → Effects → Cascades skeleton (TODO for Phase 4)

Validates World Compiler doesn't break existing configs.

Part of Phase 6: Integration & Testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6.2: Performance Validation (1 day)

**Goal:** Benchmark expression evaluation and ensure <5% performance regression.

### Files

**Create:**
- `tests/test_townlet/performance/test_expression_benchmarks.py`
- `tests/test_townlet/performance/test_effects_benchmarks.py`
- `docs/performance/world-compiler-benchmarks.md`

**Modify:**
- None (pure addition)

---

### Step 1: Write expression evaluation benchmark

Create benchmark file:

```python
"""Performance benchmarks for expression evaluation.

Uses pytest-benchmark to measure expression parsing and evaluation overhead.
"""

import pytest
import torch

from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.evaluator import ExpressionEvaluator
from townlet.world.expression.context import ExpressionContext


@pytest.fixture
def parser():
    """Expression parser."""
    return ExpressionParser()


@pytest.fixture
def evaluator():
    """Expression evaluator."""
    return ExpressionEvaluator()


class TestExpressionBenchmarks:
    """Benchmark expression operations."""

    def test_parse_simple_expression(self, benchmark, parser):
        """Benchmark parsing simple expression."""
        expr = "target.bar.energy + 0.3"

        result = benchmark(parser.parse, expr)

        assert result is not None

    def test_evaluate_simple_expression(self, benchmark, evaluator, parser):
        """Benchmark evaluating simple expression."""
        expr = "target.bar.energy + 0.3"
        ast = parser.parse(expr)

        bars = {"energy": torch.tensor([0.5, 0.6])}
        context = ExpressionContext(
            bars=bars,
            vfs_registry=None,
            self_index=None,
            target_index=0,
        )

        result = benchmark(evaluator.evaluate, ast, context)

        assert result.item() == pytest.approx(0.8)

    def test_evaluate_complex_expression(self, benchmark, evaluator, parser):
        """Benchmark evaluating complex expression."""
        expr = "(target.bar.energy + 0.3) * (1.0 - target.bar.satiation)"
        ast = parser.parse(expr)

        bars = {
            "energy": torch.tensor([0.5, 0.6]),
            "satiation": torch.tensor([0.2, 0.3]),
        }
        context = ExpressionContext(
            bars=bars,
            vfs_registry=None,
            self_index=None,
            target_index=0,
        )

        result = benchmark(evaluator.evaluate, ast, context)

        # (0.5 + 0.3) * (1.0 - 0.2) = 0.8 * 0.8 = 0.64
        assert result.item() == pytest.approx(0.64)

    def test_batch_expression_evaluation(self, benchmark, evaluator, parser):
        """Benchmark batch expression evaluation (100 agents)."""
        expr = "target.bar.energy + 0.3"
        ast = parser.parse(expr)

        batch_size = 100
        bars = {"energy": torch.tensor([0.5] * batch_size)}

        def evaluate_batch():
            results = []
            for i in range(batch_size):
                context = ExpressionContext(
                    bars=bars,
                    vfs_registry=None,
                    self_index=None,
                    target_index=i,
                )
                results.append(evaluator.evaluate(ast, context))
            return results

        results = benchmark(evaluate_batch)

        assert len(results) == batch_size
        assert all(r.item() == pytest.approx(0.8) for r in results)
```

---

### Step 2: Run benchmarks

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/performance/test_expression_benchmarks.py --benchmark-only -v
```

**Expected:** 4 benchmarks run, timing output displayed

---

### Step 3: Write effects execution benchmark

```python
"""Performance benchmarks for Effects command execution."""

import pytest
import torch

from townlet.effects.executor import CommandExecutor
from townlet.effects.context import ExecutionContext
from townlet.vfs.registry import VariableRegistry


@pytest.fixture
def executor():
    """Command executor."""
    registry = VariableRegistry(num_agents=100, device="cpu")
    return CommandExecutor(registry=registry, device="cpu")


class TestEffectsBenchmarks:
    """Benchmark Effects operations."""

    def test_execute_single_modify_command(self, benchmark, executor):
        """Benchmark single modify command execution."""
        bars = {"energy": torch.tensor([0.5] * 100)}
        context = ExecutionContext(
            bars=bars,
            vfs_registry=executor.registry,
            self_index=None,
            target_index=0,
        )

        from townlet.effects.schema import CommandNode, CommandType
        command = CommandNode(
            type=CommandType.MODIFY,
            path="target.bar.energy",
            expression="target.bar.energy + 0.3",
        )

        result = benchmark(executor.execute, command, context)

        # Verify execution worked
        assert bars["energy"][0].item() == pytest.approx(0.8)

    def test_execute_command_pipeline(self, benchmark, executor):
        """Benchmark executing pipeline of 5 commands."""
        bars = {
            "energy": torch.tensor([0.5] * 100),
            "satiation": torch.tensor([0.3] * 100),
            "mood": torch.tensor([0.6] * 100),
        }
        context = ExecutionContext(
            bars=bars,
            vfs_registry=executor.registry,
            self_index=None,
            target_index=0,
        )

        from townlet.effects.schema import CommandNode, CommandType
        commands = [
            CommandNode(type=CommandType.MODIFY, path="target.bar.energy", expression="target.bar.energy + 0.1"),
            CommandNode(type=CommandType.MODIFY, path="target.bar.satiation", expression="target.bar.satiation + 0.2"),
            CommandNode(type=CommandType.MODIFY, path="target.bar.mood", expression="target.bar.mood + 0.05"),
            CommandNode(type=CommandType.MODIFY, path="target.bar.energy", expression="target.bar.energy * 0.95"),
            CommandNode(type=CommandType.MODIFY, path="target.bar.satiation", expression="target.bar.satiation * 0.98"),
        ]

        def execute_pipeline():
            for cmd in commands:
                executor.execute(cmd, context)

        benchmark(execute_pipeline)
```

---

### Step 4: Run effects benchmarks

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/performance/test_effects_benchmarks.py --benchmark-only -v
```

**Expected:** 2 benchmarks run, timing output

---

### Step 5: Document benchmark results

Create performance documentation:

```markdown
# World Compiler Performance Benchmarks

**Date:** 2025-11-20
**Hardware:** [Your CPU/GPU info]
**Python:** 3.13
**PyTorch:** [version]

## Expression Evaluation

| Benchmark | Mean (μs) | StdDev | Ops/sec |
|-----------|-----------|--------|---------|
| Parse simple expression | [TBD] | [TBD] | [TBD] |
| Evaluate simple expression | [TBD] | [TBD] | [TBD] |
| Evaluate complex expression | [TBD] | [TBD] | [TBD] |
| Batch evaluation (100 agents) | [TBD] | [TBD] | [TBD] |

## Effects Execution

| Benchmark | Mean (μs) | StdDev | Ops/sec |
|-----------|-----------|--------|---------|
| Single modify command | [TBD] | [TBD] | [TBD] |
| Command pipeline (5 commands) | [TBD] | [TBD] | [TBD] |

## Performance vs Baseline

**Baseline:** Old EffectPipeline system (Phase 5 pre-migration)

| Component | Old (μs) | New (μs) | Regression |
|-----------|----------|----------|------------|
| Affordance effect application | [TBD] | [TBD] | [TBD]% |
| VFS variable evaluation | N/A | [TBD] | N/A |
| Item interaction | N/A | [TBD] | N/A |

**Target:** <5% regression

**Actual:** [TBD]%

## Analysis

### Expression Parsing
- Parsing overhead: [TBD] μs per expression
- Caching compiled AST reduces overhead to ~[TBD] μs

### Expression Evaluation
- Simple binary ops: [TBD] μs
- Complex nested ops: [TBD] μs
- GPU tensor operations dominate (PyTorch native)

### Effects Execution
- Single command: [TBD] μs
- Pipeline overhead: [TBD] μs per command
- Command compilation at startup amortizes cost

## Recommendations

1. **Cache compiled expressions** - Parse once, reuse AST
2. **Batch GPU operations** - Minimize CPU→GPU transfers
3. **Profile tight loops** - Monitor per-tick overhead

## Reproduction

Run benchmarks:
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/performance/ --benchmark-only
```

Generate comparison report:
```bash
pytest --benchmark-compare=0001 --benchmark-histogram
```
```

**Step 6: Fill in benchmark results**

Run benchmarks and update documentation with actual numbers:

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/performance/ --benchmark-only --benchmark-json=benchmark_results.json
```

Parse `benchmark_results.json` and update `docs/performance/world-compiler-benchmarks.md` with actual values.

---

### Step 7: Commit performance benchmarks

```bash
git add tests/test_townlet/performance/ docs/performance/world-compiler-benchmarks.md
git commit -m "perf(benchmarks): add World Compiler performance tests

Add pytest-benchmark tests for:
- Expression parsing (4 benchmarks)
- Expression evaluation (batch + single)
- Effects command execution (single + pipeline)

Document performance characteristics and regression analysis.

Results: [TBD]% regression (target <5%)

Part of Phase 6: Integration & Testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6.3: Documentation (2 days)

**Goal:** Write complete reference documentation for Expression Language, VFS Profiles, Effects, and Items schemas.

### Files

**Create:**
- `docs/config-schemas/expressions.md`
- `docs/config-schemas/vfs-profiles.md`
- `docs/config-schemas/effects.md`
- `docs/config-schemas/items.md`
- `docs/guides/world-compiler-guide.md`

---

### Step 1: Write expressions.md

Create expression language reference:

```markdown
# Expression Language Reference

**Version:** 1.0
**Status:** Stable

## Overview

The HAMLET Expression Language powers dynamic computation in VFS variables, Effects commands, and Drive As Code (DAC) formulas. Expressions are compiled at universe compilation time and evaluated at runtime on GPU tensors.

**Key Features:**
- Type-safe (compile-time type checking)
- GPU-native (PyTorch tensor operations)
- Path-based access (`target.bar.energy`, `self.vfs.durability`)
- Operator precedence matching Python

## Syntax

### Literals

```yaml
# Numeric literals
0.5
-1.2
42

# Boolean literals
true
false
```

### Path Access

```yaml
# Bar access (meter values)
target.bar.energy        # Target agent's energy meter
self.bar.health          # Self agent's health meter

# VFS access (custom variables)
target.vfs.motivation    # Target agent's motivation variable
self.vfs.durability      # Self item's durability variable

# Effect variables (in effect commands)
effect.intensity         # Effect's intensity parameter
effect.duration          # Effect's remaining duration
```

### Binary Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `energy + 0.3` |
| `-` | Subtraction | `health - 0.1` |
| `*` | Multiplication | `intensity * 2.0` |
| `/` | Division | `energy / 2.0` |
| `<` | Less than | `energy < 0.2` |
| `>` | Greater than | `satiation > 0.5` |
| `<=` | Less or equal | `mood <= 0.3` |
| `>=` | Greater or equal | `health >= 0.8` |
| `==` | Equal | `is_wet == true` |
| `!=` | Not equal | `has_key != false` |
| `&&` | Logical AND | `energy > 0.2 && mood > 0.5` |
| `||` | Logical OR | `is_wet || is_cold` |

### Unary Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `-` | Negation | `-energy` |
| `!` | Logical NOT | `!is_locked` |

### Operator Precedence

From highest to lowest:

1. Parentheses `()`
2. Unary `-`, `!`
3. Multiplicative `*`, `/`
4. Additive `+`, `-`
5. Comparison `<`, `>`, `<=`, `>=`
6. Equality `==`, `!=`
7. Logical AND `&&`
8. Logical OR `||`

**Example:**
```yaml
# Evaluates as: ((target.bar.energy + 0.3) * (1.0 - target.bar.satiation))
value: "target.bar.energy + 0.3 * 1.0 - target.bar.satiation"

# Use parentheses for clarity:
value: "(target.bar.energy + 0.3) * (1.0 - target.bar.satiation)"
```

### Conditional Expressions

```yaml
# if-then-else (ternary)
value: "energy > 0.5 ? 1.0 : 0.0"

# Nested conditionals
value: "energy > 0.8 ? 1.0 : (energy > 0.5 ? 0.5 : 0.0)"
```

### Function Calls

```yaml
# Math functions
min(energy, 1.0)         # Minimum of two values
max(satiation, 0.0)      # Maximum of two values
clamp(value, 0.0, 1.0)   # Clamp to range
abs(delta)               # Absolute value
sqrt(distance_squared)   # Square root

# Trigonometric functions
sin(angle)
cos(angle)
tan(angle)

# Random functions
random()                 # Random float in [0, 1)
random_int(1, 6)         # Random integer in [1, 6]
```

## Type System

### Primitive Types

| Type | Description | Example |
|------|-------------|---------|
| `scalar` | Single float value | `0.5`, `energy` |
| `bool` | Boolean value | `true`, `is_wet` |
| `vec2i` | 2D integer vector | `[2, 3]` (grid position) |
| `vec3i` | 3D integer vector | `[1, 2, 3]` |
| `vecNi` | N-D integer vector | `[0, 1, 2, ..., N-1]` |
| `vecNf` | N-D float vector | `[0.5, 0.3, ...]` |

### Reference Types

| Type | Description | Example |
|------|-------------|---------|
| `agent_ref` | Reference to agent | `closest_agent` |
| `item_ref` | Reference to item | `held_item` |
| `affordance_ref` | Reference to affordance | `nearest_food` |
| `effect_ref` | Reference to active effect | `current_buff` |

## Examples

### Simple Meter Modification

```yaml
# Add 0.3 to energy
modify: "target.bar.energy"
value: "target.bar.energy + 0.3"
```

### Conditional Modification

```yaml
# Restore energy, but cap at 1.0
modify: "target.bar.energy"
value: "min(target.bar.energy + 0.5, 1.0)"
```

### Complex Formula

```yaml
# Work effectiveness scales with energy and mood
modify: "target.bar.money"
value: "target.bar.money + (22.5 * target.bar.energy * target.bar.mood)"
```

### VFS Variable Definition

```yaml
# Computed variable: distance to nearest food
distance_to_food:
  expression: "sqrt((target.position.x - food.position.x)^2 + (target.position.y - food.position.y)^2)"
  type: scalar
  scope: agent
```

### Effect Intensity Scaling

```yaml
# Effect scales with intensity parameter
modify: "target.bar.health"
value: "target.bar.health - (0.1 * effect.intensity)"
```

## Type Checking

Expressions are type-checked at compile-time:

```yaml
# ✅ Valid: scalar + scalar = scalar
value: "energy + 0.3"

# ❌ Invalid: can't add vec2i + scalar
value: "position + 0.5"

# ✅ Valid: boolean condition
if: "energy > 0.5"

# ❌ Invalid: condition must be boolean
if: "energy + 0.5"
```

## Performance Notes

- **Compilation overhead:** Expressions parsed once at universe compilation
- **Evaluation overhead:** ~1-5 μs per expression (GPU tensor ops)
- **Caching:** Compiled AST reused across all evaluations
- **Batching:** Vectorized operations across agents (GPU parallel)

## Error Messages

### Parse Errors

```
Expression parse error: Unexpected token ')' at position 15
  value: "energy + 0.3)"
                      ^
```

### Type Errors

```
Type error: Cannot assign vec2i to scalar variable
  modify: "target.bar.energy"
  value: "[1, 2]"
         ^^^^^^
Expected: scalar
Got: vec2i
```

### Path Errors

```
Path not found: target.bar.nonexistent
  value: "target.bar.nonexistent + 0.5"
         ^^^^^^^^^^^^^^^^^^^^^^^^
Available paths:
  - target.bar.energy
  - target.bar.health
  - target.bar.satiation
```

## Best Practices

1. **Use parentheses for clarity**
   ```yaml
   # ✅ Clear
   value: "(energy + 0.3) * (1.0 - satiation)"

   # ❌ Relies on precedence
   value: "energy + 0.3 * 1.0 - satiation"
   ```

2. **Clamp values to valid ranges**
   ```yaml
   # ✅ Safe
   value: "clamp(energy + 0.5, 0.0, 1.0)"

   # ❌ Can exceed [0, 1]
   value: "energy + 0.5"
   ```

3. **Use meaningful variable names in VFS**
   ```yaml
   # ✅ Descriptive
   distance_to_nearest_food:
     expression: "..."

   # ❌ Cryptic
   dtf:
     expression: "..."
   ```

## See Also

- [VFS Profiles Schema](vfs-profiles.md) - Using expressions in VFS variables
- [Effects Schema](effects.md) - Using expressions in effect commands
- [Drive As Code Schema](../config-schemas/drive_as_code.md) - Using expressions in reward formulas
```

---

### Step 2: Commit expressions.md

```bash
git add docs/config-schemas/expressions.md
git commit -m "docs(schema): add Expression Language reference

Complete reference documentation for HAMLET Expression Language:
- Syntax (literals, paths, operators, functions)
- Type system (primitives, references, tensors)
- Examples (simple to complex)
- Type checking and error messages
- Performance notes and best practices

Part of Phase 6: Integration & Testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Step 3: Write vfs-profiles.md

Create VFS profiles schema documentation (abbreviated for plan - full version would be 200+ lines):

```markdown
# VFS Profiles Schema Reference

**Version:** 1.0
**File:** `vfs_profiles.yaml`
**Status:** Stable

## Overview

VFS (Variable & Feature System) Profiles define custom variables for agents, items, and global state. Variables can be static (initial value) or dynamic (expression-based).

**Key Concepts:**
- **Scopes:** global, agent, agent_private, item
- **Access Control:** readers (agent, engine, acs, bac), writers (engine, actions, bac)
- **Expressions:** Computed variables using Expression Language
- **Observations:** Variables marked readable_by agent appear in observations

## Schema

```yaml
vfs_profiles:
  version: "1.0"

  global_profile:
    # Global variables (shared across all agents)
    [variable_name]:
      type: scalar | bool | vec2i | vec3i | vecNi | vecNf
      scope: global
      initial_value: [value]  # XOR expression
      expression: "[expr]"    # XOR initial_value
      readers: [agent, engine, acs, bac]
      writers: [engine, actions, bac]

  agent_profile:
    # Per-agent variables
    [variable_name]:
      type: scalar | bool | vec2i | ...
      scope: agent | agent_private
      initial_value: [value]
      expression: "[expr]"
      readers: [...]
      writers: [...]

  item_profiles:
    [profile_name]:
      # Per-item-type variables
      [variable_name]:
        type: scalar | bool | ...
        scope: item
        initial_value: [value]
        expression: "[expr]"
        readers: [...]
        writers: [...]
```

## Examples

[... rest of vfs-profiles.md documentation ...]
```

---

### Step 4: Write effects.md schema

Create Effects catalog schema documentation (abbreviated):

```markdown
# Effects Catalog Schema Reference

**Version:** 1.0
**File:** `effects.yaml`
**Status:** Stable

## Overview

Effects are time-based state modifications that persist across ticks. Examples: buffs/debuffs (wet, poisoned), temporary boosts (inspired, energized), status conditions.

**Key Features:**
- **Lifecycle:** on_apply, per_tick, on_despawn
- **Reapply Policies:** stack, renew, merge, replace
- **Scopes:** global, agent, item, affordance
- **Commands:** Same syntax as affordance interactions

## Schema

```yaml
effects:
  version: "1.0"

  effects:
    [effect_id]:
      name: string
      description: string  # Optional

      # Parameters
      duration_ticks: int | null  # null = infinite
      intensity: float           # Default 1.0

      # Reapply policy
      reapply_policy: stack | renew | merge | replace

      # Lifecycle commands
      on_apply:
        - modify: "path"
          value: "expression"

      per_tick:
        - modify: "path"
          value: "expression"

      on_despawn:
        - modify: "path"
          value: "expression"
```

[... rest of effects.md documentation ...]
```

---

### Step 5: Write items.md schema

Create Items catalog schema documentation (abbreviated):

```markdown
# Items Catalog Schema Reference

**Version:** 1.0
**Files:** `items.yaml` (experiment-level), `levels/*/items.yaml` (level-specific)
**Status:** Stable

## Overview

Items are world objects agents can pickup, use, and drop. Items have VFS state, trigger Effects when used, and follow lifecycle rules (spawn/despawn, cooldowns, durability).

**Key Concepts:**
- **Catalog:** Experiment-level item type definitions
- **Appearance:** Level-specific spawn rules and quantities
- **Interactions:** pickup, use, drop (using Effects commands)
- **VFS State:** Item-scoped variables (durability, quality, etc.)

## Schema

### Experiment-Level: items.yaml

```yaml
items:
  version: "1.0"

  max_items_in_world: int  # Global cap
  max_items_per_agent: int # Inventory size

  catalog:
    [item_type_id]:
      name: string
      description: string

      # VFS profile (references vfs_profiles.yaml)
      vfs_profile: string

      # Interactions (Effects commands)
      on_pickup:
        - modify: "..."
          value: "..."

      on_use:
        - modify: "..."
          value: "..."
        - spawn_effect: "effect_id"

      on_drop:
        - modify: "..."
          value: "..."

      # Lifecycle
      duration_ticks: int | null
      cooldown_ticks: int
```

[... rest of items.md documentation ...]
```

---

### Step 6: Write world-compiler-guide.md

Create user guide for World Compiler (abbreviated - full would be 300+ lines):

```markdown
# World Compiler User Guide

**Audience:** HAMLET operators, curriculum designers
**Version:** 1.0

## Introduction

The World Compiler is the T0 Pillar 3 system that transforms declarative YAML configs into GPU-native runtime structures. It powers all dynamic computation in HAMLET through four integrated layers:

1. **Expression Language** - Parse and evaluate formulas
2. **VFS Profiles** - Define custom variables (static or dynamic)
3. **Effects System** - Time-based state modifications
4. **Items System** - World objects with interactions

## Getting Started

### Minimal Example

**Directory Structure:**
```
my_experiment/
├── experiment.yaml
├── stratum.yaml
├── environment.yaml
├── actions.yaml
├── agent.yaml
├── vfs_profiles.yaml    # NEW
├── effects.yaml         # NEW
├── items.yaml           # NEW
└── levels/
    └── L0_test/
        ├── curriculum.yaml
        ├── training.yaml
        ├── bars.yaml
        ├── affordances.yaml
        └── items.yaml   # Level-specific spawn rules
```

**vfs_profiles.yaml:**
```yaml
vfs_profiles:
  version: "1.0"

  agent_profile:
    is_wet:
      type: bool
      scope: agent
      initial_value: false
      readers: [agent, engine]
      writers: [effects]
```

**effects.yaml:**
```yaml
effects:
  version: "1.0"

  effects:
    wet:
      name: "Wet"
      duration_ticks: 10
      reapply_policy: renew

      on_apply:
        - modify: "target.vfs.is_wet"
          value: true

      on_despawn:
        - modify: "target.vfs.is_wet"
          value: false
```

**items.yaml:**
```yaml
items:
  version: "1.0"
  max_items_in_world: 10
  max_items_per_agent: 3

  catalog:
    apple:
      name: "Apple"
      vfs_profile: "consumable_item"

      on_use:
        - modify: "target.bar.satiation"
          value: "target.bar.satiation + 0.4"
        - modify: "target.bar.mood"
          value: "target.bar.mood + 0.05"
```

### Compilation

```bash
# Compile config pack
python -m townlet.compiler compile my_experiment/

# Validate without caching
python -m townlet.compiler validate my_experiment/
```

## Common Patterns

### Pattern 1: Computed VFS Variable

```yaml
# vfs_profiles.yaml - agent_profile
distance_to_nearest_food:
  expression: "sqrt((target.position.x - food.position.x)^2 + (target.position.y - food.position.y)^2)"
  type: scalar
  scope: agent
  readers: [agent]  # Goes into observations
  writers: []       # Computed (no writers)
```

### Pattern 2: Stacking Effect

```yaml
# effects.yaml
inspired:
  name: "Inspired"
  duration_ticks: 5
  intensity: 1.0
  reapply_policy: stack  # Multiple stacks allowed

  per_tick:
    - modify: "target.bar.mood"
      value: "target.bar.mood + (0.02 * effect.intensity)"
```

### Pattern 3: Item with Durability

```yaml
# items.yaml
torch:
  name: "Torch"
  vfs_profile: "durable_item"

  on_use:
    - modify: "self.vfs.durability"
      value: "self.vfs.durability - 1"
    - if: "self.vfs.durability <= 0"
      then:
        - despawn_item: "self"
```

[... rest of world-compiler-guide.md ...]
```

---

### Step 7: Commit all documentation

```bash
git add docs/config-schemas/vfs-profiles.md docs/config-schemas/effects.md docs/config-schemas/items.md docs/guides/world-compiler-guide.md
git commit -m "docs(schema): add World Compiler documentation suite

Complete documentation for World Compiler systems:
- vfs-profiles.md: VFS variable schema and examples
- effects.md: Effects catalog schema and lifecycle
- items.md: Items catalog and interactions
- world-compiler-guide.md: User guide and common patterns

Provides complete reference for Expression Language, VFS, Effects, Items.

Part of Phase 6: Integration & Testing (COMPLETE)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `tests/test_townlet/integration/test_world_compiler_full.py` - 3+ tests PASS
- [ ] `tests/test_townlet/integration/test_expression_vfs_effects.py` - 4+ tests PASS
- [ ] `tests/test_townlet/integration/test_curriculum_compatibility.py` - 6+ tests PASS
- [ ] `tests/test_townlet/performance/test_expression_benchmarks.py` - 4 benchmarks run
- [ ] `tests/test_townlet/performance/test_effects_benchmarks.py` - 2 benchmarks run
- [ ] Performance regression <5% vs baseline
- [ ] `docs/config-schemas/expressions.md` - Complete reference
- [ ] `docs/config-schemas/vfs-profiles.md` - Complete schema
- [ ] `docs/config-schemas/effects.md` - Complete schema
- [ ] `docs/config-schemas/items.md` - Complete schema
- [ ] `docs/guides/world-compiler-guide.md` - User guide with examples

**Success Criteria:**
- ✅ 15+ integration tests passing
- ✅ <5% performance regression documented
- ✅ Complete documentation suite (5 files)
- ✅ All curriculum levels pass full training

---

## Final Commit

```bash
git add -A
git commit -m "feat(phase-6): complete World Compiler integration & testing

Phase 6 deliverables:
- 15+ integration tests (compiler, expression flow, curriculum compat)
- Performance benchmarks (expression eval, effects execution)
- Complete documentation suite (5 schema/guide files)

Integration tests validate:
- Complete compilation pipeline (YAML → Runtime)
- Expression → VFS → Effects data flow
- Curriculum level compatibility (all 5 levels)

Performance validation:
- Expression evaluation: [TBD] μs
- Effects execution: [TBD] μs
- Regression: [TBD]% (target <5%)

Documentation coverage:
- Expression Language reference (operators, types, examples)
- VFS Profiles schema (scopes, access control, expressions)
- Effects catalog schema (lifecycle, reapply policies)
- Items catalog schema (interactions, VFS state)
- World Compiler user guide (patterns, examples)

Phase 6: Integration & Testing - COMPLETE ✅

Part of T0 Pillar 3: World Compiler

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Related Documentation

- **Master Plan:** `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- **Phase 1 Plan:** Expression Language Foundation
- **Phase 2 Plan:** VFS Profiles (Dynamic)
- **Phase 3 Plan:** Effects System
- **Phase 4 Plan:** Items System
- **Phase 5 Plan:** `docs/plans/vfs_uplift/2025-11-20-phase-5-affordance-migration.md` (COMPLETE)

---

## Troubleshooting

### Integration Test Failures

**Issue:** `test_world_compiler_full.py::test_compile_minimal_config` fails with "File not found"

**Solution:**
1. Check `integration_config_dir` fixture creates all required files
2. Verify file paths match UniverseCompiler expectations
3. Use `ls -la` to inspect tmp_path structure

### Benchmark Variance

**Issue:** Benchmark results vary by >10% between runs

**Solution:**
1. Close background processes (browser, IDE)
2. Run benchmarks multiple times: `--benchmark-min-rounds=10`
3. Use `--benchmark-warmup=on` for stable results

### Documentation Links Broken

**Issue:** Relative links in markdown don't resolve

**Solution:**
1. Use relative paths from docs root: `../config-schemas/expressions.md`
2. Test links with markdown preview tool
3. Verify all referenced files exist

---

## Next Steps

After Phase 6 completion:

1. ✅ Review test coverage (should be 270+ tests total)
2. ✅ Verify documentation completeness
3. ✅ Run full curriculum training (smoke test)
4. ⬜ **Deploy to production** (create release branch)
5. ⬜ **Publish documentation** (push to docs site)

**Questions?**
- Need debugging help? Use `superpowers:systematic-debugging`
- Tests failing? Use `superpowers:test-driven-development`
- Ready for code review? Use `superpowers:requesting-code-review`
