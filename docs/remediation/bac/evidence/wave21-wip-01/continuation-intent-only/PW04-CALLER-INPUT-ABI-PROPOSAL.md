# PW04 finite caller input-custody ABI proposal

Intent-only proposal until the appropriate factory/bank/input/runtime owners implement and review the integration; root owns scope review and serial source implementation. No source/test/runtime/Git operation accompanies this capsule. Backend qualification is attributed to root's 7e702ab8 receipt and CURRENT-BACKEND-LOCAL-SERVICE-CONTRACT.md: 262 owned and 262 independently rerun PASS. Root now reports the five-file fixture migration has 150 component PASS; the actual ordinary runner case remains REQUIRED OPEN. Integrated caller/bank/runner/native acceptance and global mypy remain OPEN.

## Stable source context

Exactly the same three charged sources remain unchanged:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/population/vectorized.py | 2329 | 629efddfd259aa5bc39f8c4c119b506f1c1eeb17b338c564751dc0ddc820cd92 |
| src/townlet/demo/runner.py | 1017 | e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf |
| src/townlet/demo/live_inference.py | 1249 | afa9fbb917d1ddef75ca0b7df26878cfbcbac79ceacce60f11e1ee5322e8e9b3 |

Actual3/4595, projected3/4640. No fourth provider/helper/test/resolver/ENV implementation inspected. The public current backend contract was read as allowed prose. It guarantees required constructor rng/unit inputs, immutable read-only service_clock_unit, explicit shared None/vector_tick, real private owner candidate RNG, and no retained provider RNG owner.

## Exact proposed seams

The actual reconstruction helper is POP2299 `_reset_rnd_state`, with one in-file caller POP2296 `load_token_network_cross_universe`. Preserve these actual names and the existing reset algorithm.

Proposed actual POP signatures:

```python
def load_token_network_cross_universe(
    self,
    source_q_network_state: dict[str, torch.Tensor],
    *,
    rng: WorldRNGState | None,
) -> TokenRosterReport: ...

def _reset_rnd_state(self, *, rng: WorldRNGState | None) -> None: ...
```

Exact forwarding in the existing call: `self._reset_rnd_state(rng=rng)`.

In existing `_fresh(rnd)`, keep every current argument and math, and add exactly:

```python
rng=rng,
service_clock_unit=rnd.service_clock_unit,
```

For Adaptive, the actual nested object passed to `_fresh` is exploration.rnd; its validated immutable unit is therefore transported without class-label policy inference. The provider validates construction inputs; the caller explicitly supplies construction custody. No strategy.rng attribute, private seed derivation, RNG snapshot extraction, new default, old-signature probing, exception-swallowing, or provider-retained RNG is introduced. The exact WorldRNGState import path must come from the current owner type receipt; this capsule does not invent a module path.

A construction callback is not warranted by the three inspected sources: they already hold all ordinary RND constructor values, and only construction-domain custody is missing. A callback would add a broader algorithm-selection surface without current evidence of need. The five-file fixture migration has no additional reset-helper dependency.

## Preserved behavior and caller fixture transport

Existing shared POP cross-universe callers/fixtures pass `rng=None` explicitly to the cross-universe entrypoint (and direct helper fixtures to their helper). The unit comes from the current RND instance, not a new caller default. Existing private reconstruction callers/fixtures must pass the real owning candidate WorldRNGState while the actual owner maintains its required model_init/component activation custody. A merely private-looking unit or a replay NumPy RNG is not a substitute. The backend owns target/predictor allocation hooks; callers must not reproduce them.

Preserve the current reset's dimensions, current optimizer LR, training_batch_size, current epsilon/min/decay and device; fresh real fixed/predictor networks, Adam and novelty/RMS; direct-RND ENV rebinding; Adaptive wrapper identity, fresh inner RND, initial-weight restoration and survival-history clearing. Preserve token transfer report, target re-copy, learner optimizer/scheduler reset and training_step_counter reset, including the current behavior for other exploration strategy types.

This is intentional fresh-strategy reconstruction for cross-universe transfer. Ordinary bank episode reset retains learned models/Adam/tails/RMS and cumulative private admission position, and must not call this reconstruction surface. Private origin/configuration/bank publication after intentional fresh reconstruction remains the owner's explicit transaction; forwarding the immutable unit does not rebase native state or authorize publication.

RR430 and LIVE348 may add explicit constructor `rng=None, service_clock_unit='vector_tick'` to preserve their actual current single shared Adaptive construction. Their actual owned source has no private selection/factory dispatch. Declared per_world selection remains REQUIRED OPEN: these arguments must not be presented as the final selection-aware route. The actual resolver/factory owner must supply the exact accepted selection/provenance and private dispatch receipt before that capability is claimed integrated.

## Evidence and required checks

Current evidence: stable three-source custody above; concrete constructor omissions; producer's qualified immutable unit/RNG allocation contract. Root reports all 76 direct constructor expressions in the five-file owner fixture migration have been transported and 150 component cases PASS. The actual runner case remains REQUIRED OPEN. These results do not establish the proposed POP reset-input implementation or its coverage PASS.

Existing migrated constructor fixtures use explicit None/vector_tick for actual shared construction and real candidate_rng/world_eligible_admission for owned private factory construction, with current exact native fixtures. When the proposed actual POP signatures are implemented, their callers must explicitly transport rng=None for shared reconstruction or the actual owner candidate RNG for private reconstruction. No default or signature fallback and no assertion weakening.

After seal and runtime reopening, root should run the actual existing reset entrypoints for direct RND and Adaptive: verify all preserved values and reset semantics above; ENV binding/wrapper identity; same immutable selected unit; genuine fresh networks/optimizer/RMS; preserved epsilon pacing; independent history; explicit private RNG custody and ambient RNG isolation under the current owner fixture. Keep existing other-strategy reset controls. Missing required rng must fail as a call-contract error, not silently select shared behavior. Invalid explicit ownership must not gain an ambient fallback. Any newly introduced input refusal must be assessed for pre-mutation ordering at the outer cross-universe operation, which currently mutates token/target/learner state before calling the reset helper; no atomicity claim follows from constructor validation alone.

Then run owner fixture selections, types/default guard and bounded formatting/lint under root's existing QA rules. These are proposed checks, not executed results. Root must retain current native exact-key/schema and prepared-install parent repairs, actual bank/context/ENV identity/lifecycle integration, and the real ordinary runner artifact/digest/receiving-load/tail/Adam/LR/clock/next-update/deep-refusal gate. Those obligations cannot be closed by constructor or reset transport.
