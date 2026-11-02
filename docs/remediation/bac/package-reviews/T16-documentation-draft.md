# T16 source-verified documentation draft — qualification pending

2026-11-02, existing `/workspace/hamlet`. Only this ignored draft is written. Root reports the R4 candidate frozen under mandatory G2:6873 selected, four workers, session5344. That campaign and new genuine clean native captures remain pending. Keep **25 qualified packages of66 /41 remaining** until root closes the actual gates. No new source commit SHA, full-suite result or CI success is assigned by this draft.

This is a finite correction to current runtime prose, not a broader README/BAC review, new design, constructor/cap change or requirement closure. Preserve the dated README source/CI stamp at28–35 and BAC's document-wide historical review stamp, together with T15's separately dated bounded correction at121–127. Earlier qualification/review/runtime receipts retain their actual trees and outcomes.

## Five-source facts and proof boundary

Exactly the existing five complete implementation/test files remain the source context, **4422 physical lines**, under the five-source/4900 projection. No sixth implementation/helper/environment/config/sampler/network/conftest/consumer source was opened. Consumer/storage/RNG facts outside this inventory are explicitly attributed to the existing source-verified prose below.

| Complete source | Lines | Freshly verified SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |529|`2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`|

Verified relevant anchors:

- RR401–454 uses one canonical `effective_run.training` copy for learner loop/size/batch inputs and existing curriculum/Adaptive construction. RR461–470 reads canonical effective brain and complete resolved replay, then names the executed episode-limit/cap derivation and its launch/declaration origins. BC534–568 establishes exactly the five effective overrides; POP325 directly preserves gamma0.
- RR474–497 calls actual `VectorizedPopulation.for_training` with all six replay leaves, declared retained-transition minimum, separate `Generator(PCG64(effective_training.seed))`, origin `authored`, executed episodes×declared cap horizon and fresh tick0. POP198–267 supplies the real public seam; POP112–149 validates and owns the complete setup. POP469–506 selects actual configured flat/recurrent replay. The named horizon is an upper bound in **vector ticks**, independent of N, transition budget, occupancy or successful updates.
- RR522's existing checkpoint load remains after construction. POP595–641 distinguishes pristine constructor buffers from loaded/owned state; POP2033–2075 installs restored replay and learned clocks then invalidates binding for adoption. RR adds no post-load reconfiguration/reseeding. This is source-level preservation evidence, not a new complete native-resume runtime proof.
- Existing ordinary construction/inspection/serving remains unchanged (POP159–195,508–537,595–641). Its normal successive flat-PER role may retain external global NumPy ownership; it does not acquire a universal fresh-PCG64 promise. Loaded supported current state retains its validated saved sampler/ownership instead of being forcibly converted to the fresh policy.
- Fresh PCG64 ownership describes **PER**, not every replay family. Flat uniform construction atPOP506 still uses its uniform buffer; recurrent uniform atPOP490 uses the selected uniform-sequence adapter without a passed owned sampler. Existing source-verified `T15-flat-contracts.md` establishes Torch uniform sampling without replacement; `T15-interface-proposal-r1.md` establishes the retained Python-random recurrent-uniform roles. Neither was re-proved by opening a sixth buffer source. Both uniform adapters and ordinary/global low-level roles remain selectable.
- The explicit factory's `replay_option_provenance` debug tuple stays None (POP453); compiled lazy binding supplies its own tuple at639–641. Canonical effective field_roles/derivations/origins retain authored versus bac-options-v1 leaf provenance. The sampler's `authored` origin is a caller seed/configuration-policy label and must not overwrite those leaf roles.

## Minimal ready-to-apply prose

The behavior statements below describe verified source. STATUS supplies qualification; source implementation is not labeled released while G2/native gates remain open. Root can apply these bounded text changes after reconciling actual qualification evidence.

### README.md:375–378 — replace only the local BAC note

```markdown
T15 learner changes (2026-11-02) cover recorded historical legality, backend readiness,
recurrent objectives and finite TD telemetry. T16 runner wiring consumes the canonical effective
brain, resolved replay policy and declared warmup, with an explicit fresh PER sampling stream
and vector-tick beta horizon. [BAC status](docs/remediation/bac/STATUS.md) records package
qualification and remaining native/runtime/learning requirements. These bounded notes do not
refresh the broader dated source/CI review above.
```

Retain the architecture table, broad known-work list and dated source/CI review. No whole-product convergence, GPU, private-curiosity or native-continuation claim follows from this note.

### docs/architecture/BAC.md:127 — add after the existing T15 bounded-correction paragraph

```markdown
T16 bounded runner correction, 2026-11-02: the runner propagation below was checked against
`demo/runner.py`, `population/vectorized.py`, `config/brain_config.py`,
`agent/optimizer_factory.py` and the new runner-readiness test. Package qualification and open
native/runtime requirements remain recorded in [BAC status](../remediation/bac/STATUS.md).
This correction preserves the broader dated review boundary above.
```

### docs/architecture/BAC.md:173 — insert this runner bullet before the existing construction/restore bullet

```markdown
- `DemoRunner.run()` eagerly constructs its learner from the canonical effective brain and
  training view. It forwards all six resolved replay leaves and declared `min_size`, preserving
  their effective roles/provenance. Fresh PER receives a separate
  `numpy.random.Generator(numpy.random.PCG64(training.seed))` with sampling origin `authored`.
  Beta uses the named upper-bound vector-tick horizon: executed maximum episodes (including a
  recorded launch override) times the declared per-episode cap, with both sources recorded.
  Population size and live-transition budget do not replace that horizon. Fresh tick0 is
  supplied before the existing checkpoint load, with no new post-load reseeding or replay
  reconfiguration (`demo/runner.py:401,461,474,522`). This fresh PER policy does not change Torch
  flat-uniform sampling, the selected recurrent-uniform adapter's Python-random role, or saved
  sampler ownership restored through existing supported loaders.
```

In the existing construction/restore bullet at173–183, retain ordinary constructor/inspection/serving, pristine-versus-owned adoption, History A and native/provider limits. Make only these related edits:

- Use the verified current factory anchor `population/vectorized.py:198` where the same factory is currently linked at204.
- Remove `natural runner for_training propagation (T16)` from the future-work list; the new bullet describes its actual source. Retain full native10/7 continuation/resource/RNG atomicity (T24/T25), private-curiosity isolation/X02 and ICM ENV reward/update integration (T18e/T18f).
- Preserve the meaning of loaded-state adoption: fresh PER ownership does not prove every restored artifact has that ownership, does not authorize overwriting saved state, and is not an exact stochastic-continuation promise.

### CLAUDE.md:209 — insert after the existing context-manager guidance and required-level line

```markdown
`run()` takes learner inputs from the canonical effective configuration and calls
`VectorizedPopulation.for_training` with resolved replay options and declared retained-transition
warmup. Fresh PER uses an owned PCG64 Generator seeded by the selected training declaration.
Its beta horizon is the executed maximum episodes times the declared per-episode cap, recorded
with launch/declaration origins in vector ticks. Fresh construction precedes the existing
checkpoint load; loaded sampler/history/clocks continue through existing validation/adoption
without a new post-load configuration call (`demo/runner.py:401,461,474,522`). Uniform replay
keeps its existing RNG roles. BAC STATUS records qualification and the remaining native10/7,
private-curiosity and provider-integration requirements.
```

Keep the context-manager examples and constructor signature unchanged. The consumer repair does not introduce a public mutable runtime-loop/cap API; its observed canonical-copy behavior and actual test-hook repair remain in their separate scoped receipt.

### docs/remediation/bac/options.md:3–8 — replace the opening paragraph only

```markdown
This package declares portable, immutable, finite-only options. Declaration loading and
resolution do not by themselves establish runtime qualification. T15 consumes resolved replay
policies through explicit or compiled-adapter population learning; T16 forwards the canonical
effective brain, all six resolved replay leaves and declared warmup through the real runner's
eager learner seam. [STATUS.md](STATUS.md) records qualification and remaining native/runtime
requirements. Consumer ownership remains effective configuration/roles T03, encoders T17,
replay T08–T16, exploration T18a–d, curriculum T20–T22, checkpoints T24–T26 and evaluation T27.
```

After the retained warmup/readiness paragraph at106–112, add:

```markdown
The runner supplies fresh PER with an explicit owned PCG64(training.seed) stream and sampling
origin `authored`; that sampler label is separate from each option leaf's authored or
bac-options-v1 provenance. Its beta horizon names the executed episode limit and declared cap
as an upper bound in vector ticks, before checkpoint loading. For supported current payloads,
existing validation/adoption preserves the saved sampler descriptor and any recorded owned RNG
state; it does not force a fresh PCG64 stream on resume. External-global sampler roles do not
gain an exact RNG-continuation guarantee.
Uniform replay retains its existing Torch/Python-random roles. Parsing the other options or
running these N1 fixtures does not qualify private-world curiosity or provider precedence.
```

Keep the existing per-family active/inactive roles and nonselected presets. This bounded T16 correction does not refresh unrelated transport/checkpoint persistence or provider-consumer assertions from unread implementations.

## STATUS and ledger — current pending text, then conditional transition

Current `docs/remediation/bac/STATUS.md:37` and ledger top-level `phase` correctly say25/66; preserve them during G2/native qualification. The dated T15 paragraph at35 and its source/tree/full/native history remain intact. A minimal pending paragraph to add before the count is:

```markdown
T16's frozen candidate eagerly forwards the canonical effective brain, all six resolved replay
leaves and declared warmup through the real runner. Fresh PER uses the selected training seed
for its separate PCG64 sampler and records a launch-adjusted upper-bound vector-tick beta
horizon before checkpoint load. Existing loaded-state adoption and ordinary constructor/
serving roles remain. Scoped source reviews and runtime selections support this change, but
mandatory G2 and new genuine clean-source native captures remain pending; T16 is not yet
qualified. Complete native10/7 continuation, private curiosity/X02, full ICM integration and
final common-source acceptance remain open.
```

AtSTATUS11, the old phrase “runner propagation and complete native continuation remain required in their subsequent packages” can be narrowed now to “T16 runner propagation has a frozen implementation candidate; its qualification and complete native continuation remain required.” After actual T16 closure, root can instead state that T16's ordinary runner propagation is qualified below while complete native continuation remains T24/T25.

After **actual** mandatory G2, new clean native captures/independent postflight, required review/guard closure and exact source identity reconciliation, root may:

1. Replace the pending T16 paragraph with a scoped qualification paragraph populated only from the actual receipt: committed source/tree, actual terminal full totals, six guards, independent review/runtime scopes and native capture/postflight identities. Persist the real qualification receipt before linking it; `evidence/wave10-qualification.json` is a proposed destination, not an existing proof claim. Preserve every failed prerequisite, R2's11PASS/1FAIL and repaired-source identity separately.
2. Make the tail of the historical T15 paragraph explicitly historical: “At the T15 checkpoint, T16 canonical runner/owned-sampler propagation, full ICM integration, private curiosity/X02 and complete native10/7 continuation remained open; later package status is recorded below.” This preserves the actual T15 boundary without contradicting a later scoped T16 release.
3. Change only the package count to **26 qualified packages of66 /40 remaining**, in STATUS37 and acceptance-ledger `phase`; retain all54 requirements/22 fresh final lenses+synthesis and final gates. Select the next existing authorized package through root's ledger, rather than inventing a next task here. Source publication/remote CI status must reflect actual exact-tip results separately.
4. Append scoped T16 package evidence to ledger rows **D02, D09, D21, G02, G06, BAC-C01, BAC-C02, BAC-C06 and BAC-C07**, retaining their existing package history. Use actual source commit, qualified tree, review/runtime receipt and qualification paths with scope `qualified_scoped_package_not_whole_requirement_closure`. Add actual evidence paths; preserve existing T15 and earlier receipt links.
5. Keep final row disposition/remaining-severity/common-candidate closure open where T37/T38 or other named owners remain; package count26 does not close those requirements. Map runner diagnostics to D02/G02, warmup/cadence to D09, genuine recurrent PER to D21, gamma0 targets to G06, and canonical policy/provenance/fresh-owned-stream boundaries to the applicable contracts. BAC-C07 must retain full native resume/atomicity as REQUIRED OPEN.

The new current nodes available for scoped ledger linkage include `test_real_runner_owned_sampling_identity`, `test_real_runner_warmup1000`, `test_real_runner_recurrent_per`, `test_real_runner_family_cadence_and_zero_gamma` and `test_real_runner_window_diagnostic` in the owned test. Their existence and scoped results do not establish joint/final acceptance by themselves.

## Current proof attribution and limits

| Evidence | Actual scope/status at drafting |
|---|---|
| Main static review, `T16-independent-review-r2.md`, including R3 addendum | Fresh source/spec/quality PASS; R2 tree `d57c3e3fc5303533fe2b7e3e220f85e3e8ba7d36`; narrow corrected R3 tree `0bdd6133f2224b25bce5668e15021fa1353accba`. R2's missed diagnostic-oracle fault is explicitly acknowledged; R3 checks its truthful correction. |
| Root R2/R3 main selections | Exact causal two GREEN; root owned run11PASS/one diagnostic assertion FAIL, then exact corrected fixed_full case PASS with unchanged other11 binding. These are separate executions, not relabeled as one final-source whole-file12PASS. Root reports six guards PASS; later full G2 owns common-source qualification. |
| `T16-independent-runtime-r3.md` | Independently executed three selected cases PASS,32.19pytest/36.62794756889343wall seconds, exact R3 tree. Covers fresh flat owned stream, eager recurrent replacement PER and corrected fixed-full/no-update diagnostics through normal checkpoints; not warmup1000/all-family/all-law/adaptive or resume proof by this reviewer. |
| R4 consumer source review/runtime | `T16-consumer-independent-review-r4.md` approves the two bounded fixture repairs. `T16-consumer-independent-runtime-r4.md` independently executes exact4 PASS,29.92pytest/35.62947058677673wall seconds, tree `51c6d53eb2a815257b7eab4bffa800fb54d8a2a2`. Root separately reports exact4/all21 direct consumers PASS. No consumer implementation was opened here. |
| Mandatory G2/new native qualification | Root reports frozen R4 full6873 selected/four workers RUNNING; fresh clean native captures and independent postflight PENDING. No full/native/release/CI success is asserted by this draft. Earlier T15 native captures retain their T15 source identity and cannot be relabeled T16 qualification. |

These selections overlap and must not be summed. Prior candidate-specific executions retain their original global trees; unchanged five-source hashes do not turn an R3 execution into R4 whole-tree qualification. No listed test/runtime command was run by this documentation writer.

The owned529-line file provides12 parameterized **fresh-run** cases. `_make_pack` at219 reads authored YAML, `_run` at267 supplies an explicit episode override and transition budget, and its load observer requires no checkpoint. All fixtures use **N1 and seed42**. Therefore they do not independently detect a hardcoded42 mutation, exercise the no-override horizon-origin branch, distinguish an erroneous N multiplier at runtime, or prove real runner resume. Actual reviewed RR492 uses the selected seed, RR464–470 handles both episode-origin branches, RR494 contains no N multiplier, and RR522 precedes no new sampler reconfiguration; those broader facts are static code evidence.

Tests354/389/416/456/492 respectively cover fresh PER ownership, literal warmup1000, both real recurrent PER laws, four-family cadence/gamma0 and fixed/adaptive diagnostics. Real samples/finite Q optimization/parameter changes accompany ownership observations. The cases do not re-prove every sampler probability/IS theorem, all uniform adapter mathematics, every alternate option value, recurrent BPTT, multiworld curiosity isolation, provider precedence or complete native continuation. Existing sampler/learner/provider/native owners and final common-source54 requirements/22 lenses remain necessary. Source-level preservation of loaded state must not be promoted to an actual fresh-only resume PASS.

Curiosity remains the existing shared AdaptiveIntrinsic/RND arrangement from selected training, one population module; these N1 controls prove no private bank/world differential. RND service continues during Q warmup. Local clocks remain retained eligible transitions for warmup, actual vector ticks for beta, and successful Q optimizer updates for LR/target. Native10/7/T24/T25, private-curiosity/X02, ICM full reward/update/continuation/T18e–f, final learning/E2E/T40, coverage>=70%, slow/applicable hardware, fresh final reviews/synthesis and exact-tip CI remain open at their actual owners.

## Custody

Guidance/prose read as needed: current README, BAC, CLAUDE, options, BAC STATUS and acceptance-ledger DATA; existing main/consumer review/runtime receipts and previously verified supplier prose. Source links in those receipts were not followed. The only write is this ignored draft. No source/test/tracked-doc/DATA/index edit, project import/runtime/pytest/collection/compiler/linter/probe, branch/worktree/checkout/source copy/deletion, subdelegation, tracker action, commit or push occurred. Existing14 checkouts remain preserved. Return stationary for root's actual G2/native results and later documentation reconciliation/application.
