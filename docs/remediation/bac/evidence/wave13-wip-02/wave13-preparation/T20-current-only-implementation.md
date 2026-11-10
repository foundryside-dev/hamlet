# T20 current-only implementation handoff

Stationary for root GREEN and fresh Astra medium review. This is authored implementation, not qualification or release. Root supplied current-only RED at HEAD `383d21ac` / tree `993b8092`: 80 collected, 46 FAIL, 34 PASS, 0 ERROR, 13.0982 seconds, including four actual R1 malformed-baseline/impossible-progress `DID NOT RAISE` witnesses. Root durably preserved that source/tests/evidence in WIP commit `af6b91f7166be8ac799cb97a08accaabf1022cb0`, explicitly not qualified/released. Those are received root observations; this worker did not execute them.

Only the five owned source/test files changed. No sixth implementation/test/helper/probe was inspected or authored. No imports/tests/runtime/guards, git/index/commit/push, subagents, branch/worktree/repository/source copies, artifact deletion/pruning or cleanup were performed. The only executable qualification-like operation was the specifically authorized formatter on the five explicit owned paths. Prose reports are ignored handoff artifacts.

## Complete inventory

Root approved the finite test ceiling increase 650→750 before expansion (`T20-current-test-budget.json`); projections are CB150 / CA950 / CS220 / EP200 / test750 = five files2270, unchanged hard5/5000. Actual total: five files1507 lines.

| Whole file | Actual lines | SHA256 | Ceiling |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` | 66 | `d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268` | 150 |
| `src/townlet/curriculum/adversarial.py` | 480 | `7bca1e8cf60826eaa83525c5425566d15337ecc095756bb1033cb99b8c6a83ad` | 950 |
| `src/townlet/curriculum/static.py` | 64 | `22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59` | 220 |
| `src/townlet/training/episode.py` | 173 | `a719b9993b11051472478a07a1103da132bf3c26ed2d6c157de9b3294b3eeb65` | 200 |
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` | 724 | `68ebad714b68bbb01ca1f5737fc83fd53f7811abc8519b2b6b12b1583a12877b` | 750 |

Formatter command: `.venv/bin/ruff format src/townlet/curriculum/base.py src/townlet/curriculum/adversarial.py src/townlet/curriculum/static.py src/townlet/training/episode.py tests/test_townlet/regressions/bac/test_curriculum_events.py`. First pass reformatted all five files; after subsequent edits, final pass reported `5 files left unchanged`, exit0. This is formatter evidence only. No collection, pass count, mypy/default count or other guard result is claimed.

## Required construction and current interfaces

```python
AdversarialCurriculum(
    *, commit_mode: str, difficulty_mode: str, adaptation_rate: float,
    min_difficulty: float, max_difficulty: float,
    survival_advance_threshold: float, survival_retreat_threshold: float,
    entropy_gate: float, min_steps_at_stage: int, device: torch.device,
)
StaticCurriculum(
    *, commit_mode: str, difficulty_level: float, reward_mode: str,
    active_meters: list[str], depletion_multiplier: float,
)
```

All policy inputs are required. Both constructors accept only commit_mode=`completion`. Adversarial accepts difficulty_mode=`stage_band` or `rate_limited`; rate/bounds/thresholds/entropy are finite and validated, dwell is a nonnegative exact integer, device is explicit. Static keeps its fixed substantive choices and completion ownership; its supplied list is copied, including valid empty rosters. Effective policies are copied into private meaning-bearing config before initialization. There is no optional attribute probing/configure bridge, legacy_step dispatch, reward-as-step tracker, fixed100 normalization, old seven-array checkpoint interpretation, YAML constructor adapter or ignored-Q decision method.

Both strategies expose the current CB contract:

```python
initialize_population(num_agents: int) -> None
prepare_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> PreparedCurriculumOutcomes
commit_prepared_episode_outcomes(prepared: PreparedCurriculumOutcomes) -> None
commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None
get_batch_decisions(agent_states: BatchedAgentState | None, agent_ids: list[str]) -> list[CurriculumDecision]
checkpoint_state() -> dict[str, Any]
validate_checkpoint_state(state: dict[str, Any]) -> None
load_state(state: dict[str, Any]) -> None
```

`get_stage_info(agent_idx: int)` is supported by both; adversarial retains its existing default0, static requires the explicit lane. No new production argument default was added. Stage-info includes current_stage, steps_at_stage, episodes_at_stage and completed fraction/progress/reward/entropy/reason/world readings, plus truthful mode/rate/activity/units and unqualified meter/reward/uncalibrated difficulty status. Get-batch decision state is a read input, never a completion accumulator. Its identity list must exactly cover initialized lanes. Decisions are lane-ordered and do not commit stages. `get_batch_decisions_with_qvalues`, `_calculate_action_entropy`, PerformanceTracker, configure_from_training and from_yaml are removed, not aliased.

Implementation placement differs from the initial proposal only to make ownership clear: `PreparedCurriculumOutcomes` is defined/exported by CB (`townlet.curriculum.base`), not CA. CA defines shared `CompletionCurriculum`, used by the concrete adversarial strategy and CS's concrete static strategy. There is one state/preparation/install implementation, not parallel completion lifecycles. Future consumers import the CB receipt type and EP shared fingerprint definition.

## Immutable envelope definition in EP

Existing EpisodeCompletion/LaneOutcome DTO fields remain current, including explicit world_id/world_episode_seq, real reward components, entropy, horizon and ending reason. Additional exact current helpers:

```python
lane_outcome_from_state(state: dict[str, Any]) -> LaneOutcome
lane_outcome_state(event: LaneOutcome) -> dict[str, Any]
freeze_lane_outcome(event: LaneOutcome) -> FrozenLaneOutcome
lane_outcome_fingerprint(event: LaneOutcome) -> str
```

`FrozenLaneOutcome` is a frozen dataclass with required `payload: bytes`, `fingerprint: str`, and `to_outcome() -> LaneOutcome`. Fingerprint is SHA256 of deterministic canonical JSON containing every envelope/embedded completion scalar and both readings' dtype, exact shape and raw contiguous logical-content bytes encoded as hex. The shared identity/content definition must be consumed by T23/POP; no second guessed hash is authorized. `lane_outcome_state` and decoding produce independent detached CPU tensors.

Explicit reading dtypes: bool, uint8, int8/16/32/64, float16/bfloat16/float32/float64, complex64/128. Native readings must be finite dense strided tensors; envelope fields are exact current DTO keys, positive duration within planned horizon, declared reason and valid scalar/world fields. Raw empty bytes are decoded using an empty typed tensor then reshaped; `frombuffer` is never called with an empty buffer. Zero-width shapes, including (0,), (2,0), (0,3), are retained rather than dropping supported constant policies. Dtype/shape/contents, including a nonempty bfloat16 reading, participate in immutable ownership and fingerprint tests. No old payload decoder, pickle fallback or fabricated ID is present.

## Preparation, generation and retries

CB's frozen `PreparedCurriculumOutcomes` has required `owner_token: object`, `generation: int`, `outcomes: tuple[FrozenLaneOutcome, ...]`. The payload graph contains immutable bytes/scalars/tuples, with no caller tensor/dict/list aliases. The owner token is an in-process capability identity, not world-binding authority or serialized state.

Pure preparation freezes and validates the entire sequence before any effect. It checks initialized lane range, exact owned DTO content, duplicate identities `(batch_episode, agent_idx)` against canonical fingerprints, conflicting duplicates within the same batch, and established per-lane world cursor consistency. New work for an established lane must keep its world_id and strictly increase world_episode_seq and batch_episode; identical already-recorded old content remains retryable. POP/world owners still validate the actual declared binding/reservation/publication; this local check does not invent roster authority.

Commit checks receipt type/owner/nonnegative generation, decodes/revalidates even a manually replaced dataclass, and verifies exact canonical frozen content. A receipt containing only already-installed equal identity/content is a no-op even when its generation is older. Any changed-content reuse refuses; a stale receipt containing new work refuses before installation and must be freshly prepared. Empty sequences are harmless no-ops. Equal duplicates within a batch install once.

For actual new work, commit computes a candidate owned state and telemetry list before mutating live state. Stage/dwell/metric/rate effects and the matching event fingerprints are installed as one state-object replacement, with prepared telemetry. No validation refusal after an earlier lane can leave partial live effects. There is no external callback/await or learning/RNG operation between candidate preparation and installation. This supports equal-content in-process reentry after a sink commits but its caller loses acknowledgement; it does not claim arbitrary process-death rollback. Load/initialize replace the owner token, invalidating every old prepared receipt even if the persisted generation equals its old value.

## Canonical native schema and metric meanings

Exact top-level keys: `version` integer2, `strategy`=`adversarial` or `static`, and `completion`. Exact completion keys: `config`, `generation`, `lanes`, `events`, `metrics`.

- Adversarial config exact keys: commit_mode, difficulty_mode, adaptation_rate, min_difficulty, max_difficulty, survival_advance_threshold, survival_retreat_threshold, entropy_gate, min_steps_at_stage. Static config exact keys: commit_mode, difficulty_level, reward_mode, active_meters, depletion_multiplier. Constructor-normalized config value types/content must agree on load; execution placement device is not serialized as metric meaning.
- Generation is an exact nonnegative integer, zero before any event and between1 and unique-event count afterward; each installation with new work increments it once.
- Lanes is an exact lane-ordered list of `{stage, dwell, episodes_at_stage, difficulty}`. Adversarial stages1–5, static0; counts are nonnegative integers. Difficulty is finite in the configured band/fixed level. Stage-band stored difficulty must agree with its stage mapping. Untouched lanes must equal authored initial state; loaded lanes cannot invent missing completion/counter history. Episode counters cannot exceed their lane's recorded completion count or exceed dwell.
- Events is an ordered list of exact `{identity, fingerprint}` dictionaries. Identity is an exact integer `(batch_episode, agent_idx)` tuple, unique/in range and monotonically increasing per lane; fingerprint is lowercase64-digit SHA256 hex. This is the idempotency/content receipt history, not executable archival data.
- Metrics is lane-ordered null for no event, otherwise exact `{event, previous_fraction}`. Event is the exact current LaneOutcome mapping with embedded exact EpisodeCompletion mapping and owned tensors. Its identity must be the latest lane identity in events and its recomputed fingerprint must match. Previous fraction is finite in [0,1], zero on the first lane completion. Current survival fraction derives only from event duration/horizon; progress derives only as current fraction minus previous_fraction. Report survival_rate and survival_baseline from the same derived fraction. There are no independent survival/baseline/progress tensors or misleading reward arrays.

R1's contradictory baseline/progress representations are removed. Adding obsolete survival_baseline/learning_progress fields to a metric row now refuses as an unknown canonical schema before installation; impossible derived progress is prevented by canonical event/horizon validity and previous-fraction bounds. Native0.8 no longer depends on comparing float32 and Python representations. Snapshot, decode and load own their tensors/nested containers; complete validation precedes live installation. Unknown/obsolete versions, fields/configs, seven-key states and legacy selector values refuse, with no conversion or invented history.

Advance/retreat retain their substantive rules: dwell adds each lane's actual eligible survival transitions once; retreat takes priority on low survival or negative progress after dwell; advancement needs high survival, positive progress, low completed policy entropy and dwell. Commit at most one stage change per unseen event, resetting stage counters on transition. Stage-band preserves its literal mapping and singleton bounds with inactive retained rate. Rate-limited starts at low and moves toward the newly committed stage target by at most rate×eligible transitions, clamped to band. Static records completion clocks/metrics without changing fixed decisions. Existing stage depletion values, meter rosters and reward labels remain intact and truthfully unqualified where appropriate.

Completion transition telemetry carries canonical agent_idx/world_id/world_episode_seq/batch_episode, boundary stages, reason and fraction/progress/entropy/dwell. Nullable old agent_id is removed; no world/row/config surrogate is presented as an agent identity. Published telemetry queue history is not native learning state; consumers drain it at the completion boundary and equal retry does not re-emit it.

## Tests and open gates

All 80 current-only RED scenarios and their substantive fraction/dwell/rate/entropy/reward/identity/refusal/negative values remain. Fixture construction is migrated only after recorded RED to the required current constructors; tracker accesses become public stage-info reads. Heterogeneous stage-band fixtures now reach stages through actual improving completions, not checkpoint stage injection. The independent low-survival/positive-progress retreat witness likewise reaches its stage through real prior completions and retains literal progress0.2/high-entropy/refusal-order assertions. Concrete R1 negative tests keep their corruption cause as obsolete-field refusal; canonical previous-fraction and event/fingerprint corruption controls cover the actual current source of progress.

Added compact dtype×shape frozen ownership witnesses (five dtypes, four empty/nonempty shapes), wrong established world/sequence/batch pure-preflight refusals, and prepared owner invalidation after equal-generation native load. They are authored, not collected/run here. Existing future resume tests explicitly drain already-published pre-save telemetry so comparisons cover newly emitted events. No historical compatibility helper/decoder remains. The direct completed-snapshot reset witness still defers real population/reset integration to T23 rather than claiming unseen runner behavior.

R1P2, mypy and defaults are implementation changes awaiting actual checks. Optional arithmetic/None tracker causes and obsolete defaults are removed; no new production argument defaults, type ignores, exemption/whitelist expansion or ratchet increase were introduced. Root must verify actual guard outcomes and lower the ratchet to measured count where appropriate; prior614>612 and nine errors are not relabeled passing by this report.

Earlier-full trigger remains YES: shared consumed API/config identity/native checkpoint meanings changed. Root owns focused GREEN, fresh full-inventory Astra medium review/repairs, owner maintenance and all standing/full/substantive gates. Existing old caller tests may fail until their named current-only maintenance slices land; preserving removed APIs to make them pass is forbidden by the owner ruling.

Pending integration: T21 explicit options/constructor/factory transport; actual world-binding/cursor producer; T18d/PW05 pure exploration preparation/idempotent effects and epsilon receipt; T22 per-world dynamics; T23 shared fingerprint/publication/bind-begin-reset/all-lane routing/static reporting and canonical transition sinks; T24–T26 exact nested native formats, current restore and completed-boundary saving. POP's old fingerprint implementation, old tracker/Q call sites and parent checkpoint validators were not inspected or edited here and must be updated by their owners against this reviewed contract. No bounded handoff acceptance, dependent integrated acceptance or BAC release is claimed before root evidence/review.

## R3 guard repair — final stationary EP

Root supplied actual R3 observations at tree `d1e0a3f56e9df6be6d470aa505214392e1839f8e` / base `af6b91f7`: 104 collected, 104 PASS, 0 warnings, 16.3021 seconds; custody checks PASS; owned four-module mypy, Ruff and Black each exit0. These are received root observations for the pre-repair tree, not new worker execution or final-tree qualification. Root also reported no-defaults ASG002 at EP148 for the raw/empty decode ternary, actual waived default count601, and six global mypy errors confined to unchanged old factory callers assigned T21. Those global caller obligations remain open.

Under narrowly scoped root clearance, replaced only that tensor decode ternary with explicit `if raw` / `else` branches. Nonempty bytes still use cloned frombuffer; empty bytes still use the exact typed empty tensor and original reshape. No behavior/default/waiver/test change was introduced. Existing twenty dtype×shape witnesses remain the root-owned affected coverage; no mirrored test was added. Root alone owns lowering the ratchet612→601 and rerunning final-tree checks.

Final EP: **176 lines**, SHA256 **`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`**. This supersedes the EP row above; other four file hashes/lines are unchanged, making final actual inventory five files1510 lines within five files2270 projected. Authorized EP-only formatter `.venv/bin/ruff format src/townlet/training/episode.py` reported `1 file left unchanged`, exit0. No runtime/import/test/guard/index/git command was run by this worker. Stationary again for root affected GREEN/static reruns and fresh complete-source Astra review.

## Current-only semantic fix round 1 — stationary after R5 RED

Root supplied actual R5 RED at tree `31debaa1c1306c795c671277b151e0e37f36997b` / base `af6b91f7`:159 collected,10 FAIL,149 PASS,0 ERROR,9.6084 seconds. Nine native impossible-effect loads and the future-generation equal receipt reached intended `DID NOT RAISE`; all149 controls, including every claimed dtype and complex/scalar/noncontiguous/malformed codec witnesses, passed. Root reported custody PASS and closed runtime before authorizing this CA-only semantic repair. These are received observations for R5, not final-tree execution by this worker.

CA now reconciles retained native effects with available history before any load installation:

- For a lane with exactly one completion, run the existing pure lane policy on its authored initial lane and the actual retained canonical event with previous fraction0. Require exact resulting stage/dwell/completion-count/difficulty. This rejects fabricated one-event dwell, unreachable stage and rate movement while preserving native0.8 representation and valid first-event outputs.
- Static episode count must equal its recorded unique lane completion count because static never resets. Both strategies require dwell and stage completion count to be zero together, and positive counters require at least latest-event eligible steps plus one eligible transition for every other counted episode.
- Adversarial stage cannot exceed initial1 plus available transition opportunities (`completion_count - episodes_at_stage`), capped at5. Reset counters require latest completed fraction/progress/entropy to permit a transition into the stored stage. Positive unreset counters at eligible dwell cannot contradict a transition the latest completed signals required. Checks use only retained signals and counts; no old payload duration/entropy/rate path is invented or reconstructed.
- Commit refuses a prepared generation greater than the current generation before the all-installed equal-content shortcut. Actual older equal receipts remain idempotently retryable, and stale receipts containing new work remain refused.

Exact first-event recomputation mutates only a temporary lane dictionary. Native validation still occurs on the owned candidate before installation, with no live state, telemetry, owner-token or RNG effects on refusal. No schema/version change, compatibility bridge, journal, default, ignore/waiver or ratchet change was introduced. EP and CS/CB source are unchanged. The same159 test scenarios/values are retained; regression changes in this stage are formatter-only. Tests-first intent/evidence remain in `T20-current-fix1-test-authoring.md`.

Root approved the test projection900 before the tests-first expansion; current five-file projection2420, hard5/5000. Final exact complete inventory superseding prior rows:

| Whole file | Lines | SHA256 | Ceiling |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` |66|`d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268`|150|
| `src/townlet/curriculum/adversarial.py` |516|`0102d954e7f96d966ae0741dfc0c96385e15604a718c0762b79ceb3e352edcc9`|950|
| `src/townlet/curriculum/static.py` |64|`22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`|220|
| `src/townlet/training/episode.py` |176|`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`|200|
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` |896|`0897c9b93c5421f9bc7defa87f3705bb5d9c1eec73354225135071c071f4aea7`|900|

Actual5/1718. Only four test lines remain below its ceiling; any further test expansion needs a finite ruling before exceeding900. Authorized formatter targeted CA and the owned test only: first output `2 files reformatted`, final output `2 files left unchanged`, both exit0. No tests/imports/runtime/guards/index/git or other source edits occurred. Root must run fresh focused GREEN/guards at this exact candidate, followed by the same Astra fix review and independent adversarial execution. Global factory six-type-error integration remains T21; no obsolete API was restored to hide it. Earlier-full and all pending cross-owner/native-boundary/release obligations remain open. This fix report claims stationarity, not passing qualification.

### R6 expression-only guard repair

Root supplied actual R6 observations:159 PASS in14.2188 seconds; owned mypy/Ruff/Black PASS; runtime subsequently closed. No-defaults reported602 against the tight601 ceiling, with the new ASG001 isolated to CA307's assignment of the boolean retreat OR predicate. Existing counted conditional/default sites were unchanged. These are received pre-repair observations, not final-tree guard evidence.

Under CA-expression-only clearance, rewrote that assignment as `any((low_survival_condition, negative_progress_condition))`. Both elements are already pure boolean comparisons; aggregation preserves the predicate and introduces no fallback/default or rule/whitelist/ratchet change. No other source/test file was edited, no mirrored test added, and no test/import/runtime/guard/index/git command run. Root retains final-tree159 regression/guard reruns, same Astra semantic-fix review and independent adversarial execution; global six unchanged factory caller errors remain T21-owned.

Final CA remains **516 lines**, new SHA256 **`ba79f1e650ac33180088475c7e3b94d92dbff083fdd6410308ef40ccbc4174cf`**, superseding only its prior inventory hash; total remains5/1718. CA-only formatter reported `1 file left unchanged`, exit0. Worker is stationary for root qualification/review.

## Current-only semantic fix round 2 — stationary after causal R8 RED

Read the complete same-reviewer `T20-current-only-independent-review-r7.md`. Root supplied actual R8 tree `03e0eb3dc3364bbb61aa40c2250d0848c5a0d2b3`:174 collected,8 FAIL,166 PASS,0 ERROR,39.6516 seconds wall. All eight newly authored multi-event rate corruptions reached actual call-phase `DID NOT RAISE`; all166 controls, including seven new genuine endpoint/interior/new-stage/singleton/native-future controls, passed. Root verified custody and closed runtime before CA-only production clearance. These are received pre-fix observations, not final-tree execution or qualification.

Only CA production changed in this fix. For rate_limited, native validation now computes target from the **stored new committed stage** and budget from rate×the retained latest event's eligible transitions. Because the predecessor lies in [L,H], the monotone update's reachable interval is `[min(T,L+B), max(T,H-B)]`. Difficulty outside that interval refuses before installation. A one-representable-float-step outward boundary allowance via `math.nextafter` tolerates arithmetic rounding without admitting a material extra rate move; existing configured-band validation still applies. Saturated intervals consequently collapse to the new stage target within that representation tolerance. Immutable rate0 is checked separately: difficulty must equal authored L exactly, including after multiple events. Stage-band inactive-rate behavior and static policy are unaffected.

The new checks use only the known band, immutable rate, latest eligible-step count and new committed stage. No prior payload reconstruction, journal, checkpoint schema/version, compatibility bridge, boolean-OR assignment/default, ignore/waiver/ratchet or test change was introduced. All174 scenarios/values are retained. Refusal still occurs during owned-candidate validation before live state, telemetry or owner-token installation; existing prepared-receipt usability controls remain applicable.

Root-approved ceilings are CB150/CA950/CS220/EP200/test1000, total five files2520, hard5/5000. Final exact inventory superseding earlier rows:

| Whole file | Lines | SHA256 | Ceiling |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` |66|`d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268`|150|
| `src/townlet/curriculum/adversarial.py` |531|`af3180a57d5c2d0e7f55fa1dc4f9e3757941f92f13ec58bbda531c8e7f8a1196`|950|
| `src/townlet/curriculum/static.py` |64|`22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`|220|
| `src/townlet/training/episode.py` |176|`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`|200|
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` |967|`e6d3b7ad72c102175d4ed4cc1541e6fa4edbce6a164012936dc5059d2e194e0e`|1000|

Actual5/1804 lines. CA-only authorized formatter `.venv/bin/ruff format src/townlet/curriculum/adversarial.py` reported `1 file left unchanged`, exit0. No tests/imports/runtime/guards/git/index/copies or other source/test edits were performed. No sixth helper/probe or architecture/caller work was opened. Final-tree GREEN/guards, same Astra semantic review and independent adversarial execution remain root-owned and unrun here. Current factory's six old caller type errors remain T21-owned; existing cross-owner/current-native/earlier-full/substantive release obligations stay open. Worker is stationary; no passing checkpoint, dependent integrated acceptance or release is claimed.

## Fix round 3 — causal native round-trip test, production unchanged

Read the full `T20-current-only-independent-review-r9.md` once it became available; an earlier read found the report not yet present, so initial authoring followed root's exact supplied proof. Root/reviewer report prior owned174 PASS/local four guards PASS601/global six old factory errors, plus independent129 PASS/45 deselected and custody PASS. Those historical passes do not include this newly authored false-refusal witness and do not qualify the next candidate.

Added exactly `test_genuine_seven_event_latest_rate_cancellation_native_roundtrip_and_future` to the same owned regression, retaining all174 existing scenarios/values. Its name includes `latest_rate` so the existing independent adversarial selection includes it. With band[0,.4], rate.01 and dwell1, four genuine improving long completions reach stage5/difficulty.4. Actual events5/6 retreat with1/2 then1/4 survival to difficulties.39/.38. Actual event7 retreats with40/400 survival to stage2 target.1. Current production evaluates `.38 + (.1 - .38)` as `.09999999999999998`, two representable values below.1, while the current one-step lower allowance is `.09999999999999999`. The test loads this genuine untouched native snapshot into an identical fresh manager and requires complete snapshot equality, then commits fresh event8 to both and checks stage3/difficulty approximately.2 and complete future equivalence. Intended RED is the real current-native load refusal; no checkpoint corruption, invented history or missing interface is involved.

Only the owned test changed. Current inventory: CB66 SHA`d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268`; CA531 SHA`af3180a57d5c2d0e7f55fa1dc4f9e3757941f92f13ec58bbda531c8e7f8a1196`; CS64 SHA`22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`; EP176 SHA`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`; test985 SHA`57750efea277a256969851ba8413eb17aa5d8810f02b673d6f02639838807ffd`. Actual five files1822 lines, projections unchanged2520 with test1000/hard5/5000. Fifteen test lines remain. Authorized owned-test formatter reported `1 file reformatted`, exit0; the subsequent function-name selection adjustment changes no formatting layout. No imports/tests/runtime/guards/git/index/copies/new source/helper files or production edits occurred. Root has the source-stationary receipt and owns causal RED before production clearance. No tolerance expansion or repair is implemented at this tests-only stage; bounded proposed next repair is cancellation-free direct target selection on saturation and directional budget movement otherwise, with no schema/compatibility/history change.

### Fix3 production — cancellation-free rate movement, stationary

Root supplied actual causal R10 RED at tree `bdae65bf9d901a445caf5cd91db501a0dca5bf52`:175 collected; targeted genuine seven-event test1 FAIL/174 deselected/0 ERROR in3.4221 seconds wall, raising the exact latest-rate validation ValueError on its own native snapshot. Root verified source/config/artifact/process/index/import/thread/registry custody and closed runtime before CA-only production clearance. This is received pre-fix evidence, not final-tree qualification by this worker.

CA production rate movement now keeps the newly committed stage target directly whenever `abs(target-current) <= budget`. Otherwise it explicitly adds the budget when approaching upward or subtracts it when approaching downward; the existing authored-band clamp remains. This removes saturated `D+(T-D)` cancellation while retaining declared per-eligible-transition rate, zero-rate behavior, singleton bounds, new-stage targets and both difficulty modes. The latest-rate validator/one-step representation allowance is unchanged; no ad-hoc tolerance widening, unavailable-history reconstruction, schema change or prior-candidate compatibility path was introduced. All175 tests and values are untouched.

Final CA **537 lines**, SHA256 **`2194cc4075096670181a50cf1be2158cd68334a07111818ad75382cd73890f4f`**, superseding its prior inventory row. Other four hashes/lines remain as in the fix3 tests-only inventory: CB66 / CS64 / EP176 / test985. Total actual five files1828 lines; same projection2520 and hard5/5000. CA-only formatter `.venv/bin/ruff format src/townlet/curriculum/adversarial.py` reported `1 file left unchanged`, exit0. Source-stationary receipt was sent immediately before this ignored prose append so root can run final checks concurrently with report completion. No runtime/import/test/guard/git/index/copy/new-file or other source/test edit was performed. Final GREEN/guards, same Astra source/fix review and independent adversarial verification remain root-owned and unrun here; six unchanged factory caller type errors and all later integration/release gates remain open. This records bounded implementation stationarity, not passing handoff/release.
