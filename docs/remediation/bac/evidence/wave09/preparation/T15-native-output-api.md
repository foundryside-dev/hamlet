# T15 native capture output API — read-only supplier handoff

This describes the existing repaired checker, not an execution result or schema change. Root fullR2 remains frozen. Exactly the same3-source3575-line context: checker1036 SHA25619e0b83130f2467a2bfd890dc79e95de6d7694e79f7fa996fa16c66b43e62eb7; POP2146 SHA2569569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a; comparator393 SHA2565a259e6ab4236caf3d1b20323ee089522c101b4e91d8a294e2deb84595536d30. All were rehashed unchanged. Only this ignored prose is written. No project import/runtime/collection, source edit, index/commit, checkout/worktree or .oracle action occurred.

## Files per explicit --output directory

Successful `capture` creates exactly these producer-managed files in the new output directory:

| Name | Content / acceptance |
|---|---|
| capture.json | Full episode-lanes.capture.v1 artifact described below; validate independently. |
| command.json | Object with exactly command (argv list), exit_status (producer integer status), pythonpath (pinned source src path). Require exit_status=0 and correct recipe/source/config/output argv. |
| stdout.log | Child _produce stdout, not the parent summary. Preserve bytes/digest; contents need not be empty. |
| stderr.log | Child _produce stderr; preserve bytes/digest and assess actual diagnostics. Nonempty alone is not a schema failure. |

The parent capture invocation additionally prints one JSON summary to its own stdout: recipe, revision, readings (integer count), contract, output. Its own stderr/exit status must be captured by root's orchestration outside the output directory if wanted; no parent log file is automatically written. Child failure still writes command.json after subprocess return, then parent raises. Preflight source_identity failure can occur before the output directory is created. Missing capture.json is never a successful capture.

The producer's temporary config copy, compiler products and budget-six database/checkpoints live under its TemporaryDirectory and are cleaned up; they are not additional persistent output filenames. Parent and child both check clean source identity. Each output path must initially not exist; no overwritten directory or reference checkout is needed.

## Exact capture JSON shape

The top-level object has exactly schema, manifest, readings, contract. Require schema="episode-lanes.capture.v1".

contract has exactly qualified and errors. For acceptance require qualified is the JSON boolean true and errors is exactly []. A consistent false/errors artifact is schema-valid and can yield capture exit0. Therefore subprocess/parent exit0 and summary do not by themselves prove qualification. The actual checker recomputes semantic_errors from readings and refuses a forged or stale contract; independent root validation must likewise assess readings, not just trust the flag.

manifest has exactly these15 keys:

| Key | Type and independent checks |
|---|---|
| source_root | Absolute resolved native root; require /workspace/hamlet. |
| revision | Full40 lowercase hexadecimal actual local post-gates commit. Require equals preflight and postflight git rev-parse HEAD; no synthetic unit revision. |
| source_sha256 |64 lowercase hex; exact source byte-inventory digest below. |
| source_stamp | Exactly {revision: same revision, source_sha256: same digest}. |
| imported_modules | Nonempty object mapping townlet or townlet.* names to absolute resolved module __file__ paths under /workspace/hamlet/src/townlet. Must contain townlet. Includes only modules with __file__, not necessarily namespace-only packages. Require no different checkout/root path. |
| config_sha256 |64 lowercase hex; SHA256 of canonical JSON config_inventory. |
| config_inventory | Object with authored and effective mappings. Each maps pack-relative *.yaml file path to SHA256 of actual file bytes. authored is the supplied pack before edits; effective is the temporary recipe-edited pack. |
| instrument_sha256 |64 lowercase hex; SHA256 of actual checker script bytes. Require the fixed/reviewed instrument hash above if no later reviewed repair occurs. |
| recipe | One of the six literal recipe names in the inventory table. Require the command's selected recipe. |
| recipe_version | Integer1. |
| seed | Integer42, the recipe ambient seed; do not relabel as the authored replay-owned seed. |
| device | String cpu. |
| actions | List of actual full-N action vectors sent to env.step, in actual call order. Each vector has2 integer action IDs; action IDs come from this compiled pack, not assumed literals. No entries for resets. Includes real inactive transport. |
| action_sha256 |64 lowercase hex; SHA256 of canonical JSON actions. |
| measured_fields | Sorted unique list of every field name in readings; require exact field-set equality and no duplicate names. |

Canonical bytes are Python stdlib json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), including its ordinary ensure_ascii=True behavior. Hash those exact UTF-8 bytes with SHA256; pretty printing is not canonical.

Source identity is independent of instrument identity: source_sha256 hashes canonical JSON of a mapping from every `git ls-files -- src pyproject.toml uv.lock` path to its current byte SHA256. The checker separately refuses any `git status --porcelain --untracked-files=all -- src configs scripts tests pyproject.toml uv.lock` output, including staged edits. The inventory does not itself include scripts/configs/tests: root must preserve the distinct clean gate, instrument hash and config inventories. Root may use read-only git commands and byte hashing after its local clean commit; never bypass this gate or rewrite prior test provenance. No source copying is required.

Authored inventory recursively includes file paths matching *.yaml only, not *.yml, from the supplied config root. Recipe edits are population.size=2; max_steps_per_episode=5 for passive-two-five/death-at-lifespan/healthy-retirement, otherwise10; max_episodes=2 only for two-episodes-reset, otherwise1; replay_buffer.batch_size=128; recording={enabled:false}. Training YAML is serialized with yaml.safe_dump(sort_keys=False), so its effective BYTE digest cannot safely be inferred merely from parsed values. The producer records the actual effective digest. All other pack files retain actual supplied bytes. Root must require authored inventory equals the actual source pack and is unchanged postflight; require all6 authored mappings agree. Effective digest differs by actual recipe edits; do not demand all6 effective inventories agree. This checker supplies the effective inventory but does not persist the temporary effective YAML itself: do not claim that effective bytes were independently re-read after cleanup.

## Reading identity, types and exact coordinate inventory

readings is a nonempty list of objects, each exactly {key,value}. key is a5-element JSON list [recipe,field,tick,agent,coordinate]; require the matching recipe throughout, no duplicate complete keys and no missing/unknown coordinates. tick is a nonnegative exact integer; agent is an exact integer >=-1. Value must be JSON-native null/string/bool/int/finite-float/list recursively; objects and NaN/Infinity are refused. Preserve native types, including bool versus int and integer versus float. Null is meaningful, not an omitted reading.

Use these coordinate groups to independently derive the complete expected-key set. Row tensor values use agents0,1. Tensor metadata uses agent=-1. A hashed tensor contributes7 keys: present/dtype/shape at agent=-1, plus value/sha256 for each agent. An unhashed tensor contributes5 keys: the same3 metadata coordinates plus each agent's value. Scalars use coordinate=value only. Actual sha256 tensor values hash detached CPU contiguous per-agent NumPy bytes, including true dtype/byte layout; they do not hash JSON arrays. Metadata describes the full tensor including N=2.

Reset boundary at tick=episode*100, including one final reset after the last real episode:

- Hashed tensors: reset_observations, reset_meters, reset_dones, reset_counts.
- Unhashed tensor: initial_energy.
- Scalar agent=-1: reset_global_tick.
- Population recipes additionally: unhashed reset_population_counts, reset_population_completed; scalar per-agent reset_completion_reason, reset_completion_survival.

Each real tick at episode*100+step:

- Hashed tensors: actions, observations, meters, dones, rewards, intrinsic_weight, extrinsic, intrinsic, shaping.
- Unhashed tensors: step_counts, ledger_active, ledger_terminal, ledger_counts, ledger_terminal_counts, active_on_entry, newly_terminal, newly_retired.
- Scalar agent=-1: global_tick, time_of_day, ledger_live_transitions.
- Scalar per-agent: eligible_observation.
- Population recipes additionally: hashed selected_q_values; scalar per-agent admitted_observation.

Additional population readings at each real tick, and additionally tick99 for budget-six:

- Unhashed tensors: population_counts, population_completed.
- Scalar agent=-1: population_total_steps, population_training_steps, replay_size.
- Scalar per-agent: completion_reason, completion_survival, completion_observation, completion_meters.

Budget-six additionally has scalar agent=-1 at tick99: runner_live_transitions, runner_budget_reached, runner_budget_shortfall, runner_episode_count. Do not invent tick99 actions/observations/Q/rewards/eligible/admitted readings. Its completion_observation/meters values refer to actual final snapshots from earlier real tick coordinates.

| Recipe | Population? | Real ticks | Reset ticks | Exact reading count | Action vectors | Distinct fields |
|---|---|---|---|---:|---:|---:|
| authored-two-five |yes|1..5|0,100|786|5|42|
| passive-two-five |no|1..5|0,100|608|5|27|
| death-at-lifespan |no|1..5|0,100|608|5|27|
| healthy-retirement |no|1..5|0,100|608|5|27|
| two-episodes-reset |yes|1..5,101..105|0,100,200|1524|10|42|
| budget-six |yes|1..4 plus population-only99|0,100|673|4|46|

Counts are static arithmetic from the complete coordinate contract, not observed runtime results. A correct count alone is insufficient: require the exact key set above. selected_q_values is full-N [2,A]; actual eligible selector row counts2,2,1,1,1 do not narrow its output geometry. actions is full-N [2]. The A/D/meter widths are real compiled dimensions, not constants specified here.

## Independent semantic checks and postflight

Reconstruct active entry from prior sticky dones separately per episode; reset starts both false. Each active row increments counts/live-transition sum; newly terminal is active AND current done. Terminal-causing rows remain eligible/admitted once; later inactive rows have eligible_observation=null and, for population recipes, admitted_observation=null. Every active eligible predecessor hash must exactly equal its admitted hash for population recipes. Replay sizes follow cumulative eligible rows across episodes, not reset-local count: authored final7, reset final14, budget final real tick4 and tick99 both6. Per real episode expected cumulative live transitions are2,4,5,6,7, or2,4,5,6 for budget; healthy-retirement instead2,4,6,8,10. Lane terminal schedules end with counts[2,5], except healthy[5,5], budget[2,4]. Full actual Q/actions and all reward/component values/hashes remain present for inactive lanes too; inactive rewards/components/intrinsic_weight must be0.0.

Recompose total as f32(f32(extrinsic+intrinsic)+shaping) with math.isclose rel_tol1e-5/abs_tol1e-6 for the existing retirement reassociation rule; do not alter actual recorded totals/components or silently strengthen this into exact recomposition. Exact coordinate comparisons remain exact when a before/after comparison is separately requested. Existing local collector.errors checks are replaced by semantic_errors for the artifact verdict as documented in the prior audit; do not report them as an additional independently persisted error list.

Validate bool[N] active_on_entry/newly_terminal/newly_retired metadata present=true, dtype=torch.bool, shape=[2]; independently reconstruct values. All resets have reset_counts=0, reset_dones=false, reset_global_tick=0; population reset completion fields null/false and counts0. Population completion reason/survival and observation/meter hashes latch exactly once at terminal; use the captured terminal-tick observation/meter row sha256, not the current later row. Healthy-retirement completes both at tick5 as retirement; other ordinary terminals are authored_terminal. Budget-six lane0 completion latches at tick2, lane1 is externally completed as budget at tick99 with survival4 and tick4 final snapshot. Its runner values must be6,true,0,1 in field order listed above. Global tick equals episode step and ledger transitions equal the independent sum. Population total_steps continues across resets; scheduled training counters reflect real readiness, not an inferred warmup128 promise.

Root's external orchestration should record parent argv/environment identity, parent exit/summary and hashes of all4 output files; validate no missing file, exact recipe, exact artifact contract/inventory, manifest digest bindings and literal native import root. Do not reject module-set differences solely because budget-six imports the real runner; compare all imported paths to the native root. Require all6 source_root/revision/source_sha256/instrument_sha256 bindings equal the expected clean native candidate. Action digests and effective config digests are per recipe, not cross-recipe constants.

After both workers have completed, recheck exact HEAD, clean execution-bearing status, full source inventory digest, checker instrument bytes and authored config inventory against preflight and every capture. The producer itself checks source/config before and after each recipe; external postflight supplies orchestration-wide custody. Preserve each original artifact and log. Any failure, unexpected output, production defect or inconsistent capture stays reportable; do not mutate source/fixtures/manifests to qualify. These native captures get their actual new postcommit SHA/tree binding and never replace the previous RED/unit/full-suite provenance. No before/after oracle checkout or comparison is necessary for these6 current-candidate qualifications.

Return stationary.
