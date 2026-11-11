# Current completed-boundary receipt API

Prose-only extraction from already-owned `src/townlet/environment/vectorized_env.py`2452 lines, SHA2563b65e6f143edf1a1a363b6b537376f2e8f3f5dc1f7ce6f6feb8ba9c06bca5256. Existing five-source context4828; no extra source, runtime/import/probe/compile/test/index/git/branch/worktree/copy/subagent action. This qualifies ENV validation ABI, not existence or correctness of unopened owner producers.

`WorldBoundaryAuthority.completed(*, closure: WorldRecord, effects: WorldOwnerReceipt) -> WorldRecord` authenticates that this authority is ENV's bound authority, requires phase closed-awaiting-release or released-completed, requires a valid current-generation ENV-issued closure record and `closure is env._world_closure`.

Outer receipt must be issued with **kind='boundary_effects'**, owner identity exactly the actual authority owner supplied to ENV.bind_boundary_authority(owner=...). Its payload has exactly these nine keys:

| Key | Exact correlation |
|---|---|
|batch_episode|exact nonnegative integer; equals closure.boundary_key|
|accepted_identity|**actual current WorldAcceptedEpisode object**, `is env._world_accepted`; NOT portable identity dict, tuple, hash or reconstructed token|
|completion_content|same_value equality with closure.completion_content|
|retirement_receipt|exact object identity `is closure.dispositions`|
|curriculum_receipt|child receipt described below|
|exploration_receipt|child receipt described below|
|population_commit_receipt|child receipt described below|
|epsilon_install_receipt|child receipt described below|
|selection_sync_receipt|child receipt described below|

Each child kind is literally its outer payload key, not a generic 'effect'/'prepared' kind:

| Outer key and required child kind | Exact registered owner role |
|---|---|
|curriculum_receipt|curriculum|
|exploration_receipt|exploration|
|population_commit_receipt|population|
|epsilon_install_receipt|exploration|
|selection_sync_receipt|selection|

For each child, ENV validates an actual WorldOwnerReceipt through actual WorldReceiptIssuer with the mapped role owner's identity from frozen env._world_role_owners. Exact child payload keyset is `{'accepted','boundary_key','completion_content'}`. Child.accepted must be the same actual current accepted token; child.boundary_key must be an exact nonnegative integer equal closure.boundary_key; child.completion_content must same_value-match closure.completion_content. WorldReceiptIssuer.validate checks actual receipt type, actual issuer type, retained issuer-issued object identity, requested exact kind and requested exact owner identity; copied/duck/constructed-but-unissued receipts refuse. Issue uses actual retained issuer `issue(*,kind,payload)` and freezes payload; retain receipts/issuer custody. Owner equality never substitutes for identity. Actual facade and BANK are distinct owners: exploration/selection role may be facade where genuinely registered, curiosity dispositions are the actual BANK owner elsewhere.

On successful validation, completed returns retained equal release record with payload `{'release_kind':'completed','next_batch_episode':closure.boundary_key+1,'closure':closure,'effects':effects}`. This does not itself install release or reset next episode. Genuine next-episode flow calls ENV.install_boundary_release(actual_release), then prepare_episode with exactly its next_batch_episode/release and actual parent reservation/reset/activation protocol. Retried completed content must preserve actual equal-record semantics; a newly fabricated outer/child object cannot be presumed an equal retry merely from matching scalar fields.

A test-local cooperative boundary controller may issue these receipts only under actual corresponding registered owner custody and attest **real completed component operations** it observed/performed. ENV validates correlation/custody, not the implementation of a claimed curriculum/commit/epsilon/selection operation. Registering synthetic stand-ins or issuing 'prepared' evidence for nonexistent work does not prove authentic owner behavior. A genuine two-episode parent test remains a limited cooperative-controller integration witness, not HC/T26 all-child preparation/publication or whole-native recovery qualification. No authorization for fabricated owner receipts or full-boundary claims follows from this ABI capsule.
