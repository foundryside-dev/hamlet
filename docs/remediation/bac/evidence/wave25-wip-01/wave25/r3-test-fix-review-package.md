# PW05 fixround1 testsfirst
fee0eac4e8e3944296fa4e22a8ad9f4a8f17f684 -> 00f65f75a79bab1fe5577f0b8337db12c287c7dd

diff --git a/tests/test_townlet/regressions/bac/test_pw_private_bank.py b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
index f78bbda6..7f1f30a0 100644
--- a/tests/test_townlet/regressions/bac/test_pw_private_bank.py
+++ b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
@@ -401,21 +401,21 @@ def test_all_inactive_shared_call_does_not_service_pending_tail(harness_factory:
     _equal(before["backend"], h.bank.snapshot_world(world_id="world1")["backend"])
 
 
 def test_completion_preserves_nonempty_gradients_and_tail(harness_factory: Any) -> None:
     h = harness_factory("adaptive_rnd")
     for tick in range(1, 8):
         _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
     before = {world: _inspect(h.bank, world, "adaptive_rnd") for world in WORLD_IDS}
     for value in before.values():
         assert any(gradient is not None and bool(gradient.ne(0).any()) for gradient in value["gradients"])
-        assert value["native"]["rnd_state"]["predictor_service"]["pending_observations"]
+        assert value["native"]["rnd_state"]["predictor_service"]["pending_observations"].shape[0] > 0
     prepared = _completion(h.bank, h.accepted, WORLD_IDS, 7)
     assert _completion(h.bank, h.accepted, WORLD_IDS, 7) is prepared
     with pytest.raises(ValueError):
         _completion(h.bank, h.accepted, WORLD_IDS, 6)
     with pytest.raises((ValueError, RuntimeError)):
         h.bank.snapshot_world(world_id="world0")
     committed = h.bank.commit_completion(prepared=prepared)
     assert h.bank.commit_completion(prepared=prepared) is committed
     WorldReceiptIssuer.validate(committed, "dispositions", h.bank)
     assert committed.payload["dispositions"] == tuple((world, "completed") for world in WORLD_IDS)
@@ -1144,10 +1144,191 @@ def test_exact_whitespace_world_id_survives_real_completion(harness_factory: Any
 
 def test_quarantine_refuses_cached_completion_success(harness_factory: Any) -> None:
     h = harness_factory("adaptive_rnd")
     _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
     prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
     receipt = h.bank.commit_completion(prepared=prepared)
     assert h.bank.commit_completion(prepared=prepared) is receipt
     h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
     with pytest.raises((RuntimeError, ValueError)):
         h.bank.commit_completion(prepared=prepared)
+
+
+@pytest.mark.parametrize("phase", ("reward", "service"))
+def test_post_provider_publication_failure_quarantines_real_effect(harness_factory: Any, monkeypatch: Any, phase: str) -> None:
+    h = harness_factory("rnd")
+    for tick in (1, 2):
+        _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
+    context = _context(3, (True, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=3)
+    if phase == "service":
+        h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+    before = h.bank._owners["world0"].snapshot()["backend"]
+    calls: list[str] = []
+
+    def publication_fault(*args: Any, **kwargs: Any) -> None:
+        calls.append(phase)
+        raise RuntimeError("injected post-provider publication allocation failure")
+
+    module = importlib.import_module(BANK_MODULE)
+    target = "CuriosityReward" if phase == "reward" else "WorldServiceReceipt"
+    with monkeypatch.context() as patch:
+        patch.setattr(module, target, publication_fault)
+        with pytest.raises(RuntimeError, match="injected post-provider"):
+            if phase == "reward":
+                h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+            else:
+                h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted)
+    assert calls == [phase]
+    after = h.bank._owners["world0"].snapshot()["backend"]
+    if phase == "reward":
+        assert after["reward_rms_count"] > before["reward_rms_count"]
+    else:
+        assert after["predictor_service"]["optimizer_updates"] > before["predictor_service"]["optimizer_updates"]
+        assert any(not torch.equal(a, b) for a, b in zip(_learned(before, "rnd"), _learned(after, "rnd"), strict=True))
+    for retry in (
+        lambda: h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True),
+        lambda: h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted),
+    ):
+        with pytest.raises((ValueError, RuntimeError), match="quarantin"):
+            retry()
+
+
+def test_completion_receipt_failure_after_observation_tracks_revision(harness_factory: Any, monkeypatch: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    before = {world: h.bank._owners[world].snapshot() for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+
+    def fail_issue(*, kind: str, payload: Any) -> Any:
+        assert kind == "prepared_dispositions"
+        raise RuntimeError("injected completion receipt allocation failure")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(h.bank._issuer, "issue", fail_issue)
+        with pytest.raises(RuntimeError, match="injected completion receipt"):
+            _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    assert h.bank.mutation_revision == revision + 1
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank._owners[world].snapshot())
+    assert h.bank._prepared is None
+
+
+@pytest.mark.parametrize("retry", ("equal", "changed_content", "changed_outcome", "changed_tensor"))
+def test_pending_completion_refuses_or_replays_before_codec_allocation(harness_factory: Any, monkeypatch: Any, retry: str) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    outcomes = _outcomes(h.accepted, WORLD_IDS, 1)
+    content = _content(outcomes)
+    prepared = h.bank.prepare_completion(
+        accepted=h.accepted,
+        boundary_key=h.accepted.batch_episode,
+        completion_content=content,
+        outcomes=outcomes,
+        participated_world_ids=WORLD_IDS,
+    )
+    assert prepared.completion_content == content
+    assert all(bytes.fromhex(payload).hex() == payload and len(fingerprint) == 64 for payload, fingerprint in content)
+    if retry == "changed_content":
+        content = ((content[0][0], "0" * 64), content[1])
+    elif retry == "changed_outcome":
+        outcomes = (outcomes[0], replace(outcomes[1], reward_total=9.0))
+    elif retry == "changed_tensor":
+        outcomes[1].outcome.final_observation.add_(1)
+    revision = h.bank.mutation_revision
+    effects: list[str] = []
+
+    def forbidden(*args: Any, **kwargs: Any) -> Any:
+        effects.append("unexpected allocation/owner observation")
+        raise RuntimeError("pending preparation performed new codec/report/owner work")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(importlib.import_module(BANK_MODULE), "freeze_lane_outcome", forbidden)
+        patch.setattr(importlib.import_module(BANK_MODULE), "lane_outcome_state", forbidden)
+        patch.setattr(h.bank, "_report", forbidden)
+        for world in WORLD_IDS:
+            patch.setattr(h.bank._owners[world], "call", forbidden)
+        if retry == "equal":
+            assert (
+                h.bank.prepare_completion(
+                    accepted=h.accepted,
+                    boundary_key=h.accepted.batch_episode,
+                    completion_content=content,
+                    outcomes=outcomes,
+                    participated_world_ids=WORLD_IDS,
+                )
+                is prepared
+            )
+        else:
+            with pytest.raises(ValueError):
+                h.bank.prepare_completion(
+                    accepted=h.accepted,
+                    boundary_key=h.accepted.batch_episode,
+                    completion_content=content,
+                    outcomes=outcomes,
+                    participated_world_ids=WORLD_IDS,
+                )
+    assert effects == []
+    assert h.bank.mutation_revision == revision
+    h.bank.commit_completion(prepared=prepared)
+
+
+def _spectator_variant(context: IntrinsicTransitionContext, *, own: bool, tick: int) -> IntrinsicTransitionContext:
+    predecessor, successor, actions = context.predecessor, context.successor, context.actions
+    row = 1 if own else 0
+    predecessor[row] += 100
+    successor[row] -= 50
+    actions[row] = 1 - actions[row]
+    return IntrinsicTransitionContext(
+        predecessor=predecessor, actions=actions, successor=successor, active_on_entry=context.active_on_entry, vector_tick=tick
+    )
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+def test_private_last_local_replay_survives_inactive_source_and_other_world_activity(
+    harness_factory: Any, monkeypatch: Any, family: str
+) -> None:
+    h = harness_factory(family)
+    original = _context(1, (False, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=original.active_on_entry, vector_tick=1)
+    reward = h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+    changed_spectator = _spectator_variant(original, own=False, tick=1)
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    replay = h.bank.reward(context=changed_spectator, stamp=stamp, accepted=h.accepted, update_stats=True)
+    _equal(reward.raw, replay.raw)
+    assert h.bank.mutation_revision == revision
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    h.bank.admit_and_service(context=changed_spectator, stamp=stamp, accepted=h.accepted)
+    _step(h.bank, h.accepted, _context(2, (True, False), 3, 10.0))
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    effects: list[str] = []
+
+    def forbidden(*args: Any, **kwargs: Any) -> Any:
+        effects.append("provider call")
+        raise RuntimeError("cached local replay invoked a provider")
+
+    with monkeypatch.context() as patch:
+        for world in WORLD_IDS:
+            patch.setattr(h.bank._owners[world], "call", forbidden)
+        replay = h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+        receipts = h.bank.admit_and_service(context=original, stamp=stamp, accepted=h.accepted)
+        _equal(reward.raw, replay.raw)
+        assert replay.raw[0] == 0 and not receipts[0].eligible
+        assert receipts[0].admitted_rows == receipts[0].optimizer_updates == 0
+        for bad, mode in (
+            (_spectator_variant(original, own=True, tick=1), True),
+            (original, False),
+            (_spectator_variant(original, own=False, tick=2), True),
+        ):
+            with pytest.raises(ValueError):
+                h.bank.reward(context=bad, stamp=stamp, accepted=h.accepted, update_stats=mode)
+    assert effects == [] and h.bank.mutation_revision == revision
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    _step(h.bank, h.accepted, _context(3, (False, True), 3, 0.0))
+    before = h.bank.snapshot_world(world_id="world1")
+    with pytest.raises(ValueError):
+        h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+    _equal(before, h.bank.snapshot_world(world_id="world1"))
