# T15 flat PER public serialization API

Static supplement at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, reusing the existing five-source / 2,125-line context. Only PB portions were revisited; no sixth source or runtime was used. PB is `src/townlet/training/prioritized_replay_buffer.py`, 1,092 lines, SHA256 `290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9`.

The actual public snapshot API is **`state = buffer.serialize()`**, signature `serialize(self) -> dict` (PB733–767). This class defines no `state_dict`, export-state, get-state or alternative serialize alias. Do not inspect private buffer attributes: the public result contains every descriptor below.

| Public returned mapping path | Meaning / exact visible values | Source |
|---|---|---|
| `state['replay_kind']` / `state['format_version']` | `'prioritized'` / `6` | PB34–35,737–738 |
| `state['sampling_mode']` | Current persisted selected sampler mode | PB321,753 |
| `state['sampling_origin']` | Current persisted origin | PB322,753 |
| `state['sampling_objective_unit']` | `'transition'` | PB287,323 |
| `state['sampling_weight_rule']` | Current rule matching the selected mode | PB288–289,324 |
| `state['sampling_rng']['ownership']` | `'owned_numpy_generator'` or `'numpy_global_legacy'` | PB311–319 |
| `state['sampling_rng']['bit_generator']` | Owned engine name; otherwise `None` | PB313,317 |
| `state['sampling_rng']['state']` | Complete deep-copied owned engine-state mapping; otherwise `None` | PB313,318 |
| `state['capacity']` / `state['alpha']` | Actual buffer capacity / PER alpha | PB739–740 |
| `state['beta']` / `state['beta_initial']` | Current effective beta / original beta | PB741–742 |
| `state['beta_annealing']` | Actual enabled flag | PB743 |
| `state['size_current']` / `state['position']` | Active retained count / physical ring position | PB746–747 |
| `state['unit_ids']` / `state['next_unit_id']` | Copied capacity-length int64 IDs / allocation counter | PB751–752 |

Owned-generator configuration has origin exactly `'authored'` or `'bac-options-v1'`. External-global ownership has successive mode and origin `'legacy-constructor'` or `'captured5-physical-slot-adapter'`, with both private engine fields `None` (PB279–309). Supported owned engine names are PCG64, PCG64DXSM, MT19937, Philox and SFC64 (PB74–80). Keep the engine-state mapping opaque to the consumer; public restore APIs own its validation.

There is **no public `configured` boolean**. The ownership descriptor distinguishes an owned configured Generator from the explicit external-global legacy role. It does not distinguish a newly constructed buffer from an attached/restored buffer; that custody comes from the caller. A legacy descriptor is not permission to overwrite attached/restored state.

**Active0 preserves the sampler.** PB733–754 includes mode/origin/objective/rule/private state, beta fields and ID counter regardless of `size_current`. Empty-state serialization changes `action_dim` to None, `legality_mode` to `'unconstrained'` and row tensors to None (PB748–760); it does not remove the sampler or reset beta/counter. Adopt an attached/restored buffer's actual public descriptor without `configure_sampling`, reseeding or generator replacement, including active0. Inspect ownership rather than treating zero occupancy as unconfigured.

`serialize()` makes an observation without sampling: priority and ID arrays are copied, row tensors detached/CPU-cloned, and private RNG state deep-copied (PB311–319,744,751,760). Editing these returned priority/ID/tensor/RNG snapshots does not configure the live buffer. No process-global RNG state is supplied for the legacy external owner.

**No vector tick or beta-horizon field exists in this standalone PER6 mapping.** Current beta is available; current vector tick, horizon and monotonic pacing custody remain caller inputs. `anneal_beta(total_steps,current_step)` uses those supplied arguments but stores neither clock/horizon (PB695–700). Do not fabricate them from occupancy, beta or ID count.

Public restore APIs remain `load_from_serialized(state)` (auto), `load_for_mode(state,*,requested_mode)`, or `prepare_serialized(state,*,expected_obs_dim)` then `load_prepared(candidate)` (PB1053–1092). PER6 restore validates/restores sampler ownership/state and IDs (PB973–975,1063–1079); adoption is not reconfiguration.

Only this ignored prose file was written (`.git/info/exclude:7`, `/.superpowers/`). PB hash/count and HEAD were checked before/after. No imports, tests/runtime, tracked/index mutation, branches/worktrees/copies or subdelegation occurred; all 14 worktrees remain preserved. Root owns integration and the active main writer; return stationary.
