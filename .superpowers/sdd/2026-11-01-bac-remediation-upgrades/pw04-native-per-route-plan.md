# PW04 native prioritized replay: finite route plan

Planning only, 2026-11-14. Production and tests remain untouched pending root's
explicit release after NR-1/R170. No imports, tests, Git, branches, worktrees,
source copies or runtime execution by this owner. Root owns integration/runtime.

## Counted source boundary

Counted before source reads: prioritized_replay_buffer.py1310,
replay_contract.py949, flat replay_buffer.py860, genuine parent fixture
test_parent_intrinsic_handoff.py900 =4019 lines/four bodies. Reserve one NEW
test_native_prioritized_replay_data.py <=400 lines; implementation growth <=581
keeps five whole bodies <=5000. Only PER and the new test are implementation
write candidates. Contract/flat/fixture are references, never edit targets.

Read AGENTS.md and native flat, POP and C API prose. Shared contracts already
provide genuine receiving replay association and exact finalizer authentication;
no shared-contract change is currently required. Future discovered shared needs
must be reported to root instead of edited here.

## Required API and ownership

Add the exact supported sibling signatures:

* stage_native_restore(state, *, expected_obs_dim: int, parent_plan: object,
  lineage: RNGOperation | None) -> StagedReplayData.
* install_native_restore(data: object, *, parent_plan: object, attempt: object,
  restored: object, lineage: RNGOperation | None) -> None.

The shared opaque data registry binds receiving owner, replay revision,
capacity/device, parent weak identity, PID/thread. It carries no currentness token.
Keep ordinary PreparedReplay installation unchanged. Native callers must use the
actual issued POP plan and actual source-entered C fixed finalizer. No arbitrary
callback, fabricated authority, private poison reset or compatibility route.

Use the existing complete PER validation/materialization to produce owned
_PrioritizedRestoreCandidate. It already preserves beta, max priority, physical
ring counters, priority array, monotonic unit IDs/counter, sampler configuration
and private Generator state, tensors, masks, component-presence flags and merged
historical archives. A small PER-private native payload holds that candidate and
the precomputed unit-ID-to-slot dictionary. This dictionary must be constructed
BEFORE BANK/publication; current ordinary load_prepared builds it at install and
therefore cannot be reused as the native installer.

Extend PER _replay_children to traverse the native payload; shared admitted
device inventory already includes all retained native records. Map the new stage
route to the existing prepare_serialized transport inventory so destination and
source device enrollment occurs before touching tensors. Materialize under the
actual replay prepare operation; revalidate the genuine parent inside it; issue
data only after complete payload construction and return only after real prepare
completion. Recheck exact PER configuration where necessary without introducing
another shared policy surface.

Installation follows the qualified flat source structure: initial owner operation
checks data and genuine C finalizer before opening a device operation; a NEW real
install invocation repeats both checks and verifies payload type. Publication
consumes the native record first, then assigns preallocated storage, priorities,
IDs/reverse map, sampler, counters, masks/action geometry and archives on the SAME
replay owner. No cloning, decoding, RNG restoration from caller data, allocation
of reverse maps or archive merging in publication. Shared quarantine handles
publication failure and genuine invocation completion uncertainty. POP plan
remains issued until sibling children and outer RNG complete.

## Finite RED and acceptance work after release

New tests use genuine make_parent(compiled) and actual configured PER ownership
from authored compiled training options, before bind. Do not replace a bound
owner. Root/source supplier must provide the exact fixture configuration recipe
within this read budget; the fixture forwards selected.training.bac_options to
resolved.options.replay. Source and target remain separate real parent fixtures.

First bounded RED cases reach missing APIs via: unissued parent refusal; actual
INITIAL source checkpoint -> target.bind -> real POP native plan -> defensive
native_replay_restore_state -> stage; and authentic data refused without genuine
C finalizer. Additional controls cover fabricated/native-versus-PreparedReplay
data, foreign owner/parent/thread, lawful receiver revision change, malformed
priorities/IDs/RNG/masks, and owned transport mutation after staging. Test budgets
must prioritize cases that exercise distinct contracts rather than mirror code.

Root observes RED before production writes. Root's real runner witness must then
select supported PER through actual configuration, save a nonempty trained native
artifact, restore to a fresh genuine receiver, and perform the NEXT real learner
update. Compare saved/restored priorities, beta, ring/ID counters, masks/component
presence, historical archives and private sampling state; sample equivalence must
include IDs/receipt/weights and subsequent priority update. Assert retained owner
identities and no alias to artifact/transport. Actual C success, one-use replay
data, stale/foreign/failed callback controls, device completion and terminal
publication failure belong to real composition evidence, not fake permission
fixtures. Root alone runs tests/type checks and retains exact candidate custody.

No pass, supported-route completion, next-learning proof, CUDA qualification or
package closure is claimed by this plan. Same signatures/choreography have been
supplied to the sequential route owner for coordination.

## Bounded RED handoff after R170 release

Root released tests only after reporting R170 runtime/custody completion.
New test_native_prioritized_replay_data.py is198 lines, SHA256
5c3761caaf614a83e7cebd4e9ff9ef8ad19fa0cadf0451a277a1681f3a1a4bff.
Whole-body total4217/five; production remains1310 and untouched. No tests/imports
were executed here. Thirteen intended cases await root RED observation.

Root supplied genuine fixture configuration: copy config DATA from
configs/test/bac_remediation/feedforward into pytest temporary storage; update
brain.yaml replay prioritized=True, priority_alpha=0.6, priority_beta=0.4,
priority_beta_annealing=True; compile with townlet.universe.compiler.UniverseCompiler
at primary_level L0_0_minimal, use_cache=False. make_parent constructs actual PER
through its existing brain/training path. No bound owner substitution occurs.

Cases cover public staging/refusal and genuine-plan ownership/currentness;
private staged-payload inspection is solely a root-approved assertion oracle.
The proposed native payload exposes its internal candidate as material, allowing
empty INITIAL priority/ID/private-sampler no-alias assertions without inventing
publication authority. Nonempty tensor/mask/history and actual native-finalizer
continuation through next learning remain explicit root integration obligations.

## Production handoff after genuine R171 RED

Root reported R171 causal test_native_per_stages_real_parent_without_publication
reached the missing stage_native_restore, collection39 passed and failed-run
custody passed3 processes at tree b1500cf0cf3f933b514a3af2fdd0752182ea450c.
Root then released this bounded implementation. This owner executed no tests,
imports or runtime checks and made no Git/worktree/copy changes.

PER now1370 lines SHA256
673c2ffb240604c3134836c8742394f978e73f195eb73750410a817452ef2b73;
current root-integrated test196 lines SHA256
e84542160183338fa48d386ac3ac26d841611c94d9f358de937b8c2730e6d7fd.
Five bodies4275 total, WRITE-FROZEN for root verification. Shared contract,
flat replay and parent fixture unchanged by this owner.

Exact APIs are stage_native_restore(state, *, expected_obs_dim: int,
parent_plan: object, lineage: RNGOperation | None) -> StagedReplayData and
install_native_restore(data: object, *, parent_plan: object, attempt: object,
restored: object, lineage: RNGOperation | None) -> None.

Implementation follows the plan: source-owned material, precomputed reverse ID
map and PER configuration pin in _NativePrioritizedPayload; traversal of this
payload in device inventory; genuine prepare transport selection, owned complete
candidate, return after prepare completion; fresh actual install operation with
repeated POP/C authentication; assignment-only publication through shared one-use
consumption/quarantine. No currentness token is retained. Existing ordinary
restore/sampling behavior is unchanged.

Independent review should verify source-owned payload no-alias guarantees,
all retained staged tensors in actual admitted device inventory, repeated
authentication under the C finalizer, and allocation-free field publication.
Actual finalizer success, consumed reuse, publication/completion failure,
nonempty masks/component history, exact sample/priority-update continuation,
real next learner update and CUDA completion remain root-owned proof obligations.
No passing test or package-closure claim follows from this implementation handoff.
