# T33 additive legacy recording generations — proposal

Status: design/implementation supplement for independent technical review. This is not an approval, production dispatch, release, or completed qualification. The coordinator selected additive preservation; no removal decision or waiver is requested. Only this prose file is written by this planner. No implementation/test/helper/probe source was inspected, imported, executed, or edited; no index, branch, worktree, checkout, source copy, or delegation was made.

References: approved plan P8/T33 and downstream contracts; wave04 `INTERFACE-CLARIFICATION.md`, `PRESERVATION-SUPPLEMENT.md`, `T33-fixed-independent-review-r2.md`; coordinator's independent baseline review and current interface declaration. The coordinator established that the original public constructor could publish the same finished episode repeatedly: canonical file bytes were overwritten and canonical SQL used `INSERT OR REPLACE`. It also established the original logged/no-throw legacy capacity behavior below; integration tests exposing its replacement by exceptions identify a real preservation regression, not stale expectations. This proposal supersedes only the earlier companion-v1 shape, unique-triple rule for legacy publications, canonical strict-INSERT choice, and candidate's raising behavior for the two established legacy queue-full cases. Canonical metric DB v1 and its admission remain unchanged. The user's preservation instruction takes precedence over AGENTS' blanket deletion guidance.

## Preserved behavior and selected approach

Keep `EpisodeRecorder(config, output_dir, database, curriculum)` callable unchanged, including `database=None`. Repeated selected completions of episode7 in one recorder before shutdown, or in separate recorder instances, continue to update `output_dir/episode_000007.msgpack.lz4` and the original canonical SQL recording lookup. The canonical SQL `file_path` remains the canonical alias path relative to `output_dir.parent`, regardless of database location. Existing compression configuration and filename selection remain; the example is the existing LZ4 case.

Add a unique immutable generation artifact for every selected publication. Receipts and the new companion index point to that artifact, never the mutable canonical alias. Keep old canonical reads as the latest view; keep the companion as immutable history. The alias contains a separately created copy of the exact published bytes: do not hard-link or symlink it to immutable history, because an ordinary subsequent write through the alias must not mutate an earlier receipt's artifact. Native recording payload format2 stays exactly metadata/steps/affordances; generation is storage/index identity, not a payload-schema change.

Alternatives considered: retaining one no-overwrite canonical file loses existing repeat publication; overwriting the receipt's sole file invalidates earlier receipts; inventing a new run ID for each repeat loses stable legacy scope and still needs a canonical latest view. Immutable history plus the mutable latest view preserves both requirements with one bounded T33 change. No automatic history deletion, retention limit, or garbage collector is introduced.

## Identity and concrete interfaces

`LEGACY_RECORDING_RUN = 'townlet:legacy-recording:v1'` stays exact. Only that exact value is reserved from `for_scope`; otherwise retain exact nonempty run-ID and nonnegative-lane admission, including strings sharing a prefix with the reserved value. The old constructor uses this run ID and lane0. Qualified `EpisodeRecorder.for_scope(config, output_dir, database, curriculum, *, run_id, lane)` retains exact-run/lane namespaces and collision refusal. A scoped row has generation0; an indexed legacy publication has a positive integer generation. A failed attempt need not consume a committed generation number: a fresh artifact nonce prevents a retry from reusing any orphan's filename.

Keep public admission/return contracts: `record_step(...) -> None`; `begin_episode(episode)`; `record_bound_step(...) -> RecordingTicket`; `finish_episode(metadata) -> RecordingTicket | None`; `shutdown() -> tuple[RecordingReceipt, ...]` or `RecordingDrainError`. The finish union explicitly includes legacy capacity rejection; a successful legacy finish returns its actual added ticket, and qualified finish returns a ticket or raises. Preserve existing arguments to the first four methods. Every admitted completion/bound-ticket group owns its own outcome and at most one selected publication; receipt bookkeeping uses actual ticket sequence identity and must not overwrite a prior group merely because episode/lane repeats. Unbound old frames remain provisional until their actual completion. Any currently admitted bound route obeys the same generation rule. Repeated shutdown reuses the same immutable outcome without new generations, alias replacements, or SQL writes.

Keep the current immutable receipt shape exactly:

`RecordingTicket(sequence: int, episode: int, lane: int)`.

`RecordingReceipt(ticket: RecordingTicket, status: Literal['persisted','not_selected','failed'], path: Path | None, index_id: int | None, error: Exception | None, storage_mode: Literal['file_only','indexed'])`.

On indexed success, `path` is the absolute immutable artifact locator and `index_id` identifies its own committed history row. The pair suffices without a new receipt generation field. File-only success has that same immutable-path guarantee and `index_id=None`; no SQL generation is required. Storage mode is selected at construction; a supplied database error never becomes file-only success. Not-selected work performs no artifact/alias/index publication and retains the existing diagnostic.

## Legacy capacity behavior and honest admission

Under the same admission lock/fence, preserve these exact old-constructor behaviors in indexed and file-only modes. If `record_step`'s actual enqueue raises `queue.Full`, log the existing warning, drop that unadmitted frame, increment the read-only cumulative `legacy_dropped_frames: int`, and return `None` without raising. Do not advance sequence, open-frame/accepted-frame counts, accepted-ticket identity, or queue ownership. If legacy `finish_episode`'s actual enqueue raises `queue.Full`, log the existing error, increment read-only cumulative `legacy_rejected_finishes: int`, and return `None`: no boundary, ticket, sequence advancement, episode reset, or accepted-work increment. Both counters start at0, are updated/read under admission locking, and never reset on successful finish or shutdown; they are observability, not new configuration/defaults.

All admissions from `for_scope`, and `record_bound_step` regardless of constructor, stay strict: actual queue-full rejection raises `queue.Full`, issues no ticket, and leaves sequence/open-frame/accepted-set state unchanged. These strict paths do not increment the two legacy-only counters. Existing finite-validation, writer-error and closed-fence failures still raise on every route; catch only the established legacy enqueue `queue.Full`, not arbitrary errors or failed checks.

Maintain a separate per-publication dropped-frame ledger in REC. A rejected legacy finish leaves that ledger and accepted frames attached to the still-open provisional/bound group; a successful boundary admission snapshots the ledger for its actual group before advancing to another group. Do not infer that a cumulative counter is permission to omit frames, reset a ledger on rejected finish, or manufacture a receipt for an unadmitted operation. Before any publication, reconcile actual accepted frames, attempted/dropped counts and supplied completion metadata. A group with known missing dropped frames, inconsistent ledger/metadata, or accepted frames without a valid end resolves to explicit failed/incomplete drain, including the actual accepted tickets/unbound identities. No successful partial artifact or fabricated complete end is permitted. A boundary rejected for capacity may be explicitly retried after capacity returns; absent a valid accepted retry, shutdown must expose the incomplete group. This preserves the no-throw call behavior while retaining C13 durability requirements.

## DB producer/consumer interfaces

DB additions/changed keywords, all in the existing DB source:

```text
DemoDatabase.recording_publication(
    *, run_id: str, episode_id: int, lane: int, legacy: bool
) -> ContextManager[int]

DemoDatabase.insert_scoped_recording(
    *, run_id, lane, sequence, generation, file_path, legacy_file_path,
    file_sha256, frame_count, final_done, metadata, legacy, reason,
    file_size, compressed_size
) -> int

DemoDatabase.get_scoped_recording(
    *, run_id: str, episode_id: int, lane: int
) -> dict[str, object] | None

DemoDatabase.list_scoped_recordings(
    *, run_id: str, lane: int
) -> list[dict[str, object]]

DemoDatabase.get_scoped_recording_by_index(
    *, index_id: int
) -> dict[str, object] | None
```

The insert signature preserves all current keyword names and adds required `generation: int` and `legacy_file_path: str | None`. `metadata` and the existing keywords keep their current data types/contracts. `file_path: str` is always the absolute immutable artifact path, equal to `str(receipt.path)`. `legacy_file_path` is the explicit canonical relative locator for legacy insertion and explicit `None` for scoped insertion; there is no inferred path base or hidden default. `generation` comes from the enclosing owned publication context:0 for scoped, otherwise `1 + MAX(committed legacy generation)` for that exact run/episode/lane, starting at1. Generation allocation is serialized through completion of publication/readback. Holes and unindexed failed attempts are allowed; publication never relies on generation alone for filename uniqueness. Strict INSERT/unique-key refusal protects history, and the returned integer is that inserted row's immutable index ID.

The context acquires DB's owned reentrant guard, validates/ensures its owned v2 association, yields the generation, and keeps the guard through artifact publication, legacy alias replacement, both SQL commits, and readbacks. Reentrant insert/read calls and close/checkpoint use this same guard. A generation context is not released and reacquired between allocation and insertion. Insert validates the supplied identity/generation; scoped generation0 cannot be made into a repeat by passing a positive number. Direct users of insert retain responsibility for their supplied file/alias; the recorder's complete publication guarantee requires the enclosing context.

`get_scoped_recording` remains an exact-run/episode/lane lookup for qualified scopes. For the reserved legacy run/lane0 it explicitly returns the highest committed positive generation; it is a latest-history lookup, not a promise that partial failures left the canonical alias/row synchronized. `list_scoped_recordings` returns all matching generations in `(episode_id ASC, generation ASC, index_id ASC)` order. `get_scoped_recording_by_index` retrieves any earlier receipt's exact row. Reads do not create an index or reinterpret another run's row as an unscoped match. Existing canonical getter/list/insert signatures and latest-row meanings remain unchanged, including canonical `INSERT OR REPLACE` behavior.

## Closed companion schema2 and ownership

Do not call a changed shape version1. The earlier companion-v1 proposal is unlanded and unqualified; the source baseline has no recording companion. Create a new closed schema with `PRAGMA user_version=2` and exactly these two user tables, pinned full DDL and corresponding implicit UNIQUE indexes:

```sql
CREATE TABLE recording_index_meta (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    schema_version INTEGER NOT NULL CHECK(schema_version=2),
    family_id TEXT NOT NULL UNIQUE,
    metric_name TEXT NOT NULL
);
CREATE TABLE recordings (
    index_id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    episode_id INTEGER NOT NULL,
    lane INTEGER NOT NULL CHECK(lane>=0),
    sequence INTEGER NOT NULL,
    generation INTEGER NOT NULL CHECK(generation>=0),
    file_path TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    frame_count INTEGER NOT NULL,
    completion_reason TEXT NOT NULL,
    total_reward REAL NOT NULL,
    extrinsic_reward REAL NOT NULL,
    intrinsic_reward REAL NOT NULL,
    shaping_reward REAL NOT NULL,
    final_done INTEGER NOT NULL CHECK(final_done IN(0,1)),
    metadata_json TEXT NOT NULL,
    CHECK((run_id='townlet:legacy-recording:v1' AND lane=0 AND generation>0)
       OR (run_id<>'townlet:legacy-recording:v1' AND generation=0)),
    UNIQUE(run_id,episode_id,lane,generation)
);
```

History rows/index IDs are never replaced, updated, renumbered, or deleted by an owned API. Validate exact columns/order/types/nullability/PKs/checks/unique indexes, version, table inventory and internal SQLite-entry treatment before mutation, using the existing strict-family approach. No trigger, view, or unexpected table is admitted in this companion. Existing producer metadata/reward/frame/ending validation stays binding.

Retain the default companion basename `db_path.name + '.recordings.sqlite3'` and explicit association/owner lifecycle. Use a distinct tagged reserved binding `townlet.recording-index:v2` in canonical `system_state`, with the reviewed safe relative basename, family_id and metric_name provenance rules. Both index schema fields are2; canonical metric `PRAGMA user_version` remains1. Preserve and refuse any present earlier v1 binding/index or conflicting/unknown reserved association without mutation. Never relabel, adopt, migrate, delete, overwrite, or regenerate earlier evidence files in place, including unassociated v1 files. If that evidence occupies the requested/default target, stop before creation and report the exact existing family; relocating/removing it is a separate custody action, not an implicit part of T33. Fresh ordinary baseline databases remain eligible for additive v2 creation.

Both stopped SQLite families must pass existing exclusive-owner/companion-free preflight before either opens/mutates. No CREATE-IF-NOT-EXISTS adoption or weaker canonical classifier. Admission does not open historical artifact paths. Creation/association directory sync is sticky until fsync and descriptor close both succeed. Reconcile the full committed reserved binding after its commit before clearing association-pending state or permitting publication: suppression/mutation by an admitted canonical trigger is failure. Keep `owned_family_paths`, close-both/error custody, and `checkpoint_owned_families()` behavior, coherent two-family relocation, unrelated canonical values/rows, and ordinary no-index-creation reads. A missing associated family is never silently reconstructed.

## Publication, serialization, and failure custody

Use a fresh nonce-bearing path under the configured output root, for example `.recording-generations/<exclusive-publication-nonce>/episode_000007.msgpack.lz4`. Nonce directory creation is exclusive, with collision retry; no successful or failed attempt reuses an existing artifact path. Scoped paths keep their current safely encoded run/lane namespace and generation0/no-overwrite rule, separate from the legacy canonical alias. Do not add generation directories to the native payload or silently change format/compression.

For indexed legacy publication, acquire the legacy output-root publication lock before the owned DB context; consistently keep this lock order. The output-root lock must coordinate separate recorder instances using that root, including file-only/indexed combinations and distinct database owners. Recommend an owned reentrant in-process wrapper plus a persistent per-root `.townlet-legacy-recording.lock` OS advisory-lock file, implemented in REC using the project's supported host locking facility; never unlink/recreate the lock inode during ordinary release. Acquisition errors fail explicitly, with no unlocked fallback. This supplies process coordination without a new source module; platform qualification belongs to the existing owner tests. Scoped publications need only their exact-scope no-overwrite/index protection. DB's RLock separately prevents canonical/companion operations on the supplied owner from interleaving; owned legacy lookups and close cannot observe an intermediate publication as a successful completed operation. A later successful file-only publication or publication to a different supplied DB may replace the shared alias without updating this DB: each DB's canonical latest row describes its own publications, and this is not a multi-database synchronization promise. Exposed raw SQLite connections/external artifact mutation retain existing caller custody.

Within those guards:

1. Allocate/validate the DB generation if indexed. A failure here may occur before any artifact is published; report that honest absence. File-only uses no DB/context/generation.
2. Serialize the unchanged format2 payload once. Stage in the destination filesystem, flush/fsync, publish the immutable artifact without overwrite, and immediately retain its actual path in receipt/error custody. Sync every newly created directory and its containing directory, including creation of the output root itself, plus the final artifact parent; close failures are failures. Read back exact compressed bytes/hash and independently validate expected payload/frame/reward/ending agreement.
3. For legacy, create a separate same-directory canonical-alias temporary file from the same bytes, flush/fsync it, atomically replace the canonical filename, fsync the output directory, and read back its exact bytes. Never truncate the previous alias in place. For scoped publication there is no legacy alias or canonical legacy SQL write.
4. For indexed legacy, preserve canonical-first commit order: `INSERT OR REPLACE` the complete original15-field row using explicit `legacy_file_path`, commit, and reconcile every expected committed field. Then strict INSERT the new companion row with its generation/immutable absolute path/hash, commit, and reconcile its complete row/index ID. Scoped publication performs only the companion insert/commit. The association must already be durably reconciled. An SQL failure has no file-only fallback.
5. Before persisted success, under the same guards, reconcile immutable artifact bytes, alias bytes where applicable, canonical full15-field row where applicable, complete companion row and durable association. Only then resolve every bound/completion ticket for this publication to the same artifact/index ID. File-only resolves after durable immutable artifact and canonical alias readback; no SQLite assertion is made. Release guards only after the result is fixed.

These are separately durable filesystem/SQLite operations, not a cross-file atomic transaction. Keep canonical-first/companion-second partial-commit custody: a later failure cannot undo an earlier committed canonical row or alias replacement. Do not remove an immutable artifact or an already committed history row on failure. A prior success receipt remains unchanged and independently verifiable even if the next alias/SQL publication fails. Legacy latest may be incoherent after an explicit failed publication; failure must name the state requiring reconciliation and must never be called persisted. A later explicit retry through an admitted recorder/lifecycle uses a fresh nonce and the next valid committed generation without laundering the earlier failure. This does not clear a sticky writer error or reopen fenced admission.

Use the existing `Exception` receipt slot for `RecordingPublicationError` in RT, with required keyword fields/read-only attributes `phase`, `cause: Exception`, `path: Path | None`, `legacy_alias_path: Path | None`, `generation: int | None`, `index_id: int | None`, `alias_state`, `canonical_state`, and `index_state`. `phase` is one of `admission/artifact/alias/canonical/index/reconciliation/durability`; the three states are `not_attempted/confirmed/unconfirmed`, with confirmed requiring the applicable operation, durability and readback checks. Retain independent observations: a commit exception with uncertain result is `unconfirmed`, not a fabricated rollback. This does not expand the receipt shape. The enclosing `RecordingDrainError` retains readonly run ID, all immutable receipts and incomplete/unbound identities on every call. Errors before publication have `receipt.path=None`; after publication it is the actual immutable artifact, never merely the mutable alias. Directory/alias/association/readback errors are failures even when bytes or rows already exist. Keep the existing acceptance fence, queue-full counters, closed-set drain, incomplete-bound failure, idempotence, and first-error propagation.

## Finite verification and owner integration

Implement within T33's existing REC/DB/RT/regression owner and fresh independent review, after the coordinator freezes the applicable candidate. No new task, final lens, helper module, or source copy is required. Preserve the independently owned raw public `writer_loop` adapter/nonselection-diagnostic repair and the separate unit-only maintenance scope. Do not replace their permanent controls with generation tests.

Add these finite cases to `test_recording_drain.py`, using real files/SQLite and independent bytes/payload/committed-row assertions:

| Case | Required observation |
|---|---|
| Two same-episode legacy publications before one shutdown | Different frozen tickets and immutable paths/index IDs, generations1/2; both original receipts still match their original bytes/rows; canonical alias/full15 row/old lookup show second data with old relative locator. |
| Separate instances and reopen | Same output root and supplied DB, then a closed-family reopen/new recorder, publish episode7 again; prior receipts/history remain readable; generation continues; latest becomes new bytes. Include DB located outside `output_dir.parent`. |
| Bound ticket routes and shutdown replay | Every admitted bound ticket resolves to its publication's exact immutable path/index; repeated shutdown returns the same outcome without extra artifact, alias, row, or generation. |
| Legacy full frame / rejected boundary | Deterministically fill the real admission queue: old `record_step` logs warning/returns None and increments only its drop counter; old `finish_episode` logs error/returns None and increments only its rejection counter. Assert no rejected-operation sequence/ticket/open-frame/accepted-set increment or reset. A dropped-frame group and a rejected-end group without an accepted retry each drain as explicit failed/incomplete, with no partial success/artifact. A separate no-drop control retries the rejected boundary after capacity returns and gets one actual ticket/full outcome. |
| Qualified capacity and error controls | `for_scope` admission methods and `record_bound_step` on either constructor raise actual `queue.Full` on rejection with no issued ticket/state advancement/legacy-counter increment. Counters remain cumulative across groups; deterministic closed-set drain accounts for every accepted item. Legacy validation, fence and writer-error controls still raise, proving the narrow Full handling does not swallow them. |
| File-only repeat | At least two distinct payloads for the same episode in one recorder and a later instance, no database; each persisted receipt keeps readable immutable bytes, `index_id=None`, mode=file_only; canonical alias has latest payload. |
| Scoped separation | Existing four run/lane scopes share episode7 successfully with generation0; reusing one exact scope refuses without overwriting its artifact/index or any legacy alias/row. Prefix-sharing valid run IDs remain accepted; exact reserved root is refused by factory. |
| Earlier-success preservation on later failure | Inject later alias replace/fsync/readback error, canonical ignored/altered full15 row, and companion commit/readback error; all earlier immutable artifacts/rows remain exact. New failed receipt retains actual artifact and phase/alias/commit custody. Test failure before file publication separately. |
| Durable binding/family/version | Existing suppressed/altered committed-binding and one-shot/persistent directory-sync witnesses still fail truthfully/retry or refuse checkpoint as specified. Closed exact v2 reopens/exports; v1/foreign/malformed/active families refuse byte-for-byte unchanged; ordinary canonical reads create nothing. |
| Competing legacy publishers | Deterministic barriers across separate recorder instances sharing output root and DB: after both succeed, latest alias/full15 row agree, no deadlock, and every reported success retains its immutable artifact/index. File-only/indexed overlap proves serialized alias replacement and each receipt's immutable bytes, without claiming a later file-only write updates SQL. Exercise lock-release on failure. |

Keep existing drain/fence/full-queue/incomplete/not-selected/native payload/compression-none/SQL-trigger controls and required execute-only owner suites; repair any candidate-era blanket expectation that the two legacy capacity calls raise, retaining the qualified strict contrasts and actual baseline behavior. No sleep-based success criterion. A publication failure is verified from before/after file/index custody, not from an assumed phase order. Preserve the real second-family-COMMIT negative control: canonical may be committed while companion row is absent, but the failed receipt identifies its immutable orphan. Do not downgrade that witness because the new guard can fail earlier in other cases.

Current attributed whole-source sizes are REC452, DB1017, RT65, regression649. Initial projected ceilings are REC650/DB1150/RT200/regression800: four files2800 lines. Routine floors may need an increase after actual count, including REC/regression for capacity preservation; choose concrete revised floors before dispatch if needed, while keeping this entire context at most5 whole source files/5000 lines including any authored reviewer probe. A fifth independent probe of at most350 would make the initial projection3150. Do not hide growth in a sixth source/module. Separate unit owner reads unit603/REC projected650/DTO243/RT projected200/builders591: five files2287 projected; it writes only the unit file, adapting DB-seam expectations for explicit generation/legacy locator/context and preserving the legacy logged capacity controls alongside qualified strict, raw-route/payload/diagnostic controls. Recount whole current files and hashes before/after every relevant owner/reviewer dispatch.

Logical order inside existing work: reconcile current raw-route/diagnostic and association-readback repairs; freeze causal RED for legacy repeat loss and legacy capacity regression; change RT failure custody plus DB v2/guard/index interfaces and REC immutable/alias publication/capacity ledger together; run focused GREEN and existing owner suites; freeze exact source/evidence; obtain fresh independent technical/current-artifact review; complete standing static/full checkpoints before dependent release. This is a logical dependency, not permission to execute or an extra task programme.

After independent design acceptance, coordinator propagates the changed P8/`recording_receipt` contract, concrete methods/legacy finish union, capacity counters/ledger, v2 shape, latest-versus-history and partial-failure semantics through the approved plan, existing interface record and affected task/overlap/brief/support metadata. Retain66 tasks/22 final lenses/55 interface records by extending the existing recording interface record, including PW11 as a consumer. T34 must drain before close and preserve original training exceptions plus publication custody, never treating a rejected legacy finish as an accepted end; T35/PW11 must distinguish immutable history from canonical latest without duplicate completed-outcome accounting; T39 must verify repeat publications/earlier receipts against by-index lookup and honest capacity/incomplete outcomes; F14 must attack actual generation/alias/SQL/admission interleavings at the final common SHA. Recount downstream whole-source ceilings (especially T34's five sources and F14's REC/RT/DB/TB/probe) before dispatch and increase routine floors only within5/5000; reslice only if that hard cap truly requires it. Future consumers inherit these same rules. Prior v1 evidence stays historical evidence and must not be relabeled as v2 qualification.

## Decision boundary

No routine user decision is required for this additive preservation approach. The coordinator/reviewer must settle technical acceptance of this concrete supplement and the exact supported output-root lock implementation, then explicitly authorize any implementation phase under the existing workflow. A genuine request to remove legacy repeat publication, canonical latest visibility, file-only use, old logged/no-throw capacity behavior, raw writer transport, or diagnostics would require the user's approval; this proposal makes none. The failed durable rule supplies neither a grant nor a restriction, and no user-only fallback is adopted. All standing project/tool requirements and later implementation/review/full/final acceptance gates remain owed.
