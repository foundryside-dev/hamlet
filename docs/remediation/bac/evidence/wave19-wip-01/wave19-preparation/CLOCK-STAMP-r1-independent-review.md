# CLOCK-STAMP actual-source independent review R1

Candidate: root-frozen base b954c812dc0e92044eb3cab503b371e3346b48a4, tree fc9be745ab293003ab8f69a8ad7dd52c23a48f2a. Contract: approved proposal SHA256 5251388f5ad7c0328b6be4825be595e4b3f8fafd2271f1babd6618ded8bac0f0, narrow CLOCK-STAMP brief and R2 design approval. Production report and root review package supplied the changed-source scope. This review examines actual changed source and tests, followed by separately root-authorized independent execution.

## Findings and verdicts

**Specification verdict: PASS for the narrow public primitive bridge.** No unresolved substantive mismatch found against the approved ABI. This does not approve implementation of bank or consumer obligations absent from this packet.

**Quality verdict: CHANGES REQUIRED for the introduced typing-gate regression below.** Independent runtime evidence remains63PASS/1CUDA_SKIP and does not clear that required gate. CUDA behavior remains unqualified. No optional extension is made a release blocker here.

R1 design findings remain resolved in actual code: stamp explicitly disables hashing; required later conversion/evaluation initialization semantics remain published in the approved capsule without adding live APIs. Future RP stamp import must still respect the documented WS-to-RP dependency and cycle-safe runtime validation handoff.

## Actual-source evidence

- WS62–93 implements frozen value-equal/hashable ServiceClock and CuriosityEventId. Clock unit uses exact str membership; `_integer` rejects bool/float/NumPy scalar aliases and enforces minima. Event identity retains exact nonempty strings with no normalization. Python integer domains remain unbounded.
- WS96–173 implements required keyword-only stamp inputs, exact tuple/EventId/string checks, duplicate refusal and common epoch. Tensor checks reject wrong type/layout/device/shape/dtype before tensor operations. Device equality is checked across all rows' vectors. Owned detach/clone candidates undergo all domain and ordered ID-content checks before any field publication. `tolist()` retains exact Python integers, so an oversized standalone ID cannot wrap into an int64 stamp. Active local0 refuses; inactive local0 and retained positive cursors are legal. Every supported tensor accessor returns a detached independent clone.
- Identity equality plus explicit `__hash__ = None` matches the approved contract and avoids tensor-generated equality. Tuple values and exact frozen EventId elements provide the promised cooperative immutable identity data. No arbitrary introspection/object.__setattr__ security boundary is claimed.
- Constructors add no provider callback, RNG call, accepted-token authentication, live cursor, receipt cache or coordinator. Clock regression, phase ordering, actual-context eligibility, retry content/expiry and current-format clone initialization remain their actual owners' obligations. The approved prose preserves whole-batch validation and refusal before future live mutation.
- Actual readonly RP context remains predecessor/actions/successor/active_on_entry/vector_tick with cloned tensor ownership and no stamp. No context migration, runtime bank qualification or PW04 provider/native-parent completion is inferred.
- Actual new regression covers typed units and minima/aliases; exact whitespace/Unicode IDs; active/inactive first and retained cursors; tuple subclasses/lengths; malformed later IDs, duplicate/order/common-epoch mismatch and oversized ID correlation; each vector's rank/dtype/layout/device/domain; noncontiguous owned inputs, independently mutated accessor results, frozen assignment and disabled hash; prior-stamp/input/global RNG preservation on late refusal; CPU no-CUDA-runtime control. CUDA ownership/mixed-device controls are conditional and were skipped on this machine. Tests do not simulate a bank to manufacture dedup evidence.

## Inventory and preservation

All four actual hashes and counts independently match the frozen production receipt:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/world_curiosity_state.py | 846 | 8eb88bbe6e0aa3bf7d40d03905d054a82b56ac2825e2970b5750a5456e8a9d6f |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 798 | 5e671b5693eb3741424b1fadb098eca6ea3d5f51599dddc1513c1f2292847848 |
| tests/test_townlet/regressions/bac/test_pw_clock_stamp.py | 317 | 3f015cfc3d354d4c7e3b5abdbaf07137d8abc37af7edc2cb2c79f0cf7c479364 |

Charged whole-file inventory4/2729 remains below named1500/800/1100/1000 ceilings and total4400. Source inspection stayed inside those four files. WS changed portion and the new test were read directly; readonly RP context and existing RNG test names were inspected. Existing RNG/body preservation was additionally verified byte-for-byte: streaming WS with only inserted lines62–173 omitted into sha256sum produced original WS hash8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82. No source copy or modified source was produced. Thus the previous KDF/descriptor/RNG/OwnedWorldBackend implementation is byte-preserved, not merely assumed unchanged from author claims.

Root separately reports collection96 and joint94PASS/2CUDA_SKIP/0warnings in14.1006s, with source191/config573/artifact13/process4 custodyPASS. These are attributed preservation evidence, not this reviewer's independent execution. The earlier tentative148 collection number is superseded; actual joint collection is96=64new+32RNG.

## Independent executable evidence

After static inspection root cleared the exact one-CPU independent slot and supplied unchanged reviewed orchestration commands. No helper source was opened. Executed from /workspace/hamlet:

`TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave19-r1-independent-spec.json`

Then:

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave19-r1-independent-spec.json`

Actual pytest target: tests/test_townlet/regressions/bac/test_pw_clock_stamp.py with --no-cov, no cacheprovider, bac_source_identity guard and root-provided basetemp. Collected64; passed63; skipped1; failures0; warnings0; xfail/xpass0. Pytest reports0.10s; full wrapper wall5.219651460647583s. Both wrapper and verifier exited0. Exec session97493 is CLOSED; no reviewer runtime session remains active.

Verifier reports exact base/tree above, source guards191, process identities1, config digests573, protected artifacts13, worktree registry records14, worktrees available1 and source_index_import_threads_fixture_custody PASS. Independent log: /workspace/bac-review-2026-11-01/qualification/wave19-r1-independent/independent.log, SHA256 9c90eddbe73f2ef8e9e3fb91db5b5f6e8f75112a0f391f724a7fbab2ffb05a0c. Manifest SHA256 658610e0db3d689b83425198b151e27b75858239a9d37bcddbc89500c8669f72; reviewed harness SHA256 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791.

## Limits and custody

Only this ignored report was written directly by the reviewer; authorized unchanged orchestration generated its normal qualification evidence. No production/test edit, extra source/helper inspection, ad hoc executable probe, branch/worktree/source copy, direct Git/index operation, deletion or subagent occurred. The root-authorized wrapper/verifier performed their established custody work.

Shared cadence and genuine learned private predictor/optimizer behavior remain required and preserved; immutable primitives do not establish those full integrations. Actual context/ENV-token binding, bank phase/retry/reset/resume/clone authority, PW04 local scheduling/native checkpoint coherence, runner format9, real-learning isolation and final BAC acceptance remain open with their named owners. This review does not replace root's other required gates or imply whole-package release.

## Required gate finding received before review closure

**R1-S1 — Medium, introduced typing regression; NOT ADDRESSED.** Root's exact frozen R1 guards report WS:105 `__hash__ = None` as incompatible assignment of None to object's `Callable[[], int]` hash attribute. Global mypy increases from the known7 errors/2files baseline to8 errors/3files. This is an introduced owned-file gate failure even though runtime hashing correctly raises TypeError and the independent64 tests pass.

Required repair: the original producer must express the explicit unhashable identity-equality contract in a way accepted by the project's required typing gate, preserving the approved ABI and existing hash refusal assertion. No broad suppression, guard weakening, baseline inflation or change to value-type hashing is authorized. Root will route the narrow typing repair after all frozen R1 jobs close, then requalify the affected exact candidate. This finding is attributed to root's executed guard, not an independently run mypy command. Specification behavior remains approved; quality approval is withheld pending that repair and required verification. No source edit was performed by this reviewer.
