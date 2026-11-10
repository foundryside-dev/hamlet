# PW07 actual current HC/replay public API facts

Root verified at a7c4cd0b19c410114aaabdd9284888fef159e84e, no code changes/runtime. Dependency API/data capsule, not an additional implementation read for PW07 workers. Historical-checkpoint source675 SHA74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4; uniform replay677 SHAd6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8.

## HC import, signatures and owned results

Module is `townlet.training.historical_checkpoint`; import its actual public functions/classes from there, or the module as a local alias.

- resolve_historical_access(payload: Mapping[str, object], *, requested_mode: AccessMode) -> HistoricalAccessPolicy.
- prepare_historical_envelope(payload: Mapping[str, object], *, requested_mode: AccessMode, validate_legacy: Callable[[Mapping[str, object]], None]) -> HistoricalPreparedEnvelope.
- encode_historical_envelope(envelope: HistoricalPreparedEnvelope) -> Mapping[str, object].
- decode_historical_envelope(state: Mapping[str, object]) -> HistoricalPreparedEnvelope.

HistoricalAccessPolicy is an owned frozen dataclass, not a dict. Attribute fields: source_formats, requested_mode, effective_mode, approval_reference, archived_row_count, active_retained_transitions, restored_clocks, guarantees, legacy_identity_recipe. The source_formats/restored_clocks mappings are owned on storage/access. Current input resolves effective_mode recorded_full_resume (or explicitly inference), recipe current-captured, active_retained_transitions equal actual retained replay rows; archived_row_count is actual embedded archive count, zero for the supplied archive-free current fixture. Current input requested archived_history_fresh_episode refuses before preparation. Source clocks retained are top-level episode/completed_live_agent_steps plus population total_steps/training_step_counter when supplied; they do not establish readiness.

HistoricalPreparedEnvelope is an owned frozen dataclass with exactly attribute fields policy, archives (tuple), available_learned_state (owned mapping). For current input, the required validate_legacy callback is not invoked; a test callback that raises if invoked is an actual branch guard. Current available_learned_state retains population_state/replay_buffer; do not access the envelope using dictionary subscripting. The encoder emits a mapping with exact keys schema_version=1, policy, archives, available_learned_state; decoder returns the real dataclass with independently owned data. Test current data fidelity rather than reconstructing a codec schema manually. Refer to PW06 fixture capsule for actual current minimal HC unit container10/pop7/current ReplayBuffer5 and its limits.

## Actual ReplayBuffer restoration

Module `townlet.training.replay_buffer`, public ReplayBuffer(capacity: int, device: torch.device). Existing push_recorded and serialization facts from PW06 remain current. Public signatures:

- validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int) returns an opaque validated-state record.
- materialize_validated(self, state) returns an opaque prepared storage candidate from that validated state.
- prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) returns an opaque prepared storage candidate, validating and materializing off-side.
- load_prepared(self, candidate) -> None transfers that actual prepared storage candidate after archive checks.
- load_for_mode(self, state: Mapping[str, Any], *, requested_mode: AccessMode) -> None validates/materializes/loads and rejects requested archived_history_fresh_episode for qualified current rows.
- load_from_serialized(self, state: Mapping[str, Any]) -> None delegates to actual auto access mode.
- serialize(self) -> dict[str, Any]; __len__, retained_transitions, historical_archives are actual supported accessors.

For an independent active restored current replay, construct a separate ReplayBuffer with the same declared capacity/device, call its prepare_serialized(actual_current_payload, expected_obs_dim=the actual observation width), then load_prepared on that real candidate (or explicit load_for_mode recorded_full_resume). No handcrafted candidate or private storage assign. Current masks/component-presence/rows remain active. Assert len/retained_transitions and actual serialize before/after; mutate destination through public pushes and prove source serialization unchanged. The current serializer returns owned chronological rows and position=size%capacity, including when live physical storage wrapped; compare that canonical representation, not an invented preserved physical insertion index.

Opaque validated/candidate implementation details are not needed by these tests and are not permission to inspect more source. This current HC plus actual uniform replay proof remains a component unit: it does not qualify DQN sampling, full native population/runner admission, or whole-parent publication. Approved historical A and actual downstream integration obligations remain unchanged.
