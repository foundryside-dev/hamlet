# APP-C1 bounded fixture API supplier

2026-11-14. Source inspection only for sole APP-C1 writer
`bac_parent_c1_implementation`. No imports, execution probes, tests, application
edits or Git writes. Existing checkout only. Exactly four allowed source bodies,
4716 lines, measured and hashed before reading; no fifth source body admitted.
References E/H/P/S below identify these exact sources relative to `/workspace/hamlet`.

| Ref | Source | Lines | SHA256 |
| --- | --- | ---: | --- |
| E | src/townlet/environment/vectorized_env.py | 2889 | e5a447b0e3d45c861e2fd5e3adcde799f80581053a9512f10af1b365509d8409 |
| H | tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py | 791 | 6cea1235f8dc149aceb5ca7352b855ac001a8bfb1e758a9c3b116f3654f2acb0 |
| P | tests/test_townlet/regressions/bac/test_initial_participation_population.py | 773 | 9186a953f79cd8b4cf2a4fea47c6ff24197ae53764b6d2e6fa33267f78000bd5 |
| S | src/townlet/training/state.py | 263 | a6f22b0b26ca6422e6a0710f9268386e8d2b7162e1a5e9a43a2decdea4c9d3e3 |

Read repository AGENTS.md, SHA256
`7cf711206c00682b317064a2ff0f49eb78ca03d899642af8be82951c12970c93`;
final `T18e-R0-PARENT-INTEGRATION-PROPOSAL-V2.md`, SHA256
`45801f6d05a751b4fa7458278f2c781290c094eafa267a65479efb34d9c427c6`;
and exact existing `T18e-R0-POP-FIXTURE-CURRENT-API.md`, SHA256
`41c31db60be7c2d0f7f65d581bbb3587ca5809a593d58ab967639e46c51cb5b8`.
The root-handoff document was read to locate the exact final proposal. This
capsule adds source facts; it does not independently qualify runtime behavior.

## Actual ENV return and earned service identities

`rig = make_parent(compiled, family, scope)` then `rig.enter()` supplies the real
ENV, POP, runtime, BANK, accepted episode, genuine POP activation and genuine
runtime/BANK activation (H43–237). `rig.enter()` executes setup before a proposed
active controller invocation; these fixtures contain no RNG controller enrollment
or retained-operation helper. Its accepted roster is IDS, batch zero by default,
sequences `(1,) * 8` on the first cycle (H296–302). No fabricated token is needed.

The concrete component call sequence supported by the source signatures is:

```python
candidate = rig.candidate()
prepared = rig.population.prepare_vector_step(**candidate)
observations, rewards, dones, info = rig.env.step(
    candidate["actions"], vector_step=prepared
)
handoff = info["intrinsic_transition"]
receipts = rig.runtime.admit_and_service(
    context=handoff.context,
    stamp=handoff.stamp,
    accepted=handoff.accepted,
)
```

This is the proposal's component sequence, to run under its genuine registered
controller invocation and explicit runtime/BANK binding once implemented. It is
not a source-demonstrated full POP step or completion sequence. Do NOT separately
claim `prepared` before ENV.step: ENV itself calls the actual claim callback once
(E1318). H327–332 explicitly establish that a direct claim consumes the handle
and is neither physics nor service. `candidate()` uses genuine accepted identity,
IDS, cloned POP current observation, first legal action from real ENV masks, and
cloned current activity (H136–144). For an all-active enter, these are real legal
actions without invoking the learner or synthesizing replay rows.

ENV.step's signature is `(actions, depletion_multiplier=1.0, *, vector_step)`
and its result is precisely a four-tuple, not BatchedAgentState (E1277–1285,
E1480). Observation shape is `[num_agents, observation_dim]`; reward and bool
done shapes are `[num_agents]`. Returned `dones` is `self.dones` itself, not an
owned clone. `info` contains the handoff, cloned successor masks, active/newly
terminal/newly retired/count/position readings, successful interactions, reward
components, intrinsic weight, and effect spawn refusals (E1464–1477).

ENV makes its context at E1409 with cloned predecessor/actions/activity, a real
successor observation, and the integer returned by POP's claim callback. It calls
`runtime.prepare_step_stamp(accepted=accepted, world_ids=self.world_ids,
active_on_entry=active_on_entry, vector_tick=vector_tick)` at E1416, then creates
`IntrinsicStepHandoff(intrinsic_context, intrinsic_stamp, accepted)` at E1422.
The reward calculator receives those SAME context/stamp/accepted objects.
The final observation is read again after retirement and next-hour publication;
do not assume object identity with `handoff.context.successor` (E1412 vs E1449).
H409–435 asserts value equality for the actual fixture and exact handoff identity
for both runtime.reward and admit_and_service. It also asserts `update_stats=True`
for the actual reward call. `observe_runtime(monkeypatch, rig)` (H265–281) delegates
actual reward/service calls and records `(kwargs, result)`; it creates no authority.

ENV.step does not directly call admit_and_service, replay, Q, optimizer, or
curriculum. It DOES call the actual POP claim callback, runtime.prepare_step_stamp,
the action executor, VTC runner, registry, reward calculator, observation encoder,
mask builder, and configured effects/items/VFS machinery. E1559 returns an actual
`vfs_randomness.instant(...)`; runner/evaluator calls receive those draws. No
`lineage`, `domain.operation`, invocation, or RNG participant enrollment appears
in this ENV source. Other called bodies are opaque here. Therefore this supplier
cannot certify that runtime is the ONLY standalone RNG participant reached by
ENV.step under a controller operation. In particular, external calculator,
executor, manager, VFS and POP claim implementations must not be inferred pure,
nonparticipating, or already migrated from this call graph. The all-active fixture
source assertions are not a current execution result under the new binding.

## Completion and actual committed-batch callback

The factory passes `validate_committed_batch` whose body delegates exactly to
`owner["population"].validate_committed_batch(batch_episode=batch_episode,
outcomes=outcomes)` (H195–196, H208). Runtime owns the callback invocation contract;
its body was deliberately not read by this supplier. Neither factory callback
accepts a synthetic readiness flag or replaces the POP validator.

`prepare_close(rig)` (P118–141) first calls actual `pop.flush_episode(lane,
reason="budget")` for EVERY lane, then reads `events = pop.completed_outcomes`.
It derives participants from these events, canonical content using each actual
`freeze_lane_outcome`, prepares curriculum, calls runtime.prepare_completion,
then ENV.prepare_episode_close with the BANK's actual prepared receipt. It returns
`(closing, curriculum, bank, events, content)`. It does NOT commit POP outcomes.

`close(rig, prepared, release=...)` has this exact effect order (P144–169):

1. ENV.freeze_episode_close(closing).
2. Actual curriculum.commit_prepared_episode_outcomes(curriculum).
3. `retirement = runtime.commit_completion(prepared=bank)`.
4. `pop.commit_episode_outcomes(events)` — this is the fixture's genuine POP
   commitment entry and the relevant delegated runtime.commit_batch_episode seam.
5. pop.sync_exploration_metrics; compare actual epsilon tensor.
6. Retain cooperative effect issuers for actual owners and issue receipts AFTER
   the effects above; ENV.close_episode with actual retirement; obtain boundary
   release; optionally install it. Return the actual retirement receipt.

`ParentFixture.complete()` (H93–134) performs the analogous complete sequence,
always installs release, and returns actual outcomes. The existing callback
failure test H656–690 earns outcomes using real POP.step_population, flushes all
lanes, then transparently wraps runtime.commit_batch_episode while calling actual
pop.commit_episode_outcomes. Its assertions distinguish pending commitment and
completed-batch ledger advancement. This is a demonstrated source fixture route,
not newly executed evidence.

Every positive normal-close usage in H/P first executes POP.step_population.
The direct component ENV step above advances ENV and claims a POP vector step,
but its body does not run POP post-step accounting or completion publication.
No public fixture helper completes that pending POP vector from the returned
tuple. P463–472 explicitly demonstrates that a prepared pending vector blocks
flush_episode; after direct claim it remains distinct from actual POP advancement.
Thus direct ENV step + prepare_close is NOT established as a healthy completion
route; do not repair it by private POP writes or fake outcomes. The still-unmigrated
POP path or a separately sourced genuine completion API remains a prerequisite
for the positive completion/committed-batch tests supplied here.

Zero-step clarification requested by the writer: `prepare_close` has no explicit
zero-step guard in its helper body, but the behavior of POP.flush_episode and
POP.validate_committed_batch at zero steps is opaque here. No H/P example proves
zero-step normal closure or empty committed-batch acceptance. E2654–2656 computes
actual participants exclusively from positive ENV step_counts and refuses if that
set differs from supplied participants. Hence positive budget outcomes after zero
physical steps would not provide valid ENV closure. Empty-participation acceptance
by other children is not implied. The actual whole-retirement fixture P747–773
uses genuine POP/runtime empty proofs and ENV abandonment; it does not close,
advance completed-batch cadence, or issue normal release. Root's retained POP
source can resolve zero-step flush/validator behavior without this supplier
reading a fifth body.

## BatchedAgentState and private initialization

The actual class is `townlet.training.state.BatchedAgentState` (S188), with
constructor (S209–220):

```python
BatchedAgentState(
    observations, actions, rewards, dones, epsilons,
    intrinsic_rewards, survival_times, device, info=None,
)
```

All first eight arguments are required; each tensor is batched, observations is
two-dimensional, dones is bool, and the declared device is torch.device. `info`
defaults to a new empty dictionary. Constructor simply retains passed references
and does no validation, cloning, readiness publication, or capability issuance
(S228–236). `.batch_size` reads observations.shape[0]. This DTO cannot stand in for
a POP-completed transition or accepted authority.

A data-only DTO can be assembled from an ACTUALLY RETURNED ENV tuple: observations,
rewards, dones and info from the tuple; actions from `handoff.context.actions`;
survival_times from `info["step_counts"]`; epsilons from actual
`runtime.epsilon_tensor(batch_size=observations.shape[0], device=observations.device)`;
intrinsic_rewards from the actual delegated reward result captured by
observe_runtime (`calls["reward"][-1][1].raw`), whose use as state intrinsic reward
is asserted at H435; and device from observations.device. This is a source-derived
data mapping, NOT an existing H/P constructor invocation or current selector test.
It leaves all live POP state untouched. Retain actual reward observation rather
than equating raw intrinsic reward with the composed intrinsic component.

Neither H nor P imports or constructs BatchedAgentState directly. Their runtime
selector observer delegates `original_select(values, state, masks)` supplied by
real POP (P261–266); A-only source assertions establish shapes `(1, action_dim)`,
`(1, observation_dim)`, `(1, action_dim)` after real POP selection. Their public
selector helper calls real POP.select_greedy_actions or
POP.select_epsilon_greedy_actions (P75–76). No source-local positive pre-step DTO
construction, direct Q-call contract, or new controller enrollment API is supplied
by these fixtures. The writer-owned runtime body must establish which DTO fields
its selector consumes; missing current observations/values are not permission to
fabricate readiness or overwrite live POP state.

No H/P call to runtime.prepare_private_initialization exists. `initialization=None`
occurs only on POP.prepare_checkpoint_state for initial transport. Consequently
this bounded inspection establishes NO runtime private-initialization kwargs,
state schema, or positive private-init fixture route. These facts belong to the
writer-owned runtime body or the separately supplied BANK fixture contract.
