# Updated BaC design baseline for reconciliation

**Baseline ID: BAC-2026-11-01-r2. Source under review: `4aa5363b5de54d9a112977c32c2975f37627197f`. Contract IDs BAC-C01–BAC-C13 are unchanged.**

This is Astra's revised design direction, made concrete for the user's request to reconcile the codebase against the updated design. Use **BAC-C01–BAC-C13 below as the common review baseline across B01–B12**. It is a design/review artifact, not an implementation receipt or authorization to begin production fixes. [architecture.md](architecture.md) remains the historical first-pass review; the corrections here take precedence for consolidation.

**Direction: extend the declarative DRL foundation and repair its contracts, preferring additive remedies.** Preserve the compiled world/token boundary, four Q-network families, shared learner and explicit lane lifecycle. The current layer-2 focus and unbuilt cognition describe implementation status and this review's evidence scope; they do not prohibit adding graphs, registries, features, complexity, algorithms or options. The needed seams are effective configuration, transition records, owned completion records, clocks, load modes and durable output ownership.

## Approval boundary — binding user instruction for r2

The user states: **“the design isn't fixed, as a rule you can always extend or add new features, complexity or options. If you want to remove, degrade or consolidate, please surface to me for approval”.** This overrides earlier removal/no-defaults-as-deletion recommendations and applies to every contract below, including any remaining refusal language.

- Additive implementation, extra explicit modes and stronger capabilities do not need an additional removal approval. This review itself still changes no production code.
- **APPROVAL REQUIRED:** removing, restricting, degrading, renaming away or consolidating usable behavior, public APIs or accepted authoring options. Present the concrete affected surface, retained alternative and tradeoffs before taking that action. A detected defect/design mismatch does not approve its reductive remedy.
- Fixing negative-dimension crashes or nonfinite-parameter corruption does not remove a working capability. Do not extend that reasoning to working zero-width constant policies, inactive/preset content, sampling choices or other actual narrowing.
- “Deferred” means not currently qualified/delivered, never forbidden to extend. Prefer implementing or explicitly describing accepted options over deleting them. Truthful inactive/preset status is permissible; silent ineffectiveness is not a substitute for such a contract.
- Deduplicating **defect lists** was explicitly authorized and remains allowed. It is distinct from consolidating code capabilities/options. Observed evidence and refutations remain; classification is recalibrated where the updated contract permits the behavior. In particular, B01-D3 moves to a design/identity-semantics gap as stated below.

Status labels distinguish authority:

- **E — existing contract:** supported by current product/specification or an explicit existing API promise. A failure can be an implemented defect now.
- **C — clarification:** resolves conflicting terminology or makes an existing boundary precise. It is the reconciliation choice for this baseline; it does not prove old code was wrong under an ambiguous specification.
- **R — revised design judgment:** a new or strengthened expectation chosen by Astra for this review baseline. A current mismatch is a design gap unless independent evidence also establishes an existing-contract violation. It is not retroactively a regression.

For every reconciliation row record contract ID, owner, observed behavior, evidence strength, severity, known/new status and disposition: **holds / existing-contract defect / revised-design gap / deferred capability / refuted / unqualified**. Runtime reachability and source proof remain separate; a new normative sentence never upgrades a weak witness.

## BAC-C01 — Realized scope and supported-family boundary [E/C]

**Expected behavior:** BaC declares and constructs `feedforward`, `dueling`, `token_set` and token-native `recurrent` Q-networks, the supported optimizer/loss families, Q-learning controls and supported replay. Compiler-owned observation/action geometry feeds those networks. A combination counts as operationally supported only through compile, construct, rollout, eligible learning where applicable, save/load and serving—not because its DTO parses. Publish a support matrix and make unsupported states clear before runtime allocation. Recurrent PER is currently compile-accepted and runtime-unsupported: implementing it is an additive remedy; closing its accepted authoring door is **APPROVAL REQUIRED**, not the selected remedy.

**Supported / deferred:** layer 2 and bounded family parity are required. Cognitive topology, personalities, compliance/governance, named cognitive modules, execution DAGs and zero-shot transfer competence remain deferred. Shared weights across N independent single-agent worlds remain supported; this does not make their environment state shared.

**Owners:** B01/B02/B03/B04/B07/B08/B09; B11 world boundary. **Prior authority:** README architecture/completion; BAC §§2–3; STATUS §3 S1. Clarifies what “supported” means; supersedes no future-layer target. **Acceptance:** positive family/combination matrix and truthful diagnostics, with explicit unqualified cells; use refusal tests only for invalid inputs or a specifically approved narrowing.

## BAC-C02 — Effective authored configuration and strict, lossless validation [E/C/R]

**Expected behavior:** recognize and strictly validate all authored content before lowering it; lowering must never erase an authored key to make validation succeed. Invalid content receives a located diagnostic; new authoring placements/options may be supported additively. Exactly the selected architecture/optimizer/schedule variant is active in that execution. **Preserve accepted inactive blocks/options as explicitly inactive or preset content**, with validated contents, selection semantics and authored-versus-effective identity. Rejecting/removing that content instead is **APPROVAL REQUIRED**. Selected numeric geometry must be constructible. Negative widths, Nesterov without required momentum and infinite learning rate may refuse before runtime construction because the demonstrated combinations do not supply working capabilities.

Preserve the current complete level-brain replacement and five existing training overrides: gamma, target-update interval, Double DQN, learning rate and replay capacity. They are the current contract, not a ceiling on additional options or explicitly defined merge modes. Produce or deterministically derive one effective run view used by compiler identity, factories, runner, serving and telemetry. It records origin/override precedence and active/inactive status. A stored selected **base** brain plus training is valid; consumers must not confuse that base with the effective brain. Distinguish authored content identity, effective configuration identity, cache freshness and transfer compatibility; retained presets belong to authored identity without masquerading as executed computation. This baseline does not demand that all descriptive text be removed from hashes.

**Evidence recalibration — B01-D3 / historical A4 inactive-field component:** accepted nonselected family blocks, optimizer options and schedule presets can be legitimate retained authoring content. Their changing a content hash while leaving the selected computation unchanged is not inherently wrong behavior. No active chosen knob was demonstrated ignored by this finding. Classify it as a **revised-design/identity-semantics gap**, not an automatic P2 implemented defect or missing-refusal obligation. Specify whether each existing hash denotes authored configuration or runtime-effective behavior before judging its inclusion of presets. The separate negative-width/Nesterov/nonfinite findings retain their own observed failure evidence.

**Design resolutions:** behavioral numerics used in the demonstrated optimization paths must be finite [R]; gamma `[0,1]`, including zero as a valid myopic experiment, must agree across brain and overriding training DTO [C/R]. **Preserve the demonstrated zero-width constant-policy capability** and make its behavior explicit. Rejecting zero-width layers or replacing that capability with a narrower family is **APPROVAL REQUIRED**; zero width is not the negative-width crash.

**Supported / deferred:** preserve current authoring options; additions need explicit semantics rather than silent precedence. **Owners:** B01/B07, consumers B03/B08/B09/B10/B12. **Prior authority:** BAC §2.1; brain override/provenance contracts; declarations strictness; STATUS no-defaults, subject to the newer user approval boundary. **Acceptance:** every admitted knob has an observed active effect, explicit inactive/preset/derived role, or a justified diagnostic; compile→effective object→consumer→identity tests cover retained inactive content, constant policies and invalid/nonfinite controls. Removing an admitted surface is not an automatic acceptance strategy.

## BAC-C03 — Content discovery is the end-to-end authoring interface [E]

**Expected behavior:** all supported launch, train, resume, serve and evaluation entry points obtain resolved declarations and provenance from the same content-discovery/compilation surface. Renaming or nesting a valid `experiment`/`training`/`brain` declaration, or using supported multi-document YAML, must not produce a filename preflight failure after successful compilation. Scope and declaration content determine meaning; filenames remain transport. Missing/duplicate/misplaced families still refuse through the canonical located diagnostic.

**Supported / deferred:** preserve and extend currently supported declaration transport; no new dynamic plugin loader is required by this evidence. **Owners:** B07/B12, B09 consumers. **Prior authority:** README authoring layout/discovery; declarations.md; current training schema scope. Overrides old fixed-filename examples as requirements. **Acceptance:** one pack through compile/cache→CLI→runner/serving before and after transport-only changes; effective semantics remain equal. A changed cache fingerprint is permitted. Existing direct loaders can gain canonical discovery behind their public interfaces. Removing/consolidating those APIs is **APPROVAL REQUIRED**, even when no production caller was found.

## BAC-C04 — Observation/context integrity and representation capability [E/R]

**Expected behavior:** preserve the compact dynamic observation ABI; attach the correct immutable target-universe context at the token-native network boundary. Presence gates both live payload and static context. Absent rows contribute zero encoder gradient, and an empty set remains finite. Flat/dueling policies are serialization-layout-bound; token-native transfer is type-schema-bound. Semantic row permutations carry their associated context.

**Revised capability requirement:** a general-purpose token representation must not be invariant for *every parameter setting* to swapping live values between simultaneously present, behaviorally distinct same-type descriptors when the task needs those associations. Token-order permutation invariance is required; descriptor/value reassignment invariance is not. This is an expressivity requirement, not a demand that every random network give distinct outputs, nor a learning guarantee.

B02 proves current Linear→mean pooling loses these associations before the nonlinear Q-head. The literal old recipe is implemented correctly, and its current limitation must be described honestly. **Preferred additive direction:** retain and extend the mean encoder so a mean-pooled family can express descriptor/value interactions, supplying the proof/witness before choosing an encoder. Additional encoder modes may preserve the existing linear sum-statistic behavior alongside the stronger capability. Relegating mean to a restricted ablation, removing it, changing selection to attention or otherwise degrading/consolidating existing choices is **APPROVAL REQUIRED**, not settled by this baseline. Attention's positive control proves one viable distinction, not that all packs must use attention or that it solves all aliases.

**Supported / deferred:** compact ABI and current families remain; additional spatial/token representations or cognition topology are permitted extensions, not requirements inferred from this finding. **Owners:** B02, B01/B07 capability declarations, B08 context/transfer. **Prior authority:** token design binding amendment/PDR-0131; §1 descriptor rationale and §4 recipe/advisory; brain aggregator reference. **R corrects the old advisory's capability claim; it does not allege noncompliance with its old literal Linear recipe or authorize removing that option.** Acceptance includes B02's authored complementary-variable swap, legitimate semantic permutation, masking/empty cases and recurrent frame-memory separation, plus preservation of existing choices unless a change is approved.

## BAC-C05 — Transition identity and exact successor legality [E/C]

**Expected behavior:** every admitted transition represents a lane active entering the step, including its terminal step. It owns predecessor observation, chosen action, canonical reward/components, successor observation, terminal/bootstrap meaning and **the successor's legal-action set**. Store the successor mask or an equally sufficient immutable historical representation; never ask the current live environment to reconstruct a sampled successor's legality.

Rollout random selection assigns exactly zero probability to disabled actions. Greedy selection, vanilla max and Double-DQN online argmax use the legal set; target evaluation follows that selected legal action. Apply this to every family, PER and every recurrent interior/window boundary. Authored terminal/retirement suppress bootstrap; runner cap/budget truncation preserves valid successor bootstrap. Terminal successors need no valid selectable action because they do not bootstrap. A live nonterminal state with no legal action must terminate under an explicitly declared rule or refuse diagnostically; silently choosing an unmasked action is not the new baseline's policy [C].

**Supported / deferred:** existing action vocabulary/masks; arbitrary new authored action-predicate language remains deferred. **Owners:** B11 legality producer; B03 learner; B04 storage; B05 selection; B09 serving. **Prior authority:** enabled-actions contract, Q-learning semantics, PRD-0005. Clarifies their shared transition boundary. **Acceptance:** B03's actual 51-versus-3 target/wrong-direction witness becomes 3 with the correct update direction, across global/state-dependent illegality, both DQN variants, sequence interior/boundary and terminal controls. Capture sampler probabilities; do not require a rare invalid native draw to prove nonzero illegal mass.

## BAC-C06 — Replay objective, readiness and finite capacity [E/C/R]

**Expected behavior:** replay retains only eligible transitions and intact episode boundaries, including successors. Capacity and `min_size` mean **retained eligible transitions** for every family; nonrecurrent batch size counts transitions, recurrent batch size counts sequences. Learning requires declared warmup, scheduled update opportunity and a genuinely sampleable batch. A fixed hidden minimum of 16 episodes is not a substitute. Temporarily short episodes cause an explicit no-update/readiness result, not a run crash. Add storage/sampling capabilities where needed for accepted geometry, or surface exact impossibility under the selected fixed-window semantics; do not silently starve. Closing accepted geometry/options instead of extending them is **APPROVAL REQUIRED**; no added mechanism may falsely claim a full length-eight window from one retained transition.

**Sampling design judgment:** preserve uniform replay's declared uniform objective and expose explicit, mathematically supported PER semantics/options. Independent draws **with replacement** are an additive option matching the existing `P(i)`/inverse-probability formula [R]. Retaining **without replacement** requires its own documented inclusion probabilities and matching estimator. Do not combine one sampler with the other's weights. At beta=1, expected weighted gradient must equal the declared uniform-buffer objective up to a declared deterministic normalization factor; normalization for that claim cannot depend on the random sampled batch. Mandatory replacement of the existing sampler or consolidation into one sampling mode is **APPROVAL REQUIRED**. Sample/probability/priority numerics must stay finite or diagnose failure before corrupting replay [R].

**Supported / deferred:** fixed-window zero-start recurrent learning remains supported. Burn-in, padding, recurrent PER, alternative retention and memory controls may be added; current absence is not a ban. Preserve existing retention choices or obtain approval for narrowing. **Owners:** B04/B03, B01/B07 cross-field checks. **Prior authority:** brain replay/PER formulas, training sequence/capacity/warmup, PRD-0005. Clarifies units and requires matching sampling mathematics without choosing a single mandatory sampler. **Acceptance:** per-mode exact estimator tests, finite numerical controls, warmup1000, 16 short episodes/sequence3 without crash, viable small-capacity sequence learning and truthful geometry diagnostics; refusal is not the assumed remedy for an accepted option.

## BAC-C07 — Owned lane completion and the learning-clock ledger [E/C]

**Expected behavior:** population owns once-only completion snapshots. Later world ticks cannot rewrite a completed lane's survival, final values or rewards. Curriculum, recorder, database and metrics consume the same outcomes; adding another death route must not duplicate completion. Reset closes or refuses unfinished nonempty episodes before mutation and resets per-lane recurrent accumulation/memory once. Shared learner updates from valid history may continue while another lane is complete.

**Clock choices for this baseline:**

| Clock/control | Unit and advancing event |
|---|---|
| World/vector tick; `train_frequency` | One accepted vector step; retained current cadence |
| Live-transition budget | Sum of lanes active entering accepted steps |
| Replay warmup/capacity | Retained eligible transitions; sampleability is a separate condition |
| Optimizer, target synchronization, LR schedule | Successful learner optimizer updates; no advancement during warmup or skipped samples |
| Lane survival/stage dwell | Eligible transitions of that lane; completion reports its actual length |
| Epsilon decay / runner episode index | One completed batch episode, applied exactly once before a continuation checkpoint |
| RND predictor update | One consumed predictor minibatch; eligible-sample admission has its own count |
| PER beta pacing | Vector ticks against a declared or explicitly derived vector-tick horizon, recorded as such; not mislabeled live transitions or learner steps |
| Recording/checkpoint interval | Completed batch episodes, with explicit initial/final-save policy |

LR schedules use successful optimizer updates: **this clarification supersedes brain.md's episode-unit examples**, retaining the verified runtime choice. PER's `max_episodes * max_steps_per_episode` may be a named upper-bound horizon; it is not actual realized experience or a guarantee beta reaches1 when episodes end early. No blanket `total_steps` conversion.

**Supported / deferred:** current synchronous batch episodes; partial per-lane auto-reset is not required. **Owners:** B03/B09 event/clock owners; B04/B05/B06/B10/B11 consumers. **Prior authority:** PRD-0005 and its planning resolution, brain target-update clarification. **Acceptance:** authored lengths `[2,5]`→7 transitions/5 vector ticks/2 completions, reversed order and two resets; separate warmup/train-frequency/target/scheduler witness so equal counters cannot mask unit errors.

## BAC-C08 — Exploration, predictor admission and reward ownership [E/C/R]

**Expected behavior:** one explicit runtime owner resolves the supported exploration strategy and intrinsic-weight parameters; environment reward composition owns the single canonical total consumed by replay. Predictor admission and normalization consume the specified eligible observation rows only; completed lanes contribute none later. Adaptive completion consumes each owned lane outcome once. Telemetry distinguishes raw novelty, effective intrinsic contribution and total reward.

There is no current `intrinsic.enabled` or `intrinsic.annealing.enabled` training field. Both are refused today; do not invent ignored-toggle findings, although adding such options is allowed. Initial weight zero is valid; it means zero intrinsic reward contribution, not by itself a promise to skip predictor computation. Preserve accepted drive/training strategy choices and resolve their active/inactive semantics under C02, preferring additive implementation; removing or narrowing them requires approval. Broader intrinsic strategies are not presumed implemented.

**Predictor design judgment:** add an occupancy-driven FIFO mode that drains complete minibatches and retains the incomplete tail [R]. Preserve paced-update behavior as an explicit option with a defined bounded retention/backpressure policy; do not silently replace potentially useful pacing with mandatory full draining. Record admission/update/retention counts and include pending observations in the chosen continuation contract. Explicit authored retention/drop options may be added; current unbounded backlog is not a bounded policy. Removing/consolidating pacing options requires approval. Flat compact RND input remains supported even for token-native policies; token-native intrinsic encoders may be added.

**Owners:** B05/B03, B09 config/checkpoint, B11 composition, B10 diagnostics. **Prior authority:** PRD-0005 eligibility and RND cadence; token spec §3b; README intrinsic-integration limitations. R makes service/retention choices explicit; pending-tail loss remains a design gap against the old weaker restart claim. **Acceptance:** identifiable seven-row ingestion/update witness; occupancy-driven mode consumes512 rows as four batches of128; paced mode obeys its declared update/retention limits; once-only completion; zero-weight composition; pending-tail continuation.

## BAC-C09 — Curriculum event ownership and per-world application [E/C/R]

**Expected behavior:** curriculum receives completed-lane outcomes through one completion interface. It retains completed survival statistics for later decisions instead of reading reset episode accumulators. Survival fraction uses the declared planned episode horizon, not fixed100; supplied ending reason identifies truncation. Stage dwell advances by the lane's eligible transitions, not the number of completion calls. Compare performance with a baseline in the same declared units. Bounds include singleton bands: `[0.6,0.6]` yields0.6.

Per-lane decisions must reach the corresponding independent world's dynamics. A shared scalar may be used only when all lanes intentionally share that decision; lane0 is not a broadcast authority for differing stages. A difficulty label is not evidence of calibrated task difficulty. Preserve accepted adaptation-rate controls and add a defined unit/consumer or explicit inactive role under C02; removing/refusing those controls is **APPROVAL REQUIRED**.

**Design scope:** completion-driven stage commitment is a proposed explicit mode [C/R]; per-step execution uses its committed decision. Other commitment schedules may be retained or added with named clocks. Shared-learner policies can remain shared, but world interventions and their identities are per world. Generic authored stage graphs, active-meter rosters and reward-mode switching are not yet qualified and may be implemented additively. Preserve their accepted knobs/outputs while making current inactivity truthful; removing, degrading or consolidating them is **APPROVAL REQUIRED**. Adding a stage topology does not itself repair the demonstrated survival/depletion bugs; both need evidence.

**Owners:** B06 curriculum; B03 forwarding; B11 dynamics; B09 completion routing; B10 reporting. **Prior authority:** PRD-0005 once-only truthful inputs; CurriculumManager per-agent contract; STATUS S1; known curriculum-authoring gap. Clarifies completion metrics and commitment; does not claim generic-stage capabilities are already delivered. **Acceptance:** full-survival completion followed by meaningful decisions, actual10-step dwell, singleton bounds, and heterogeneous valid stages `[1,5]` applied through the real population/environment to multipliers `[.2,1]`. B06's existing factory/environment replay is evidence, not yet that full-population witness.

## BAC-C10 — Checkpoint boundary, selection and explicit resume modes [E/C/R]

**Expected behavior:** periodic and final checkpoints describe the same boundary: completed episodes and all corresponding episode-end updates are committed; the artifact unambiguously identifies the **next** runner episode. Restore neither skips nor repeats epsilon decay, completion or curriculum updates. Latest means numeric sequence/episode identity within the selected run, never lexical filename order. Authored checkpoint cadence governs periodic saves; final-save policy is separate. Validate identity and owned payloads before applying runtime mutations.

**Modes:** (1) **learned-state fresh-episode restart** is the supported baseline; restore weights/target, optimizer/scheduler, replay, exploration/normalization/annealing, curriculum, persistent world state, clocks and next-episode identity, then reset episode-local state exactly once. Predictor pending tail is included under revised C08. (2) **Exact stochastic continuation** is deferred until all RNG streams, replay index-to-transition mapping and other scheduling/state dependencies are inventoried and restored. Mid-episode execution continuation is also deferred. (3) **Inference load** restores policy identity for evaluation/viewing under C12 and does not pretend to continue training. (4) **Cross-universe transfer** is a distinct operation under C11.

Persist the chosen mode and its guarantees [R]. Current VFS `{seed,episode}` restoration is not a claim about torch/Python/numpy/effects/items streams. A checksum proves file agreement, not external trust; trusted-local loading assumptions stay explicit. This baseline does not reopen checkpoint security as a new audit.

**Owners:** B08/B09, state owners B03/B04/B05/B06/B11. **Prior authority:** README strict identity/separate transfer; PRD-0005 fresh-episode restart; STATUS §7.4. Clarifies next-episode semantics and separates modes; stronger full-RNG continuation remains explicitly deferred. **Acceptance:** periodic restart epsilon .4 rather than .8 in B09's witness; newest100000 beats99999 with correct weights; periodic/final boundary comparison; malformed-state no-mutation controls; no exact-stream claim until its independent differential passes.

## BAC-C11 — Safe, loud token transfer [E/C/R]

**Expected behavior:** transfer validates source type-schema semantics as well as parameter geometry before mutation. A complete shared-type load cannot silently retain fresh bias and claim clean. Preserve partial transfer as an explicit option if useful, reporting each retained/cold-started parameter and a non-clean result; strict-complete mode may refuse missing parameters. Removing accepted partial-load behavior outright is **APPROVAL REQUIRED**. New target types may cold-start and source-only types may drop, both reported explicitly. Non-type modules have explicit loaded/cold-started status. Target compiled static context remains target-owned; weight transfer never overwrites it. Q-head shape compatibility is mechanical compatibility, not preserved action/reward meaning or zero-shot competence.

Add a higher-level fresh-target transfer mode: fresh replay, optimizer/scheduler, learning clocks, rollout memory and RND/annealing state, with target weights recopied from transferred online weights. Any pacing carried from the source is an explicit recorded choice [R]. Other live-target/state-retaining modes may be preserved or added with explicit compatibility and state-ownership policies; the fresh-target recommendation does not authorize deleting working alternatives or silently discarding their state. Low-level state-dictionary helpers may assume validated metadata only behind this higher-level boundary; they cannot alone establish artifact compatibility.

**Supported / deferred:** current same-engine token/recurrent transfer remains; provenance-carrying and explicit state-policy modes extend that utility scope. **Owners:** B08/B03, B02 schema/context, B07 artifact, B09 consuming modes. **Prior authority:** token design §4 transfer and §5 tested contract; README transfer separation. Clarifies complete loaded-type meaning and strengthens caller preconditions. **Acceptance:** strict-complete mode refuses incomplete state before mutation; explicit partial mode reports every missing/cold-started parameter truthfully; incompatible same-shape schemas are diagnosed; target buffers remain unchanged; fresh-target mode has empty learner history. B08-O1/O2 remain qualified boundary observations, not retroactive production failures.

## BAC-C12 — Serving/evaluation parity and declared experiment interventions [E/C/R]

**Expected behavior:** deterministic/greedy inference explicitly uses evaluation mode; training updates explicitly use training mode. Loading a checkpoint must not leave dropout active in a supposedly deterministic served policy. An explicit stochastic/MC-dropout serving mode may preserve and make useful the current stochastic behavior; removing a useful mode rather than making its semantics explicit requires approval. The supported family uses the same observation/context, legal-action rules and recurrent hidden-state advancement in train/serve. Displaying Q-values does not advance recurrent memory again. One episode reset means one world/row/random-episode advancement.

For policy-quality evaluation, use an explicit evaluation run view: policy identity, seed/world identity, cap, exploration, curriculum difficulty and reward metric. Defaults derive visibly from the selected compiled run; interactive viewer deviations are named overrides, not silently equivalent evaluation. Episode cap500 is not an implicit universal evaluation contract. Evaluation/serving activity must not perturb training RNG/state [R]; isolate streams or processes and qualify interleaving before claiming that property.

Real experiment interventions and checkpoint/model handoff cadence must be declared and recorded. **Correction:** the episode5000 call honors `randomize_affordances:false`; B09's actual fixed-layout witness refutes the original architecture hypothesis. Do not count it as a layout mutation. Its misleading “generalization” log is documentation/telemetry drift, and no effect under every other substrate is inferred.

**Supported / deferred:** four-family serving and honest mode/identity are required; browser UX completeness and new intervention languages are deferred. **Owners:** B09/B12, B02/B03 modes/memory, B08 identity, B10 reporting, B11 reset. **Prior authority:** current inference API, brain dropout contracts, README viewer qualification limitations. C/R establishes an explicit evaluation contract without falsely declaring the current viewer a qualified evaluator. **Acceptance:** repeated same-observation greedy eval with dropout configured, one-reset counter witness, train-update mode control, named-viewer overrides, and a training/serving interleaving differential.

## BAC-C13 — Truthful and durable outcomes, telemetry and recording [E/C]

**Expected behavior:** immutable completion outcomes and canonical reward components feed database, per-agent metrics, selected recordings and export inputs consistently. Every reported counter names its C07 unit; hyperparameters show actual effective settings; model displays identify the loaded checkpoint and its age/sequence. No post-terminal row is labeled new experience. Do not infer numerical conflation merely from a generic label when the counters happen to be equal.

Accepted recording work remains owned until it is durably written/indexed or an explicit failure is returned. Ordinary shutdown drains accepted frames/end markers before stopping the writer and closing its database; successful thread exit alone is not a durability receipt. File/index disagreement or dropped accepted output prevents a success claim. This contract requires correct selected-output persistence, not a new recording-selection engine.

**Supported / deferred:** current periodic selection and canonical accounting; richer performance/stage/boundary selection is not yet qualified and may be implemented additively. Preserve accepted selection fields and make their current active/inactive status explicit under C02. Deleting, refusing or consolidating those options is **APPROVAL REQUIRED**; implementing them does not require that removal approval. **Owners:** B10; B03/B09 completion/cleanup producers; B06 curriculum; B08 checkpoint identity; B12 exports/evaluation. **Prior authority:** PRD-0005 AC4–6 and ordinary-cleanup acceptance; existing recorder drain promise. **Acceptance:** `[2,5]` sink reconciliation, reward/end-reason round trips, ordinary immediate shutdown with queued entries, one matching file/index, failure propagation. B10's 10/10 direct API failures and passing naturally timed runner control establish a timing-dependent defect, not universal output loss.

## Concrete reconciliation map

One root cause may map to several contracts; count it once. Report IDs remain stable even when the updated design changes their disposition.

| Evidence / finding | Primary contract | Related contracts | Reconciliation disposition |
|---|---|---|---|
| B01-D1/D2/D4 invalid widths, Nesterov, infinite LR | C02 | C01 | Existing validity/refusal defects; finite-only rule made explicit |
| B01-D3 inactive blocks / historical A4 inactive-field component | C02 | C10 | **Reclassified: revised-design/identity-semantics gap, not confirmed implemented defect.** Nonselected presets and content-hash movement may be legitimate; no active ignored knob proved. Preserve options; removal requires approval |
| B01-G1 scheduler units | C07 | C02 | Clarification: optimizer updates win over stale episode examples |
| B01-G2 gamma zero | C02 | C01 | Clarified target `[0,1]`; current training schema is a design/spec mismatch |
| B01-G3 recurrent PER + coordinator ordinary-runner receipt | C01 | C02/C06 | Concrete P2 compile/runtime support mismatch; implement recurrent PER additively, or seek approval before closing accepted authoring |
| B02-G1 linear mean alias | C04 | C02 | Revised representation gap; literal old recipe is implemented |
| B03-D1 illegal targets | C05 | C06 | Reproduced P1 existing-contract defect, 8 real-update cases |
| B03-D2 short-sequence crash | C06 | C07 | Reproduced P1 readiness defect |
| B03-D3 / B09-X01 ignored min_size | C06 | C02/C07 | One reproduced warmup defect, multiple witnesses |
| B03-G1 / B04-G02 recurrent capacity/readiness | C06 | C02 | Consolidate geometry/starvation causes without merging distinct triggers |
| B04-D01 PER estimator mismatch | C06 | C07 | Existing mathematical defect; add explicit matching sampling/estimator modes; mandatory single-sampler consolidation requires approval |
| B04-C01 finite-priority overflow | C06 | C02 | API-level candidate; do not promote production reachability |
| D05-01 positive masked probability | C05 | C08 | Distribution/source-proved defect; no native illegal-draw incident claimed |
| G05-01 pending RND tail | C08 | C10 | Revised continuation gap, independent of missing RNG |
| G05-02 / C05-01 predictor backlog/cadence | C08 | C07 | Revised bounded-service requirement resolves previously ambiguous cadence |
| B06-D01/D02 curriculum metrics/clocks | C09 | C07/C13 | Existing event/unit defects; do not add duplicate completion calls |
| B06-D03 singleton band | C09 | C02 | Existing bound violation |
| B06-D04 lane0 depletion broadcast | C09 | C05 | Boundary-proved dropped decision; full-population witness still needed |
| B06-G01/G02 generic stages / inert rate | C09 | C02 | Additive stage/rate implementation permitted; preserve accepted knobs; removal/degradation/consolidation requires approval |
| B07-D1 erased nested sidecars | C02 | C03/C13 | Reproduced strict-validation defect |
| B08-D1 partial shared-type transfer | C11 | C02 | False clean report remains reproduced; explicit truthful partial-load mode can preserve capability; do not claim normal producer emits partial input |
| B08-O1/O2 transfer/import integrity observations | C11/C02 | C10 | New-boundary qualification work; no newly proved ordinary cache regression |
| B09-D01 epsilon restart | C10 | C07/C08 | Reproduced P1, replaces A3's source-only status |
| B09-D02 lexical newest selection | C10 | C12/C13 | Reproduced P1 older-weight load |
| B09-D03 serving dropout | C12 | C01 | Reproduced inference-mode defect |
| B09-D04 checkpoint interval | C02 | C07/C10 | Reproduced surviving part of historical A2 |
| Historical A2 fixed-layout mutation | C12 | C13 | **Refuted**; remove from defect totals, retain misleading log as drift |
| Invented intrinsic.enabled toggles | C02 | C08 | **Refuted**; fields do not exist and fail strict validation |
| B09-K01 final index | C10 | C07 | Known P3 discrepancy; repair boundary without double-counting epsilon |
| B09-G01 / B04-G01 exact RNG continuation | C10 | C12 | Known deferred guarantee; do not claim exact continuation |
| B09-G02 double reset / evaluation policy | C12 | C10 | Observed double reset plus clarified evaluation-policy gap |
| B10-D1 recorder shutdown | C13 | C07/C12 | Known/open, currently reproduced timing-dependent P1 |
| B10-G1 periodic-only criteria | C13 | C02 | Unqualified peripheral capability; additive implementation allowed; accepted-option removal requires approval |
| B11 authored2/5 boundary | C05/C07 | C08/C13 | Fresh uniform/PER/recurrent collection, two resets, caps/budgets and retirement controls hold; no new owned defects/gaps, no optimizer/RND update claim |
| B12-D01 / root content transport | C03 | C02/C12 | Confirmed compile→CLI/runner failures for renamed training/experiment and multi-document transport; one root-cause group |
| B12-G01 historical FF-only evaluator | C12 | C01 | Current generic evaluation capability unqualified; historical instrument need not be rewritten into a new evaluator |
| B12-G02 unused direct config loaders | C03 | C02 | Additive discovery support allowed; removal/consolidation of public loaders requires approval; not another production launch defect |

## Delivery and evidence policy

Reconcile every slice against its contract IDs, then repair existing P1/P2 defects and adopted layer-2 design gaps in dependency order: C02/C03 configuration; C04–C06 representations/transitions/replay; C07–C09 lifecycle/clocks/exploration/curriculum; C10–C13 restart/transfer/serving/persistence. Work may run in bounded parallel slices, but cross-seam acceptance is joint. This ordering is not authorization for fixes in this review task.

A delivery candidate needs bounded authored end-to-end witnesses, negative controls, exact state/identity assertions and the required unfiltered checks at one SHA. All four brain families need honest support-matrix results. Exact stochastic continuation, cognition layers and richer recording/stage features are currently unqualified; they may be added, but old target prose alone does not prove a present regression. Accepted inactive behavior needs explicit semantics or additive implementation under C02. Narrowing/refusing an accepted surface is a separate approval-required proposal, not an automatic route to a green review.

Learning qualification comes afterward: finite-budget comparisons against named baselines, separating extrinsic reward, intrinsic contribution and survival, under the recorded run/evaluation config. Historical `64c93e3b` canary results do not establish behavior at this reviewed SHA or explain any new finding's cause.

**Evidence/read limits:** r1 read all B01–B12 reports, INDEX, the coordinator's `coordinator-recurrent-per.json`, and the earlier architecture/spec evidence. r2 updates only this design artifact against the new user rule; it adds no source reads or probes. Source citations carried inside reports are attributed reviewer evidence, not additional Astra implementation inspection. Astra's source inventory remains exactly the original five files / 4354 lines. No production changes or additional training/probes were performed for this document. Stronger R clauses are reviewable design judgments, not claims that they already run or permission for a removal/degradation/consolidation remedy.
