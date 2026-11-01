# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-astra-core-review-r1.md`, SHA256 `828a48d75d209834daa2e498a513aa59c4efdd10af834c18eea9668e52eee579`, retained unchanged. Portable rendering normalizes execution paths.

# T14 independent core review R1

Verdict: **STATIC REVIEW CLEAR; independent runtime qualification pending.** No concrete P1/P2 defect or optional P3 finding identified in the complete retained five-source design/implementation assessment. This verdict does not certify unrun R1 tests, native acceptance, integration or release. R0 remains a separate unchanged historical report.

## Exact candidate and source custody

Existing `/workspace/hamlet`, base HEAD `01f2f64f42c2932177729607b337419355cb2720`, common candidate `324438ad58d9d5a85bba54e18be1ee225ada5969`, root manifest `wave08/green-r1-candidate.json` (112 guarded paths). Read-only Git comparison independently confirmed the index matches this candidate and the unstaged tracked diff is empty; no index/write-tree operation occurred. Full manifest guarding beyond this source inventory remains root-owned.

| Complete retained source | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/sequential_replay_buffer.py |1815|f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c|
| src/townlet/training/per_sampling.py |163|0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| tests/test_townlet/regressions/bac/test_recurrent_per.py |677|941747bb722eaa2c7a33dc7fa879dc591481f29cc73cfb4d837334854c8533bb|

Total **5/3171**, within reserved5/4350 and hard5/5000. The four unchanged sources and complete R0 SB were retained from their whole-source inspection; the exact candidate-to-candidate SB diff was inspected to bind the complete retained source assessment to R1. No sixth implementation/test/helper source was read. Other owners' unit/compact/native tests and HC/POP implementations were not opened.

Governing approved interface: R1 proposal `d6708084cb8bb63ba3febf8860b24a5f8b7a846da609c18ac2988aca35e77239`, approval `37d9bda30b9a7b00f2a084f1c70fb754d16cf293082b43e2892823346a50d2a8`, accepted P2/P3 frozen-plan identity `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`. Actual caller semantics are attributed only to prose `T14-HC-native-preparation.md`, SHA `b3a5e3e238e25d9ece19dee987bbecd69599539dfbe42c0ecd8cb5b8518868d7`.

## Complete contract assessment

**Mathematics and clock.** Explicit factory configuration distinguishes PER from uniform storage and clones an explicitly selected Generator. Absolute monotonic vector ticks determine beta from recorded initial beta/horizon independently of samples and warmup. Persistent admission/update/restore probes invoke public PS at beta0/B1 on discarded cloned RNG. Actual sample requests alone use actual B/current beta. Inspected PS preserves positive support, direct beta-tempered log weights, successive full-N all-one weights and law-specific ordered conditional corrections; SB preserves proposal order/q/population/rule and only adjusts the objective label. Nothing in R1 reintroduces hypothetical beta1 weight rejection, sample-max normalization, implicit RNG or optimizer-paced clocks.

**Contexts and state lifecycle.** Per-L populations enumerate actual contiguous retained fragment contexts in deterministic endpoint order. The first/end transition IDs and episode identity distinguish tail-context changes, with L supplied by each independent domain. Refresh retains unchanged handles/priorities, retires replaced contexts, stages all affected domains and allocates from a monotonic global counter. Clear preserves maximum/counter/configuration/RNG/clocks and admitted lengths. Readiness observes actual window counts and B/law availability without admitting a domain or changing state. Whole-episode and tail retention remain separately available.

**Update/sample atomicity.** Priority updates validate active IDs, real floating TD shapes, canonical masks and selected finite rows; stable float64 mean avoids intermediate overflow. Duplicate updates merge by maximum independent of ordering. Every affected full priority vector is owned and support-checked before one state assignment, with the running maximum installed at the same boundary. Sampling stages domain admission and RNG, constructs and validates the complete owned batch—including component presence, real lengths and successor masks—before installing its priority/RNG state. A failed first sample cannot admit its domain; a later numerical weight refusal cannot poison accepted persistent state.

**Restore and ownership.** Closed format7 validates exact configuration/provenance/declarations, beta formula, canonical domain cardinality/order/keys, unique bounded IDs, positive epsilon-bounded priorities and recorded maximum. Portable codec reconstruction fixes the five named families, validates complete public state layout/ranges and canonical re-encoding, and owns RNG state. All fallible tensor/device/RNG/support preparation occurs off-side. New uniform/PER or immutable-PER target incompatibilities are checked during validate/materialize, before the attributed POP learned writes, not solely in the installer. Recorded mutable clock/RNG/domain state is restored rather than compared with the target's sampling history.

**Preservation.** The genuine captured6 adapter keeps every active row/mask/ID/options/count/archive, derives only new PER state with explicit provenance and preserves target handle high-water/tick. Uniform6 output stays closed6; unconfigured7 adoption and configured-uniform refusal remain explicit. Historical5 approved-A archive/fresh replay, tagged inspection transport, designated new legacy rows, public dictionary sampling and both uniform adapters remain distinct. Archives never seed qualified readiness/domains. Current archival-reset refusal prevents silent loss of captured history. No removal/degradation/consolidation is introduced.

**R1 corrections.** Exact tree comparison shows one diagnostic adds the word `codec`; equivalent explicit branches replace three ternaries; duplicate reduction uses membership rather than a default-valued get; the global seen-handle set is explicitly typed `set[int]`. The first duplicate value previously equaled max(epsilon, priority), and earlier validation guarantees priority>=epsilon, so direct first assignment preserves semantics. These corrections preserve the complete mathematics/transport/lifecycle above. No whitelist or ratchet change is claimed by this reviewer; root reports the standing ratchet remains613.

## Evidence, gaps and runtime status

The retained counted regression covers exhaustive finite ordered/replacement SB→PS expectations with a nonconstant local LSTM, both objectives and reducers, multi-L context identities and eviction, duplicate/mixed-domain atomicity, five-family codec continuation, injected late sample/materialization failures, extreme full-N/beta0/fractional acceptance and actual-weight refusal, observational readiness/ticks, malformed restore, genuine captured6 DATA and historical/inspection/uniform controls, and early configured-target refusal. Both required named test nodes remain. No concrete missing test exposed a new counterexample during this assessment.

Root reports R0 core69PASS, native64PASS plus one diagnostic-regex mismatch, and affected-owner stale format-expectation failures. Those are **root-attributed R0 results**, not independent R1 evidence. R1 root collection/batch and this reviewer's independent run are still pending at this report revision. No project import/runtime/pytest/collection was executed by this reviewer. R1 must not inherit R0's green core result as its own executed result. A later exact-candidate runtime supplement is required before independent runtime completion.

## Limits and disposition

Only core storage/sampling/contract/options/countable regression sources are reviewed. Raw POP6/inner7 transport remains distinct from HC demo10/pop7 classification; neither automatic authored recurrent-PER training nor full native current admission is established here. T15 factory/producer/weighted recurrent learner/tick wiring and required X04 finite unweighted mean-TD telemetry remain due before release/G2. Native C07, T24/T25, evolved optimizer continuation, inference/resource/RNG isolation and final BAC acceptance remain OPEN. A new existing-consumer regression still requires repair and re-review before affected release.

Only this ignored report is written. R0 remains unchanged. No source/test/index mutation, staging/commit, branch/worktree/source copy/deletion, new executable probe/helper, runtime or subdelegation occurred. Existing14 worktrees remain untouched. User preservation/History A overrides blanket deletion guidance; no durable rule or user-only fallback was adopted, and the failed rule grants/restricts nothing. Actual instructions/tool approvals govern. Returned stationary pending root's runtime allocation.
