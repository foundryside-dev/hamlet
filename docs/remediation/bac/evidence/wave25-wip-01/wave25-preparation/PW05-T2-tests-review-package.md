Previouslyreviewedtest b5bd.../901 presentinbase6f451471c2fa865633dd93658991b2253fb68a10
T2actualcandidateb8ae552954aff5a094a8eae019fd788bf70eaa61
Onlysource/testdelta ownedBANKtest1153; noBANKimplementation.
diff --git a/tests/test_townlet/regressions/bac/test_pw_private_bank.py b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
index 78c9a137..f78bbda6 100644
--- a/tests/test_townlet/regressions/bac/test_pw_private_bank.py
+++ b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
@@ -148,30 +148,33 @@ def _updates(state: dict[str, Any], family: str) -> int:
     return _rnd_native(state, family)["predictor_service"]["optimizer_updates"]
 
 
 def _ownership(backend: Any, family: str) -> dict[str, Any]:
     """Read actual published provider objects; return scalars/data, never live objects."""
     result: dict[str, Any] = {"backend": id(backend)}
     if family not in TRAINABLE:
         result["native"] = backend.checkpoint_state()
+        if family == "count_based":
+            result["counts_container"] = id(backend._counts)  # Root-published actual OrderedDict.
         return result
     actual = backend.rnd if family == "adaptive_rnd" else backend
     models = (
         (actual.encoder, actual.inverse_model, actual.forward_model)
         if family == "icm"
         else (
             actual.fixed_network,
             actual.predictor_network,
         )
     )
     parameters = [parameter for model in models for parameter in model.parameters()]
     result.update(
         models=tuple(id(model) for model in models),
         parameters=tuple(id(parameter) for parameter in parameters),
+        trainable_parameters=tuple(id(parameter) for parameter in parameters if parameter.requires_grad),
         storage=tuple(_storage(parameter) for parameter in parameters),
         optimizer=id(actual.optimizer),
         optimizer_parameters=tuple(id(parameter) for group in actual.optimizer.param_groups for parameter in group["params"]),
         gradient_storage=tuple(_storage(parameter.grad) for parameter in parameters if parameter.grad is not None),
         gradients=tuple(None if parameter.grad is None else parameter.grad.detach().clone() for parameter in parameters),
         moment_storage=tuple(_storage(tensor) for tensor in _tensors(actual.optimizer.state)),
         native=backend.checkpoint_state(),
     )
@@ -229,21 +232,24 @@ def test_private_models_moments_and_queues_do_not_alias(harness_factory: Any, fa
     first, second = harness_factory(family), harness_factory(family)
     for harness in (first, second):
         for tick in range(1, 8):
             _step(harness.bank, harness.accepted, _context(tick, (True, True), 3, 0.7))
     views = [_inspect(h.bank, world, family) for h in (first, second) for world in WORLD_IDS]
     for index, left in enumerate(views):
         for right in views[index + 1 :]:
             assert left["backend"] != right["backend"]
+            if family == "count_based":
+                assert left["counts_container"] != right["counts_container"]
             if family in TRAINABLE:
                 for field in ("models", "parameters", "storage", "gradient_storage", "moment_storage"):
                     assert set(left[field]).isdisjoint(right[field]), field
                 assert left["optimizer"] != right["optimizer"]
-                assert set(left["optimizer_parameters"]) <= set(left["parameters"])
+                assert len(left["optimizer_parameters"]) == len(left["trainable_parameters"])
+                assert set(left["optimizer_parameters"]) == set(left["trainable_parameters"])
                 for field in ("queue", "rms", "history"):
                     if field in left:
                         assert left[field] != right[field]
     snapshot = first.bank.snapshot_world(world_id="world1")
     before = deepcopy(snapshot)
     for tensor in _tensors(snapshot):
         if tensor.numel():
             tensor.zero_()
@@ -417,16 +423,17 @@ def test_completion_preserves_nonempty_gradients_and_tail(harness_factory: Any)
         after = _inspect(h.bank, world, "adaptive_rnd")
         for field in (
             "models",
             "parameters",
             "storage",
             "optimizer",
             "optimizer_parameters",
             "gradient_storage",
+            "moment_storage",
             "gradients",
             "queue",
             "rms",
         ):
             _equal(before[world][field], after[field])
         _equal(before[world]["native"]["rnd_state"], after["native"]["rnd_state"])
         assert after["native"]["survival_history"] == [7]
 
@@ -714,16 +721,19 @@ class _Harness:
         effects = self.boundary.receipt(
             "boundary_effects",
             batch_episode=self.accepted.batch_episode,
             accepted_identity=self.accepted,
             completion_content=content,
             retirement_receipt=committed,
             **children,
         )
+        self.last_completion_content = content
+        self.last_completion_receipt = committed
+        _equal(committed.payload["completion_content"], content)
         self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
         self.begin(self.accepted.batch_episode + 1)
 
 
 @pytest.fixture
 def harness_factory(compiled: Any) -> Any:
     def make(
         family: str,
@@ -848,28 +858,33 @@ def test_exact_id_not_row_or_spectator_controls_private_state(harness_factory: A
                 active_on_entry=active,
                 vector_tick=tick,
             )
             _, reward, _ = _step(h.bank, h.accepted, context)
             outputs.append((reward.raw[index], reward.scales[index], h.bank.snapshot_world(world_id="world1")))
         for raw, scale, snapshot in outputs[1:]:
             _equal(outputs[0][0], raw)
             _equal(outputs[0][1], scale)
-            _equal(outputs[0][2]["backend"], snapshot["backend"])
-            _equal(outputs[0][2]["cursor"], snapshot["cursor"])
+            _equal(_private_domain(outputs[0][2], allowed_ticks=None), _private_domain(snapshot, allowed_ticks=None))
 
 
 def test_adaptive_real_history_weight_and_per_row_scale(harness_factory: Any) -> None:
     first, second = harness_factory("adaptive_rnd"), harness_factory("adaptive_rnd")
     for episode in range(10):
         for h, other_survival in ((first, 1), (second, 12)):
             _step(h.bank, h.accepted, _context(episode + 1, (True, True), 3, float(other_survival)))
             h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
             h.close_and_begin(7, world0_steps=other_survival)
-        _equal(first.bank.snapshot_world(world_id="world1"), second.bank.snapshot_world(world_id="world1"))
+        _equal(
+            _private_domain(first.bank.snapshot_world(world_id="world1"), allowed_ticks=None),
+            _private_domain(second.bank.snapshot_world(world_id="world1"), allowed_ticks=None),
+        )
+        assert first.last_completion_content != second.last_completion_content
+        _equal(first.last_completion_receipt.payload["completion_content"], first.last_completion_content)
+        _equal(second.last_completion_receipt.payload["completion_content"], second.last_completion_content)
     snapshots = {world: _native(first.bank.snapshot_world(world_id=world)) for world in WORLD_IDS}
     assert snapshots["world1"]["survival_history"] == [7] * 10
     assert snapshots["world0"]["survival_history"] == [1] * 10
     assert snapshots["world1"]["current_intrinsic_weight"] < snapshots["world1"]["initial_intrinsic_weight"]
     _, reward, _ = _step(first.bank, first.accepted, _context(100, (True, True), 3, 0.0))
     assert reward.scales[1].item() == pytest.approx(snapshots["world1"]["current_intrinsic_weight"])
     assert reward.scales[0] > reward.scales[1]
     assert reward.scales.shape == (2,)
@@ -894,8 +909,245 @@ def test_completion_content_is_full_canonical_outcome_not_just_hash(harness_fact
             accepted=h.accepted,
             boundary_key=h.accepted.batch_episode,
             completion_content=tuple(content),
             outcomes=outcomes,
             participated_world_ids=WORLD_IDS,
         )
     for world, state in zip(WORLD_IDS, before, strict=True):
         _equal(state, h.bank.snapshot_world(world_id=world))
+
+
+def _private_domain(snapshot: dict[str, Any], *, allowed_ticks: set[int] | None) -> dict[str, Any]:
+    """Compare EVERY world-local field; check separate roster/binding provenance.
+
+    Snapshot caches are explicitly world-local. Whole-bank completion correlation
+    is asserted on actual receipts, never hidden in a local learned-state cache.
+    Only reserved global ticks in cache/pending metadata may be normalized, and
+    only for the deliberately different-tick differential.
+    """
+    result = deepcopy(snapshot)
+    descriptor = WorldCuriosityDescriptor.from_dict(result.pop("descriptor"))
+    world = result["world_id"]
+    assert world in descriptor.world_ids
+    result["stable_descriptor"] = {
+        key: value
+        for key, value in descriptor.to_dict().items()
+        if key not in ("world_ids", "canonical_world_ids", "world_binding_hash", "seeds")
+    }
+    result["world_seeds"] = dict(descriptor.seeds[world])
+    binding = result.pop("accepted_identity")
+    if binding is None:
+        result["accepted_world_identity"] = None
+    else:
+        assert len(binding["world_ids"]) == len(binding["world_episode_seqs"])
+        assert len(set(binding["world_ids"])) == len(binding["world_ids"])
+        index = binding["world_ids"].index(world)
+        assert binding["world_episode_seqs"][index] == result["cursor"]["accepted_episode_seq"]
+        result["accepted_world_identity"] = (binding["batch_episode"], world, binding["world_episode_seqs"][index])
+
+    def provenance(value: Any) -> Any:
+        if isinstance(value, dict):
+            owned = {}
+            for key, item in value.items():
+                if key == "vector_tick" and allowed_ticks is not None:
+                    assert type(item) is int and item in allowed_ticks
+                    owned[key] = "explicit-global-provenance"
+                else:
+                    owned[key] = provenance(item)
+            return owned
+        if isinstance(value, tuple):
+            return tuple(provenance(item) for item in value)
+        if isinstance(value, list):
+            return [provenance(item) for item in value]
+        return value
+
+    # Do not omit absent, pending, completion or retry data: all keys remain.
+    result["phase_cache"] = provenance(result["phase_cache"])
+    result["pending_step"] = provenance(result["pending_step"])
+    return result
+
+
+def test_private_count_same_bin_and_owned_container_mutation(harness_factory: Any) -> None:
+    first, second = harness_factory("count_based"), harness_factory("count_based")
+    context = IntrinsicTransitionContext(
+        predecessor=torch.zeros(2, 3),
+        actions=torch.zeros(2, dtype=torch.int64),
+        successor=torch.ones(2, 3),
+        active_on_entry=torch.ones(2, dtype=torch.bool),
+        vector_tick=1,
+    )
+    _, reward, _ = _step(first.bank, first.accepted, context)
+    assert reward.raw.tolist() == [1.0, 1.0]  # Same bins, distinct real dictionaries.
+    untouched = second.bank.snapshot_world(world_id="world1")
+    before = {world: first.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    modified = first.bank.snapshot_world(world_id="world0")
+    native = _native(modified)
+    assert native["counts"] and native["lru"]
+    native["counts"].clear()
+    native["lru"].clear()
+    for world in WORLD_IDS:
+        _equal(before[world], first.bank.snapshot_world(world_id=world))
+    _equal(untouched, second.bank.snapshot_world(world_id="world1"))
+    _, next_reward, _ = _step(
+        first.bank,
+        first.accepted,
+        IntrinsicTransitionContext(
+            predecessor=context.predecessor,
+            actions=context.actions,
+            successor=context.successor,
+            active_on_entry=torch.tensor([False, True]),
+            vector_tick=2,
+        ),
+    )
+    assert next_reward.raw[1].item() == pytest.approx(2**-0.5)
+    _equal(before["world0"]["backend"], first.bank.snapshot_world(world_id="world0")["backend"])
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+def test_private_idle_ticks_do_not_change_local_updates_or_retry_cache(harness_factory: Any, family: str) -> None:
+    first, second = harness_factory(family), harness_factory(family)
+    initial = _native(first.bank.snapshot_world(world_id="world1"))
+    for local in range(1, 10):
+        for offset, active in ((-2, (True, False)), (-1, (False, False))):
+            _step(second.bank, second.accepted, _context(local * 10 + offset, active, 3, 99.0))
+        results = []
+        for h, tick in ((first, local), (second, local * 10)):
+            predecessor = torch.full((2, 3), local / 13, dtype=torch.float32)
+            context = IntrinsicTransitionContext(
+                predecessor=predecessor,
+                actions=torch.full((2,), local % 2, dtype=torch.int64),
+                successor=predecessor + 0.2,
+                active_on_entry=torch.tensor([False, True]),
+                vector_tick=tick,
+            )
+            stamp, reward, _ = _step(h.bank, h.accepted, context)
+            before_retry = h.bank.snapshot_world(world_id="world1")
+            replay = h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+            h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted)
+            _equal(reward.raw, replay.raw)
+            _equal(before_retry, h.bank.snapshot_world(world_id="world1"))
+            results.append((reward, _private_domain(before_retry, allowed_ticks={tick})))
+        _equal(results[0][0].raw[1], results[1][0].raw[1])
+        _equal(results[0][0].scales[1], results[1][0].scales[1])
+        _equal(results[0][1], results[1][1])
+    final = _native(first.bank.snapshot_world(world_id="world1"))
+    if family in TRAINABLE:
+        assert _updates(final, family) >= 2
+        assert any(not torch.equal(a, b) for a, b in zip(_learned(initial, family), _learned(final, family), strict=True))
+        assert any(bool(item["exp_avg"].ne(0).any()) for item in _optimizer(final, family)["state"].values())
+
+
+def _seed_numeric_prefix(backend: Any, sources: Any) -> None:
+    # Synthetic VALID learned prefix via real algorithm; not nine ENV episodes.
+    for _ in range(9):
+        backend.update_on_episode_end(10**20)
+
+
+def test_pristine_adaptive_numeric_refusal_control(compiled: Any) -> None:
+    policy = _policy(compiled, "adaptive_rnd", "per_world")
+    owner = _owned(policy, _descriptor(policy, WORLD_IDS, 3), "world1")
+    owner.call(_seed_numeric_prefix)
+    state = owner.snapshot()
+    owner.call(lambda backend, sources: backend.validate_state(state["backend"]))
+
+    def candidate(backend: Any, sources: Any) -> bool:
+        from copy import copy
+
+        other = copy(backend)
+        other.survival_history = list(backend.survival_history)
+        with pytest.raises(ValueError):
+            other.update_on_episode_end(1)
+        return True
+
+    assert owner.call(candidate) is True
+    _equal(state, owner.snapshot())
+
+
+def test_expected_numeric_completion_refusal_only_advances_observation_revision(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    h.bank._owners["world1"].call(_seed_numeric_prefix)
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    with pytest.raises(ValueError):
+        _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    assert h.bank.mutation_revision == revision + 1
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    # A genuine subsequent local operation proves neither owner nor bank was
+    # falsely quarantined by expected off-side arithmetic refusal.
+    _step(h.bank, h.accepted, _context(2, (True, True), 3, 0.0))
+
+
+def test_unexpected_callback_failure_quarantines_earlier_success_and_replay(harness_factory: Any) -> None:
+    h = harness_factory("rnd")
+    old_context = _context(1, (True, True), 3, 0.0)
+    old_stamp, _, _ = _step(h.bank, h.accepted, old_context)
+    calls: list[str] = []
+
+    def inject(backend: Any, sources: Any) -> None:
+        def fail(*args: Any, **kwargs: Any) -> None:
+            calls.append("world1")
+            raise RuntimeError("injected real owned reward operation failure")
+
+        backend.compute_intrinsic_rewards = fail
+
+    h.bank._owners["world1"].call(inject)
+    before = h.bank.snapshot_world(world_id="world0")
+    context = _context(2, (True, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=2)
+    with pytest.raises(RuntimeError, match="injected real owned"):
+        h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+    assert calls == ["world1"]
+    # Direct WS diagnostic of the earlier healthy owner proves a real preceding
+    # effect occurred; no attempt to roll that effect back is permitted.
+    state = h.bank._owners["world0"].snapshot()["backend"]
+    assert state["reward_rms_count"] > _native(before)["reward_rms_count"]
+    for operation in (
+        lambda: h.bank.reward(context=old_context, stamp=old_stamp, accepted=h.accepted, update_stats=True),
+        lambda: h.bank.admit_and_service(context=old_context, stamp=old_stamp, accepted=h.accepted),
+        lambda: h.bank.snapshot_world(world_id="world0"),
+    ):
+        with pytest.raises((RuntimeError, ValueError)):
+            operation()
+
+
+@pytest.mark.parametrize("pending", ("step", "completion"))
+def test_conservative_quarantine_after_actual_env_abandon_refusal(harness_factory: Any, pending: str) -> None:
+    h = harness_factory("adaptive_rnd")
+    h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
+    context = _context(1, (True, True), 3, 0.0)
+    if pending == "completion":
+        _step(h.bank, h.accepted, context)
+        prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    else:
+        stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=1)
+    with pytest.raises(ValueError):
+        h.env.abandon_episode(accepted=h.accepted, reason="empty_participation")
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    with pytest.raises((RuntimeError, ValueError)):
+        if pending == "completion":
+            h.bank.commit_completion(prepared=prepared)
+        else:
+            h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+
+
+def test_exact_whitespace_world_id_survives_real_completion(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd", ids=(" ", "world1"))
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    prepared = _completion(h.bank, h.accepted, h.accepted.world_ids, 1)
+    receipt = h.bank.commit_completion(prepared=prepared)
+    assert receipt.payload["dispositions"][0] == (" ", "completed")
+    state = h.bank.snapshot_world(world_id=" ")
+    assert state["world_id"] == " " and _native(state)["survival_history"] == [1]
+
+
+def test_quarantine_refuses_cached_completion_success(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    receipt = h.bank.commit_completion(prepared=prepared)
+    assert h.bank.commit_completion(prepared=prepared) is receipt
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    with pytest.raises((RuntimeError, ValueError)):
+        h.bank.commit_completion(prepared=prepared)
