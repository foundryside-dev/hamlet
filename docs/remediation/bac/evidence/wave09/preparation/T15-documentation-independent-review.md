# T15 documentation — independent adversarial source review

Review date: 2026-11-02 UTC. Reviewed draft SHA256: `244b78d855d241338e7c84314a153becf6f06b80ee054e970bd6438e90e54592`. Assigned candidate: `f71c52fad680a74da1b90cc7470455fc90f4fa3f`, parent HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. This is a fresh bounded source-verification pass, not a design pass, runtime receipt, whole-BAC acceptance or entire-README reverification.

Verdict: the proposed target/recurrent/readiness/ownership corrections are substantially supported within the five-source boundary. Apply the narrowly scoped wording corrections below before publishing the corresponding claims. No P1 defect, capability removal, degraded acceptance or unsafe native invocation was found in this draft. Pending qualification remains pending. This verdict does not qualify T15.

## Defects and wording gaps

### P2 — Action-validation statement promises more validation than the source performs

Draft, Candidate behavior paragraph beginning “Action selection validates full-N Q/mask/eligibility geometry”: `_validate_selection` (population/vectorized.py:1015) checks eligibility bool/type, shape against `values.shape[:1]`, device, mask bool/type/shape/device against `values`, and eligible rows with no legal action. It does not explicitly validate Q rank, floating dtype, N against `self.num_agents`, or A against `self.action_dim`. The production caller obtains full-N Q from `_rollout_q`; that is a producer/caller property, not the complete independent shape validator promised by the sentence. The provider-return check enforces shape/dtype/device, not selected-action range or legality. Those omissions are not newly demonstrated production defects here; this finding concerns the stronger documentation guarantee.

Source-verified replacement:

> Production rollout computes full-population Q values. Selection checks that bool eligibility and bool action masks have matching Q-row geometry and device, and refuses an eligible row without a legal action. For K>0 it calls the configured provider once with the K eligible Q/mask/state rows, including aligned epsilons, checks the returned int64[K] shape/device, and scatters the actions into full-N transport. Inactive transport entries retain unmasked argmax. With K=0 it does not call the provider. Recurrent inactive hidden state is preserved.

This also repairs the original unconditional “exactly once” claim: `_select_eligible` guards the call with `eligible.any()` (1031), so it makes zero calls with no eligible rows. The checker observes full-N Q/actions and actual successful flat `push_recorded` calls; it uses a scripted selector in these recipes (checker:605–622), so the native checker by itself does not establish genuine-provider selection behavior. Keep independent genuine-provider evidence separately attributed.

### P3 — Scope “gamma zero avoids reading Q” to target arithmetic

`legal_td_target` and `legal_bootstrap` (q_targets.py:19–80) do not read Q entries to choose a successor value when gamma is zero; they still validate tensor metadata. The population nevertheless executes target successor forwards, and Double DQN online successor forwards, before calling the helper (population/vectorized.py:692–710, 741–750). An unqualified sentence can be mistaken for a promise to skip network computation, side effects or failures.

Source-verified replacement:

> With gamma zero the target helper returns the finite canonical rewards without reading Q entries for successor selection; population network forwards still run. Non-bootstrap successor values are exactly zero. On bootstrapped rows all legal selector Q entries and the chosen target Q entry must be finite; nonfinite illegal or unused terminal outputs do not enter target arithmetic.

This also makes explicit that the finite-selection requirement covers every legal selector entry, not only the eventually selected action. No runtime execution or new performance claim supports a stronger statement.

### P3 — Qualify readiness logging and the public warmup lower bound

The draft says the population “logs changed reason/retained/sampleable diagnostics.” `_learn` (715–726) logs these only when unready and the signature changes; ready signatures are saved without a corresponding log. Replace with “logs changed unready reason/retained/sampleable diagnostics.”

The positive warmup bound in the schema paragraph is accurate for authored `ReplayBufferConfig.min_size > 0` (training_v2_config.py:109). The explicit `for_training` setup accepts `min_transitions >= 0` (`_ReplaySetup.create`, population/vectorized.py:141). Do not generalize the authoring bound into a universal public-factory positivity guarantee. Suggested clarification: “Authored min_size is positive and no greater than capacity; the explicit construction seam accepts a nonnegative retained-transition threshold.”

### P3 — Preserve review-date scope when applying BAC replacements

BAC.md still identifies its current/reviewed source sweep as 2026-08-31 and its runtime algorithm cost as verified 2026-08-24. Replacing the stale recurrent claims is correct, but this bounded pass cannot refresh the document-wide stamp or its unrelated schema/compiler/network/provenance claims. Add a local dated note beside the corrected runtime text identifying the five-source T15 candidate review and pending qualification; retain the older broader review stamp as historical. Likewise retain README's dated 6475cc5b source/CI paragraph. PDR-0039 requires a ground-truth sweep, verified-fact draft and adversarial pass at merge; this bounded review is only the adversarial/source check of this T15 draft, not satisfaction of the whole merge gate.

## Claims supported within the boundary

- Recorded successor masks, vanilla legal maximum and Double online-selection/target-evaluation are directly visible in q_targets.py. The population consumes each stored successor, without querying current-world legality for sampled Bellman targets. The imported mask validator's internal guarantees are outside this source scope.
- Recurrent evaluation groups by actual lengths; online current prefixes remain graph-connected, target prefixes are separate, successor branches are under no-grad, online bootstrap hidden tensors are detached, and returned branch states are discarded. Padding is excluded from network evaluation and residual arithmetic. Double adds an online successor evaluation per real timestep per length group. The proposed BAC/CLAUDE replacement correctly removes the old one-boundary-forward/two-unroll/reused-unroll description.
- The objective reduces selected loss rows per unit, multiplies each returned detached unit weight once, and averages units. Real context rows still participate in unweighted TD telemetry. Promotion of both residual operands to float64 before subtraction is present. This supports the bounded large-residual telemetry repair, not a universal finite optimizer/loss guarantee.
- The population calls readiness before sample_batch; no unready update changes optimizer count, scheduler or target cadence. Beta is paced after actual vector-tick increment, before a scheduled draw, including warmup/unscheduled ticks. It is a vector clock, not a row/episode/update clock. Recurrent episode finalization/commit occurs after that tick's learning opportunity; pending rows do not satisfy retained warmup merely by existing.
- Flat admission selects actual active-entry rows and splits by configured capacity, validated against the bound replay capacity. It retains DAC total and component rewards. Recurrent collection retains exact successor observations/masks/recorded bits and commits at completion or explicit flush.
- `for_training` accepts explicit resolved six-leaf policy, RNG/origin, horizon derivation and current tick; setup copies policy and Generator. The compiled adapter uses training seed with PCG64 and explicit episode-limit precedence. Factory network-family dispatch preserves feedforward/recurrent/dueling/token_set. Detailed network and aggregator implementation remains unreviewed here.
- Lazy binding compares constructor identity/state and loaded state, not occupancy alone. Qualified bindings are validated; supported recurrent adaptations are staged offside. Raw POP6 validation and optimizer deep-copy are present. Current replay load is not a full-native resource/RNG atomicity claim; the draft correctly leaves T24/T25 open.
- Per-world omission-derived pending capacities use cardinality1, with authored overrides and separate provenance. This is resolver behavior; it is not runtime isolation proof.

## Supplier/API evidence limits

Read `T15-sequence-serialization-api.md` as attributed root source-verified prose only. It supplies current6/current7 descriptors, sampleable context/cardinality rules, historical inspection envelopes and archive merge semantics. Its sequential implementation links were not followed. Independent direct evidence here establishes how population calls and handles these APIs, not a new review of their implementations.

Flat replay cardinality/priority behavior, actual network zero-state implementation, provider algorithms, compiler override/hash semantics, native checkpoint reconciliation, runner propagation and imported mask-contract internals are not independently established by these five files. Preserve existing approved supplier/evidence attribution; do not label them freshly source-verified by this reviewer. In particular the retained CLAUDE statement that training overrides are included in brain_hash remains existing prose, not fresh verification from this scope.

The proposed preservation paragraph keeps all four architectures, both aggregators, laws/adapters/objectives/retention/reducers, low-level interfaces, reward components, lifecycle paths and the shared-curiosity alternative in scope. It is an acceptance obligation, not proof of every capability's runtime behavior. Genuine ICM transition reward/update/continuation and X02 stay REQUIRED OPEN. No claim here authorizes deletion or consolidation.

## Native command review

All six listed recipe names and capture arguments match the checker parser. They select only existing `/workspace/hamlet`, invoke its interpreter with `-P`, disable bytecode, and name external fresh output locations plus the stated scratch TMPDIR. The checker refuses execution-bearing dirt before output creation; its producer uses selected-root PYTHONPATH, CPU selection and source/config postflight. No allow-dirty bypass, oracle bootstrap, .oracle write, source checkout/copy, worktree creation or deletion appears in the six commands. The checker does internally copy configuration to a temporary recipe directory and create run/output artifacts; the draft accurately delegates normal artifact setup to root. Commands were not executed, and filesystem existence/availability of their interpreter, scratch/config/output locations was not independently qualified.

Exit zero does not require contract.qualified=true: validation permits a self-consistent failed semantic contract. The draft correctly requires inspection of qualified/errors and exact identity. Source digest covers tracked src plus pyproject.toml/uv.lock; configuration and instrument have separate identities. Do not describe that digest alone as covering every tracked execution-bearing byte. Comparison also requires instrument and actual action identity; old captures cannot be made comparable merely by accepting changed coordinates. The inherited overwritten collector.errors limitation is visible; this review establishes no new reachable false qualification and does not upgrade it to a material blocker.

## Qualification custody

As supplied by root, current fullR2 is RUNNING: 6861 selected, four workers, candidate f71c52fad680a74da1b90cc7470455fc90f4fa3f. Six clean-committed genuine native captures remain owed. This reviewer did not inspect live campaign state or execute checks; root must replace the running status only with its actual terminal receipt and identity. FullR0 1ERROR/3536PASS/11SKIP and fullR1 1FAIL/6222PASS/14SKIP remain failed retained campaigns. Scoped checks and static reviews do not turn either into PASS.

Keep 24/66 qualified, T15 unqualified, all 54 effective requirements and 22 final lenses open at this checkpoint. Coverage, slow/applicable hardware, learning/E2E/T40, native-current, final common-source reviews/synthesis and exact-tip remote CI remain owed. CUDA is locally unavailable, not qualified. No final whole-BAC or entire-README acceptance is given.

## Independently measured implementation inventory

Exactly five complete implementation files, 3991 physical lines, were read. SHA256 and wc counts were independently measured from the actual files; all match the reviewed draft.

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| src/townlet/config/training_v2_config.py | 435 | `ad097576f88e1e2a09ae816ccff823e9623e7d5584b0d0411b07efb2f6ba1dfc` |
| src/townlet/config/bac_options.py | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| src/townlet/training/q_targets.py | 80 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| scripts/check_episode_lanes.py | 1036 | `19e0b83130f2467a2bfd890dc79e95de6d7694e79f7fa996fa16c66b43e62eb7` |

Guidance/prose examined: repository AGENTS.md; PDR-0039; the assigned T15 draft; sequence API supplier prose; existing README/BAC/CLAUDE/options/STATUS anchors. No sixth helper/provider/replay/runner/test implementation source was opened. No source/test/tracked-document edit, project import/runtime, test collection, linter, index/commit/push, branch/worktree, source copy/deletion, tracker mutation or subdelegation was performed. Existing fourteen worktrees were untouched. Only this ignored review artifact was written; ignored status was checked before writing. Root retains final documentation application and qualification ownership. Reviewer is stationary after this report.

## Disposition clarification — Q4 boundary (2026-11-02)

Root requested a contract-boundary check of the first P2 wording finding against approved `T15-interface-proposal-r1.md` Q4. That prose expressly requires bool[N] membership and full-N bool[N,A] mask geometry, and expressly skips the selector when K=0. This clarification supersedes any interpretation of the earlier finding as a demonstrated implementation defect or permission to weaken Q4.

The five-source evidence identifies no accepted public input route for externally supplied Q/mask tensors. `step_population(envs)` constructs membership from `~envs.dones`, produces Q via `_rollout_q(active_on_entry)`, obtains masks from `envs.get_action_masks()`, and constructs its temporary state from population-owned tensors. The public `select_greedy_actions(env)` likewise generates its Q internally and obtains environment masks; `select_epsilon_greedy_actions(env, epsilon)` generates its Q internally before calling the imported eligible helper. Neither public selector accepts caller Q/mask arguments. Population initialization creates `current_obs` with self.num_agents rows, builds each network with self.action_dim, and creates recurrent hidden state for self.num_agents. For supported population/environment/network producers this supplies self-N/self-A Q geometry; `_validate_selection` then enforces exact matching bool membership/mask geometry and devices. These producer contracts, rather than independent revalidation of every dimension constant, establish the full-N composition. Actual network/environment/helper internals remain supplier boundaries under the five-source restriction.

The callable accepting arbitrary tensors is private `_select_eligible(values, state, masks, eligible)`, with private `_validate_selection(values, masks, eligible)` beneath it. A direct private call with jointly malformed matching Q/mask/eligibility geometry, replacement of q_network, or mutation of population tensors is not demonstrated here to be an accepted production/public-selector input route. No concrete supported case was found that silently transports malformed geometry. Consequently the original P2 is **not sustained as a material accepted-contract gap**. Its distinction between producer-established geometry and explicit validator checks is optional P3 documentation precision; it creates no source-repair requirement, new programme or qualification blocker. Preserve the required full-N invariant in final prose.

Recommended complete wording: “On supported production inputs, population-owned rollout and environment masks provide full-N Q/mask geometry. Selection validates matching bool[N] membership and bool[N,A] masks/device, rejects eligible live-empty masks before provider selection, and for K>0 calls the configured provider once with aligned eligible rows before scattering into full-N transport; K=0 makes no provider call.” This preserves Q4 rather than replacing its invariant with a weaker relative-shape promise. There remains no fresh runtime result from this review.

Only this clarification was appended to the existing ignored report. The earlier report remains preserved above; no additional implementation source, runtime, edit or delegation was used. Stationary.
