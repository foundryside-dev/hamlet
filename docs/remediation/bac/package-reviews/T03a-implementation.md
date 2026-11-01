# T03a historical archive work report

Phase 1 tests ready: regression source written; execution and production edits remain paused for the common source freeze.

Inspected complete listed source only: checkpoint_utils.py (777 lines), brain_config.py (568), replay_contract.py (222). The owned regression is 372 lines after Black, giving 1939 complete source lines in four files so far; the fifth owned production file is absent. Root authorized mechanical test-ceiling expansion from 350 to 400 for formatting, preserving the same five files and requirements. With production at its 450-line ceiling the total remains at most 2389. No helper source, branch, worktree, repository copy, staging, commit, reset, or test/import execution was used.

Native DATA: portable manifest, complete uniform/PER/sequence-trained producer artifacts, their JSON inventories, and their native YAML configurations. Read-only SHA256 verification matches the manifest: uniform `44a77c9e6edf183eaa5cb5761bad4999f0947175d51e8b308b7c2d3fcaf99d6d`; PER `8b4102b02e9a6d94e31095b67a5b1bb8e57641f60f3c3658fa2cb2f313f33c30`; sequence-trained `f5ca18d9e4f8c8f9398d585fc2a7861d23883ca9a8ae7175c964e2e97e16ced6`. Versions are demo9/population6/replay4,4,5; retained native rows are 4,4,34.

Regression covers actual old outer/runtime/replay validation, approved dispatch and explicit full-resume refusal, exact complete archival state, priorities and recurrent episode boundaries, rewards/dtypes, source/getter/query ownership, six archive constructor fields, separate available learned state and clocks, zero prepared active retained rows, exact export and state/artifact digests, old brain/training identities and five overrides, incompatible new options, standalone envelope relocation, schema/state/digest corruption, differing serialization with equal state digest, deep malformed input and atomic preparation/publication/readback failure.

The actual legacy callback also constructs the source-selected native population geometry and calls the existing population.validate_checkpoint_state without loading/installing checkpoint state. Only its public interfaces supplied by the coordinator were used. Intended causal RED after freeze: importing the owned test fails because the new historical_checkpoint module is absent. No RED or GREEN claim is made in this phase.

Root-authorized phase-1 scoped Black and Ruff passed using the project virtualenv. Final regression SHA256: `078800bf816d1b0ecbc9e6564cae6ab7c1e960cb8cced2cff41810a5b9ea346b`. Five test functions each consume the three genuine native artifact variants. Source is now stationary pending root's shared freeze and causal RED authorization.

## Phase 2 implementation ready

Root recorded causal RED on the frozen three-test image: the owned test failed collection with the intended missing historical_checkpoint import (exit 2). Root then authorized production implementation and a mechanical HC ceiling increase from 450 to 700 with the same five files and requirements.

HC now implements approval-linked old/current access policy, owned immutable six-field archives, exact native replay query/export, standalone envelope encoding/decoding, old brain/training identity recipes and five overrides, and separate available learned state. `state-sha256:v1` uses versioned length-framed type tags, preserves dict/OrderedDict and sequence types/order, distinguishes scalar/key types, and encodes tensor dtype/shape/byte order/logical raw bits independently of device. No pickle/JSON/repr state-hash shortcut or fabricated file verification is used. Native export uses a temporary file, fsync, expected-state-digest verification after readback, exclusive hard-link publication, directory fsync, and cleanup on failure. Its artifact digest hashes actual exported bytes.

Embedded native-current archives use the root-approved `historical_archives` key; standalone envelope serialization uses `archives`. HC retains qualified current replay and checks recorded successor legality. Complete current runtime validation/installation remains with the later loaders/adapters, as root confirmed; HC prepares packets without runtime installation. Archives never advance active retained counters or supply sampling methods.

The owned test correction strengthens the actual old callback with existing pack/VFS identity validators plus independently computed old brain/training recipes and level hashes. It additionally refuses a changed brain identity before preparation. Full population/replay validation stays present; no scratch-universe hash is patched or retagged.

Scoped Black and Ruff pass on the two owned paths. Actual whole-source inventory: HC 509, checkpoint_utils 777, brain_config 568, replay_contract 222, test 397 = 2473 lines across exactly five files. No runtime execution, additional source reads, index mutation, staging, commits, worktrees, branches, copies, or delegation occurred during this phase. Source is stationary pending root's fixed-image GREEN.

Implementation-ready SHA256: HC `6ab341e35dd959645eeb1717b136feb5f2a8efa6a903ac19ca64824e9182202c`; regression `5dca328391648d4aeea3283937640385bd5638f3c5e005511a356766cbcbdb2e`.

## Repair phase A: tests ready, production unchanged

Root's first frozen run recorded 11 passed and four PER harness failures. The scratch PER constructor now receives recorded beta_initial (0.4), preserving the real validator's distinction from annealed beta (1.0). Format9 helper test calls now pass training=None explicitly in preparation for the no-defaults correction; historical behavior is unchanged.

Added permanent node `tests/test_townlet/regressions/bac/test_historical_dispatch.py::test_sequence_archive_queries_preserve_partial_reward_component_coverage[sequence-trained]`. It deep-copies the complete pinned native sequence artifact, makes one episode's intrinsic component absent and leaves its final done False, then runs the actual old callback. It demands exact known-only and later-only component values, cross-window known values with explicit per-component bool presence masks, no component value for an entirely absent query, independent complete coverage of other components, exact native export, unchanged original native file, and no source mapping mutation. Intended new RED is the known-only query's missing rewards_intrinsic key caused by HC's current global drop.

Scoped Black/Ruff pass. Test: 439 lines, SHA256 `7cd2aacc90e26bf97fbe3da4b599ccba77f8dce6caac5ae94e682c714c3f287e`. HC remains byte-identical at 509 lines, SHA256 `6ab341e35dd959645eeb1717b136feb5f2a8efa6a903ac19ca64824e9182202c`. Five-file source total is 2515 lines. No pytest, runtime import/probe, production change, index mutation, extra source read, copy, or delegation occurred. Source is stationary for root's repair RED freeze.

## Repair phase B: implementation ready

Root's frozen repair RED confirmed the intended missing intrinsic-component KeyError; the corrected PER positive independently passed (one failed, one passed). HC query repair now returns per-component `*_present` bool tensors. Each selected known value is copied exactly even when another episode lacks that component. Cross-window unknown positions are zero placeholders under false presence; entirely unrecorded selections omit the component value. Other reward components retain independent coverage. The source archive, its state digest recipe, and native export remain unchanged in meaning. Sequential final dones need not be True; no stricter requirement was introduced.

Type repairs use checked mapping-sequence/tensor narrowing, explicit policy/tuple unions, and validated embedded-archive parsing. No type-ignore bypass was added. The reported no-default violations were rewritten using explicit branches and required `format9_brain_hash(..., training=...)`; callers already pass explicit None when no overrides apply. No whitelist or ratchet changed.

Scoped Black check and Ruff pass on both owned paths. HC is 602 lines, SHA256 `4df70b6bec0201ce5b2117a0b95ae06052b71933447f4c4f80603161cb444a54`; the frozen test remains 439 lines, SHA256 `7cd2aacc90e26bf97fbe3da4b599ccba77f8dce6caac5ae94e682c714c3f287e`. The complete five-source inventory is 2608 lines. No pytest, runtime source import/probe, mypy or broad guard execution occurred during this writer phase; root owns those fixed-image checks. Source is stationary for shared GREEN. No extra source/helper/index/copy/delegation changes occurred.
