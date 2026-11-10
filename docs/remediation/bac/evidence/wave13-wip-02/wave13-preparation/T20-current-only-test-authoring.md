# T20 current-only tests-first handoff

Stationary: tests authored only. All four production files still have R1 hashes. No tests, imports, runtime commands, formatter, index/commit/push, subagents, branches/worktrees/copies, cleanup or artifact deletion were performed. Root must observe meaningful RED before authorizing production edits. No execution result is claimed here.

Read the updated task brief first, approved no-compat amendment, Astra R2 approval, R1 source review, and the owned regression. Earlier allowed implementation reads remain within the same four files; no sixth implementation/test/helper/probe was inspected. Authority is the explicit owner current-only ruling and amendment SHA256 `2a33daacf77c0e8823917a6e27cf3b3a1eb2bbd5a05e071a06010ada9405410d`.

## Inventory

| Whole file | Actual lines | SHA256 | Projection |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` | 92 | `2605ebcbb413e3db990081fa481a1517a647bfb276dc2898e3a17526c5411c92` | 150 |
| `src/townlet/curriculum/adversarial.py` | 803 | `086439b0d3e20e4e543bd24493f69c3eeaa99bc52005ddceef013a249a46eb59` | 950 |
| `src/townlet/curriculum/static.py` | 149 | `128faa2cc1732cd841817a9d1471c6014960012e34eb74d28a22d22ef51942a6` | 220 |
| `src/townlet/training/episode.py` | 66 | `5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9` | 200 |
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` | 613 | `b7e7b771deaa96c85c4f937c73383f376f6f94e9417c269cc0600a3faf2e5d06` | 650 |

Actual 5/1723; projection 5/2170, hard 5/5000. The test has 37 lines of remaining headroom before any future formatting; stop/reslice if readable final formatting needs more. No expansion is requested now.

## Exact proposed current API for T21/T23

Replace the legacy constructor/configure probing route after RED with one explicit adversarial initialization:

```python
AdversarialCurriculum(
    *, commit_mode: str, difficulty_mode: str, adaptation_rate: float,
    min_difficulty: float, max_difficulty: float,
    survival_advance_threshold: float, survival_retreat_threshold: float,
    entropy_gate: float, min_steps_at_stage: int, device: torch.device,
)
```

All arguments required; commit_mode accepts only `completion`, the two difficulty modes remain supported. No global max_steps_per_episode denominator: each outcome supplies its horizon. T21 passes its resolved explicit options and threshold/band/rate fields, rather than passing an unrelated DTO and probing optional attributes. Freeze these meanings before `initialize_population(num_agents: int) -> None`. Remove `configure_from_training`, obsolete tracker construction/attributes/hooks, legacy_step, and decision-time mutation rather than retaining old dispatch.

Keep current decision entry points `get_batch_decisions(agent_states, agent_ids)` and `get_batch_decisions_with_qvalues(agent_states, agent_ids, q_values)` as reads; their supplied state/Q-values do not override committed completion entropy. Static retains explicit fixed difficulty/reward/meter/depletion choices, adds required keyword `commit_mode: str` accepting only completion, and supports reporting without an old tracker. No current feature family is removed.

Both strategies implement:

```python
prepare_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> PreparedCurriculumOutcomes
commit_prepared_episode_outcomes(prepared: PreparedCurriculumOutcomes) -> None
commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None  # prepare + commit
checkpoint_state() -> dict[str, Any]
validate_checkpoint_state(state: dict[str, Any]) -> None
load_state(state: dict[str, Any]) -> None
get_stage_info(agent_idx: int = 0) -> dict[str, Any]  # retain existing default only
```

`PreparedCurriculumOutcomes` is a frozen dataclass in CA with required fields `owner_token: object`, `generation: int`, and `outcomes: tuple[FrozenLaneOutcome, ...]`. No tensor/dict/list aliases are exposed through its owned event payloads. Its owner token is an in-process identity, not serialized world authority. EP supplies frozen `FrozenLaneOutcome` containing canonical immutable `payload: bytes` and `fingerprint: str`, plus shared `freeze_lane_outcome(event: LaneOutcome) -> FrozenLaneOutcome` and `lane_outcome_fingerprint(event: LaneOutcome) -> str`. The complete envelope, embedded completion, tensor dtype/shape/raw contents participate in the fingerprint. Proposed payload encoding is deterministic canonical JSON metadata plus tensor dtype/shape/raw-byte hex; it is current encoding, not pickle or an old decoder. T23/POP consumes this shared definition after reviewed implementation, not a separately guessed fingerprint.

Preparation checks the whole batch, current configuration/generation, event identities and equal/changed duplicate contents without changing state, events or RNG. It owns immutable event readings before returning. Commit refuses a foreign owner or stale generation before mutation. An identical already-applied receipt remains retryable despite its old generation if every contained identity/fingerprint already matches installed effects; changed-content retry refuses. A stale receipt containing new work must be freshly prepared. Repeated identical entries within one prepared batch produce one effect; conflicting entries refuse the entire batch. Compute next owned state and telemetry first and install them with event receipts and the incremented generation together; do not rely on partial live mutation/rollback. This is an in-process retry contract, not arbitrary process-death recovery.

## Exact proposed native state

Top-level exact keys: `version`, `strategy`, `completion`. Version is integer 2. Strategy is `adversarial` or `static`. Completion exact keys: `config`, `generation`, `lanes`, `events`, `metrics`.

- `config` is the exact meaning-bearing current configuration. Adversarial keys: `commit_mode`, `difficulty_mode`, `adaptation_rate`, `min_difficulty`, `max_difficulty`, `survival_advance_threshold`, `survival_retreat_threshold`, `entropy_gate`, `min_steps_at_stage`. Static keys: `commit_mode`, `difficulty_level`, `reward_mode`, `active_meters`, `depletion_multiplier`. Device is execution placement, not metric meaning.
- `generation` is a nonnegative integer, advanced by each atomic preparation installation with new events. Load invalidates existing in-process receipts even when restoring an equal generation, by replacing its owner token.
- `lanes` is an exact lane-ordered list of dictionaries with keys `stage`, `dwell`, `episodes_at_stage`, `difficulty`. Adversarial stages are 1–5; static reports stage 0. Counters are nonnegative integers; difficulty is finite within the selected band/fixed level. Static never adapts.
- `events` is an ordered list of exact dictionaries `identity` (integer `(batch_episode, agent_idx)` pair) and `fingerprint` (canonical SHA256 hex). Identities are unique and in range; retries compare full-envelope content. No historical seven-key tensor interpretation is accepted.
- `metrics` is lane-ordered: null for no completion, otherwise exact keys `event`, `previous_fraction`. `event` is the owned current LaneOutcome mapping with exactly its declared dataclass fields, including an embedded exact EpisodeCompletion mapping and owned tensor readings. `previous_fraction` is finite in [0,1], initially zero. Derive current fraction from `event.outcome.survival_time / event.planned_horizon`, and progress by subtracting previous_fraction. Reward components, entropy, ending reason and world identity come from that canonical event. Validate its identity/fingerprint against `events`. No independent stored survival tensor, baseline tensor, learning-progress field or reward-as-step accumulator exists. Report `survival_rate` and `survival_baseline` from the same derived fraction.

Validate exact schemas/types, stage/counter/rate bounds, fingerprints/metric-event linkage, and config agreement before any installation. Snapshots/load own tensors and nested containers. Unknown versions/keys, obsolete redundant metric fields and old formats refuse loudly. There is no automatic upgrade or missing-history default. Reporting adds lane stage/dwell/completion counts so tests and T23 no longer read tracker internals. Completion transition telemetry uses canonical agent_idx/world_id/world_episode_seq/batch_episode only; remove nullable old agent_id slot.

## RED organization and scenario disposition

The fixture intentionally remains on the reachable R1 constructor/configure API for this first RED packet. Migrating it before RED would conceal the actual review defect. After root captures RED and clears implementation, migrate this fixture to the required current constructor and tracker assertions to supported stage-info fields in the same owned file. There will be no retained compatibility constructor/helper/branch.

`test_checkpoint_contradiction_or_impossible_progress_refuses_atomically` is the concrete R1 witness: from a real stage-2 full-survival native snapshot, alter only existing `completion.metrics[0].survival_baseline` to zero or `learning_progress` to 2/-2/1e300, expect ValueError and complete unchanged state. These tests reach the actual restore assertion in R1; no missing new API is involved. Under the new schema those fields are obsolete redundant content and must refuse as unknown, while canonical previous-fraction range and fingerprint-linkage tests protect the actual new source of progress. No redundant representation is introduced to keep an obsolete test shape.

Existing 22 parametrized scenarios are reconciled: the legacy-positive step case is replaced by `test_obsolete_commit_mode_is_refused`. The old completion-step no-op case becomes repeated decision-read purity; obsolete tracker hooks are to be removed, not kept as no-ops. The reset witness removes direct mutation of obsolete reward-as-step accumulator fields and continues to require retained 10/10 completion after next-decision reads. Actual population reset integration remains T23-owned; this direct consumer test does not claim that integration. Other fraction/dwell/rate/entropy/retreat/reward/cap/lane cases retain their substantive literal expectations and are to migrate public access only after RED.

New test groups, all in this file:

- Concrete R1 contradiction/impossible-progress atomic refusal; valid .8 restore and equal-fraction future stage preservation.
- Malformed later lane/zero/excess/reason full-batch atomic refusal; snapshots include native state, all lane info, decisions, transition telemetry and global CPU torch RNG.
- Changed duplicates for all reward components/total, entropy, world ID/sequence, horizon, duration, reason, both final readings, and observation dtype/shape. Equal-content separate instances/deepcopies are idempotent.
- Pure prepare, immutable receipt, once-only prepared retry, later invalid lane preflight, owned content despite caller tensor mutation, stale generation, foreign owner and conflicting same-batch duplicates. Missing API failures are explicit assertions, separate from R1 restore failures.
- Exact current schema and absence of tracker protocol; top-level version/missing/unknown/strategy/obsolete refusals; nested config/missing/unknown/stage bounds/negative counters/bad rate/duplicate or invalid identities/missing metrics/invalid previous fraction/event-content or fingerprint mismatch/negative generation atomic refusal. Current-schema helpers assert the expected new schema first, with no fallback or old decoder.
- Rate-limited future resume equivalence across retreat/advance/equal-fraction movement, duplicate replay without movement, saved and installed nested-container/tensor isolation. Future-equivalence tests explicitly drain source transition telemetry before saving, so the comparison covers newly emitted future events rather than requiring checkpoint persistence of an already-published historical queue.
- Canonical transition identity with no legacy alias; static pure preparation, unchanged decisions and equal-vs-changed retry semantics.

Case counts have not been collected or executed. Root must distinguish assertion-based R1 corruption RED, new schema/interface assertions, existing passes, and any unexpected collection/call error rather than treating all failures as equal evidence.

## Open obligations and concerns

R1 P2 is not fixed by test authoring; nine mypy errors and defaults614>612 remain open until implementation and root evidence. Removing optional arithmetic/tracker fields and obsolete defaults should repair causes, never ratchets/waivers/ignores. The proposed exact current schema replaces historical interpretation; old artifacts remain preserved as evidence.

The accepted amendment requires broader current-caller maintenance, T21 resolved option/factory transport, real world binding ownership, exploration preflight/idempotent sinks, T23 POP/runner routing/static reporting, completion telemetry sink updates, and T24–T26 nested checkpoint/boundary agreement. None is delivered by these unit-level consumer tests. Earlier full default pytest and every standing guard remain mandatory at the coherent candidate; historical R1 results do not qualify the new protocols.

EP's 200-line projection and regression's 650-line projection are tight for canonical immutable encoding and readable negative tests. A concrete finite reslice must precede any ceiling breach. No new helper file or functional reduction is proposed. Worker remains stationary for root RED and API/schema review.
