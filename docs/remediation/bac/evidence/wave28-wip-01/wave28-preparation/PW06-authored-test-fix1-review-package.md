# PW06 authoredtestfix1 exactdiff
7b29ea746c91e539e24ccd674566f143c1200d61 -> 35f03dd64a2a30a7f5d773b2e9086511f4e02b8b

diff --git a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
index 2a2dd4df..e1584e5c 100644
--- a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
+++ b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
@@ -17,23 +17,30 @@ from pathlib import Path
 import numpy as np
 import pytest
 import torch
 
 from townlet.config.bac_options import BaCOptions
 from townlet.config.drive_as_code import IntrinsicStrategyConfig
 from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
 from townlet.config.training_v2_config import TrainingV2Config
 from townlet.config.world_roster import WorldRosterDeclaration
 from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
+from townlet.exploration import scoped_curiosity as bank_module
 from townlet.exploration.provider_factory import make_backend
 from townlet.exploration.scoped_curiosity import CuriosityBank
-from townlet.exploration.world_curiosity_state import OwnedWorldBackend, ServiceClock, WorldCuriosityDescriptor, WorldRNGState
+from townlet.exploration.world_curiosity_state import (
+    CuriosityStepStamp,
+    OwnedWorldBackend,
+    ServiceClock,
+    WorldCuriosityDescriptor,
+    WorldRNGState,
+)
 from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
 from townlet.training.historical_checkpoint import (
     decode_historical_envelope,
     encode_historical_envelope,
     prepare_historical_envelope,
     resolve_historical_access,
 )
 from townlet.training.replay_buffer import ReplayBuffer
 from townlet.training.state import RewardTensor
 from townlet.universe.compiler import UniverseCompiler
@@ -308,21 +315,24 @@ class Rig:
         context = self.context(tick, active)
         stamp = self.reserve(context)
         reward = self.bank.reward(context=context, stamp=stamp, accepted=self.accepted, update_stats=True)
         receipt = self.bank.admit_and_service(context=context, stamp=stamp, accepted=self.accepted)
         return context, stamp, reward, receipt
 
     def train(self):
         before = {world: self.bank.snapshot_world(world_id=world)["backend"] for world in self.order}
         last = None
         for tick in range(1, 6):
-            last = self.event(tick, IDS)
+            active = IDS
+            if self.scope == "shared" and tick == 5:
+                active = (IDS[0],)
+            last = self.event(tick, active)
         for world in self.order:
             saved = self.bank.snapshot_world(world_id=world)["backend"]
             if self.scope == "per_world":
                 assert_real_learning(before[world]["backend"], saved["backend"], self.family)
             else:
                 assert_real_learning(before[world], saved, self.family)
         return last
 
     def completion_arguments(self):
         outcomes = tuple(
@@ -457,20 +467,103 @@ def by_id(state):
 
 def no_live_change(rig, state, operation):
     revision, globals_before = rig.bank.mutation_revision, ambient()
     with pytest.raises(REFUSAL):
         operation()
     assert rig.bank.mutation_revision == revision
     same(ambient(), globals_before)
     same(rig.bank.checkpoint_state(), state)
 
 
+class OwnerTrace:
+    """Bounded public-boundary instrumentation; all actual owners stay real."""
+
+    def __init__(self, patch):
+        self.owners, self.events = [], []
+        construct = OwnedWorldBackend.construct
+
+        def record_construct(cls, *, rng, factory):
+            self.events.append(("construct", None))
+            owner = construct(rng=rng, factory=factory)
+            self.owners.append((rng.snapshot()["world_id"], owner))
+            return owner
+
+        patch.setattr(OwnedWorldBackend, "construct", classmethod(record_construct))
+
+        def record_factory(*args, **kwargs):
+            self.events.append(("factory", None))
+            return make_backend(*args, **kwargs)
+
+        patch.setattr(bank_module, "make_backend", record_factory)
+        for name in ("call", "snapshot", "prepare_restore", "install"):
+            self.wrap(patch, name)
+
+    def wrap(self, patch, name):
+        # Explicit known public operations, not discovery of private members.
+        operations = {
+            "call": OwnedWorldBackend.call,
+            "snapshot": OwnedWorldBackend.snapshot,
+            "prepare_restore": OwnedWorldBackend.prepare_restore,
+            "install": OwnedWorldBackend.install,
+        }
+        operation = operations[name]
+
+        def record(owner, *args, **kwargs):
+            self.events.append((name, id(owner)))
+            result = operation(owner, *args, **kwargs)
+            if name == "prepare_restore":
+                self.events.append(("prepared_native", id(owner)))
+            return result
+
+        patch.setattr(OwnedWorldBackend, name, record)
+
+    def latest(self):
+        return dict(self.owners)
+
+
+def actual_owner_witness(owner, family):
+    def inspect(backend, sources):
+        del sources
+        modules = {}
+        if family == "icm":
+            modules.update(encoder=backend.encoder, inverse_model=backend.inverse_model, forward_model=backend.forward_model)
+            adam = backend.optimizer
+        else:
+            provider = backend.rnd if family == "adaptive_rnd" else backend
+            modules.update(predictor_network=provider.predictor_network, fixed_network=provider.fixed_network)
+            adam = provider.optimizer
+        result = {}
+        trainable = []
+        for label, module in modules.items():
+            for name, parameter in module.named_parameters():
+                gradient = parameter.grad
+                if label == "fixed_network":
+                    assert gradient is None
+                moments = adam.state.get(parameter, {})
+                result[f"{label}.{name}"] = {
+                    "value": parameter.detach().clone(),
+                    "gradient": None if gradient is None else gradient.detach().clone(),
+                    "moment": {key: value.detach().clone() for key, value in moments.items()},
+                    "parameter_id": id(parameter),
+                    "pointers": [parameter.data_ptr()]
+                    + ([] if gradient is None else [gradient.data_ptr()])
+                    + [value.data_ptr() for value in moments.values()],
+                }
+                if label != "fixed_network":
+                    trainable.append(id(parameter))
+        assert set(trainable) == {id(parameter) for group in adam.param_groups for parameter in group["params"]}
+        assert {id(parameter) for parameter in adam.state}.issubset(set(trainable))
+        return result
+
+    return owner.call(inspect)
+
+
 @pytest.mark.parametrize("family", FAMILIES)
 @pytest.mark.parametrize("scope", ("per_world", "shared"))
 def test_pristine_real_bank_env_producer_control(compiled, family, scope):
     """No CP lookup: root runs this genuine fixture/learning control first."""
     rig = Rig(compiled, family, scope, IDS)
     activation = rig.begin(1)
     WorldReceiptIssuer.validate(activation, kind="activation", owner=rig.bank)
     rig.env.validate_accepted_episode(accepted=rig.accepted)
     with pytest.raises(REFUSAL):
         rig.env.validate_accepted_episode(accepted=copy(rig.accepted))
@@ -482,21 +575,21 @@ def test_pristine_real_bank_env_producer_control(compiled, family, scope):
     assert replay == receipts and rig.bank.mutation_revision == revision
     snapshots = [rig.bank.snapshot_world(world_id=world) for world in IDS]
     if scope == "per_world":
         a, b = snapshots[0]["backend"], snapshots[1]["backend"]
         assert a["rng"]["world_id"] == IDS[0] and b["rng"]["world_id"] == IDS[1]
     if family == "count_based":
         counts = snapshots[0]["backend"]
         if scope == "per_world":
             counts = counts["backend"]
         assert len(counts["counts"]) > 0 and set(counts["lru"]) == set(counts["counts"])
-        assert sum(counts["counts"].values()) == (5 if scope == "per_world" else 10)
+        assert sum(counts["counts"].values()) == (5 if scope == "per_world" else 9)
     if family in TRAINABLE:
         assert any(item.optimizer_updates > 0 for item in receipts) or any(
             service_native(snapshots[0]["backend"]["backend"] if scope == "per_world" else snapshots[0]["backend"], family)[key]
             for key in (("counters",) if family == "icm" else ("optimizer_updates",))
         )
 
 
 @pytest.mark.parametrize("family", TRAINABLE)
 def test_pristine_owned_provider_gradient_pairing_control(compiled, family):
     """Actual owner public callbacks; no BANK checkpoint or CP import."""
@@ -650,22 +743,24 @@ def test_private_restore_matches_by_world_id(compiled, family):
     destination.begin(2)
     assert dict(destination.env.accepted_episode_seqs) == dict.fromkeys(IDS, 2)
     revision = destination.bank.mutation_revision
     destination.bank.begin_episode(accepted=destination.accepted)
     assert destination.bank.mutation_revision == revision
     after_begin = destination.bank.checkpoint_state()
     assert after_begin["completion"] is None
     for world in after_begin["worlds"]:
         assert world["cursor"]["eligible_seq"] == 0 and not world["phase_cache"]
     destination.event(6, IDS)
+    destination.event(7, IDS)
     source.begin(2)
     source.event(6, IDS)
+    source.event(7, IDS)
     for world in IDS:
         same(by_id(destination.bank.checkpoint_state())[world], by_id(source.bank.checkpoint_state())[world])
 
 
 BAD_METADATA = ("missing_id", "extra_id", "duplicate_id", "wrong_id", "scope", "provider", "policy", "geometry", "cursor", "cache")
 
 
 def corrupt(state, defect, family):
     last = state["worlds"][-1]
     if defect == "missing_id":
@@ -819,66 +914,101 @@ def test_initial_and_live_scope_roundtrip(compiled, family, scope):
     same(ambient(), before_rng)
     rig.bank.install_restore(prepared=prepared)
     revision = rig.bank.mutation_revision
     replay = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
     same(replay.raw, reward.raw)
     same(replay.scales, reward.scales)
     assert rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted) == receipts
     assert rig.bank.mutation_revision == revision
     independent(saved, rig.bank.checkpoint_state())
     rig.event(6, IDS)
+    rig.event(7, IDS)
     expected_next = rig.bank.checkpoint_state()
     prepared = prepare(rig, saved, "live_episode", None)
     rig.bank.install_restore(prepared=prepared)
     rig.event(6, IDS)
+    rig.event(7, IDS)
     same(rig.bank.checkpoint_state(), expected_next)
 
 
 @pytest.mark.parametrize("family", FAMILIES)
 @pytest.mark.parametrize("phase", ("reserved", "rewarded", "settled", "inactive", "stale_private"))
 def test_live_phase_dedup_resume(compiled, family, phase):
     rig = Rig(compiled, family, "per_world", IDS)
     rig.begin(1)
     rig.train()
     active = () if phase == "inactive" else (IDS[0],)
     context = rig.context(6, active)
     stamp = rig.reserve(context)
     reward, receipts = None, None
     if phase != "reserved":
         reward = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
     if phase in ("settled", "inactive", "stale_private"):
         receipts = rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
     if phase == "stale_private":
         rig.event(7, (IDS[1],))
     saved = rig.bank.checkpoint_state()
+    source, source_context, source_stamp = rig, context, stamp
+    rig = Rig(compiled, family, "per_world", IDS[::-1])
+    rig.begin(1)
+    indexes = [source.order.index(world) for world in rig.order]
+    context = IntrinsicTransitionContext(
+        predecessor=context.predecessor[indexes],
+        actions=context.actions[indexes],
+        successor=context.successor[indexes],
+        active_on_entry=context.active_on_entry[indexes],
+        vector_tick=context.vector_tick,
+    )
+    stamp = CuriosityStepStamp(
+        event_ids=tuple(stamp.event_ids[i] for i in indexes),
+        world_ids=rig.order,
+        world_episode_seqs=stamp.world_episode_seqs[indexes],
+        eligible_seqs=stamp.eligible_seqs[indexes],
+        eligible=stamp.eligible[indexes],
+    )
     prepared = prepare(rig, saved, "live_episode", None)
     rig.bank.install_restore(prepared=prepared)
+    restored = rig.bank.checkpoint_state()
     revision = rig.bank.mutation_revision
     replay = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
     if reward is not None:
-        same(replay.raw, reward.raw)
-        same(replay.scales, reward.scales)
+        same(replay.raw, reward.raw[indexes])
+        same(replay.scales, reward.scales[indexes])
         assert rig.bank.mutation_revision == revision
     served = rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
     if receipts is not None:
-        assert served == receipts and rig.bank.mutation_revision == revision
+        assert served == tuple(receipts[i] for i in indexes) and rig.bank.mutation_revision == revision
+    source.bank.reward(context=source_context, stamp=source_stamp, accepted=source.accepted, update_stats=True)
+    source.bank.admit_and_service(context=source_context, stamp=source_stamp, accepted=source.accepted)
+    for world in IDS:
+        same(by_id(source.bank.checkpoint_state())[world], by_id(rig.bank.checkpoint_state())[world])
+    if phase == "stale_private":
+        same(rig.bank.checkpoint_state()["step"], restored["step"])
     if active:
         stable = rig.bank.checkpoint_state()
         no_live_change(rig, stable, lambda: rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=False))
         changed = IntrinsicTransitionContext(
             predecessor=context.predecessor + 1,
             actions=context.actions,
             successor=context.successor,
             active_on_entry=context.active_on_entry,
             vector_tick=context.vector_tick,
         )
         no_live_change(rig, stable, lambda: rig.bank.reward(context=changed, stamp=stamp, accepted=rig.accepted, update_stats=True))
+        changed_tick = IntrinsicTransitionContext(
+            predecessor=context.predecessor,
+            actions=context.actions,
+            successor=context.successor,
+            active_on_entry=context.active_on_entry,
+            vector_tick=context.vector_tick + 100,
+        )
+        no_live_change(rig, stable, lambda: rig.bank.reward(context=changed_tick, stamp=stamp, accepted=rig.accepted, update_stats=True))
 
 
 @pytest.mark.parametrize("family", TRAINABLE)
 def test_native_gradients_are_owned_before_next_update(compiled, family):
     rig = Rig(compiled, family, "per_world", IDS)
     initial = rig.bank.checkpoint_state()
     assert all(value is None for world in initial["worlds"] for module in world["gradients"].values() for value in module.values())
     rig.begin(1)
     rig.train()
     saved = rig.bank.checkpoint_state()
@@ -902,20 +1032,73 @@ def test_native_gradients_are_owned_before_next_update(compiled, family):
     prepared = prepare(rig, saved, "live_episode", None)
     for world in saved["worlds"]:
         for module in world["gradients"].values():
             for value in module.values():
                 value.fill_(291.0)
     rig.bank.install_restore(prepared=prepared)
     restored = rig.bank.checkpoint_state()
     assert all(not bool((value == 291).all()) for world in restored["worlds"] for value in tensors(world["gradients"]))
 
 
+@pytest.mark.parametrize("family", TRAINABLE)
+def test_installed_actual_parameters_gradients_adam_and_source_isolation(compiled, monkeypatch, family):
+    trace = OwnerTrace(monkeypatch)
+    source = Rig(compiled, family, "per_world", IDS)
+    source.begin(1)
+    source.train()
+    source_owners = trace.latest()
+    source_actual = {world: actual_owner_witness(source_owners[world], family) for world in IDS}
+    saved = source.bank.checkpoint_state()
+    # Exercise real installed None/zero values independently of CP re-export.
+    module = next(iter(saved["worlds"][0]["gradients"].values()))
+    names = list(module)
+    module[names[0]], module[names[1]] = None, torch.zeros_like(module[names[1]])
+    destination = Rig(compiled, family, "per_world", IDS[::-1])
+    destination.begin(1)
+    prepared = prepare(destination, saved, "live_episode", None)
+    destination.bank.install_restore(prepared=prepared)
+    installed = trace.latest()
+    actual = {world: actual_owner_witness(installed[world], family) for world in IDS}
+    source_storage = {pointer for values in source_actual.values() for item in values.values() for pointer in item["pointers"]}
+    destination_storage = {pointer for values in actual.values() for item in values.values() for pointer in item["pointers"]}
+    assert source_storage.isdisjoint(destination_storage)
+    for world in IDS:
+        for name, witness in actual[world].items():
+            same(witness["value"], source_actual[world][name]["value"])
+            same(witness["moment"], source_actual[world][name]["moment"])
+            assert set(witness["pointers"]).isdisjoint(source_actual[world][name]["pointers"])
+            if not name.startswith("fixed_network."):
+                expected = by_id(saved)[world]["gradients"]
+                # Explicit known family names; no private owner/model discovery.
+                prefix, parameter = name.split(".", 1)
+                label = prefix if family != "adaptive_rnd" else "rnd.predictor_network"
+                same(witness["gradient"], expected[label][parameter])
+        assert set(actual[world]) == set(source_actual[world])
+    destination.event(6, IDS)
+    destination.event(7, IDS)
+    for world in IDS:
+        same(actual_owner_witness(source_owners[world], family), source_actual[world])
+        assert any(
+            not torch.equal(item["value"], actual[world][name]["value"])
+            for name, item in actual_owner_witness(installed[world], family).items()
+        )
+    # Independent active-Parameter witness on a representative last-world refusal.
+    state = destination.bank.checkpoint_state()
+    before = {world: actual_owner_witness(installed[world], family) for world in IDS}
+    malformed = deepcopy(state)
+    corrupt(malformed, "moment", family)
+    with pytest.raises(REFUSAL):
+        prepare(destination, malformed, "live_episode", None)
+    for world in IDS:
+        same(actual_owner_witness(installed[world], family), before[world])
+
+
 @pytest.mark.parametrize("defect", ("foreign", "copy", "consumed", "snapshot", "real_mutation", "caller_mutation"))
 def test_restore_token_and_input_custody(compiled, defect):
     rig = Rig(compiled, "rnd", "per_world", IDS)
     rig.begin(1)
     rig.train()
     saved = rig.bank.checkpoint_state()
     prepared = prepare(rig, saved, "live_episode", None)
     if defect == "caller_mutation":
         expected = deepcopy(saved)
         next(tensors(saved["worlds"][0]["backend"]["backend"])).fill_(713.0)
@@ -932,93 +1115,119 @@ def test_restore_token_and_input_custody(compiled, defect):
         prepared = copy(prepared)
     if defect == "foreign":
         other = Rig(compiled, "rnd", "per_world", IDS)
         before = other.bank.checkpoint_state()
         no_live_change(other, before, lambda: other.bank.install_restore(prepared=prepared))
     else:
         before = rig.bank.checkpoint_state() if defect in ("snapshot", "real_mutation") else deepcopy(saved)
         no_live_change(rig, before, lambda: rig.bank.install_restore(prepared=prepared))
 
 
-@pytest.mark.parametrize("allocation", ("report", "last_owner", "last_clone"))
+@pytest.mark.parametrize("allocation", ("report", "last_owner", "cache", "receipt", "outcome"))
 def test_restore_allocation_refusal_is_atomic(compiled, monkeypatch, allocation):
+    trace = OwnerTrace(monkeypatch)
     rig = Rig(compiled, "rnd", "per_world", IDS)
     rig.begin(1)
     rig.train()
+    mode, parent = "live_episode", None
+    if allocation == "outcome":
+        rig.actual_step()
+        world_state, _ = rig.complete()
+        saved = rig.bank.checkpoint_state()
+        rig = Rig(compiled, "rnd", "per_world", IDS[::-1])
+        parent = Correlation(rig, world_state)
+        mode = "completed_boundary"
+    else:
+        saved = rig.bank.checkpoint_state()
+    active = trace.latest()
+    actual_before = {world: actual_owner_witness(active[world], "rnd") for world in IDS}
     before = rig.bank.checkpoint_state()
     revision, globals_before = rig.bank.mutation_revision, ambient()
+    trace.events.clear()
     if allocation == "report":
         rig.reject_restore_allocation = True
         with pytest.raises(MemoryError, match="admitted restore"):
-            prepare(rig, before, "live_episode", None)
+            prepare(rig, saved, mode, parent)
         assert rig.reports[-1].operation == "restore"
+        assert not trace.events
         rig.reject_restore_allocation = False
     elif allocation == "last_owner":
         original = OwnedWorldBackend.construct
         calls = []
 
         def fail_last(cls, *, rng, factory):
             calls.append(rng.snapshot()["world_id"])
             if len(calls) == 2:
                 raise MemoryError("last actual owner allocation")
             return original(rng=rng, factory=factory)
 
         with monkeypatch.context() as patch:
             patch.setattr(OwnedWorldBackend, "construct", classmethod(fail_last))
             with pytest.raises(MemoryError, match="last actual owner"):
-                prepare(rig, before, "live_episode", None)
+                prepare(rig, saved, mode, parent)
         assert calls == list(IDS)
+        assert any(name == "prepared_native" for name, _ in trace.events)
     else:
-        original = torch.Tensor.clone
-        calls = []
-
-        def count_clone(value, *args, **kwargs):
-            calls.append(value.numel())
-            return original(value, *args, **kwargs)
-
-        with monkeypatch.context() as patch:
-            patch.setattr(torch.Tensor, "clone", count_clone)
-            prepare(rig, before, "live_episode", None)
-        last, count = len(calls), 0
-        assert last > 20
-
-        def fail_final_clone(value, *args, **kwargs):
-            nonlocal count
-            count += 1
-            if count == last:
-                raise MemoryError("last real tensor allocation")
-            return original(value, *args, **kwargs)
+        # Proposed precise same-CP allocation seam, not a current provider API.
+        # CP must call it only after actual native candidates are prepared.
+        from townlet.exploration import curiosity_checkpoint as checkpoint
+
+        original = checkpoint._allocate_runtime_data
+        reached = []
+
+        def refuse_section(*, section, value):
+            if section == allocation:
+                assert sum(name == "prepared_native" for name, _ in trace.events) >= 2
+                assert value is not None
+                if section == "cache":
+                    same(value, {world["world_id"]: world["phase_cache"] for world in saved["worlds"]})
+                elif section == "receipt":
+                    same(value, saved["step"]["receipts"])
+                elif section == "outcome":
+                    same(value, saved["completion"]["outcomes"])
+                reached.append(section)
+                raise MemoryError(f"late CP {section} allocation")
+            return original(section=section, value=value)
 
         with monkeypatch.context() as patch:
-            patch.setattr(torch.Tensor, "clone", fail_final_clone)
-            with pytest.raises(MemoryError, match="last real tensor"):
-                prepare(rig, before, "live_episode", None)
-        assert count == last
+            patch.setattr(checkpoint, "_allocate_runtime_data", refuse_section)
+            with pytest.raises(MemoryError, match=f"late CP {allocation}"):
+                prepare(rig, saved, mode, parent)
+        assert reached == [allocation]
     assert rig.bank.mutation_revision == revision
     same(ambient(), globals_before)
+    assert not any(owner_id in {id(owner) for owner in active.values()} for _, owner_id in trace.events)
+    for world in IDS:
+        same(actual_owner_witness(active[world], "rnd"), actual_before[world])
     same(rig.bank.checkpoint_state(), before)
-    prepared = prepare(rig, before, "live_episode", None)
+    prepared = prepare(rig, saved, mode, parent)
     rig.bank.install_restore(prepared=prepared)
+    if parent is not None:
+        parent.install_env()
+        rig.begin(2)
     rig.event(6, IDS)
 
 
-def test_pending_completion_export_refuses_purely(compiled):
+def test_pending_completion_export_refuses_purely(compiled, monkeypatch):
+    trace = OwnerTrace(monkeypatch)
     rig = Rig(compiled, "adaptive_rnd", "per_world", IDS)
     rig.begin(1)
     rig.actual_step()
     rig.train()
     arguments = rig.completion_arguments()
     prepared = rig.bank.prepare_completion(**arguments)
     revision, globals_before = rig.bank.mutation_revision, ambient()
     report_count, issues = len(rig.reports), list(rig.issued)
+    trace.events.clear()
     with pytest.raises(REFUSAL):
         rig.bank.checkpoint_state()
+    assert not trace.events
     assert rig.bank.mutation_revision == revision and len(rig.reports) == report_count
     same(rig.issued, issues)
     same(ambient(), globals_before)
     assert rig.bank.prepare_completion(**arguments) is prepared
     receipt = rig.bank.commit_completion(prepared=prepared)
     assert rig.bank.commit_completion(prepared=prepared) is receipt
 
 
 @pytest.mark.parametrize("order", (IDS, IDS[::-1]), ids=("same", "reversed"))
 def test_historical_completion_cannot_authorize_receiving_live_close(compiled, order):
