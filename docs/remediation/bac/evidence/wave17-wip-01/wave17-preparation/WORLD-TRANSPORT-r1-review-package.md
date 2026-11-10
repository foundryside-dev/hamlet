# Actual current-world transport review

Base86ee0d91; stagedR1tree6f46f449b2c851dc8838e00f48e7fddc8e436dc1.

 src/townlet/environment/env_factory.py             |   7 +
 src/townlet/environment/vectorized_env.py          |   5 +-
 src/townlet/universe/compiled.py                   |  14 +-
 .../bac/test_world_constructor_transport.py        | 211 +++++++++++++++++++++
 4 files changed, 234 insertions(+), 3 deletions(-)

diff --git a/src/townlet/environment/env_factory.py b/src/townlet/environment/env_factory.py
index 0e4a50f8..810b0685 100644
--- a/src/townlet/environment/env_factory.py
+++ b/src/townlet/environment/env_factory.py
@@ -4,16 +4,17 @@ from __future__ import annotations
 
 from typing import TYPE_CHECKING
 
 import torch
 
 from townlet.universe.dto import MeterMetadata
 
 if TYPE_CHECKING:
+    from townlet.config.world_roster import WorldRosterDeclaration
     from townlet.environment.vectorized_env import VectorizedHamletEnv
     from townlet.universe.compiled import CompiledUniverse
 
 
 # Valid VFS variable types for VariableDef.
 _VALID_VFS_TYPES = frozenset({"scalar", "bool", "tensor1d", "tensor2d", "tensor3d", "tensorNd", "agent_ref", "item_ref"})
 
 
@@ -55,16 +56,19 @@ def _resolve_deployable_affordances(
 
 def from_universe(
     env_cls: type[VectorizedHamletEnv],
     universe: CompiledUniverse,
     *,
     level_name: str,
     num_agents: int,
     device: torch.device | str,
+    world_roster: WorldRosterDeclaration,
+    training_seed: int,
+    lane_world_ids: tuple[str, ...],
 ) -> VectorizedHamletEnv:
     """Instantiate an environment using metadata from a compiled universe."""
     if level_name is None:
         raise ValueError(
             "VectorizedHamletEnv.from_universe requires an explicit level_name; "
             "implicit default level selection is not allowed in v2.1 runtime."
         )
 
@@ -73,9 +77,12 @@ def from_universe(
     else:
         torch_device = device
 
     return env_cls(
         universe=universe,
         level_name=level_name,
         num_agents=num_agents,
         device=torch_device,
+        world_roster=world_roster,
+        training_seed=training_seed,
+        lane_world_ids=lane_world_ids,
     )
diff --git a/src/townlet/environment/vectorized_env.py b/src/townlet/environment/vectorized_env.py
index 5a8f77c0..34837b29 100644
--- a/src/townlet/environment/vectorized_env.py
+++ b/src/townlet/environment/vectorized_env.py
@@ -1057,18 +1057,19 @@ class VectorizedHamletEnv:
             num_agents: Number of parallel agents
             device: PyTorch device (explicit)
 
         Returns:
             VectorizedHamletEnv instance
         """
         if level_name is None:
             raise ValueError("level_name must be explicit")
-        return cls(
-            universe=universe,
+        return env_factory.from_universe(
+            cls,
+            universe,
             level_name=level_name,
             num_agents=num_agents,
             device=device,
             world_roster=world_roster,
             training_seed=training_seed,
             lane_world_ids=lane_world_ids,
         )
 
diff --git a/src/townlet/universe/compiled.py b/src/townlet/universe/compiled.py
index 1fa8c622..05b21f61 100644
--- a/src/townlet/universe/compiled.py
+++ b/src/townlet/universe/compiled.py
@@ -2,17 +2,17 @@
 
 from __future__ import annotations
 
 from collections.abc import Mapping
 from copy import deepcopy
 from dataclasses import dataclass, fields, is_dataclass, replace
 from dataclasses import field as dataclass_field
 from pathlib import Path
-from typing import Any
+from typing import TYPE_CHECKING, Any
 
 import msgpack  # type: ignore[import]
 import torch
 
 from townlet.config.actions_config import ActionsConfig
 from townlet.config.affordances_v2_config import AffordancesV2Config
 from townlet.config.bars_v2_config import BarsV2Config
 from townlet.config.brain_config import BrainConfig
@@ -64,16 +64,19 @@ from townlet.vfs.schema_hashes import compute_expression_schema_hash, compute_va
 from townlet.vfs.transition_schedule import (
     VTCTransitionSchedule,
     build_vtc_transition_schedule,
     serialize_vtc_transition_schedule,
     transition_rules_from_payload,
 )
 from townlet.world.expression.references import ENTITY_NAMES
 
+if TYPE_CHECKING:
+    from townlet.config.world_roster import WorldRosterDeclaration
+
 # 1.15: the bars block became N per-meter observation fields with per-meter normalization
 # specs, and VFS source widths split from observed widths (PDR-0054 W3/W4). Every cache built
 # before that describes a different observation layout, so the bump converts a silent
 # wrong-shape serve into the "recompile the config pack" error this constant already implements.
 # 1.16: the `obs_vfs` block became one field per exposed global/agent profile variable plus
 # the `obs_item_slots` feature (PDR-0075). A pack whose only profile variables are item-scoped
 # does not touch vfs_profiles.yaml for this cut, so its config fingerprint would NOT change and
 # a pre-cut cache would serve the old field list silently — the bump is what refuses it.
@@ -764,37 +767,46 @@ class CompiledUniverse:
     # === Runtime adapters ===
 
     def create_environment(
         self,
         *,
         num_agents: int,
         level_name: str,
         device: str | torch.device,
+        world_roster: WorldRosterDeclaration,
+        training_seed: int,
+        lane_world_ids: tuple[str, ...],
     ):
         """Instantiate a VectorizedHamletEnv from this compiled universe.
 
         Args:
             num_agents: Number of parallel agents to simulate.
             level_name: Curriculum level name to instantiate. Must be provided
                 explicitly; no default level selection is performed.
             device: PyTorch device or device string (e.g., \"cpu\", \"cuda\"). Required.
+            world_roster: Explicit authored world declaration.
+            training_seed: Explicit nonnegative run seed.
+            lane_world_ids: Exact declared world membership in requested lane order.
 
         Returns:
             VectorizedHamletEnv instance
         """
 
         # Lazy import to avoid circular dependency at module import time.
         from townlet.environment.vectorized_env import VectorizedHamletEnv
 
         return VectorizedHamletEnv.from_universe(
             self,
             level_name=level_name,
             num_agents=num_agents,
             device=device,
+            world_roster=world_roster,
+            training_seed=training_seed,
+            lane_world_ids=lane_world_ids,
         )
 
 
 def _items_appearance_from_plain(payload: Any, sources: Mapping[str, ExpressionSource]) -> ItemsAppearanceConfig | None:
     """Rebuild a level's spawn rules, re-deriving each `when_ast` from its `when` text.
 
     The `when` string is the authority; the AST is a parse of it with every pure
     expression variable inlined, exactly as `VFSCompiler.compile_item_spawn_conditions`
diff --git a/tests/test_townlet/regressions/bac/test_world_constructor_transport.py b/tests/test_townlet/regressions/bac/test_world_constructor_transport.py
new file mode 100644
index 00000000..4ce38238
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_world_constructor_transport.py
@@ -0,0 +1,211 @@
+"""Required current world identity reaches real constructor entry points."""
+
+from __future__ import annotations
+
+from pathlib import Path
+from typing import Any
+
+import pytest
+import torch
+
+from townlet.config.world_roster import WorldRosterDeclaration, canonical_hash
+from townlet.environment import env_factory
+from townlet.environment.vectorized_env import VectorizedHamletEnv
+from townlet.universe.compiled import CompiledUniverse
+from townlet.universe.compiler import UniverseCompiler
+
+AUTHORED_IDS = ("world:amber/007", "world:birch/002")
+SEED = 918273
+ROUTES = ("compiled", "factory", "classmethod")
+
+
+@pytest.fixture(scope="module")
+def compiled() -> CompiledUniverse:
+    """Compile the actual current authored pack, without using mutable caches."""
+    result = UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)
+    assert result.to_dict()["compiled_schema_version"] == "1.42"
+    return result
+
+
+@pytest.fixture
+def roster() -> WorldRosterDeclaration:
+    return WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(AUTHORED_IDS)})
+
+
+def constructor_inputs(roster: WorldRosterDeclaration) -> dict[str, Any]:
+    return {
+        "level_name": "L0_test",
+        "num_agents": len(AUTHORED_IDS),
+        "device": "cpu",
+        "world_roster": roster,
+        "training_seed": SEED,
+        "lane_world_ids": AUTHORED_IDS,
+    }
+
+
+def construct(route: str, compiled: CompiledUniverse, inputs: dict[str, Any]) -> VectorizedHamletEnv:
+    if route == "compiled":
+        return compiled.create_environment(**inputs)
+    if route == "factory":
+        return env_factory.from_universe(VectorizedHamletEnv, compiled, **inputs)
+    assert route == "classmethod"
+    return VectorizedHamletEnv.from_universe(compiled, **inputs)
+
+
+def assert_fresh(env: VectorizedHamletEnv, ids: tuple[str, ...]) -> None:
+    assert env.world_ids == ids
+    assert dict(env.accepted_episode_seqs) == dict.fromkeys(ids, 0)
+    assert env.world_phase == "fresh-unbound"
+    assert not bool(env.step_counts.any())
+    with pytest.raises(TypeError, match="reservation"):
+        env.reset()
+    assert env.world_phase == "fresh-unbound"
+    assert dict(env.accepted_episode_seqs) == dict.fromkeys(ids, 0)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize("device", ("cpu", torch.device("cpu")))
+def test_real_entry_point_transports_explicit_world_identity(compiled, roster, route, device):
+    inputs = constructor_inputs(roster)
+    inputs["device"] = device
+    before = roster.to_dict()
+    env = construct(route, compiled, inputs)
+    assert_fresh(env, AUTHORED_IDS)
+    assert env.device == torch.device("cpu")
+    assert env.num_agents == len(AUTHORED_IDS)
+    assert env.universe is compiled
+    assert env.level is compiled.get_level("L0_test")
+    assert env.level_name == "L0_test"
+    assert env.semantic_execution_identity == canonical_hash(
+        {"execution": compiled.execution_hash, "membership": roster.semantic_identity, "seed": SEED}
+    )
+    assert roster.to_dict() == before
+    assert env.token_spec == env.level.token_spec
+    assert env.meter_count == env.metadata.meter_count
+    assert env.meters.shape == (len(AUTHORED_IDS), env.meter_count)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+def test_reversed_lane_binding_preserves_authored_roster_and_semantic_identity(compiled, roster, route):
+    inputs = constructor_inputs(roster)
+    before = roster.to_dict()
+    forward = construct(route, compiled, inputs)
+    inputs["lane_world_ids"] = tuple(reversed(AUTHORED_IDS))
+    reverse = construct(route, compiled, inputs)
+    assert_fresh(reverse, tuple(reversed(AUTHORED_IDS)))
+    assert reverse.semantic_execution_identity == forward.semantic_execution_identity
+    assert roster.to_dict() == before
+    assert before["world_ids"] == list(AUTHORED_IDS)
+    assert forward.world_ids == AUTHORED_IDS
+
+
+@pytest.mark.parametrize("route", ROUTES)
+def test_explicit_seed_changes_world_identity_without_changing_compiled_policy(compiled, roster, route):
+    inputs = constructor_inputs(roster)
+    original_policy = compiled.effective_run.to_dict()
+    first = construct(route, compiled, inputs)
+    inputs["training_seed"] = SEED + 1
+    second = construct(route, compiled, inputs)
+    assert first.semantic_execution_identity != second.semantic_execution_identity
+    assert second.semantic_execution_identity == canonical_hash(
+        {"execution": compiled.execution_hash, "membership": roster.semantic_identity, "seed": SEED + 1}
+    )
+    assert compiled.effective_run.to_dict() == original_policy
+    assert_fresh(first, AUTHORED_IDS)
+    assert_fresh(second, AUTHORED_IDS)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+def test_fresh_instances_own_live_tensors_and_cursor_views(compiled, roster, route):
+    first = construct(route, compiled, constructor_inputs(roster))
+    second = construct(route, compiled, constructor_inputs(roster))
+    assert first is not second
+    assert first.meters is not second.meters
+    assert first.step_counts is not second.step_counts
+    baseline = second.meters.clone()
+    first.meters.add_(13)
+    first.step_counts.add_(7)
+    assert torch.equal(second.meters, baseline)
+    assert_fresh(second, AUTHORED_IDS)
+    with pytest.raises(TypeError):
+        first.accepted_episode_seqs[AUTHORED_IDS[0]] = 99
+    assert dict(first.accepted_episode_seqs) == dict.fromkeys(AUTHORED_IDS, 0)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize("missing", ("world_roster", "training_seed", "lane_world_ids", "level_name", "num_agents", "device"))
+def test_absent_explicit_constructor_inputs_refuse_before_rng(compiled, roster, route, missing):
+    inputs = constructor_inputs(roster)
+    inputs.pop(missing)
+    before = torch.random.get_rng_state().clone()
+    with pytest.raises(TypeError, match=missing):
+        construct(route, compiled, inputs)
+    assert torch.equal(torch.random.get_rng_state(), before)
+
+
+@pytest.mark.parametrize("route", ROUTES)
+@pytest.mark.parametrize(
+    ("field", "value"),
+    (
+        ("world_roster", None),
+        ("world_roster", {"schema": "world-roster-v1", "world_ids": list(AUTHORED_IDS)}),
+        ("training_seed", None),
+        ("training_seed", True),
+        ("training_seed", -1),
+        ("training_seed", 1.0),
+        ("lane_world_ids", None),
+        ("lane_world_ids", (AUTHORED_IDS[0], AUTHORED_IDS[0])),
+        ("lane_world_ids", (AUTHORED_IDS[0], "foreign")),
+        ("lane_world_ids", (AUTHORED_IDS[0],)),
+        ("lane_world_ids", (AUTHORED_IDS[0], "")),
+        ("num_agents", 0),
+        ("num_agents", True),
+        ("num_agents", 1),
+        ("num_agents", 2.0),
+        ("level_name", None),
+        ("level_name", "missing-current-level"),
+        ("device", None),
+    ),
+)
+def test_malformed_inputs_refuse_before_rng_or_existing_live_mutation(compiled, roster, route, field, value):
+    existing = VectorizedHamletEnv.from_universe(compiled, **constructor_inputs(roster))
+    tensors = (existing.positions.clone(), existing.meters.clone(), existing.step_counts.clone())
+    identity = existing.semantic_execution_identity
+    authored = roster.to_dict()
+    inputs = constructor_inputs(roster)
+    inputs[field] = value
+    before = torch.random.get_rng_state().clone()
+    with pytest.raises((ValueError, KeyError)):
+        construct(route, compiled, inputs)
+    assert torch.equal(torch.random.get_rng_state(), before)
+    assert existing.semantic_execution_identity == identity
+    assert existing.world_phase == "fresh-unbound"
+    assert dict(existing.accepted_episode_seqs) == dict.fromkeys(AUTHORED_IDS, 0)
+    for actual, expected in zip((existing.positions, existing.meters, existing.step_counts), tensors, strict=True):
+        assert torch.equal(actual, expected)
+    assert roster.to_dict() == authored
+
+
+def test_classmethod_uses_factory_for_real_subclass_construction(compiled, roster, monkeypatch):
+    class SpecializedEnv(VectorizedHamletEnv):
+        pass
+
+    original = env_factory.from_universe
+    received = []
+
+    def through_factory(env_cls, universe, **inputs):
+        received.append((env_cls, universe, dict(inputs)))
+        return original(env_cls, universe, **inputs)
+
+    monkeypatch.setattr(env_factory, "from_universe", through_factory)
+    inputs = constructor_inputs(roster)
+    env = SpecializedEnv.from_universe(compiled, **inputs)
+    assert type(env) is SpecializedEnv
+    assert_fresh(env, AUTHORED_IDS)
+    assert len(received) == 1
+    env_cls, actual_universe, actual_inputs = received[0]
+    assert env_cls is SpecializedEnv
+    assert actual_universe is compiled
+    assert actual_inputs == inputs
+    assert actual_inputs["world_roster"] is roster
+    assert actual_inputs["lane_world_ids"] is inputs["lane_world_ids"]
