# Replay load_for_mode: exact standalone negative-test contract

2026-11-14. Prose-only source addendum to [current replay/core supplier](T18e-R0-PARENT-REPLAY-CURRENT-SUPPLIER.md), SHA256 `f6c48b621acbc26f9198a8e25f71a6f25b29fc4697d8f3e7d0bf77a0154b7b37`. Requested by root for [native/replay fixture repair plan v1](T18e-R0-NATIVE-REPLAY-FIXTURE-REPAIR-PLAN-v1.md), whose SHA256 was verified as `683f4f5560cbb8a41cf4d4975c127a4201150766bc620961c44597ba94b0e6bb`. Root reports published WIP22 HEAD `23701174e5418aca5e8fc90cbe694f773d3ebff6`; no Git command was run for this addendum. Fixture line784 and its intended captured-replay wrong-policy negative are supplied context, not a fixture-body read.

The existing four-body budget remains 4202 lines; no additional implementation/test body was read. Original source files alone were rehashed, all unchanged:

| Path under src/townlet | Lines | SHA256 |
| --- | ---: | --- |
| exploration/rng_custody.py | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| training/replay_contract.py | 881 | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| training/replay_buffer.py | 816 | `683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d` |
| training/prioritized_replay_buffer.py | 1310 | `7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29` |

No import, runtime/test, APP/source edit, Git action, source copy, checkout/worktree/branch or deletion occurred. This new prose file is the sole write. G/C/F/P below refer respectively to those four files.

## Signature and intended refusal

Both current public methods have exactly this signature (F802, P1292), with no defaults and no wrapper on load_for_mode itself:

```python
def load_for_mode(
    self, state: Mapping[str, Any], *,
    requested_mode: history.AccessMode,
    lineage: RNGOperation | None,
) -> None:
```

For the supplied standalone fixture, pass explicit `lineage=None` and the existing wrong policy `requested_mode="archived_history_fresh_episode"` with its otherwise valid captured replay transport. Omitting lineage fails Python argument binding with TypeError before the method body; it is not archive-policy evidence. None is the correct explicit standalone choice, not a default or a nested-parent fallback. The policy-negative path itself exits before it consumes/authenticates that lineage, so the refusal also cannot serve as a lineage-authentication test.

For successfully validated captured/current data (`validated.legacy_state is None`), the exact reached policy exceptions are:

| Owner | Source | Exception |
| --- | --- | --- |
| ReplayBuffer | F810–811 | `ValueError("current replay cannot discard qualified active rows")` |
| PrioritizedReplayBuffer | P1298–1299 | `ValueError("current PER cannot discard qualified active rows")` |

The fixture must establish valid input and reach this intended branch; a broad ValueError alone could instead accept an earlier malformed-schema/content refusal. An exact message assertion is a direct causal witness for this current negative. The original retained-row, legality, component-presence, ownership and source-isolation assertions remain independent obligations. No fixture code was inspected or edited here.

## Ordered phases and owner health

1. After successful argument binding, unsupported requested_mode values refuse immediately with `ValueError("requested_mode is unsupported")` (F804–805, P1293–1294), before replay health/owner acquisition or transport validation. This is a different negative from the intended recognized-but-incompatible archive policy.
2. Recognized modes validate the complete transport first. Flat explicitly enters `_local_operation("load_for_mode", (state,), {}, mutation=False)` and calls `_validate_serialized(..., expected_obs_dim=None)` (F806–807). PER calls its public `validate_serialized(..., expected_obs_dim=None)` (P1295), decorated `@replay_local(mutation=False)` (P1254–1257); C598–605 supplies the same local-operation protocol for that route.
3. Local validation acquires real replay owner exclusion, checks `_replay_healthy`, refuses unrelated lifecycle reentry and inventories the route (C230–242,437–475). CPU-only validation uses owner exclusion without ambient RNG admission. If its actual source work needs CUDA, the existing authenticated local gate resolves and completes that inventory under the producer protocol. Local validation is not sample/prepare/install admission and creates no PreparedReplay handle.
4. Only after successful validation and normal exit of that local scope does load_for_mode apply the archive policy checks. The captured/current wrong-policy ValueError above is therefore outside the local validation context and before `materialize_validated` or `load_prepared`. Unless an external scope independently retains it, the local validation's owner lock has already been released. A quarantined owner, malformed input, local CUDA refusal or completion failure prevents this intended policy branch from being reached; none should be mistaken for the desired negative.
5. Compatible policy proceeds to materialize/install with the caller-supplied lineage (F812, P1300). That later path is not executed by this policy negative and remains governed by the original issuer/currentness and admission rules.

The opposite recognized policy mismatch is maskless historical data (`validated.legacy_state is not None`) with requested_mode="recorded_full_resume" (F808–809, P1296–1297). It raises `HistoricalLegalityUnavailable("missing historical successor masks; use approved archived_history_fresh_episode")`; C27 defines that class as a ValueError subclass. Do not substitute this different branch for the captured/current refusal. PER captured5 and current6 are handled as nonlegacy data by its validator; maskless4 is legacy (P949–953). Flat current5 is nonlegacy and maskless4 legacy (F553–557).

## Exception effects for legitimate negative testing

The intended policy ValueError is an ordinary direct replay exception, not a failure escaping a managed native owner callback. It does not itself latch replay health, advance replay mutation revision, poison the domain, issue/consume a handle, or publish replay storage. Both local validation routes use mutation=False. CPU local cleanup simply clears `_replay_scope` (C444–452). A body validation exception alone similarly does not quarantine replay; CUDA local completion uncertainty is separately detected and quarantines in C472–475, with poison/reporting in G858–895. Bootstrap/query failures retain their independent effects described in the original supplier; successful validation copies are real work even when the later policy refuses.

Accordingly a standalone `pytest.raises(ValueError, match=...)` around the actual load_for_mode call with explicit lineage=None is the appropriate caller-level negative shape. There is no replay requirement to catch that expected policy exception inside a callback to keep replay healthy. If a fixture chooses to wrap the call in some other managed owner callback, that other owner's exception-latching contract remains separate and is not overridden by this addendum. Do not add such a callback or mask unexpected errors merely to exercise this replay policy branch.

This source addendum supplies no executed RED/GREEN, broad gate reduction, B6/hardware qualification or parent acceptance. All original fixture assertions, root custody and independent review obligations remain.
