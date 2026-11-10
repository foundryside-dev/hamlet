# T18d none-scale authored test review

SPEC: APPROVED for the narrow prerequisite authored-test baton.

QUALITY: APPROVED for the same static scope. No material findings requiring test edits. This is not fixed-production approval or a runtime PASS claim.

Reviewed the brief, authored report and authored patch against AGENTS.md, original T18d acceptance, current BANK/checkpoint public contracts, readiness guidance and the wave32 checkpoint receipt. Existing no-backwards-compatibility instruction supersedes original adapter wording. Examined the relevant real Rig/independent witness paths and current BANK producer/restore and CP cache validation. No fifth implementation/helper/provider/RP/WS/ENV/HC source was opened, and no runtime introspection was performed.

## Exact bounded inventory

Independently measured with wc and sha256sum during this review:

| Whole source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/curiosity_checkpoint.py | 1135 / 1200 | 9499dad4774ab6df303e970ff2871436e9f018c5e5bbf8482faaf7df1873d740 |
| src/townlet/exploration/scoped_curiosity.py | 1282 / 1300 | a122097fa313e335a4213499627dc1b071aa02600984829dc08d80ddba0bb363 |
| tests/test_townlet/regressions/bac/test_pw_scope_conversion.py | 1456 / 1456 | 672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 |
| tests/test_townlet/regressions/bac/test_none_scale.py | 233 / 1000 | 646797d6f256c6396f57b0203413614bb0c4b7b2786b764ed62c425b45e53a13 |

Actual total 4106; ceiling total 4956 <= 5000. Inspection used only this four-source envelope. Public contract inventories are documentary evidence, not extra implementation reads. No source/test modifications, runtime/import/compile/probes, Git/index operations, branches/worktrees/copies, publication or subagents were used. Only this requested ignored review artifact was written; its ignored status is inherited from root/authored-report custody, not independently queried with Git.

## Evidence supporting the verdict

- Both shared and per_world cases create real selected none policy via the existing fixture. That fixture explicitly writes initial_weight=0.4, and the new test independently asserts the resolved positive value before work. Expected zero raw/scales and contribution are literal tensors compared by the independent equal witness, not production-derived expectations.
- Mixed eligible/inactive rows flow through actual Rig ENV stepping and BANK reward/service. The first selected-scale assertion inspects the real returned BANK scales; zero contribution alone cannot pass it. Current BANK lines 568–571 select 0.4 for none, so the assertion targets the stated defect directly. No passing payload is manufactured and no assertion is weakened to fit current output.
- Tests check unchanged reward and service retries, event identity, BANK revision and exact checkpoint state, zero predictor clocks/counters/loss, genuine eligible BANK cursor progress, unchanged native none state and real local/step caches. Checkpoint exports themselves advance revision; retry captures its reference revision after export and checks it before the comparison export, which is consistent with the existing contract.
- Live restore prepares and installs genuine current producer transport under the actual accepted capability, verifies replayed current reward/service, and continues a real next step. Completed restore uses real Rig completion, actual retained ENV parent preparation/correlation and parent installation before a genuine next episode. Fixture other-role receipts remain cooperative interfaces as already documented; they are not substituted BANK or ENV capability implementations.
- Prepared ownership checks mutate caller cache and retained parent callback views only after preparation. Installed state must still equal the original saved current transport. Negative cases clone a genuine producer export and corrupt only the intended transport fields; selected_nonzero changes both local cached scale and corresponding step scale to 0.4, preventing correlation mismatch alone from satisfying the refusal test.
- Corruption tests cover both phases and scopes, raw_nonzero, missing_scale and obsolete schema as well as coherent selected_nonzero. They check no mutation of BANK state/revision, actual native/provider identity witnesses, caller input and ambient Torch RNG. Each then prepares/installs the unchanged original current state on the same destination and continues; live cases also retry the restored current reward/service. This rules out blanket refusal as an acceptable implementation.
- Current CP lines 903–913 require nonadaptive cached scale equal to initial_intrinsic_weight while requiring none raw zero. Consequently healthy zero-scale exports become acceptable only after coherent producer and validator repair. Producer-only and validator-only changes cannot satisfy the whole suite. There is no fallback, migration, hidden normalization, fabricated native source, provider patch or new helper source in the authored patch.

## Reachability and limits

Static control-flow inspection finds no obstacle to the later healthy/negative restore assertions once BANK emits truthful zero selected none scale and CP accepts exactly that scale. Until that coordinated repair, the first actual scale assertion intentionally stops those scenarios. Root reported successful collection of 22 identities in 5.9403 seconds with actual Rig imports; that is attributed collection evidence, not 22 passed behavior tests. Root subsequently reported both actual causal cases RED in 16.7776 seconds at current816728bf: both scopes reached assert_reward with scales [0.4, 0] versus literal expected [0, 0], after correct raw/eligibility and genuine ENV/native paths. Root reported negative custody PASS and all runtime closed. This is attributed root evidence; this reviewer ran no tests. Broader 22-case RED adds no prerequisite evidence because later cases intentionally depend on truthful zero producer output.

The 22 authored identities comprise 2 direct cases, 2 live restore cases, 2 completed restore cases and 16 corruption cases. They cover this narrow CPU, synthetic 3D/two-action geometry, ordinary current-cache requirement. All-inactive batches, alternate update_stats modes, origin-bearing conversion archives, other selected families and broader owner/codec behavior rely on their existing suites and are not newly qualified here. None has no trainable parameters, so the fixture's parameter/optimizer storage sets are empty for this family; native equality and provider identity still supply meaningful refusal evidence. No new full simulator continuation promise follows.

Actual whole fixed-source review and authorized runtime/coherent owner-suite verification remain required after the separate production baton. Original T18d facade/global selector/current HC/parent/POP/runner/replay learning, T26, full/default/coverage/slow/hardware, final54requirements22lenses and exact-tip CI remain open. This review closes no original T18d acceptance package and does not increase original28/66 releases.

## Actual fixed-source and design review

SPEC: APPROVED. QUALITY: APPROVED. No material findings in the narrow coordinated BANK/CP repair. This supersedes the earlier pending fixed-source review gate, but does not claim runtime verification or completion of T18d.

Reviewed the actual candidate production patch, appended author report and whole current CP/BANK sources, including their construction, reward/retry, service, completion, current codecs, parent authentication, initialization/origin validation and restore publication interfaces. The initial combined output was truncated; bounded subsequent reads supplied the production sections for inspection. The already reviewed new test and reused genuine fixture remain frozen. Candidate identity b848b95aec04d580b9d188f10061f1e5c9173ddb and base c1de are root-supplied; no Git query was made.

Independently remeasured current source inventory:

| Whole source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/curiosity_checkpoint.py | 1138 / 1200 | 4de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a |
| src/townlet/exploration/scoped_curiosity.py | 1284 / 1300 | 294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f |
| tests/test_townlet/regressions/bac/test_pw_scope_conversion.py | 1456 / 1456 | 672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 |
| tests/test_townlet/regressions/bac/test_none_scale.py | 233 / 1000 | 646797d6f256c6396f57b0203413614bb0c4b7b2786b764ed62c425b45e53a13 |

Actual total 4111, ceiling total 4956. No fifth implementation source or helper was inspected or introduced by this review.

The producer selects 0.0 inside its actual provider callback for none. It still invokes the real provider novelty operation through the existing owned/shared call boundary. The selected zero flows through the ordinary float32 device tensor assignment into CuriosityReward, pending reward and local reward cache; no facade or return-only masking exists. Shared and per_world grouping both use this callback. Inactive rows retain the preexisting zero initialization and no provider call. Private local retry and shared current retry reuse those same zero-bearing caches, rather than recomputing or replacing the reward. Service remains unchanged and continues to advance genuine eligible BANK positions without predictor clocks or counters for none.

The checkpoint validator still first checks exact local fields, tensor shape/dtype/device/finiteness, provenance, cursor equations, completion and step/local correlation. It now independently requires none cached selected scale to equal a float32, selected-device zero using the existing exact comparator, and retains the separate none raw-zero requirement. A coherent 0.4 edit to both cache representations therefore fails semantic scale validation even though their mutual equality holds. Healthy current zero caches reach native preparation and owned publication without normalization. Missing scale and obsolete schema still fail existing strict checks. Restore refusal remains before live provider publication; revision-bound handles and final accepted-token authentication are unchanged.

The other strategy branches remain substantive: adaptive reads its actual current provider weight and keeps its existing bounded cache check; Count/RND/ICM continue to use resolved initial weight and exact nonadaptive cache validation. No scope exception, capability reduction, new option, compatibility fallback, historical rewrite or provider algorithm change appears. Initial/private_initialized states have no reward cache, so the new semantic check does not invent work. Shared-to-private initialization validates actual source records, and origin validation recursively validates archived source records through the same corrected validator. Consequently obsolete nonzero none caches also refuse inside current origins rather than being silently migrated. Freshly produced truthful source archives retain the existing owned/archive/baseline semantics.

The frozen tests remain appropriate and reachable after this coordinated repair. Their positive live/completed restore and healthy retry cases prevent a validator that simply rejects every none cache from passing; their coherent corruption cases prevent replacing semantic validation with cross-cache equality. No test edits or fabricated passing payload accompany the fix. Existing broader family/conversion/owner/codec suites remain the required runtime regression evidence; this static review does not replace them.

No runtime/import/compile/probes, source edits, Git/index operations, copies, subagents or publication occurred in this review baton. Root collection/focused checks were in progress at assignment; this reviewer claims no new runtime result. Await the separately authorized pinned independent runtime specification. All integration, hardware, release-count and original-T18d limitations above remain in force.

## Separately authorized independent runtime

Root subsequently granted the exact one-worker independent spec after reporting current collection22 PASS in6.8824s and focused2 PASS in15.1871s. Executed only the prescribed locked runner and its verifier in /workspace/hamlet:

`python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave33-r2-independent-spec.json`

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave33-r2-independent-spec.json`

Actual independent child exit0; verifier exit0. Verified 22 passed, zero skipped/xfailed/xpassed/warnings, wall279.65746450424194s. Candidate b848b95aec04d580b9d188f10061f1e5c9173ddb, base c1de41509ae108848fd5bf295487510254daab6b. Verifier reports source/index/import/thread/fixture custody PASS with355 source guards,573 config digests,13 protected artifacts,2 process identities,14 registry records and1 available worktree. The runner log SHA256 is b1cafed713e14af977778d8c3fda8b9bb2239e9cf48ece2f4e82749ec520932e; manifest SHA25699593ea5ad4a43ae5f07a3a8737898130c21df0fbe16aa26e3c0fcef7b8ec9b9; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791.

Final bounded verdict: SPEC APPROVED; QUALITY APPROVED; independent22 runtime PASS on the exact fixed CP/BANK hashes recorded above. No material findings or scope waivers. This supplies actual healthy live/completed restore, coherent corruption refusal, unchanged retry and no-predictor-work evidence for the authored cases, beyond the earlier static reachability judgment. Root's broader coherent regression gate remains separately owned. No additional probes, source/test/index edits, copies or subagents were used. Whole T18d, integration/hardware/CI and original28/66 release limitations remain unchanged.
