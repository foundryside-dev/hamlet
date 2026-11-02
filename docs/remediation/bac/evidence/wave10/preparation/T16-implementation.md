# T16 runner wiring implementation — GREEN/review pending

Implemented the explicitly cleared minimal production wiring in the existing `/workspace/hamlet`. Only `src/townlet/demo/runner.py` changed in this turn, plus this requested ignored receipt. The owned test remains frozen at `4b9fdcc73192b91db199111b4c2a07186e50fa1afc5bd6a77aa1e2909660939a`; no assertion, parameterization, fixture, observer or budget changed. Entry/current HEAD remains `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`.

## Observed RED prerequisite and clearance

Root's R1 narrow run genuinely reached the intended missing contracts after actual finite learning and normal checkpoint publication. Both cases failed their real post-run observations: successive flat PER's public owner was `numpy_global_legacy` instead of `owned_numpy_generator`, and the recurrent initial public format was5 instead of its selected captured7. Actual log `/workspace/bac-review-2026-11-01/qualification/wave10-r1-narrow/narrow.log` was read and its SHA256 independently matched `91fc51653147ce5380c6f278b8ede29647102b0b86bf37d19b974388e6b3dc38`. Log reports2 failed in18.00s; root reports22.1510 harness wall seconds, collection12PASS/4.95wall and Black/Ruff PASS. Root reports exact tree `8665f26a`,160 source paths/three identities/573 configs/13 artifacts/14 checkouts custody PASS. These executions remain root-owned evidence, not locally rerun results.

That meaningful RED is distinct from retained R0's observer-induced PicklingError prerequisite failure. Root explicitly cleared minimal RR production wiring after R1 and closed all local runtimes. No new design/approval/review loop was introduced.

## Concrete change and API

Actual RR diff is **33 additions/17 deletions**,1001→1017 physical lines:

- AtRR401, capture the canonical effective training copy once and use it for population size, loop/frequency/batch/sequence/gradient inputs, curriculum construction and the existing shared AdaptiveIntrinsic/RND constructor parameters. The actual module type/arrangement and selected field values are preserved; no repaired provider selector/private-curiosity claim is introduced.
- AtRR461–470, consume `self.effective_run.effective_brain` and complete resolved `self.effective_run.options.replay`, rather than recomputing the same five brain overrides locally. The selected brain's gamma0, target interval, Double DQN, effective LR and capacity remain the existing canonical override semantics; PER/architecture/scheduler/options remain selected content.
- AtRR474–497, call the already-qualified public `VectorizedPopulation.for_training(...)` with every prior construction input and the seven required qualified inputs below. POP and all other public constructors/serving routes remain unchanged.

| Required factory input | Actual supplied runner value |
|---|---|
| `replay_options` | canonical complete six-leaf resolved replay object, with explicit non-None assertion |
| `min_transitions` | canonical `effective_training.replay_buffer.min_size` |
| `replay_rng` | separate explicit `np.random.Generator(np.random.PCG64(effective_training.seed))` |
| `replay_origin` | `authored` for this approved caller-owned seed/configuration policy |
| `beta_vector_tick_horizon` | executed `self.max_episodes * loop_cfg.max_steps_per_episode` |
| `beta_horizon_origin` | names actual launch override when present, otherwise declared training episode field; always names the declared cap field/value and actual absolute training declaration path/line; labels the product upper-bound vector ticks |
| `current_vector_tick` | explicit fresh0 at initial construction |

The explicit NumPy Generator is separate from global NumPy and curiosity streams; no new global seeding/reseeding or curiosity KDF/stream reuse was added. No N multiplier, live-transition budget, optimizer count, episode index or replay occupancy substitutes for beta's vector-tick upper bound. The factory owns/copies its policy and RNG according to the unchanged qualified POP implementation.

Existing canonical field_roles/derivations/origins, authored/execution/training identities, absolute training source and immutable launch-overrides map remain untouched. The sampler's origin does not overwrite per-leaf authored/bac-options-v1 provenance. The explicit factory's optional debug `replay_option_provenance` tuple behavior is unchanged; complete leaf provenance remains in the existing canonical effective view. No new local omission table, warmup default, authoring field, checkpoint version or public compatibility branch was introduced.

## Preservation and actual boundaries

Fresh tick0/configuration occurs **before** the existing real checkpoint load, now atRR522. Nothing reconfigures replay or reapplies fresh clocks after that load. Existing POP load/binding/adoption remains responsible for loaded current rows, archives, priorities/stable IDs/domains, sampler state and restored cumulative clocks; its implementation is unchanged. This RR wiring does not extend raw POP/current storage evidence into complete native10/7 atomic/continuation guarantees, which remain T24/T25 ownership.

All low-level/global legacy sampling interfaces and ordinary construction/inspection/serving roles remain callable because POP was not edited. Genuine selected recurrent PER is now constructed through its real factory policy, without a false non-PER brain or manual replay attachment. Backend readiness still owns retained warmup and row/window support, including fixed-full diagnostics and additive adaptive-prefix. Existing optimizer/LR/target and vector beta clocks remain POP's actual qualified behavior. No historical maskless optimizer path, deletion, archive clearing or current captured-history reset was added; approved History A remains intact.

Curiosity scope remains the existing **shared** RR AdaptiveIntrinsic/RND arrangement, origin its selected-training constructor, world_binding one existing population module. Guarantee here is limited to explicit resolved replay/warmup/sampling identity/horizon propagation. Local units remain retained eligible transitions for warmup, vector ticks for beta and successful Q updates for LR/target. RND predictor service continues independently of Q warmup. Declared provider_parameter_source/private options alone acquire no new runtime qualification; strict per-world B and the shared alternative remain preserved with their owners.

## Exact five-source custody

No sixth implementation/helper/network/environment/sampler/config/test/conftest was opened. Same bounded inventory, actual **5 files/4419 physical lines**, effective projection RR1200/POP2200/BC600/OF200/test700 = **5/4900**:

| Complete source | Actual lines | Current SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |526|`4b9fdcc73192b91db199111b4c2a07186e50fa1afc5bd6a77aa1e2909660939a`|

Complete actual diff was read. Standard-library AST parsing succeeds for RR and the frozen test; max physical line lengths are140/133. No project imports/runtime, pytest, collection, compiler, linter/formatter, gate or probe ran during writing. Accordingly **GREEN, lint and runtime/review dispositions remain PENDING**; syntax success alone proves none of them.

Fresh tracked status shows only the owned unstaged RR modification and root's already staged owned test; no index operation was performed. Only RR and this ignored `.git/info/exclude:7` `/.superpowers/` receipt were written. No new branch/worktree/checkout/project-source copy/deletion, tracker action, subdelegation, commit or push occurred; all14 existing checkouts remain preserved. Canonical YAML DATA packs remain unchanged.

## Stationary handoff

Root owns exact-two GREEN, all12 owned cases, affected owner selection, all six guards, fresh Astra MEDIUM implementation review and mandatory full G2. Root also retains the actual-patch earlier-full-trigger assessment and exact-tip remote CI/publication. Full-suite status for this candidate is NOT RUN; next required full gate G2. No focused/source-only observation declares repository green or T16 released. Return stationary now so root can freeze/reconcile the candidate and execute those checks; no further source/runtime work follows without concrete clearance.
