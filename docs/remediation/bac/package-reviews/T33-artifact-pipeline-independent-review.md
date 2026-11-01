# Artifact-pipeline maintenance r11 — independent static review

**Scoped PASS: no P1/P2 finding in the artifact-pipeline test maintenance delta.** The actual fixed source implements the observer and complete-family clone design without weakening the existing ordinary-drain, payload, consumer or corruption assertions. This is a static source/spec review, not a runtime result, consumer implementation qualification, whole-BAC review or release approval.

## Frozen receipt and scope

Workspace: `/workspace/hamlet` only. HEAD: `214408b107730b4511b8a690541569aeca4b7b67`. Candidate manifest: `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave04-preparation/generation-green-r11-candidate.json`. Candidate/index tree: `eada2071e845a03f1bf4e34c7e9b3cfc21c505d6`.

`git diff --exit-code` returned 0, establishing no tracked working-tree/index difference. `git diff --cached --exit-code eada2071e845a03f1bf4e34c7e9b3cfc21c505d6` returned 0, establishing exact whole-index equality with the frozen candidate tree. HEAD was checked before and after the review. All five working source SHA256 values below were read and verified; all manifest-covered values match. The unchanged sinks file is absent from the manifest's source list and is identified by its own working hash and frozen-index blob below.

| Complete authorized source | Lines | SHA256 | Frozen index blob |
|---|---:|---|---|
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` | `d6d3f7985e74a6e63334fffd23e48fdac62a5b3c` |
| `src/townlet/recording/recorder.py` | 699 | `8fca0b033bdc74f9e8146006c029b8bce6228b067f89b72109e1a886f4a32825` | `53a226b846bce9c4472ac12371ebce5a5a96b38c` |
| `src/townlet/demo/database.py` | 1178 | `7335e9798d15e14721e5278cb4e7402eea7f7da2344187c56f8bc8e42b93902e` | `0e8050842972774d2b169d748a7e10ff17417955` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 297 | `7e4aa29416b3fcfd01470ba143d3eec43172d66cff9aa4120ef6e28b245dcd8a` | `0441f417ce521e7822c210552f610a112c9d8481` |
| `tests/test_townlet/regressions/test_episode_recording_shutdown.py` | 184 | `9874eed75d1b7491a5a8ef5fca1af7430b61aaff52037b8948b84e2636b67fa2` | `b6d82ac29e1df1ec6c1971b6e89b1d118d9986fc` |

Exactly five complete source paths, 2782 unique current source lines. No sixth source/helper/probe was inspected. Read the repository `AGENTS.md`, the manifest and the three authorized ignored prose documents: `artifact-pipeline-observer-causal-diagnosis.md`, `artifact-pipeline-family-interface-capsule.md`, and `artifact-pipeline-maintenance-r11.md`. The session's explicit preservation requirement governs over AGENTS' blanket pre-release compatibility deletion rule. No durable user-only policy was created or assumed.

Read the staged artifact/shutdown diffs against HEAD and the artifact diff from prior frozen tree `973ba6470ae481c0d14050c19f1022614a1b5bcd` to r11. That prior-tree comparison has only two changed path names: artifact pipeline and `tests/test_townlet/integration/test_reward_component_flow.py`; the latter's contents were not read and are not reviewed here. Production recorder/database content has no r10-to-r11 change. Existing broader HEAD-to-candidate production changes are context for this bounded maintenance review, not independently qualified in their entirety by this report.

## Findings and interface reasoning

### Observer normalization preserves the real transport

Pipeline100–126 explicitly handles `_Capture.frame`, `_Boundary.marker`, bare `RecordedStep`, and bare `EpisodeEndMarker`, returning `None` for other objects. These match recorder97–109,342,367 and writer435–473. Both hooks call the actual original queue operation first. They append the original contained DTO references, and `_get` returns the original outer item unchanged. No DTO reconstruction, deepcopy, fabricated accepted work, altered admission or writer substitution is introduced. The hooks run within the queue methods' existing mutex; ordering therefore remains tied to actual insertion/removal.

The existing ordered `[id(item) ...]` equality remains at pipeline173, followed by the nonvacuous four-frame/two-boundary counts175–176. Per-boundary metadata and frame comparison222–232 still joins those observed objects to the real unpacked files. The safe outstanding-item serializer109–113 handles the recorder's non-dataclass stop sentinel without replacing or relaxing the empty-queue assertion172. The separate maintained shutdown observer40–66 uses the same explicit transport normalization; its existing assertions are retained.

### Family copying uses the closed-owner contract

Sinks118–128 builds `run_dir/demo.db` and `run_dir/checkpoints`, runs the ordinary real runner context and returns after context exit. Pipeline134–178 requires the actual writer stopped, queue and episode buffer empty, two recordings/two payloads, two completed episodes and fourteen observed eligible transitions. The raw SQLite inspection is closed at138–141 before later source-family ownership.

Pipeline371–377 opens and closes the original associated DB owner before calling `checkpoint_owned_families()`. DB1135–1169 closes/checkpoints both connections and propagates close failures. DB809–821 refuses an open/failed/incomplete owner, independently revalidates the stopped main and associated index and returns the owned paths; schema/index admission refuses any WAL/SHM/journal companions at DB327–385,87–129. Requiring two returned mains matches this indexed-recording fixture. Copying each to `root / family_path.name` preserves the canonical basename and reserved association's companion basename. The copied DB path is derived from the same original name.

The copy code neither edits the reserved binding/family identity nor regenerates an empty index, changes immutable locators/digests, or copies a live WAL family. Keeping original absolute immutable-history paths is consistent with DB132–169's admission checks, which validate row structure/metadata without opening artifact locators. Public canonical lookup remains DB733–751; the corrupt target continues to use the stored canonical relative alias under the clone's checkpoint root. Recorder187,593,605 establishes that relative alias separately from its immutable generation locator. This is coherent stopped fixture custody, not a concurrent/online backup guarantee.

### Clone control and semantic binding reach the intended oracle

Before mutation, pipeline378–382 writes the intact alias to the cloned checkpoint location and requires `load_episode(0)` plus original steps through that copied DB and checkpoint root. That owner exits before target corruption383–411 and the second owner412. An initial family/path admission exception therefore cannot count as a successful corruption refusal.

All eight corruption names and mutation bodies359–410 remain. Structural branches still require failed loading and empty replay state421–422. The two semantic controls still require successful loading and an independent eligibility/reward-ledger assertion failure415–419; the new `replay.steps == data['steps']`417 binds that success to the changed payload. An implementation that silently chooses unrelated intact immutable history can no longer satisfy the semantic control just because the on-disk copied alias is malformed. No canonical SQL or companion evidence is rewritten to manufacture success.

## Preserved evidence and assertions

- Ordinary public cleanup, actual accepted/dequeued object identity, four frames/two ends, stopped writer, empty queue/buffer, two real files/index rows and fourteen actual eligible transitions remain at134–178. No sleeps, polls, extra joins, manual finish or synthetic payload replacement was added.
- Independent active-lane ledger193–214 retains native version, completion reason, eligible frame count/order, action use, done, meters, effective reward components, metadata sums and terminal zero-reward checks. File/queued DTO equality, SQL survival2/batch5/live7, metadata/sizes, and real per-agent TensorBoard scalars remain217–256.
- ReplayManager load/steps/seek/back/reset/reload and LiveInferenceServer startup, real replay handlers/messages, reward/position/meters/metadata/reset/shutdown remain259–335. Optional Q-values/time/progress assertions remain conditional on actual payload fields322–326.
- Both real exporters, exact transition metadata7/14, curve equality and realized-live metadata remain338–356. All eight corruption cases, clean original-ledger check367, original compressed-artifact SHA256 equality423 and corruption outcome JSON424 remain.
- Actual revision and six resolved class source paths/SHA256 values85–98, config digests165–167, ticks, ordinary accepted/dequeued/outstanding/buffer/liveness/files/SQL evidence154–170 and final status/error/outcome persistence181–190 remain. The six source-byte identity reads are test behavior read as source here; this reviewer did not execute those reads or inspect the corresponding extra implementations.

## Limits and remaining qualification

No static P1/P2 repair is requested for this maintenance delta. There is no newly identified scoped assertion gap requiring a source change.

This reviewer ran no project imports, runtime, pytest, lint, probes or helpers. Maintainer-reported static Black/Ruff results are read as prose evidence, not rerun or promoted to runtime proof. Root owns all execution and repairs. A complete focused module and ordinary observer controls must still establish actual consumer routing and lifecycle behavior on the frozen candidate; static source compatibility alone does not establish a passing test result.

DTO validator, ReplayManager, LiveInferenceServer, DemoRunner, RT/exporter implementations and authored fixture helpers were not opened. Exact structural payload acceptance, consumer file selection, live server ownership/cleanup, optional-field branch execution and exporter implementation correctness remain outside this source receipt. Existing prose runtime DATA was not re-executed or independently qualified. No whole-BAC or release claim follows.

No source/test/index edits, staging, commits, branches/worktrees, source checkouts/copies/deletions or subdelegation were performed. The only write by this reviewer is this ignored prose report. The frozen HEAD/index/working-tree checks remained unchanged immediately before writing it.
