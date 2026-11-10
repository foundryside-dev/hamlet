# T18e genuine model raw2 fixture facts

READONLY finite extraction, 2026-11-10. Only this ignored prose was written. Exactly five whole frozen implementation sources were inspected, metadata first, 3890 total lines <=5000. No sixth body, helper/test body, RP/ENV/parent body, runtime/import/probe/compile/test, introspection, git/index action, source copy, branch/worktree/checkout or subagent. Truncated displays were completed with bounded source reads. No execution or successful test is claimed. Current runtime/checkpoint contracts and T18e-COMPOSER-SCALE-API / T18e-PARENT-FIXTURE-FACTS are attributed public dependencies.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py |834|0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d|
| src/townlet/exploration/icm.py |481|eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f|
| src/townlet/exploration/provider_factory.py |153|7ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0|
| src/townlet/exploration/curiosity_checkpoint.py |1138|4de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a|
| src/townlet/exploration/scoped_curiosity.py |1284|294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f|

## Smallest clean control: actual ICM initial model

Use a genuine ordinary newly constructed same-scope runtime selected for `icm`, with ordinary BANK origin None. Install explicit initial native model values through public runtime export/prepare/install **before reset/accepted activation/first reward**. This is controlled model initialization, not claimed learned trajectory or fabricated service history. It needs no RMS/history calibration, fake provider, patched reward method, mocked raw, replacement composer or child escape.

Actual geometry is N=8 for the unchanged real pack. Obtain D from actual selected compiled TokenSpec and A from actual selected compiled action metadata, consistently with real ENV; use actual roster/seed/device and real accepted-step predecessor/actions/successor context. No synthetic D3/A2 fixture. Let F/H be selected actual positive `feature_dim`/`hidden_dim`; there is no requirement to reduce them. The construction uses three genuine two-Linear/ReLU modules (icm.py107-112).

Only change these eight native tensor values, retaining exported tensor layout/device/dtype and key/container structure. All are finite dense float32 tensors in the ICM checkpoint's owned CPU native representation (icm.py31-43,291-315):

| Native path | Exact shape | Explicit value |
| --- | --- | --- |
| encoder['0.weight'] |[H,D]|zero|
| encoder['0.bias'] |[H]|zero|
| encoder['2.weight'] |[F,H]|zero|
| encoder['2.bias'] |[F]|zero|
| forward_model['0.weight'] |[H,F+A]|zero|
| forward_model['0.bias'] |[H]|zero|
| forward_model['2.weight'] |[F,H]|zero|
| forward_model['2.bias'] |[F]|2.0 in every element|

`encoder` and `forward_model` are actual native top-level keys. The Sequential state keys are exactly `0.weight,0.bias,2.weight,2.bias`, not `net.*`, `model.*` or a guessed wrapper. Leave `inverse_model` unchanged; its genuine shape is 0.weight[H,2F],0.bias[H],2.weight[A,H],2.bias[A]. It participates in training, not novelty computation. Preserve its exact exported keys too.

Actual reward formula (icm.py169-182):

```
features = encoder(real_predecessor[active])
target = encoder(real_successor[active])
inputs = cat(features, one_hot(real_actions[active], A))
raw[active] = 0.5 * mean((forward_model(inputs) - target)**2, dim=1)
```

The initialized encoder yields zero, forward yields 2 in every feature, giving `0.5*mean(4)=2` for every eligible row regardless of genuine observations/actions. Ineligible rows are exact0. The coefficient is **0.5**, so forward bias sqrt(2) would be wrong. With finite actual observations, zero/2 binary float32 values produce exact2; an ordinary float32 assertion tolerance is acceptable for the end-to-end component arithmetic. This establishes a genuine executed model reward under explicit initial weights when the owner runs it; no execution happened here.

`update_stats=True` is valid and should remain the normal rollout setting. ICM only checks its boolean type; reward does not change stats, model, optimizer, queue, counters or service clocks. There is no reward RMS in this family. Learning/admission is a separate subsequent actual `admit_and_service` phase (icm.py190-272; BANK609 onward). Reward must precede service (BANK622). Service may legitimately train after capture; do not reset/undo it to preserve the first reward. Existing selected batch size suffices. If deliberately selecting a no-update first service, author actual training_batch_size>8 and capacity>=batch size through the real resolver before construction; never alter a live ledger or suppress service.

## Exact public owned installation route

Use only facade operations from the qualified CURRENT-EXPLORATION-RUNTIME-CONTRACT (wave34); the runtime owns BANK privately. The current facade envelope is exactly `schema,policy,bank,selector,cadence`, schema `exploration-runtime-state-v1`. The actual BANK envelope is `curiosity-bank-state-v2` (BANK955-1036). These are native paths in **owned export data**, not object attribute escape paths:

- `saved = runtime.checkpoint_state()` returns owned current data.
- Shared ICM native: `saved['bank']['shared_backend']['native']`.
- Per-world ICM native: for each actual ID's record in `saved['bank']['worlds']`, `record['backend']['backend']`. Match the `record['world_id']` string, never infer ownership from row position. Set all eight owners if expecting all eight eligible raw values2.
- Shared gradients remain `saved['bank']['shared_backend']['gradients']`; private gradients remain `record['gradients']`. Leave both unchanged.
- Modify only the eight tensor contents above inside those native payloads.
- `prepared = runtime.prepare_restore(state=saved, mode='initial', accepted=None, parent_restore=None, validate_parent_restore=None)`.
- `runtime.install_restore(prepared=prepared)` immediately, with no intervening runtime action/export/snapshot/begin or other owner mutation.

The runtime constructor's separately required `validate_parent_cadence` callback still authenticates real initial parent cadence even when the BANK parent pair is None/None. It must already be a genuine parent-owned closure, not a no-op added for this control. If the integration requires actual INITIAL parent correlation, provide its genuine preparation/validator pair instead of None/None. The existing initial mode explicitly supports either pair (CP227-241; public runtime contract). No new reset/system feature is needed. No direct BANK access, model attribute access, `__dict__`, module introspection or callback child escape is needed.

Then perform the ordinary genuine ENV reset/activation/accepted-step flow under the already qualified owner APIs. Registration retains the actual BANK identity delivered to `issuer_factory(owner)`; the runtime facade is not that ENV curiosity owner. Installation occurs while BANK is initial and no actual accepted token exists; never fabricate a token to load initial state. After installation begin with the actual ENV-issued reset token, prepare real stamp, call actual runtime reward using actual context, and capture returned `.raw`/`.scales`. Restore is fixture setup; it does not itself establish ENV acceptance or parent-global completion.

BANK prepare_restore1160-1229 validates portable state, records, then actual native validator/load on off-side genuine providers; ICM validate_state delegates to prepare_state383, exact keys/shapes/dtypes/finiteness are enforced317-331. Shared loads candidate and checks exact native roundtrip; private passes exact owned native/RNG envelope through actual owner prepare/install, then attaches exported gradients. Public facade wraps opaque BANK handle plus selector/cadence preparation. Installation checks destination identity/revision/single use. Export/snapshot advances revision, so do not use one as a freshness check between prepare and install. The actual implementation is source-backed here for BANK/ICM/CP; outer facade details are supplied public contract, not an RP body inspection.

## Metadata retained truthfully

Start with an actual fresh ordinary export; do not construct a partial dictionary. Preserve **every field except the eight chosen model tensors**. In native ICM these required keys remain: `schema,policy,policy_identity,config,encoder,inverse_model,forward_model,optimizer,epsilon,epsilon_decay,epsilon_min,pending,counters,last_loss,service_clock_unit,service_position,ordinary_updates_at_position` (icm.py291).

Keep complete actual resolved policy, identity, config D/A/F/H/LR/inverse/forward weights/batch/capacity/source-device, epsilon schedule and inverse weights. Fresh actual optimizer state is empty, its exact Adam groups remain unchanged; model initialization does not create successful optimizer steps. Fresh `pending=[]`, all five counters exact int0, `last_loss=0.0`, budget int0, service position None shared / exact int0 private. Preserve exported types instead of rewriting them. Keep fresh gradients None at all real parameter paths for encoder/inverse_model/forward_model. Keep private envelope schema/healthy/native/RNG exactly exported apart from chosen native tensors; initialization RNG continuation remains the truthful after-construction stream. Do not invent/draw/rewind seeds or record training to justify controlled initialization.

Preserve outer schema/policy/selector/cadence. Preserve BANK descriptor, seed, world ordering/IDs, source_device, curiosity_epoch0, initialization_origin=None, bank_phase='initial', dispatch_identity=None, step=None, completion=None; every initial world cursor is exact zero/false/None and phase_cache empty. Shared records retain backend/gradients None; private shared_backend remains None. No completion/history/survival/pending rows are manufactured. Native validation checks exact Adam state/update count and row conservation, so changing counts without actual work would rightly fail.

Select `policy.initial_intrinsic_weight == 0.5` through the parent author's owned qualified RP resolver before constructing this runtime. BANK573 chooses exactly that field for ICM; neither inverse_weight nor forward_weight is the runtime reward scale. Constructor parameters must equal the complete actual `policy.provider_parameters` mapping (icm.py75-95; factory96-112). Positive F/H/batch/capacity and positive LR are required; capacity>=batch; inverse/forward training weights nonnegative. The supplied public runtime contract qualifies the selected initial-scale field, but does not give an authored resolver keyword spelling or prove any uninspected helper's default equals.5. Do not guess either; parent owns RP. No post-resolution policy mutation or altered identity is part of this control.

Use independently real authored drive base.25 and compiled modifier2 from T18e-COMPOSER-SCALE-API. Actual eligible captured raw2/scales.5 enter the real composer separately. Expected nonterminal effective intrinsic is `2*.5*.25*2=.5`; modifier-only weight is2; historical intrinsic_raw diagnostic is raw*base=.5; provider_intrinsic_raw is2; runtime_intrinsic_scale is.5. Terminal/inactive ENV behavior remains the accepted-step owner's actual contract. Constant extrinsic1 and qualified real shaping.1 yield1.6 before any separately owned retirement effect. These expected values are not a claim of an executed integration test.

## Explicit refusals and finite controls

1. Wrong model key, shape, dtype, NaN/Inf fails native geometry/type/value validation; missing/extra native fields fail complete-schema validation. Preserve other model/optimizer/RNG fields.
2. Foreign/stale/consumed prepare handles fail; an extra export/snapshot after prepare deliberately invalidates freshness. Prepare/install belongs to one runtime receiver.
3. Wrong policy/descriptor/scale, seed, world membership, phase, device or actual service unit fails strict ordinary restore. Setting policy initial weight only inside transported data cannot change selected policy.
4. **Origin-bearing unstarted private state is different:** CP417 `validate_boundary_template` requires exact complete fresh factory template or transformed archived clone template when ordinary restoring origin-bearing initial/private_initialized data. Arbitrarily editing those native tensors fails `unstarted native state contradicts selected initialization`. This control deliberately uses ordinary same-scope initial origin=None; that restriction does not apply. No fake source archive or alternate initialization label should be introduced.
5. If a test specifically requires the explicit shared-to-private initialization route, the smallest valid controlled route is a genuine ordinary shared INITIAL runtime with the same controlled ICM native tensors installed first, then export its complete current runtime and use real `clone_learned_archive_pending` to an untouched authored private receiver under existing source/target/cadence checks. Despite its API name, preserve truthful source zero training counters/empty tails; claim controlled initial-model inheritance, not learning. `fresh_private` intentionally discards source model control and cannot prove raw2. Actual clone preparation creates its own truthful fresh private RNG and origin. This is an existing API, not needed for the simpler ordinary control.
6. Capture first genuine reward before actual service; repeat same exact event/mode uses BANK reward cache and does not recompute. Changed context or reward mode refuses. ICM regular service remains once, including zero-scale controls. For scale0 or1 controls construct a separate genuine resolved runtime/policy; do not rewrite reward output or cached scale.

## RND distinction

RND is genuine but less simple for this particular **normal rollout stats-updating** raw2 control. Native network tensor keys are `net.0.weight/bias`, `net.2.weight/bias`, `net.4.weight/bias`, with shapes [256,D]/[256], [128,256]/[128], [E,128]/[E] for both fixed_network and predictor_network (rnd.py113-128). Native keys include fixed_network,predictor_network,optimizer,epsilon/epsilon_min/epsilon_decay,obs_dim,embed_dim,reward_rms_mean/var/count,schema,predictor_service. Its normalized provider output is MSE / (sqrt(current RMS var)+1e-8), **without ICM's half coefficient**. With update_stats=True, the real batch updates RMS before division (268-306). Fresh honest RMS is mean0,var1,count1e-4; constant2 prediction delta therefore gives MSE4 but not provider raw4 or2 after this first update. Do not overwrite RMS history or suppress update_stats to force the number. RND service does not update reward normalization; reward cache prevents a duplicate real stats update for the same event. A once-updating RND calibration could be separately derived, but adds unnecessary statistical/numerical dependency. Choose ICM for this named constant-raw fixture; all original RND/adaptive provider/statistics coverage remains separately owed.

## Narrow followup: shared ICM clock is the context vector tick

Same five-source/3890-line scope; no new body or execution. The missing `vector_tick=` keyword at BANK's shared ICM service call is **not a defect**: ICM's complete transition context already carries it.

Exact path:

1. BANK `_context` stores `vector_tick=context.vector_tick` in content and verifies the current reservation tick (scoped_curiosity.py460-493).
2. BANK `_row_context(content, group)` constructs the genuine IntrinsicTransitionContext with selected rows and unchanged `vector_tick=content['vector_tick']` (510-517). Shared grouping contains all actual eligible rows.
3. BANK service sets its public receipt clock to `ServiceClock(policy.service_clock_unit, context.vector_tick)` in shared scope, then calls actual `backend.admit_and_service(payload)` for ICM (645-667).
4. Actual `ICMExploration.admit_and_service(context)` requires selected unit `vector_tick`, requires the actual context type, and **explicitly returns** `self.admit_and_service_at(context, clock=ServiceClock('vector_tick', context.vector_tick))` (icm.py218-225). There is no legacy implicit position+1 path.
5. Actual `admit_and_service_at` validates actual context, exact ServiceClock type and unit, validates context tick, requires `clock.position == context.vector_tick`, and rejects `clock.position < previous` when a prior native service position exists (227-242). For shared mode it passes that same position directly into `_admit_rows` (245-246).
6. `_admit_rows` updates `_service_position` to the supplied position and resets ordinary pacing budget only when that position changes (259-261). Admission counters separately increase per actual admitted row, not per vector tick. Shared clock position and admitted_rows are different quantities.

Consequently the explicit equivalent call is `backend.admit_and_service_at(context, clock=ServiceClock(unit='vector_tick', position=context.vector_tick))`. The convenience method and that explicit typed call have the same shared unit/position semantics; the explicit call additionally permits a mismatched clock argument to be supplied and refused. Constructor unit labeling is enforced by the actual delegation and validator, not merely asserted metadata.

Noncontiguous increasing supplied ticks are valid; there is no +1 requirement for shared ICM. Repeated equal tick retains the same ordinary update budget; backward tick refuses. BANK itself only accepts a subsequent new reservation after prior service and with a strictly greater reservation tick; an exact settled event retry returns cached receipts and never calls native service again. Direct native equal-tick calls are still possible and share native budget, but are not a BANK replay bypass.

`begin_episode` clears BANK episode-local caches/reservation and advances accepted identity; it does not reconstruct/reset the shared provider or its service position (BANK360-392). Thus an episode-local caller resetting context tick below the last serviced native position would legitimately fail `ICM shared clock must match context and not regress`. Equal prior position is allowed by native validation; BANK has no cross-episode reservation tick history after begin. These sources prove the service uses the supplied context tick, not that an uninspected parent supplies authentic monotonic global time. Actual parent correlation must authenticate that supplied value against its own authoritative vector-step domain and preserve it through resets/restores. Do not enforce equality between shared position and admissions/call count/episode count.

For an all-inactive BANK step, shared `groups=[]`, so no native ICM service call occurs, no native service position/budget/queue is touched, and the public shared receipts tuple is empty (BANK620-635). The actual BANK pending step is settled. A later eligible step may legitimately jump over all such inactive vector ticks. Therefore shared native service_position is the **last supplied eligible grouped service tick**, not necessarily the latest overall parent vector tick. A parent correlation invariant must allow lag caused by inactive steps; unit remains vector_tick. By contrast, a direct native all-inactive call (outside BANK) would still execute `_admit_rows(..., indices=[], position=clock.position)` and can update native position/reset budget or service an existing full queue; it is not the path taken by BANK and must not be substituted for it.

Private ICM remains intentionally different: BANK passes explicit world eligible-admission clock (plus truthful inherited baseline where applicable); native validates delta equals number of active rows, then admits each row at previous+offset+1. That private path must not be projected onto shared semantics. No source-backed shared ICM clock defect is identified by this followup. The inference from the absent keyword to legacy call-count cadence is refuted by the actual adapter implementation.

## Narrow followup: public reward statistics and service-once assertions

Same five-source scope; no additional body or execution. These assertions use `runtime.checkpoint_state()` owned portable data, never private child/module access. Let E0 be an export after genuine begin/stamp preparation and before reward, E1 after first genuine reward(update_stats=True), E1r after its identical cached retry, E2 after genuine service, E2r after identical cached service retry. Export/snapshot is an observer that advances revision; use these diagnostic observations only outside any outstanding prepared restore/completion transaction. Compare relevant payload values, not an assertion that observation has no revision effect. Before capture, retain the actual current accepted token/context/stamp; do not recreate authority from exported identities.

For every export `B = E['bank']`:

- Shared native `P = B['shared_backend']['native']`; shared gradients `B['shared_backend']['gradients']`.
- Private: find record R in `B['worlds']` by actual `R['world_id']`; `P=R['backend']['backend']`, gradients `R['gradients']`, RNG envelope `R['backend']['rng']`. Preserve ID association when comparing. No RND wrapper `rnd_state` is present for plain rnd.
- Every world record's `R['cursor']` has accepted_episode_seq,eligible_seq,cumulative_service_position exact nonnegative ints; participated bool; disposition None in live mode. `R['phase_cache']` holds encoded local reward/service evidence. These are BANK episode/service cursors, not RMS sample counts or native optimizer steps.
- `B['step']` is the current live reservation DTO: original_binding,stamp,tick,active,context,update_stats,reward,receipts,serviced. Actual `tick` is context vector_tick; active is bool[N]. Stamp world_episode_seqs/eligible_seqs are int64[N], eligible bool[N], event_ids tuple[N]; phase reward is None or dict raw/scales float32[N],eligible bool[N],event_ids tuple[N],scope string. Real N=8 unchanged-pack population, actual D/A as established above.

### Plain RND native statistics

`P['reward_rms_mean']`, `P['reward_rms_var']`, `P['reward_rms_count']` are native finite numeric scalars (Python/NumPy scalar types retained), not scalar tensors. Fresh mean=0.0,var=1.0,count=1e-4 (rnd.py64-107). Do not cast or replace exported statistics to make an assertion pass. `compute_intrinsic_rewards` computes per-row MSE, updates RMS with that actual eligible batch when update_stats=True, then divides by sqrt(updated var)+1e-8 (268-306). Reward normalization belongs solely to reward, not service.

Let K be actual active_on_entry.sum():

- Shared E1 count equals E0 count+K, within scalar roundoff; native shared provider is called once with K eligible successor rows when K>0.
- Private: each eligible ID's E1 count equals its E0 count+1; each ineligible ID's count/mean/var is unchanged. This is one genuine singleton normalization update per active owner, not one shared K-row update copied to each owner.
- E1 mean/var are actual computed moments and may legitimately equal old moments for some data; count increment is the robust update-once witness. Require finite mean, finite var>=0, positive count. Fresh shared first K rows count is 1e-4+K; fresh private active owner count is 1e-4+1. Count is a pseudo-count plus eligible reward samples, not exact int admissions.
- E1r entire RMS triple equals E1 exactly. E2 and E2r RMS triple also equal E1: neither actual service nor retries normalize rewards. E1r/E2r raw/scales and event metadata equal their original captured cached values.
- E1 native model, optimizer, predictor service subtree and gradients equal E0; reward runs under no_grad and only RMS changes. No reward-side queue admission/optimizer update occurs. Scope-owned RNG continuation remains unchanged for this deterministic model reward; checkpoint comparison uses the exported actual owner envelope, no RNG probe.

These facts hold with actual policy initial_intrinsic_weight=0.0: BANK reward callback computes novelty independently of choosing policy scale, so raw/stats remain genuine and scale0 does not skip normalization or later service. Actual eligible scale is0, raw need not0. No suppression of update_stats or overwrite of cached raw/statistics is permitted.

### Plain RND service subtree and deltas

`S=P['predictor_service']` has exact fields `version,training_batch_size,options,pending_observations,admitted_rows,consumed_rows,dropped_rows,optimizer_updates,optimizer_step_offset,service_clock_unit,service_position,ordinary_updates_at_position,step_counter` (rnd.py550-580). pending_observations is dense finite float32[q,D] on selected provider device; q can0, preserving the actual [0,D] tensor. Counters/batch/budget/step_counter are exact ints; optimizer_step_offset is a signed exact int, not a claimed number of BANK updates. options is actual centrally selected service policy. Service position is None for fresh shared,0 fresh private; after actual service it is the shared supplied context tick or private cumulative native admissions. Unit is respectively vector_tick or world_eligible_admission.

E1/E1r S equals E0 S. Between E1 and E2, for K>0 shared Delta admitted_rows=K; private each active ID Delta admitted_rows=1, inactive ID S unchanged. For each native provider let a,c,d,u be the actual admitted/consumed/dropped/update deltas and q0,q1 actual queue lengths: `a = c+d+q1-q0`, `c = u*training_batch_size`; cumulative `A=C+D+q` and `C=U*training_batch_size`. Drops/updates may be nonzero depending on existing tail and selected overflow/pacing; do not require zero or assume optimizer_updates increments once per reward. Match actual public receipt admitted/consumed/dropped/optimizer_updates/pending_rows to these native deltas/occupancy. RND receipt mandatory_service_updates represents this call's overflow_optimizer_updates; there is **no native cumulative mandatory counter** in this subtree. Do not invent one.

Native optimizer step equals cumulative optimizer_updates+optimizer_step_offset as validated by actual native restore; preserve true Adam state. No code in BANK's admit_and_service route changes RND step_counter; it is not authoritative vector time. Shared equal service tick retains ordinary pacing budget; increasing tick resets that tick's ordinary budget. Private clock advances by real admission count. Service consumes actual predecessor rows, while reward consumes actual successor rows. E2r native model/optimizer/service ledger/queue/RMS/gradients and private RNG envelope equal E2; no second admission or training occurs through exact BANK cached retry.

### ICM service and absence of normalizer

ICM native has **no RMS fields**. Do not add reward_rms_count/mean/var or infer an update from a nonexistent normalizer. E1 and E1r complete native ICM payload, gradients and private RNG equal E0: actual reward validates update_stats=True and computes raw from genuine predecessor/actions/successor, without admission or learning.

ICM `P['pending']` is list[q] of exact dicts predecessor float32[D] CPU,action exact int in[0,A),successor float32[D] CPU (owned native checkpoints). `P['counters']` exact keys admitted_rows,consumed_rows,dropped_rows,optimizer_updates,mandatory_service_updates, all exact nonnegative ints. Native `service_clock_unit,service_position,ordinary_updates_at_position,last_loss` are top-level, not under predictor_service. last_loss is the actual latest successful training loss (initial0.0); model/optimizer changes occur only through real service. Private native model/pending tensors exported by ICM are owned CPU snapshots even if actual destination is CUDA; gradient transport remains actual selected device.

Same E1-to-E2 active admission deltas and row conservation as RND: a=K shared/1 per active private; cumulative A=C+D+len(pending), C=U*batch, mandatory_service_updates<=U. Additionally actual Delta mandatory_service_updates matches that public ICM service receipt and cannot exceed Delta optimizer_updates. Clock semantics are the shared context-tick adapter established in the prior appendix and private eligible admission clock. E2r preserves native payload/gradients/RNG exactly; cached retry does not train/admit again. Policy scale0 does not suppress ICM reward or real service.

### BANK phase/cursor distinctions and inactive case

E0 current stamp may reserve next eligible sequence, but cursor eligible_seq/cumulative_service_position still reflect previously **serviced** events. At E1, BANK step.reward holds captured raw/scales, step.update_stats=True, step.serviced=False, receipts None; each active local reward cache records exact event/content/update_stats/raw/scale. Native RND count has advanced, while every BANK cursor and service ledger remains E0. Thus requiring reward RMS count to equal eligible_seq is wrong.

At E2 each active cursor eligible_seq becomes its stamp event eligible_seq, cumulative_service_position increases exactly1, participated=True; inactive cursors stay unchanged. accepted_episode_seq stays the genuine accepted episode sequence throughout these phases, never increments once per reward/service. Step.serviced=True and actual receipts are encoded. Exact service/reward retry does not advance these cursors again. Cache-returned reward after service retains captured pre-training raw even if genuine service changed models; recomputing reward directly on a provider would not test the public once contract.

All-inactive K=0: BANK reward invokes no provider; raw/scales are float32[N] zeros, eligible bool[N] false. All native RMS/model/optimizer/queue/counters/clock/gradients/private RNG and per-world cursors stay unchanged through reward and service. BANK still records/settles its actual reservation. Shared service receipts tuple is empty; private has N inactive receipts, each eligible=False,clock=None,all row/update/pending values0,last_loss0.0. Inactive receipt pending_rows0 is an inactive effect receipt, **not a reading of an existing private native queue's occupancy**. No inactive row receives an RMS pseudo-sample/admission. Later active shared native clock can jump past skipped inactive vector ticks.

Exact retry means actual authenticated accepted token, same stamp/events, same predecessor/actions/successor/activity/tick and same update_stats mode; changed content/mode refuses under BANK provenance checks. Observation exports do not authorize alternate contexts. These source-backed facts cover plain rnd and icm only. Adaptive normalizer/history nesting and Count visitation behavior require their separately qualified public contracts or producer ownership; no additional adaptive/count body was inspected and no new behavior is asserted here.
