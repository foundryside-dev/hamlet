# Review provenance

Historical finding/design review. The source identity in its body is historical; final repair and qualification are recorded in the implementation receipt.

Original artifact `T12-astra-review-r1.md`, SHA256 `e45f1220d990972624f64bd9ab0d8e2b4542ffa83aab58e9ec2df5231f2b2b19`, retained unchanged. This portable rendering normalizes execution paths. Runtime results are coordinator-attributed unless the body explicitly records reviewer execution.

# T12 independent source/spec review R1

**Verdict: BLOCKED — one confirmed static P2 archive-preservation defect.** No P1 found. The configured format6 producer and its causal tests cover substantial intended behavior, but the supported two-argument old5 auto-import route silently omits retained archives on its next serialization. Root's passing focused suite does not cover that second save/load path. Repair and fresh candidate review are required before T12 release. This is a finite producer review, not native T24/T25 qualification or final BAC closure.

## Exact candidate, inventory and custody

Reviewed existing `/workspace/hamlet`, HEAD `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`; staged candidate `37451f06a3a0d60ab8c6ecb4b33b8f6e9aa8f1a0`; manifest `wave06/green-r1-candidate.json`. Exactly five complete source files, **2987 lines**, were inspected:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/sequential_replay_buffer.py | 1170 | c805ee611d33d77d1478390a354a569ceeeed23c91540cf7cfd78629ce8730de |
| src/townlet/training/historical_checkpoint.py | 666 | 013fe456f867bc9b5e28ab95ee9b07e5b0fa155653abfd07de3a35159c969761 |
| src/townlet/training/replay_contract.py | 222 | 3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/regressions/bac/test_sequence_history.py | 635 | 35cdc7c634968e3991ea56292375c3a0feebce66737886168a64fc08e6877d1c |

Read the task-T12 brief, active T12 brief/interface capsule/consumer audit, and wave04 NATIVE-CURRENT-HANDOFF prose. Existing root AGENTS.md and higher user preservation authority remain controlling; no failed governance rule or user-only fallback is adopted. Relevant verification-before-completion evidence discipline is retained. No sixth Episode/PB/POP/helper/owner-test source was opened. No project import, runtime experiment, test, source/index edit, git write-tree, branch/worktree/source copy, deletion, tracker mutation or subdelegation occurred. Only this ignored report is written. Identity checks use `GIT_OPTIONAL_LOCKS=0` and cached comparison to the supplied tree.

## P2 — Accepted unconfigured old5 import loses its archive on the next save

**Location:** `src/townlet/training/sequential_replay_buffer.py:451–487` (especially 453–461), with the producing import path at 618–621, 1047–1062 and 680–685.

**Contract:** Approved Option A preserves every original old replay field for query/export while removing imported unrecorded rows from sampling. The accepted capsule requires complete archival records in portable state so relocation does not depend on external history, and preserves the two-argument constructor/public load/legacy exact5 inspection route. The consumer audit expressly expects a genuine old5 archival-fresh0 positive alongside retained legacy transport coverage. No approval authorizes dropping imported history when a supported public save is called.

**Concrete counterexample from actual code (not executed by this reviewer):**

1. Build a valid nonnegative-action old5 artifact through the two-argument constructor, `store_episode`, and `serialize`; the regression's `old_state(False)` supplies exactly this producer.
2. Create another two-argument `SequentialReplayBuffer(capacity, device)` and call its public `load_from_serialized(old5)`.
3. Legacy materialization creates a real `HistoricalReplayArchive`, returns `_empty_prepared`, and installs active0 plus that archive. Because `_empty_prepared` copies `self._configured`, the receiving buffer stays unconfigured. Its `historical_archives[0]` correctly contains the original rows at this point.
4. Call the same receiver's public `serialize()`. The `_configured` branch is false, so the empty-episodes branch returns only the exact five old keys with `num_transitions=0, episodes=[]`. `_historical_archives` is never included. The nonempty legacy branch also omits archives if newly authored legacy rows have subsequently been added.
5. Relocate that serialization and load it into a fresh receiver. It can at most archive the empty/new legacy payload; the original archive's digest, rows, boundaries, rewards/components and source domain are absent and cannot be queried/exported from the relocated artifact.

The original source file is not modified; the defect is silent loss from the newly produced portable artifact. This is not the known native outer-registry accounting issue: all calls occur in the inspected standalone sequential buffer, and the bytes are absent from the only saved payload. It also does not require malformed input, private field mutation, fabricated masks or unsupported negative actions.

**Missing regression:** test_sequence_history.py:439–452 proves first-import active0 and in-memory archive ownership on both auto and validate/materialize/load paths, but never serializes that unconfigured result. Tests 455–497 prove a configured current6 archive roundtrip, which takes a different branch and cannot detect this loss.

**Required repair outcome:** Preserve owned archive rows/domain/digest through a second portable save/load on this accepted route, including when newly authored legacy transport rows coexist with imported history. Keep imported history unsampleable, preserve the genuine legacy exact5 inspection representation/API, and do not invent an action vocabulary, resolved options or recorded legality to force the unconfigured object into qualified6. An additive archive-bearing transport path/explicit representation can reconcile these requirements; simply refusing previously supported load/save or discarding history is not authorized. The coordinator should settle that bounded ABI reconciliation before implementation. Add the causal roundtrip control to the same counted regression, then rerun root evidence and obtain fresh review.

## Whole-producer source/spec assessment

**Counts, readiness and draw laws:** SB:721–731 separates qualified retained rows from legacy transport counts without redefining `__len__`. SB:859–893 checks requested configured identity, computes actual sampleable windows/endpoints, and gives capacity impossibility precedence over warmup, then window availability. No hidden16 or B>M shortage gate is introduced. The two nonprioritized adapters remain independent with replacement. SB:918–935 implements actual fixed legacy episode weighting and uniform-start probability `n/[S*(n-L+1)]`, adaptive legacy endpoint probability `1/M`, and uniform-window probability `1/M`; nonuniform fixed draws get `1/(M*p)` weights. Equal-length/L1 special cases truthfully use uniform weights. Receipt mode records the active adapter rather than falsely adopting the inactive PER sampling_mode. OP:45–51 and 190–198 preserve the distinct fields and versioned legacy default. RC receipt schema permits these declared strings. Actual proposal/frequency controls at test:289–333 inspect sampled endpoints and reported probabilities/weights, not only a separately enumerated formula.

**Real fragments and endpoint identity:** SB:812–857 validates then clones before admission, allocates monotonically increasing episode/transition IDs, and stages whole-episode or oldest-transition-tail retention before installation. Tail slicing advances offset and preserves surviving endpoint IDs. SB:907–972 builds windows strictly within each retained fragment and uses its final transition ID as the sampled unit identity. Adaptive windows never invent evicted context; fixed windows require L real rows. Lengths describe real prefixes independently of anchor/window loss selection. Tests cover capacity1/L8, capacity15, 16 short episodes, terminal/truncation successors and current6 ID continuation. Clear retains archive custody and ID monotonicity.

**Legality, objectives, components and ownership:** Captured admission requires explicit positive A, actual bool masks/recorded bits, valid actions, finite float32 fields and no interior terminal (SB:760–810); RC:33–43 refuses nonterminal empty successors while permitting terminal empty sets. Explicit unconstrained store creates all-legal masks only for newly authored input with declared A (SB:257–269). Old imports never receive synthesized masks. Optional components remain exact per-episode values or None; SequentialReplayBatch presence flags distinguish missing components from zero values and false padding (SB:76–100, 952–972), while composed total rewards are not recomputed. Base RC validates real rows independently of loss_mask, forbids post-terminal real continuation, and clones all tensor transport fields (151–222). Admission, serialization, sample transport and current validated payloads detach/clone tensors. Test:624–635 verifies autograd detachment.

**Current6 validation/preparation:** The configured serializer records exact geometry/options, counters, real fragments and nested archive records (SB:989–1003). SB:1075–1154 validates exact keys/version/types, destination identity, real row shape/legality, counts, bounds, ordered distinct IDs and component metadata, and owns current fragment tensors. Materialization performs device copies and archive validation/dedup before installation (618–643). `load_prepared` checks compatible configuration and retained-history preservation before reference assignment (666–685); provider callers must finish all off-side preparation before installing a multi-owner native state. Current6 archival-reset mode refuses instead of clearing captured rows (1156–1170). The additive explicit `prepare_for_mode`/`load_for_mode` entry points preserve existing auto-wrapper signatures without adding behavioral default arguments, consistent with the active brief. No confirmed partial mutation on the ordinary current6 load path was found.

**Historical fidelity and strict inspection:** Pure legacy5 inspection retains the exact old structural schema and callable negative-action inspection behavior without licensing those actions for captured learning (SB:514–616). Materialization of an old validated artifact archives it rather than activating old rows. Explicit old5 full resume refuses. HC's entire staged diff is the narrow removal of its interior-terminal archive rejection at 215–216; positive episode lengths, schema/dtypes/finite checks, nonnegative archival actions, widths/counts and domain digest remain enforced. It does not loosen current6 terminal rules or flat/PER archival validation. The actual legacy sampler still emits [T,T,F] on a full3 sample with a terminal at index1 (SB:422–435), while HC query/export now preserves every original row (test:410–436). This is the accepted evidence-preservation repair, not a new post-terminal learner path.

**Archive identity:** SB:1005–1045 reconstructs validated HC archives before dedup and checks kind/observation width. Domain-aware digests and canonical content are reused rather than reimplemented. Configured current6 carries full records; corrupted nested content refuses and separate archive domains remain distinct by digest. This successful configured path does not cure the P2 unconfigured save omission above.

## Refuted hypotheses and bounded gaps

Refuted: PER's default without-replacement field silently changes SB draws; B>M necessarily fails; length2/L3 must crash after16 episodes; tail eviction splices neighboring episodes; anchor masks disguise post-terminal real rows; missing components are recomposed into totals; legacy5 materialize bypasses approvedA; current6 requested archival mode clears captured rows; HC's terminal change weakens active6 validation. The cited code and counted controls distinguish these cases.

No optional P3 is asserted. Tests do not exhaust every corrupt ID/fragment metadata combination, every device failure or every legitimate archive source-domain combination; these are coverage limits, not new confirmed findings. No new numeric/feature restrictions or cleanup scope is requested.

## Runtime evidence and native handoff

This reviewer ran no runtime/tests. Root's completed R1 focused log and result JSON were read: `qualification/wave06-green-r1-quick/T12.log` and `T12-result.json` report **50 passed in 4.48s**, exit0, **10.46s wall**, on the supplied HEAD/tree. Manifest digest in that result is `e0a29decc1c75222dcf7e11216268378a950af81539d2834a8ae0d69fff4932d`. These passing existing controls do not reproduce or refute the newly identified second-save omission.

Root additionally attributes original RED **41 failures / 9 positive passes**, existing legacy-owner **51 PASS**, initial collection170, and current collection135. These are root evidence, not independent execution; no broader green, source commit or package release is claimed here. Other active qualification jobs are outside this review verdict.

Native T24/T25 complete current replay/population/learned-state validation in full-resume AND inference, canonical outer registry/nested-subset reconciliation/domain-aware dedup/single accounting, atomic resource/RNG installation and genuine old9/6 continuation remain **REQUIRED OPEN**. HC access classification is prepared/unadmitted until those native validators run. Outer-only different-kind history must remain native-owned; it is not forced into this sequence buffer. Storage-only success and this finite review cannot close those obligations or final BAC acceptance.

## Final stationarity receipt

Before and after review: exact five hashes and 1170+666+222+294+635 = 2987 line counts match the supplied manifest; HEAD remains `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`; read-only cached comparison to `37451f06a3a0d60ab8c6ecb4b33b8f6e9aa8f1a0` exits0. Index byte SHA256 remains `7d9eaf3547304bdf9fdf118443700fda881dcf1e65d19ebfafb054e4e57524c2`. Unstaged tracked diff is empty; the eight staged candidate paths are unchanged. Report is ignored. The current collection log was directly checked and confirms 135 tests collected in0.13s. Review complete and stationary; source/spec blocker remains distinct from root's 50 passing focused tests.
