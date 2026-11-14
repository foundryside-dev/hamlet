# PW04 replay owner API reconciliation

2026-11-14. Read-only source supplier. No implementation, imports, tests, Git,
branch/worktree/copy, deletion or delegation. The only write is this capsule.
Four complete bodies, exactly 4,937 lines:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `training/replay_contract.py` | 881 | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| `training/replay_buffer.py` | 816 | `683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d` |
| `training/prioritized_replay_buffer.py` | 1310 | `7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29` |
| `training/sequential_replay_buffer.py` | 1930 | `e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317` |

Paths are relative to `src/townlet/`. POP, C3, RNG core and historical archive
implementation bodies were not opened. Their contracts are attributed to root's
source-qualified messages and the approved C3 design/native assessment.

## Source-confirmed obstacle

Existing replay APIs do preserve the concrete receiver object when used normally,
but cannot satisfy the requested staged native composition unchanged.

`ReplayCustody._issue_replay` at contract:531 associates each opaque
`PreparedReplay` with its actual issuer registry, receiver revision and a core
currentness token. `_validate_replay` at542 checks the revision and calls actual
`process_rng_domain().validate_current`. All three `load_prepared` implementations
use this check before publishing. The imported core's exact generation/revision
rules are supplier facts, not newly inspected here: BANK's intervening operations
can stale that earlier token. Moving the handle between owners, refreshing its
token or ignoring that refusal is not a valid integration.

There is a second concrete issue: all three current installers allocate and clone
again after looking up their material, before `_validate_replay` and publication.
Flat clones every storage tensor and merges archives (flat:781); PER also copies
priority/unit arrays, builds the reverse ID map and clones the sampler (PER:1267);
sequential clones the episode deque, policy and priority state (sequential:832).
Therefore merely postponing an ordinary `prepare_serialized`/`load_prepared` pair
until the finalizer retains stable owner identity but does **not** meet the agreed
pre-materialization-before-BANK-cut requirement. It leaves substantive allocation
and validation after native publication. Do not describe that workaround as the
approved staged implementation.

There is no current public safe-owner-clone or staged-data transfer API in these
four bodies. `_clone_sampler`/`_clone_rng` are data utilities, not owner cloning.
Owner custody includes a lock, registered participant, healthy/revision state and
weak prepared-capability registry. A generic dictionary transplant is not safe.

## Smallest additive route

Add an explicit native **data staging** route, separate from `PreparedReplay`.
Suggested names below are proposed interfaces, not existing methods:

- `replay.stage_native_restore(state, *, expected_obs_dim, parent_plan, lineage)`
  returns an opaque owner-issued `StagedReplayData` reference.
- `replay.install_native_restore(data, *, parent_plan, attempt, restored, lineage)`
  installs the already-owned material during the genuine C3 fixed finalizer.

The first object is deliberately **not installation authority or an old RNG
token**. It owns a complete private, validated publication payload. It must have
no public mutable tensor/array/policy accessor. It records the actual replay
issuer, revision and receiving configuration, genuine native parent-plan identity,
and creating PID/thread; it is one-use and cannot be copied/serialized. The real
POP/native plan must authenticate its own exact issued plan and the matching
child-data association. An arbitrary object passed twice, caller boolean or no-op
callback does not establish parent-plan authority. That exact parent verifier is
still a native-consumer API to implement/source-review; this supplier has not
inspected such an implementation.

Staging executes actual replay prepare/device custody, fully validates and owns
the input, merges receiving archives, allocates the complete destination payload,
and returns it only after genuine completion succeeds. It does **not** call
`_issue_replay` or promise that a currentness token will survive subsequent BANK
work. All staging happens before the selected BANK/runtime token-sensitive cut.

At installation, source must authenticate the exact data record, its genuine
parent-plan association and one-use state, current healthy receiver/revision and
receiving geometry. It must also authenticate the actual C3 finalizer permission.
C's owner and root have agreed the proposed source-owned hook:

`townlet.environment.restore_attempt.validate_restore_finalizer(attempt=..., owner=replay, restored=...) -> None`

That hook is to check the issued attempt registry/PID/thread/live lexical scope,
actual `FINALIZING` stage and one-use callback identity, exact installed world/
release pair and pinned registered role owners. It performs no admission, RNG
operation, export or fresh-bound A check after world installation. It is not yet
an implementation result. Replay's staged data and parent plan remain independently
one-use/revision-bound; the hook alone does not verify their semantic contents.

Publication then occurs under a **new genuine current replay install invocation**
and owner exclusion. It transfers the private preallocated payload by assignments;
there is no old `PreparedReplay` to refresh or bypass. Existing prepare/load APIs
and all of their core-token refusal behavior remain unchanged. This is an explicit
new source-authorized native route, not a fallback when ordinary installation
fails. Materialized data can survive unrelated core operations because it carried
no installation authority; authority is earned only by the actual finalizer and
current install invocation. An independently reviewed implementation must verify
this separation, not simply rename a stale prepared handle.

Keep the real replay object, `_replay_participant`, lock and custody registries.
Consume the native data record once and advance owner revision on publication.
Preserve actual quarantine on publication/completion failure; C must terminally
fence partial/uncertain composed restore. No rollback, silent retry, successful
receipt or replacement owner follows a failed publication.

## Exact staged publication contents

Reuse existing validation/materialization semantics; prepare the following final
assignment payloads **before** BANK preparation, including work currently delayed
until `load_prepared`:

| Kind | Publication payload to own in advance |
| --- | --- |
| Flat | Every `_STORAGE_FIELDS` tensor, size/position/wrapped status, action dimension/legality mode, complete merged archive tuple. Preserve chronological-row normalization in `serialize`. |
| PER | Every storage tensor, beta/priorities/max priority, position/size, action/legality metadata, unit IDs/next ID/reverse ID map, cloned sampler including RNG state and sampling identity, complete merged archives. Preserve physical ring/priority alignment. |
| Sequential, including prioritized | Owned episode deque/fragments and transition count; configured/action/legality identity; deep-owned replay options; next episode/transition IDs; merged archives; complete priority state, domains, support, beta/tick/horizon/origin and cloned RNG. Preserve configured uniform-versus-prioritized identity. |

Flat `_materialize_serialized` already validates owned transport again and
allocates target-capacity tensors. PER does the same plus owned priority/sampler
material. Sequential repeats transport validation and captured-compatibility
checks, owns fragments/options/priority and verifies supported domains. The new
route should use these producer responsibilities, not duplicate weaker parsing.
It additionally moves the current install-time clones/map construction/archive
merge into the staged private publication payload. Because consumers never receive
mutable material and publication consumes it, a second install-time clone is not
needed to preserve input ownership.

Archive handling is not simple assignment of incoming archives. Flat/PER retain
receiver-plus-incoming archives through `_merge_archives`; sequential additionally
checks observation width and contradictory content under one domain identity.
Retain these semantics and the owner's approved inspection-only history policy.
No historical training fallback is introduced.

Device planning must explicitly inventory **both** retained native staged data and
current owner material, including archive tensors/source devices. Current
`_device_plan(admitted=True)` enumerates `_replay_prepared`, not the proposed data
registry, so it must be extended for the new route. Use real source-owned prepare/
install device planning and completion; do not hide GPU copies behind a CPU-only
classification. No CUDA qualification was performed here.

Uniform flat sampling uses `torch.randperm` at flat:383 and its serialized state
has no dedicated sampler RNG field. PER serializes `sampling_rng`; prioritized
sequential serializes full priority RNG/tick state. The actual native parent must
also cover whatever process/domain RNG continuity uniform sampling requires.
This is an explicit integration check, not a claim that the unseen parent/core
currently omits that state.

## Finite implementation and evidence boundary

Suggested measured packets: (1) shared data-record/custody and flat publication
route; (2) PER route; (3) sequential route; each includes focused tests and a
source-qualified supplier capsule for bodies outside its <=5/5000 inventory.
This supplier already uses 4,937 lines and is not an implementation owner.
No source extraction/consolidation is proposed.

Required focused proof is finite: malformed data refuses before any live mutation;
caller input cannot alias staged or installed values; an actual intervening BANK
prepare/install does not turn data into a stale-token bypass; genuine finalizer
publication preserves owner/participant identity and complete payload; changed
receiver/parent/attempt, foreign/copied/consumed plans and calls outside finalizer
refuse; archives and sampler/recurrent continuation remain exact; actual publish/
completion failure is truthful and terminal in the parent; ordinary PreparedReplay
stale-token rejection and lawful standalone behavior remain intact.

These child controls do not replace the original runner artifact/restore/next-real-
update acceptance. The C3 hook and native parent-plan association are agreed or
proposed source interfaces, not implemented/qualified facts in this capsule.
