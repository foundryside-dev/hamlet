# PW06 policy/recorded-replay/WorldRecord fixture facts — source-verified by root
Root source-inspected actual bac_options.py/exploration_policy.py, current qualified PW05 fixture inputs, replay_buffer.py, training/state.py, HC675 and world_roster.py. No extra implementation-source read is authorized to worker; descriptions and JSON below are data/API facts, not hidden fixture code to import. No new runtime proof here.

## Actual typed policy construction
Exact imports: townlet.config.bac_options.BaCOptions; townlet.config.drive_as_code.IntrinsicStrategyConfig; townlet.config.training_v2_config.TrainingV2Config; townlet.config.exploration_policy.resolve_exploration_policy. Real signature resolve_exploration_policy(drive_intrinsic,training,options), positional three or exact keywords drive_intrinsic/training/options. Drive strategy is selector for all5none/count_based/rnd/adaptive_rnd/icm; typed options do not select strategy. Compile token_set_smoke primaryL0_test use_cacheFalse as existing actual fixture capsule; compiled.get_level('L0_test') owns level.drive.intrinsic and level.training. Clone level.drive.intrinsic.model_dump(), set strategy to desired actual family, validate IntrinsicStrategyConfig.model_validate. Clone level.training.model_dump and replace the following existing nested data before TrainingV2Config.model_validate: replay_buffer.batch_size=2; intrinsic.rnd.feature_dim=4,learning_rate=0.001; intrinsic.initial_weight=0.4,survival_window=10,min_survival_fraction=0.1; training_loop.max_steps_per_episode=20; intrinsic.annealing.min_weight=0.01,threshold=100.0,decay_rate=0.9. Preserve every other compiled required field.
Actual BaCOptions.model_validate mapping for private below. For shared set curiosity_scope.scope='shared' AND seed_policy='legacy_shared_v1'. That literal is the CURRENT typed shared seed-policy label, not an obsolete artifact loader or permission to add compatibility. Do not invent 'shared_v1' or silently omit scope. All5 families can use this options data; actual resolver marks nonselected provider presets inactive. RND/adaptive derive B2/E4/LR.001 and queue4; ICM explicit B2/F4/H8/queue4/LR.001. Policy.actual scope is reflected by the actual resolver's full current identity, not manual dataclass construction.
{
  "curiosity_scope": {
    "scope": "per_world",
    "seed_policy": "world_id_derived_v1"
  },
  "provider_parameter_source": "training",
  "rnd": {
    "service_mode": "paced_fifo",
    "max_updates_per_tick": 1,
    "max_pending_rows": 4,
    "overflow_policy": "drop_oldest"
  },
  "providers": {
    "count_based": {
      "quantization_width": 0.125,
      "max_entries": 16
    },
    "icm": {
      "feature_dim": 4,
      "hidden_dim": 8,
      "learning_rate": 0.001,
      "inverse_weight": 0.8,
      "forward_weight": 0.2,
      "training_batch_size": 2,
      "max_pending_transitions": 4
    }
  }
}

## Actual current recorded uniform replay fixture (format5, not historical format4)
Import ReplayBuffer from townlet.training.replay_buffer. Constructor ReplayBuffer(capacity:int,device:torch.device); e.g.capacity4/deviceCPU. Public push_recorded(observations,actions,rewards,next_observations,dones,next_action_masks) accepts corresponding arguments by name or position. Actual RewardTensor import townlet.training.state; constructor total with keyword extrinsic,intrinsic,shaping,is_composed. Supply explicit is_composed=True, total float32[N], components optional float32[N] or None. A concrete two-row fixture: observations finitefloat32[2,3], next_observations same shape; actionsint64[0,1]; totalfloat32[1,2], extrinsicfloat32[0.5,1], intrinsicfloat32[0.5,1], shapingNone; donesbool[False,True]; successor maskbool[[True,False],[False,False]] (terminal empty support is valid). No call to unconstrained push; it does not establish recorded masks. Public serialize()->owned chronological CPUdict, not state_dict/checkpoint_state. It emits replay_kind='standard',format_version5,capacity,size2,position2,action_dim2,legality_mode,historical_archives[], observations/actions/rewards/next_observations/dones, rewards_extrinsic/rewards_intrinsic/rewards_shaping, next_action_masks,legality_recorded and all3component '_present' tensors. For this input legality_recorded isTrue both rows, ext/int presenceTrue and shaping presenceFalse; wholly absent shaping serializesNone. Use actual serialize result rather than copying private row schema or manually marking capture.

HC.resolve_historical_access(payload,*,requested_mode) recognizes current demo10/population7/standard5. Minimal caller-provided HC-container metadata around the REAL replay serialize result: top version10, action_dim2, episode3,completed_live_agent_steps7; population_state mapping version7,total_steps9,training_step_counter2,replay_buffer=actual serialized replay. This is a minimal actual-HC admission fixture, NOT a complete valid DemoRunner/DQN native checkpoint. It exercises actual current captured replay and source clocks without inventing full parent ownership. requested_mode='recorded_full_resume' returns current policy, active_retained_transitions2, archived0, no fresh/archive reset. 'archived_history_fresh_episode' must refuse this current captured data. HC.prepare_historical_envelope(payload,*,requested_mode,validate_legacy) clones data and resolves actual current policy; validate_legacy is required by existing HC signature but is NOT called on current data. A test-local callback that raises if called is a genuine guard, not an always-success validation stub. Returned available_learned_state preserves full supplied current replay rows/masks/presence/clocks independently; encode_historical_envelope and decode_historical_envelope are real owned codecs. Existing HC implementation is already one of worker's3 authorized whole sources. This unit does not qualify full real parent native admission, sampler behavior or historical training.

## Actual WorldRecord data access
world_roster.py312 defines frozen eq=False WorldRecord. Public .payload property returns a NEW dict whose values pass owned_value. Public attribute access for payload keys (e.g.prepared.state,prepared.destination_world_ids,prepared.destination_vfs_context) likewise returns owned_value. .kind is the record kind. No getter reveals private owner/generation and data does not authenticate its own origin. Real prepared_restore has exact3payloadkeys as ENV capsule. Copying or structurally constructing a record is not actual authority. Tests must obtain real ENV preparation and use the approved actual-parent callback, never an always-success correlation callback or assumed private accessor.

## Exact ENV literals, meter row and actual restored authority callback
Root inspected ENV2403 at41e57423. Public checkpoint_world_state kind is EXACT uppercase INITIAL or COMPLETED. prepare_world_restore validates that same kind against saved state['kind']; use uppercase COMPLETED throughout these native calls. Public world_phase strings are lowercase hyphenated: fresh-unbound initially; fresh-bound after authority role binding; bootstrap-ready after bootstrap/INITIAL install; active-awaiting-activation after accepted reset; active after activation; boundary-pending after freeze; closed-awaiting-release after close; released-completed after completed release; quarantined on failure. CP's approved own mode string completed_boundary is separate from ENV snapshot kind and phase.
ENV publicly annotates meters:torch.Tensor, allocates shape(num_agents,meter_count),dtypefloat32 ondevice; env.meters[index] is the actual public tensor row (live view, not owned snapshot). Supply a detached CPU clone for outcome ownership; actual LaneOutcome already takes detached CPU copies on construction as documented. Nothing requires private meter access.
WorldBoundaryAuthority.restored(*,restore:WorldRecord,boundary:WorldOwnerReceipt)->WorldRecord requires actual bound ENV fresh-bound and calls actual ENV issued-record validation for restore kind prepared_restore. It validates boundary as actual issuer receipt kind restored_boundary belonging to authority/checkpoint owner. EXACT boundary payload keys are kind,state,prepared. boundary.prepared MUST BE the exact restore WorldRecord object (not its payload/dict, not a copied record). boundary.payload['kind'] must equal restore.state['kind'] (uppercase COMPLETED or INITIAL), and boundary.state must exactly match restore.state. Returned release has release_kind='restored',next_batch_episode fromstate,restore exactrecord. To call install_world_restore then pass prepared=that exact restore and release=this actual returned release. This is the available existing PUBLIC actual parent correlation validator; no private ENV validation call is needed. A local checkpoint-role fixture may issue its actual restored_boundary receipt and invoke this public authority method, labeling other-child preparation as a unit limitation; it must not simply return success without actual authority/record/identity checks. Counterexamples with copied/foreign prepared record or mismatching state/kind must actually fail.
