# T18d source-verified historical fixture/API capsule

Readonly source audit; no imports, Python execution, torch load, runtime probes, tests, git operations, artifact writes or implementation changes. This document is the sole output. It supplies dependency facts to an author whose implementation/test source budget is exhausted; consuming this prose and the named JSON manifests does not require reading another implementation file. It does not authorize a runtime probe by this auditor.

## Source inventory and custody

Exactly two implementation/test sources read (whole-file conservative charge 1114 lines):

| Path relative to /workspace/hamlet | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/historical_checkpoint.py | 675 (ceiling750) | 74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4 |
| tests/test_townlet/regressions/bac/test_historical_dispatch.py | 439 (ceiling600) | 7cd2aacc90e26bf97fbe3da4b599ccba77f8dce6caac5ae94e682c714c3f287e |

Other reads were policy/prose/data only: AGENTS.md; docs/remediation/bac/HISTORICAL-REPLAY-DECISION.md; tests/test_townlet/fixtures/bac_historical/{portable-manifest.json,historical-evidence-review.md}; tests/test_townlet/fixtures/bac_per_current5/portable-manifest.json; tests/test_townlet/fixtures/bac_sequence_current6/portable-manifest.json; .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave29-preparation/PW07-SOURCE-VERIFIED-REPLAY-HC-API.md. Filename listings found the decision. No artifact was opened or rehashed here; artifact digests below are manifest claims, with the parent's separately established custody checks remaining separate evidence.

AGENTS forbids legacy runtime fallbacks. The current historical decision preserves old artifacts for read/query/export under BAC-HISTORY-A-2026-11-01, excludes maskless old rows from constrained learning, and preserves current captured-mask replay. This capsule concerns existing archive and component APIs, not revival of removed native runtime providers.

## Exact callable entry points

Import implementation API from `townlet.training.historical_checkpoint` (module alias `hc`). These signatures are verified in the source above:

- `archive_standalone_replay(state: Mapping[str, object]) -> HistoricalReplayArchive`
- `resolve_historical_access(payload: Mapping[str, object], *, requested_mode: AccessMode) -> HistoricalAccessPolicy`
- `prepare_historical_envelope(payload: Mapping[str, object], *, requested_mode: AccessMode, validate_legacy: Callable[[Mapping[str, object]], None]) -> HistoricalPreparedEnvelope`
- `encode_historical_envelope(envelope: HistoricalPreparedEnvelope) -> Mapping[str, object]`
- `decode_historical_envelope(state: Mapping[str, object]) -> HistoricalPreparedEnvelope`
- `format9_training_hash(training) -> str`
- `format9_brain_hash(brain, *, training) -> str`

`AccessMode` is Literal["auto", "recorded_full_resume", "archived_history_fresh_episode", "inference"]. Required keywords have no defaults. Historical policy is a frozen dataclass, not a subscriptable mapping: attributes `source_formats, requested_mode, effective_mode, approval_reference, archived_row_count, active_retained_transitions, restored_clocks, guarantees, legacy_identity_recipe`. Envelope attributes are exactly `policy, archives, available_learned_state`.

Archive constructor fields, in order: `HistoricalReplayArchive(source_formats, original_state, source_digest, archived_row_count, reward_semantics, approval_reference)`. Prefer `archive_standalone_replay` rather than hand-computing its typed digest. Public archive methods are `query_rows(self, *, offset: int, limit: int) -> Mapping[str, Tensor]` and `export(self, destination: Path) -> ArchiveExportReceipt`. Receipt attributes: `destination, source_digest, row_count, output_digest`. No sample/push/add/update-priorities route exists on the archive. Original state and formats are cloned on storage/access.

`archive_standalone_replay` accepts the actual historical replay subtree, validates exact native pre-capture shape/schema, clones it and returns a genuine archive. Its source domain is exactly `{"scope":"standalone_replay", "replay":4-or-5, "replay_kind":actual-kind}`. It makes no native demo/population provenance claim. `source_digest` is a framed typed-state digest (`state-sha256:v1:`), distinct from file SHA256. It includes source domain, so standalone and full-container archive digests need not agree for the same replay.

`query_rows` returns cloned inspection rows. Sequential queries flatten episode order and add episode_ids; PER adds copied priorities for retained rows. Core rows: observations/actions/rewards/next_observations/dones. Components are rewards_extrinsic/rewards_intrinsic/rewards_shaping; each has a Boolean `*_present` query mask. Whole-missing component selections omit its value tensor; mixed missing positions use zero placeholders only under false presence masks. Queries do not invent next_action_masks/legality_recorded. Offset/limit must be exact nonnegative ints (bool refused).

`export` preserves original replay state into a NEW destination: verified temporary save/readback and typed digest check, no-clobber hard-link publication, file/directory fsync; an existing path/symlink refuses. Export is not byte-for-byte reproduction of original pickle serialization; receipt output_digest is `artifact-sha256:` of new bytes. Use a new scratch destination, never a frozen fixture path.

## Existing genuine fixture loader and the full-native helper limit

The only loader/helper definitions verified here are in tests/test_townlet/regressions/bac/test_historical_dispatch.py:

- `native(request)` is `@pytest.fixture(params=("uniform", "per", "sequence-trained"))`. It returns `(payload, record, path)`. It reads canonical_artifacts from bac_historical/portable-manifest.json, selects request.param, verifies file SHA256, calls `checkpoint_io.safe_torch_load(path, map_location="cpu", allow_unsafe_pickle=True)`, verifies exact outer/population/replay key ORDER, versions9/6/native replay version and retained count. `checkpoint_io` is `townlet.training.checkpoint_utils`. This is the exact observed loader call, not a read of checkpoint_utils implementation or proof of its complete signature.
- `legacy_population(kind, level)` has `@lru_cache(maxsize=3)` and returns `(universe, env, curriculum, exploration, obs_dim, pack_brain)`. Kind maps standard->uniform, prioritized->per, sequential->sequence-trained; it compiles DATA/label-pack with primary_level=level,use_cache=False.
- `legacy_validator(payload)` performs old outer/runtime validation, constructs matching replay owner and calls validate_serialized(expected_obs_dim=obs_dim), checks pack/VFS/level identity and format9 brain/training hashes, constructs VectorizedPopulation and validates checkpoint state.
- `prepared(payload, *, requested_mode="auto")` wraps `legacy_validator` as the required callback, invokes prepare_historical_envelope, and asserts callback called exactly once. `expected_rows(replay)` and `assert_exact(actual, expected)` are comparison helpers; expected_rows assumes each component is a tensor and is unsuitable for an all-None/partial component variant.

These are file-level test symbols, not a proven reusable installed fixture module. Pytest fixtures cannot be called as normal functions. Importing this test file itself executes top-level imports including `townlet.exploration.adaptive_intrinsic.AdaptiveIntrinsicExploration`. No import was attempted here. Thus do NOT describe `native`/`prepared` as currently import-safe reusable helpers. A new test can use the manifest + exact verified loader call in its own authorized source budget; that does not require reading checkpoint_utils or this test's source.

The precise full-native dependency gap: legacy_population requires the old AdaptiveIntrinsicExploration provider and training.intrinsic.rnd/annealing/min_survival_fraction/survival_window state recipe; legacy_validator also constructs old replay owners and old VectorizedPopulation API and expects old outer validators to accept demo9/pop6. The parent's current runtime has removed historical fallback/provider support. This two-source audit cannot establish those old imports/constructors/validators remain callable, nor supply a current owner-native validator for their old state. The helper is not a certified full-native preparation route. A no-op/generic fake validator would falsely certify native admission and must not replace it. No sixth implementation read is needed to state this limit.

For actual native history inspection, the source-verified route that does not depend on that missing callback is: verify manifest file digest, load trusted native artifact with the observed safe_torch_load call, take payload["population_state"]["replay_buffer"], and call `hc.archive_standalone_replay(actual_subtree)`. Compare archive.original_state/query/export against that actual subtree. This proves the standalone archival boundary on genuine bytes, not whole-native restore or learned-state admission. `resolve_historical_access` can separately resolve supported actual native format and archive counts, but does not replace identity/runtime validation. Preparing a full native envelope remains limited until an authorized owner-native validator is supplied; never imply that standalone archive success resolves that gap.

## Full-envelope behavior and current captured replay

Supported HC full-container domains currently are historical demo9/pop6 with standard4/prioritized4/sequential5; current demo10/pop7 with standard5/prioritized5-or6/sequential6-or7. Formats do not infer authenticity of a hand-built container.

For native demo9, resolve auto => archived_history_fresh_episode, old retained rows archived, active count0; recorded_full_resume raises HistoricalLegalityUnavailable for absent successor masks. Inference resolves inference. Preparation clones payload, resolves policy, invokes supplied validate_legacy once on the owned full payload, then pops replay_buffer from owned population_state into a full-domain archive. Available nonreplay state is preserved as data; this function does not instantiate/restore any runtime owner. Source clocks alone do not establish replay readiness. Source provider guarantee explicitly names AdaptiveIntrinsicExploration and absent unrecorded masks/RND tails/RNG. Reward marker is `historical_recorded_pre_fix`; no reward rewriting.

For current10/pop7 captured replay, requested archived_history_fresh_episode refuses. Auto => recorded_full_resume; explicit inference => inference. Captured masks/legality and actual rows remain active; validate_legacy is required syntactically but is NOT invoked (a callback that raises if called is an honest branch guard). Envelope retains population_state.replay_buffer. HC validates masks/policy, not every owner-specific native field. Current embedded archive discovery in this API is top-level payload["historical_archives"], not a recursive search into replay_buffer. A current replay artifact with replay-level archives must explicitly supply actual archives at the HC container boundary if testing their HC preservation, with claims restricted to component wrapping. Do not silently drop them or claim a synthetic10/7 wrapper is a native checkpoint.

Codec emits exactly schema_version1, policy, archives, available_learned_state; decode returns owned dataclasses and verifies archive schemas/digests. It does not reopen source artifact. Mutations of source/query/encoded/decoded data must not alter independently owned archive data.

PW07 prose documents public uniform ReplayBuffer(capacity:int,device:torch.device), prepare_serialized(state,*,expected_obs_dim), load_prepared(candidate), load_for_mode(state,*,requested_mode), serialize(), retained_transitions/historical_archives. It is dependency prose for uniform only; this audit did not inspect or establish PER/sequential current owner restoration APIs. Do not transfer uniform signatures blindly to those owners.

## Genuine historical fixture facts (manifest/review evidence)

Base: tests/test_townlet/fixtures/bac_historical. Matching full packs are uniform-pack, per-pack, sequence-trained-pack; per-file pack hashes, key inventories, reward tensor digests and independent restore results are in portable-manifest.json. Producer source4aa5363b5de54d9a112977c32c2975f37627197f used native demo save with actual training, not learner/optimizer mocks.

| Artifact | SHA256 | Bytes | Native versions demo/pop/replay | Kind/count key | Rows | Training counter/Adam steps |
|---|---|---:|---|---|---:|---|
| uniform.pt | 44a77c9e6edf183eaa5cb5761bad4999f0947175d51e8b308b7c2d3fcaf99d6d | 1340853 | 9/6/4 | standard/size | 4 | 3/3 |
| per.pt | 8b4102b02e9a6d94e31095b67a5b1bb8e57641f60f3c3658fa2cb2f313f33c30 | 1341237 | 9/6/4 | prioritized/size_current | 4 | 3/3 |
| sequence-trained.pt | f5ca18d9e4f8c8f9398d585fc2a7861d23883ca9a8ae7175c964e2e97e16ced6 | 1463292 | 9/6/5 | sequential/num_transitions | 34 | 2/2 |

Uniform/PER: episode2, completed_live_agent_steps=total_steps=4. Sequence: saved episode18, clocks34, 17 complete two-step episodes, capacity64, sequence_length2/batch2/min2. Initial16-episode capture had32 rows but no updates; resume to18 produced34 and2 real updates. Optional sequence.pt is a smaller untrained artifact, not equivalent learned-state evidence. Historical source dimensions are NOT declared numerically in the permitted manifests/review; do not guess them or infer all historical geometry from current transport data. Derive actual widths from loaded trusted tensors only in an independently authorized test, or obtain additional authorized data/prose.

Exact historical sequential top-level replay schema is replay_kind,format_version,capacity,num_transitions,episodes. Each episode owns observations,actions,rewards,next_observations,dones and three optional reward components. Historical standard schema additionally uses position,size; PER uses alpha,beta,beta_initial,beta_annealing,priorities,max_priority,position,size_current. No historical masks exist. Row validator requires float32 obs/next_obs/rewards/components, int64 actions, bool dones; observations are [rows,obs_dim], scalar fields [rows]; all present values finite and devices aligned. PER priority array is float32 capacity-length. These are validation requirements, not an unperformed fresh artifact inventory.

Historical review records exact whole-population/replay restores in separate processes against the pinned OLD runtime with matching packs and zero additional learning steps, including components and ownership. Those past results do not establish current runtime compatibility, current reward semantics, complete RNG continuation, or whole-parent current-projector correctness.

## Authentic current replay captures and their limits

These are captured replay states, not whole demo checkpoints. Their newly recorded rows use declared synthetic transport; they are neither historical row reconstructions nor minimal invented schema dictionaries.

PER5 base tests/test_townlet/fixtures/bac_per_current5:

- per5-captured.pt SHA9a85394d9f36cd5660fe7a6c6944d600ce18e44410b63f5beb50203fd379b296 (5422 bytes), archive_count0.
- per5-captured-with-per4-archive.pt SHA029558d19fdae42f14e61432af8353c1c078db554a7e3b39519d39b50dadfe60 (12588 bytes), archive_count1.
- Capacity3, row shape[3,2], masks[3,3], physical rows[3,4,2], position2, retained3; beta_initial.4/beta.7, priorities[3.0000009536743164,5.000000953674316,7.000000953674316], max_priority8.000000953674316. Exact key inventory includes format_version,replay_kind,capacity,action_dim,legality_mode,legality_recorded,next_action_masks,historical_archives; component values plus presence; priorities and beta fields.
- Genuine PER4 source is per.pt above, subtree population_state/replay_buffer, standalone archive digest state-sha256:v1:e0f91ae6452cd46c4f027dae390a54daad271cf6ac53a95d2f7cf8f8cd1db5f3. Capture installed that archive in one owner, then pushed rows0..4 with finite priority updates/wrap/beta anneal. Producer07ce97550cf2f9dae67cb56d1d8014218c39d523. No authored-world/optimizer execution, C01 reachability or future PER6 adapter proof.

Sequence6 base tests/test_townlet/fixtures/bac_sequence_current6:

- sequence6-captured.pt SHA02e19371fc3131db51a9569fc6d5175de5a11416e2d6cea075d441ebd8bc8434 (archive0).
- sequence6-captured-with-sequence5-archive.pt SHA0a40c2dbba0d64f804f91f1a5600994385777a660d4a40c851e7aa3111fa239b (archive34).
- CPU, capacity3, observation_dim118, action_dim12, retained3, format6. Episodes IDs[0,1], original_lengths[4,2], start_offsets[3,0], transition_ids[[3],[4,5]]. Dones flattened[false,false,true]. Masks allow only action3, then action1, then terminal all-false. Component-presence extrinsic/shaping[true,false,false], intrinsic[false,true,true].
- Genuine source sequence-trained.pt above, standalone digest state-sha256:v1:dd86526bcc0b461d40c37cc84e2ffe77d850d6fce471140ecafe5a146412ad03, source native versions9/6/replay5. Synthetic first episode externally ended done=False; second ends[False,True]. Only new rows have declared masks. No natural-trajectory claim. Qualified producer495360d68c167b741d8ed5016c0921f995aac1f4 and qualified source treef88f7cb3e3d0203ab199a2d898e3b0f8370d7e48 are distinct from staged candidate tree279e9b7ebc978e6b1f4977953b91fd251ebbf233.

## Finite consumption choices without another implementation read

1. Consume manifests and this prose only to author an actual-artifact standalone HC archive/query/ownership/new-destination-export regression using a verified native subtree. This avoids missing native provider APIs and proves the genuine historical read-only boundary.
2. Use the actual PER5/sequence6 captured replay files with their manifests for current replay/data custody preservation. Any minimal10/7 HC wrapper is explicitly a component fixture; preserve real replay archives at the documented HC boundary and use a raising unused callback. Do not claim whole-native admission or owner restore unless separately supplied API evidence authorizes it.
3. Use already source-budgeted uniform current fixture/owner APIs plus PW07 prose to cover current masks/active rows/HC encode-decode ownership, naming its component scope honestly.
4. If full genuine native envelope/restore is required, record the precise missing owner-native validator/provider recipe as blocked evidence. Ask coordinator for an authorized reusable validation entry point or data/prose evidence; do not open a sixth source, resurrect legacy provider, or pass a generic fake validator.

No result here qualifies the entire parent projector, runner restore, reward correction or publication. No code/test execution is claimed.

## Fixture re-export/request details and outstanding required admission

If the repository test namespace is importable, the corresponding re-export spelling is `from tests.test_townlet.regressions.bac.test_historical_dispatch import native`. This is the actual file/symbol location, not a verified successful import: test package discoverability was not inspected and the module's removed-provider imports remain a blocker. Do not import this module merely to obtain its loader in the current runtime. A pytest fixture exposed in a test module is consumed as a `native` argument; select one genuine artifact with `@pytest.mark.parametrize("native", ("sequence-trained",), indirect=True)` (the exact existing usage), or analogously uniform/per. The fixture receives request.param and yields `(payload, record, path)`; it is not `native("sequence-trained")` or a direct `native(request)` call. Its default parametrization already covers all three canonical labels. No regular public `load_native(label)` helper exists in the two inspected sources.

The narrowly reusable existing loader expression is `checkpoint_io.safe_torch_load(path, map_location="cpu", allow_unsafe_pickle=True)` AFTER comparison of `hashlib.sha256(path.read_bytes()).hexdigest()` to the selected manifest record["sha256"]. Obtaining path requires DATA/record["artifact"] and selection of canonical_artifacts where label matches the chosen name. Reusing this known call inside an independently authorized test does not attest that the old test fixture's validation/import dependencies work.

Actual current captured replay container classification may use `resolve_historical_access(container, requested_mode="auto")`; preparation may use `prepare_historical_envelope(container, requested_mode="auto", validate_legacy=must_not_be_called)` only when actual container metadata is current10/pop7 and its masks/counts pass the described checks. `must_not_be_called` must raise, so accidental historical dispatch fails. Such a callback asserts the current branch and supplies NO native historical validation. Real existing archive objects/records must remain represented at the correct container boundary; wrapper metadata is explicit test transport, never fabricated native history.

Matching parent admission and full historical native preparation remain REQUIRED later owner repair, not optional scope and not closed by these cases. The cases above establish only the existing HC preservation boundary while that repair remains outstanding.
