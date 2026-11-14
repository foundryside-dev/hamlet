# C2 POP claim predecessor facts v1

2026-11-14. Metadata-only source supply by `bac_pop_standalone_step_prepare` to root and `bac_parent_env_c2_prepare`. Root authorized this prose artifact. No APP edit, import, test, Git operation, branch, worktree, source copy or deletion. Repository AGENTS.md was read.

Source: `src/townlet/population/vectorized.py`, 3163 lines, SHA256 `6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022`. This body was already charged to the standalone-step preparation packet; no extra implementation body was opened for this addendum. Its other charged body is parent-handoff791, for 3954 total lines. These facts do not qualify C2 implementation or execution.

## Exact claim and reverse-call route

`claim_vector_step`1384 refuses an existing `_step_inspection`, then retains a fresh inspection marker through `_claim_vector_step`, clearing its own marker in `finally`. `_claim_vector_step`1410 requires exact `PreparedVectorStep` type, identity membership in `self._vector_steps`, and stage `prepared` before calling `_step_record`1284.

`_step_record` refuses `accepted is None` or `accepted is not self._accepted`, as well as failed/checkpoint/selection/reset preparation or pending owned reset. It calls ENV `validate_accepted_episode(accepted=accepted)`, then `_validate_owned_training`944. The latter obtains `prior` from `_check_owned_state`906 and calls exactly:

```python
self.env.validate_initial_participation(
    accepted=prior.accepted,
    participation=self._initial_decision.participation,
    predecessor=prior.observation,
)
```

The predecessor at this reverse call is the owned prior reading, not the incoming claim argument and not a requirement for `current_obs` object identity. `_check_owned_state` requires exact accepted/decision identity, reset-record/decision identity, prior.accepted identity, matching vector tick and present masks. It compares current observation/completion/counts and ENV dones/counts with the prior using layout/dtype/device/shape and `torch.equal`. It also preserves the retired-lane no-participation invariants. It repeats the owned-state check after ENV validation.

Later `_step_record` checks incoming predecessor geometry, finiteness and `torch.equal(predecessor, self.current_obs)`, then clones it into the candidate. `_same_step` requires accepted identity, equal tick/world order and tensor equality against the retained record. Only after those checks does claim publish the participant set and stage `executing`. The exact retained handle registry and stage authenticate this execution; a separately fabricated value-equivalent handle has no membership.

## Genuine ownership boundary

No public genuine unowned or `accepted=None` claim succeeds. POP `reset`1110 requires a matching explicitly begun binding. Every fresh healthy reset calls `_prepare_initial_participation` and `_publish_initial_participation`; the exact ENV commit return is stored in `decision.participation`1099, and the decision/prior pair is published before activation finalization. Only after those checks does reset install accepted/activation1235. Provisional `participation=None` exists during private reset preparation, not at a healthy published claim boundary.

Unowned selector success can be a genuine positive control. It does not supply an unowned step-claim positive control. A C2 test must not fabricate participation/private POP state to invent that route. These are POP facts; ENV's exact retained accepted/participation checks remain C2-owned source facts.
