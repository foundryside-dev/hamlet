# Packet M: exact conversion Rig callable facts v1

2026-11-14. Metadata addendum by `/root/bac_c2_owner_failure_reconciliation` for `/root/bac_manual_physical_session` and root. Same fresh supplier custody as env-custody-fixture-api-facts-v1: four bodies/2975 lines; no additional body read. Rehashed the charged conversion fixture before inspecting its Rig/event methods: `tests/test_townlet/regressions/bac/test_pw_scope_conversion.py`,1511 lines,SHA256 `9b8783d2f1263e5e6f21a91ed319ebf280b79dc633a9c6dec8a98bdab006d85f`. No APP edits, runtime/import/test execution, Git operation or source copy. These are source facts, not a claim the new manual route already works.

Import paths:

```python
from tests.test_townlet.regressions.bac.test_pw_scope_conversion import Rig, compiled, policy, service
from townlet.universe.compiler import UniverseCompiler
from townlet.config.world_roster import WorldRosterDeclaration
```

`compiled` is the pytest module-scoped fixture at75, returning `UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)`. Import it for pytest injection; do not directly call the decorated fixture. The compiler class import above and `from pathlib import Path` support a separately declared ordinary fixture with that exact compiler call.

| Source line | Exact callable signature | Actual result |
| ---: | --- | --- |
| 79 | policy(compiled, family, scope, mode) | Resolved exploration policy. All four arguments required; for example family none/rnd, scope shared/per_world, mode paced_fifo. |
| 113 | Rig.__init__(self, compiled, selected, ids=IDS, *, width=3, seed=701, membership=IDS) | Constructs Rig; IDS=('A','B'). Pass selected=policy(...) as second positional or named argument. |
| 150 | Rig.begin(self, batch) | None; updates release, accepted and batches. |
| 172 | Rig.close(self) | None; performs actual BANK/ENV close and assigns release. No returned closure/disposition receipt. |
| 237 | Rig.world_state(self) | ENV COMPLETED checkpoint dictionary. |
| 245 | Rig.prepare_parent(self, source) | (self.parent, validate_callback); callback route has the existing restore-correlation gap described below. |
| 268 | Rig.install_parent(self) | None; assigns release from ENV install. Does not assign accepted. |
| 272 | service(bank, accepted, tick, active) | (context, stamp, reward, receipts). All four arguments required. |

The methods are unannotated in source; return descriptions above come from actual bodies, not inferred type hints. Exact line locations may be checked against the source hash; the stable authority is the hash and spelling.

Construction establishes these members: `roster`, `env`, `reports` (list), `bank`, `issuer` (WorldReceiptIssuer(owner=self)), `authority`, `release=None`, `accepted=None`, `batches=[]`. It binds all nine actual role identities: curiosity is the genuine bank; population/curriculum/exploration/network/optimizer/scheduler/replay/selection are explicitly local Rig owner interfaces. It does not construct POP/runtime/Q/replay or bind a claim callback. Manual binding may therefore be attempted after constructor and before begin, using population_owner=rig, subject to the new producer's full checks. Those local role receipts never attest production learning.

`begin(batch)` bootstraps and installs release only when release is None. It prepares and validates the actual reservation, resets ENV and retains only reset.accepted, issues genuine local population activation, calls actual bank.begin_episode(accepted=...), activates ENV with both receipts, then appends batch. It discards the reset observation and does not run initial participation or retirement. It is the existing all-active/no-decision choreography; A-only-from-entry tests must use the approved full participation protocol rather than force dones or pretend begin already did it.

**Never call Rig.step for Packet M.** Its old body writes dones and calls ENV without a genuine current vector decision. Root authorized fixture constructor/begin/close/service reuse, not that obsolete method or private flag changes. New physical work must go through the genuinely issued new manual session.

`service(bank, accepted, tick, active)` creates width3 CPU float32 predecessor arange(rows*3).reshape(rows,3)*0.07+tick*0.2, successor +0.11, int actions index%2, bool activity from the supplied Python bool sequence, and exact synthetic vector_tick=tick. It obtains actual bank.prepare_step_stamp with accepted/world IDs/context activity/tick, invokes bank.reward(...,update_stats=True), then bank.admit_and_service with the same context/stamp/accepted; returns all four real results. It does **no physical step**. Supply one bool per accepted world; it does not derive masks from ENV dones. Width3/action2 is fixed by this helper, so use matching Rig width=3 rather than assuming it follows arbitrary constructor width.

For no-hidden-BANK-event assertions, transparently observe the real bank's prepare_step_stamp/reward/admit_and_service around the new manual step and require no calls. Use an explicit `service(...)` afterward as the separate positive event control. A manual-only step with no BANK events cannot establish this fixture's positive close: close chooses participants from the real bank's participated cursors and ENV checks actual physical counts. Physical and synthetic participants must genuinely agree at closure. The helper reads existing bank._cursor to derive participation; this is its declared fixture read, not permission for Packet M to mutate BANK fields or fabricate participation.

`close()` builds local manual-summary LaneOutcomes using those actual BANK participants, real ENV step_counts/meters and fixed fixture summary fields (reason cap, horizon20, zero width3 final observation, reward totals1.0/0.5/0.5/0.0, entropy0). It freezes canonical content; obtains real BANK completion preparation; prepares/freezes ENV close; commits BANK; closes ENV with genuine dispositions; issues five child local-role receipts plus boundary_effects only after these effects; then installs the authority.completed release. Subsequent `begin(next_batch)` reuses that actual release. Do not interpret this as production POP outcome accumulation or replace the earned disposition with a fabricated receipt.

`world_state()` calls `env.checkpoint_world_state(kind="COMPLETED", release=self.release, retained_binding_batches=tuple(self.batches), initial=None)` and returns its owned transport. The existing direct ENV restore call shapes are:

```python
world_state = source.world_state()
prepared = destination.env.prepare_world_restore(
    kind="COMPLETED", state=world_state, world_roster=destination.roster,
    destination_world_ids=destination.env.world_ids,
    semantic_execution_identity=destination.env.semantic_execution_identity,
)
boundary = destination.issuer.issue(
    kind="restored_boundary",
    payload={"kind": "COMPLETED", "state": world_state, "prepared": prepared},
)
release = destination.authority.restored(restore=prepared, boundary=boundary)
installed = destination.env.install_world_restore(prepared=prepared, release=release)
```

These exact individual call signatures/payload fields are observed in Rig.prepare_parent/install_parent. The snippet places authority issuance at a normal standalone controller boundary, **not inside BANK correlation**; it is a proposed ENV-only test composition for the ENV source owner to validate, not new runtime evidence or BANK restoration. Do not call Rig.prepare_parent's retained callback as a workaround: that callback issues authority.restored during BANK correlation, the separately unresolved current restore-composition gap.

A fresh Rig still has accepted=None after install_parent; only release is updated. These inspected fixture methods provide no public accessor for ENV's reconstructed last-closed accepted token. A None/foreign token refusal alone proves identity refusal, not specifically that genuine completed history cannot authorize live work. Packet M's ENV source owner must select the actual meaningful current-history refusal witness using its admitted ENV contract; this supplier cannot invent a receipt field or token accessor. No receiving BANK restoration, seq2 BANK activation, active simulator restore, copied session history or full T26 continuation is established here.
