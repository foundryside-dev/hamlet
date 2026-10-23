=================== hamlet-0071c78ee9
ID:       hamlet-0071c78ee9
Title:    observable: true does not make a variable observable — it is the mark-and-sweep evaluation selector, and a mark naming no global-profile variable crashes the env at step 1
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:34.562453+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-13 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

On variables_reference.yaml, observable: true emits NO observation field for any scope (verified for global/agent/agent_private/pair/affordance; total_dims unchanged). Its only function: enter vfs_observation_marks, consumed as the mark-and-sweep evaluation set for the GLOBAL PROFILE — a different file's variables (see the G-2a ticket). The two roles collide: a mark naming no global-profile variable is KeyError 'VFS mark(s) not found in profile' at step 1. extract_observation_marks silently drops pair/group/affordance/zone/message marks. A key named 'observable' whose function is 'evaluate this, and crash if you cannot find it' — misnamed, cross-file, and load-bearing.
=================== hamlet-0268336cd1
ID:       hamlet-0268336cd1
Title:    env.reset() does not restore a global VFS variable's declared initial_value, and there is no declarative way to say 'episode-scoped global'
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:24.129720+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G7); independently reproduces the blind run's G-10.

Measured: grow the container to 243 occupied cells, call env.reset(), read back — still 243. lifetime: persistent is doing exactly what it says. The gap is that there is no declarative alternative: an author cannot say 'this global is episode-scoped and resets with the episode'.

RELATED, SAME FAMILY, DIFFERENT MECHANISM: hamlet-d76684f549 (effects survive env.reset() with elapsed_ticks continuing). That one is about spawned effects; this one is about global VFS variables. Together they are the 'what survives the episode boundary, and can an author declare it?' question that docs/product/current-state.md has carried as an open question across three reproductions.

Bears on facet B-F3 (rooted-at-a-declared-origin) and is FLAGGED, NOT SCORED — the audit's scope was B-F2 only. NOT FIXED — substrate freeze.
=================== hamlet-02bd5a3eaa
ID:       hamlet-02bd5a3eaa
Title:    zone scope is dead vocabulary: declared in VariableScope, no manager, no runtime consumer (Trial B by-catch)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-18T15:25:37.125604+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
VariableScope.ZONE ('Per-zone state [num_zones, ...]', vfs/schema.py:40) is accepted in variable declarations but no ZoneManager or zone runtime exists anywhere in src/townlet/ — same dead-vocabulary shape as CapabilityConfig (hamlet-6b24c0bd83). Assessed by source read during Trial B surface scouting (not hit in-pack, so not counted as an encountered INERT surface). Idea K (world-acts-on-agent) pre-registers zone scope as a doubted surface — this issue is the evidence it will hit. Record: docs/product/trials/0001/B-20260819.md.
=================== hamlet-2ca2cb373f
ID:       hamlet-2ca2cb373f
Title:    Engine/VTC writeback never validates against the declared schema: set_engine_value skips declaration shape/dtype checks and VTC write expressions anchor to phase-snapshot shapes
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T11:11:47.122901+00:00
Labels:   recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Files the general case behind hamlet-57a5126baa (now closed): the effects route commits through registry.set with full declared-schema validation, but the engine/VTC writeback route never consults the declaration at all. Recorded as the doc's own remaining-work item: docs/architecture/vfs.md §6.3 ("The unvalidated path is set_engine_value(), which the engine/VTC writeback uses") and §21.1 item 4.

THE CHAIN, verified at this tree:

1. VTC write expressions are validated only against the PHASE SNAPSHOT, never the declared schema. vtc.py:851 _coerce_expression_tensor checks value.shape against target.shape where target = phase_snapshot[write.variable_id] (vtc.py:485) — i.e. whatever storage currently holds — and COERCES dtype to the snapshot's dtype rather than validating it. Same pattern at the social-residue variant (vtc.py:1516).

2. The commit path skips declaration checks by design. registry.py:567 set_engine_value checks existence and engine write permission, validates shape ONLY for sparse pair variables, and coerces dtype via .to(dtype=expected_dtype). Both production call sites go through it: the evaluator writeback (vectorized_env.py:1084) and EVERY VTC phase commit (_commit_vtc_transition_state, vectorized_env.py:1207).

3. The carve-out that motivates the bypass is itself the drift vector. The docstring's stated reason: expressions on variables declared as global scalars can legitimately produce per-agent batches when they read batched bar state. So a variable declared scope: global, type: scalar can hold a (num_agents,) tensor at runtime — the declaration is not an invariant. Once storage has drifted, the phase-snapshot anchor in (1) validates FUTURE writes against the drifted shape, so the declared schema can never pull state back.

WHY IT MATTERS BEYOND TODAY: every future rule source that compiles into a VTC phase inherits this path. The declared schema is the authoring contract (No-Defaults Principle: the declaration is what the author reasoned about); a write surface that never checks it means a compiler bug or a bad write expression corrupts storage silently and the corruption becomes the new validation anchor.

SHAPE OF A FIX (not prescribed): either (a) make declared scope/shape win at writeback — resolve the batched-global carve-out the same way hamlet-cf16cdb6c4 resolved reads (declared scope wins; a batched result for a declared-global scalar is a compile error or an explicit reduction, not a silent storage widening), then set_engine_value can validate like registry.set; or (b) land declared-schema validation in the clamp_and_validate transition phase — the declared-but-empty phase tracked by hamlet-f46e2b381a, whose name promises exactly this "validate" half. Sequence with that ticket either way.

Related: hamlet-57a5126baa (effects route, closed — the contrast case), hamlet-cf16cdb6c4 (declared-scope-wins precedent), hamlet-f46e2b381a (clamp_and_validate phase).
=================== hamlet-3381043d2e
ID:       hamlet-3381043d2e
Title:    Action writes are unreachable from config: ActionsCompiler hardcodes writes=() and no WriteSpec is ever constructed from any YAML surface (Trial O blind re-run)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T15:20:41.291327+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial O blind re-run (gap G-1) and INDEPENDENTLY VERIFIED at HEAD before filing.

MEASURED:
- 'WriteSpec(' appears exactly 3 times under src/townlet/, ALL in src/townlet/vfs/schema.py (the class definition at :220 and two docstring examples at :231/:243). No production code path constructs one.
- src/townlet/universe/compilers/actions.py:205 hardcodes 'writes=()' when building the runtime action space.
- ActionConfig (src/townlet/environment/action_config.py:84) DOES declare 'writes: list[WriteSpec]' with a description ('Variables this action writes with expressions'), so the field exists on the model and is never populated from a pack.

Classification ABSENT: the declared capability exists in the schema and is reachable from no config file.

CORRECTION TO THE SOURCE REPORT: the blind record attributes the refusal to a class named 'CustomActionConfig' forbidding a writes key. There is no CustomActionConfig in action_config.py (the classes are ActionConfig and ActionSpaceConfig) and the writes field is present rather than forbidden. The substantive finding -- hardcoded writes=() plus zero WriteSpec construction -- holds and is what is filed here.

RELATED: this is the same shape as hamlet-1b9af9088c (spawn_item) and hamlet-a737e444c0 (effects blind to position/time) -- the grammar declares a capability the execution path never threads data for. Candidate for triage as ONE unit rather than three tickets.
=================== hamlet-4597fd5d04
ID:       hamlet-4597fd5d04
Title:    environment.yaml variables are hardcoded lifetime: tick — no accumulator, counter, or cooldown can survive a step on this surface, and no key changes it
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:03.775916+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-7 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence (four consecutive interactions: env-var stays 5.0 while the agent-profile control accumulates 5/10/15/20).

compilers/observation.py:866 hardcodes lifetime='tick' for every environment.yaml variable; reset_tick_scoped() runs at the top of every step(). The write lands and IS observed within the same tick, so the surface is not useless — but every cross-tick accumulator silently resets. configs/simple names its env vars time_since_last_sleep / time_since_last_doctor / time_since_last_cook — exactly the shape that cannot work here. Same family as hamlet-0268336cd1 (lifetime hardcoded 'persistent' on vfs_profiles.yaml) — the two surfaces hardcode OPPOSITE lifetimes and neither is declarable; the shared fix is one declarable lifetime key.
=================== hamlet-5f99e89865
ID:       hamlet-5f99e89865
Title:    environment.yaml variables hardcode lifetime=tick — declared counters/accumulators silently reset every step
Status:   triage
Priority: P2
Type:     bug
Created:  2026-08-22T12:33:55.938870+00:00
Ready:    YES (no blockers)

--- Description ---
Round-2 VFS review (systems S8). environment.yaml variables are hardcoded lifetime='tick'; configs/simple/environment.yaml declares time_since_last_sleep / time_since_last_doctor — exactly the accumulator shape that silently resets each step. Global-profile variables are hardcoded 'persistent' (episode-scoped globals undeclarable — related hamlet-0268336cd1). The one surface that CAN declare lifetime (variables_reference.yaml) is isolated from affordances/effects/drive references (symbol-table exclusion). Silent wrong-behavior, not a crash.
=================== hamlet-83a043a9b9
ID:       hamlet-83a043a9b9
Title:    agent_private is INERT as a privacy declaration: the variable lands fully observable in every agent's observation row
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:51.609579+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-1 (docs/product/assessments/vfs-gap-analysis-20260821.md), INDEPENDENTLY VERIFIED by the standing agent (grep + encoder read).

VariableScope.AGENT_PRIVATE is documented as hidden-from-observations / observable-only-by-owner. Neither enforcement point is on the observation path: (1) registry.get(reader='agent') refuses correctly — but nothing in the runtime ever passes reader='agent'; the only occurrences are three docstring examples (registry.py:94/500/504), every real site passes 'engine'. (2) The observation encoder branches scope in ('agent', 'agent_private') — identical treatment — and reads through registry.get_agent(), which has NO access control (registry.py:774).

Measured: an agent_private variable written to 99.0 appears at its observation columns in EVERY agent's row, value tracking under negative control (60->0.6, 20->0.2). The declaration is a no-op on a surface an author reads as a guarantee: every information-asymmetry mechanic (private goal, hidden inventory, secret state) is unimplementable and APPEARS implemented. Textbook INERT — the debt class.
=================== hamlet-8b5af63108
ID:       hamlet-8b5af63108
Title:    tensorNd is entirely undocumented: the container type that carries Trial B — and genuinely works — cannot be discovered from the docs
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:24.467080+00:00
Labels:   docs, prd-0001-trial
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G8); confirms the blind run's G-1.

config/vfs_profiles_config.py:39-52 accepts tensor1d / tensor2d / tensor3d / tensorNd. docs/config-schemas/vfs-profiles.md documents a SMALLER vocabulary and does not mention tensorNd at all.

WHY THIS IS FILED AT MORE THAN DOC-ROT PRIORITY: the audit's finding is that the capability is REAL — a global-profile tensorNd genuinely expresses one entity's state as a set of occupied cells, observation-encoded faithfully, and it is what made the blind run's B-F2 PASS sound. An undiscoverable working capability is the worst case for a product whose north-star is authorability: it costs the author the whole feature AND makes the substrate look less capable than it is. Note the blind run reached it only by source-reading (its own discovery-path annotation records 'source-reading-required').

Bears on the PDR-0086 discovery-path metric row.
=================== hamlet-8c354c90bb
ID:       hamlet-8c354c90bb
Title:    initial_value_mode (all five members) is unreachable from vfs_profiles.yaml: compile_variable falls through to parser.parse(None) — the working registry implementation has no door from the profile surface
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.787499+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G3).

registry.py:653-654 INTENDS to raise "initial_value_mode 'eye' requires square 2D shape" — which is correct and is a good loud refusal. What the author actually sees is:

  AttributeError: 'NoneType' object has no attribute 'expandtabs'

The compiler's error formatter fails on the raised error before the real message reaches the author. The refusal is right; the diagnostic is unusable.

This is a FAILURE LOUDNESS defect (see metrics.md input metric 'Failure loudness' — an authoring mistake should produce a clear compile-time error). A correct refusal rendered unreadable is only marginally better than a silent no-op, because the author cannot act on it. NOT FIXED — substrate freeze.
=================== hamlet-b5cd718368
ID:       hamlet-b5cd718368
Title:    vec2i/vec3i/vecNi/vecNf accepted by the profile DTOs and rejected by the compiler: two type vocabularies disagree by four members
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:53.341065+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-4 (docs/product/assessments/vfs-gap-analysis-20260821.md) — the analysis found this recorded as an in-tree comment (trial_b_blind_organism/vfs_profiles.yaml, blind run gap G-5) but NEVER FILED; filing now closes the untracked confirm.

The profile DTO Literal accepts vec2i/vec3i/vecNi/vecNf — the DTO validator even enforces dims for vecNi/vecNf, a validation rule for types that can never compile — while the compiler runtime type set rejects all four. Verbatim refusals for both profiles and all four types in assessment §3.2. Declared-then-refused (BLOCKED, loud) — but the DTO half is a false promise the author pays for late.
=================== hamlet-b9a3bcbde2
ID:       hamlet-b9a3bcbde2
Title:    A bare vfs.X write to an agent-scoped variable writes the WHOLE agent batch, once per interacting actor — the shortest spelling is the wrong one
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:21:04.512606+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-9 (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

effects/context.py set_path for vfs.* calls registry.set with the whole tensor; the affordance engine runs the command list once per interacting agent, the effect manager once per active effect instance. Measured: modify vfs.avar value 'vfs.avar + 5.0', 2 agents both interacting -> [10.0, 10.0] (not [5.0, 5.0]); effect route +10/tick with 2 instances -> [20,20]->[40,40]->[60,60]; a global gets the same doubling. The correct per-agent form (target.vfs.X) exists on the affordance route and gives [5.0,5.0] — but nothing warns, and vfs.X is the shorter, more obvious spelling.

Counterpart of hamlet-57a5126baa (the indexed route's bypass): together they are the whole write-addressing question. Related: the fix for hamlet-cf16cdb6c4 made vfs.X scope-aware for READS; write fan-out semantics are this ticket.
=================== hamlet-c6c6c241c5
ID:       hamlet-c6c6c241c5
Title:    A variable declared with expression: cannot reference VFS state — the field is accepted by the DTO and refused at compile Stage 6
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.454144+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G6).

vfs_profiles_config.py:57 accepts 'expression:' as one of three mutually-exclusive init sources, so it reads to an author as an available passive-dynamics surface. Declaring organism_cells with expression: "max(vfs.organism_cells, 1.0)" is refused at Stage 6:

  Reference traversal requires schema entry for 'vfs.organism_cells'

So the surface is declarable and not usable for this scope — the declared-but-inert shape, in its BLOCKED variant (it fails loudly rather than silently). Likely the same root cause as hamlet-cf16cdb6c4 (A-G1): the schema has no entry for the global path. Re-test after A-G1. NOT FIXED — substrate freeze.
=================== hamlet-cb0ccdaa98
ID:       hamlet-cb0ccdaa98
Title:    Cascades cannot target VFS variables: CascadeConfig source/target are typed as meter names, so there is no declarative per-tick passive dynamic over a tensor container
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T08:00:23.119535+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial B tensorNd evidence audit (B-tensornd-audit-20260821.md, gap A-G5).

config/environment_config.py:161-168 types CascadeConfig.source and .target as meter names, and validation refuses anything else with [CASCADE_INVALID_METER]. Cascades are the declarative per-tick passive-dynamics surface, so a tensor container has NO passive dynamic available to it.

variables_reference.yaml does not fill the hole either: it is documented as static-only (no expressions, no item-scoped variables), per CLAUDE.md's VFS section.

Bears on the same class as hamlet-cf16cdb6c4 (A-G1) and hamlet-a737e444c0: the ways a declared world-state container can be made to CHANGE on its own are all closed. NOT FIXED — substrate freeze.
=================== hamlet-cebe51077a
ID:       hamlet-cebe51077a
Title:    Transition phase names are a closed canonical set at compile — designer-named phases refuse, and VFS.md's own design examples (action_costs, passive_depletion, threshold_cascades, emergency_relocation) are unauthorable as written
Status:   triage
Priority: P1
Type:     bug
Created:  2026-08-24T17:44:58.799430+00:00
Ready:    YES (no blockers)

--- Description ---
Surfaced 2026-08-25 by the VFS documentation-truth loop (pass 3, docs/architecture/VFS.md §11.4). sort_key in vfs/transition_graph.py / transition_schedule.py refuses any phase name outside DEFAULT_TRANSITION_PHASES at compile, so the phase names used throughout the doc's §10.2/§12.3/§13.3/§14.3 examples cannot be declared by a pack. Additionally, action writes scheduled after apply_completion_bonuses raise at the first env.step (transition_schedule.py:123-127) — a compile-green/runtime-crash seam. Per CLAUDE.md this is the load-bearing defect shape: a designer cannot express phase structure in config without editing Python. Coverage at HEAD: 11 of 18 canonical phases have compiler-emitted rules, 7 are engine-imperative. Decide: (a) open the phase vocabulary to declared names with declared ordering (declarative surface), or (b) keep the closed set and rewrite the doc examples to canonical names + make the post-completion-bonus write refusal a compile error. Either way the runtime raise must move to compile time.
=================== hamlet-de52c40c03
ID:       hamlet-de52c40c03
Title:    Item-profile VFS expressions never evaluate, and the item expression schema uses bare bar names instead of the bar. namespace
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:52.649784+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-2(c) (docs/product/assessments/vfs-gap-analysis-20260821.md). Analyst-attested with executed evidence.

Nothing in the runtime evaluates CompiledItemProfile.variables[].ast — measured: item expression (energy*100) holds 0.0 across steps under eager. Additionally the item schema namespace differs from global/agent: 'bar.energy' is refused at Stage 6 with available paths ['energy', 'health', ...] — bare names. So the same expression text is valid in one profile and a compile error in another. Adjacent to hamlet-f2a37a8c8a (item accessor gap) but a distinct mechanism.
=================== hamlet-f2a37a8c8a
ID:       hamlet-f2a37a8c8a
Title:    Item-scoped variables are unreachable through registry.get(): the accessor the VFS docs name as THE read path raises KeyError (Trial F evidence audit)
Status:   triage
Priority: P2
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-19T16:24:35.077079+00:00
Labels:   prd-0001-trial, recovery:WS-4
Ready:    YES (no blockers)

--- Description ---
Found by the Trial F evidence audit (docs/product/trials/0001/F-evidence-audit-20260820.md), reported there with a reproduction. NOT independently re-verified by the standing agent at filing time -- stated so the next reader does not assume it was.

CLAIM: item-scoped variables cannot be read through registry.get(), which docs/architecture/vfs-current-implementation.md and docs/config-schemas/variables.md name as the read path with access control enforced at registry.get()/set(). The audit reports KeyError. The values ARE reachable -- the audit read the durability value four independent ways, including at its compiled observation offset -- so this is an accessor gap, not missing state.

WHY IT MATTERS: 'read the variable I declared' is a first-order authoring operation, and the documented accessor is the one that does not work for one of the nine declared scopes. Same family as the item-observation questions in hamlet-1ad6383186.

VERIFY FIRST: reproduce the KeyError and establish whether it covers all item-scoped variables or only those declared through item_profiles, before treating the docs or the accessor as the defect.
=================== hamlet-f54b887148
ID:       hamlet-f54b887148
Title:    A global tensor whose leading dim equals num_agents hard-fails at the first step — live on configs/trial_b_blind_organism at num_agents=3
Status:   triage
Priority: P1
Type:     bug
Parent:   hamlet-15050f280a
Created:  2026-08-21T10:19:52.996124+00:00
Labels:   recovery:WS-4, vfs-gap-analysis
Ready:    YES (no blockers)

--- Description ---
VFS gap analysis G-3 (docs/product/assessments/vfs-gap-analysis-20260821.md), INDEPENDENTLY REPRODUCED by the standing agent at HEAD on the UNMODIFIED landed pack: ValueError: global_active_mask length 243 does not match global_vfs_dim 81 — configs/trial_b_blind_organism, first env.step(), num_agents=3.

RULE (measured, assessment §4 G-3): a global tensor variable fails exactly when its leading dimension equals num_agents. Probe pack with global tensor2d shape [2,2]: OK at num_agents=1/3/4, crashes at num_agents=2. Trial pack with tensorNd shape [3,3,3,3,3]: OK at num_agents=1 (the ONLY agent count its trial evidence was gathered at), crashes at num_agents=3.

MECHANISM: observation_builder.py _flatten_to_batch decides already-batched-vs-broadcast from value.shape[0] == batch_size ALONE. For a global variable that equality is a coincidence, not a fact: the container is treated as per-agent and contributes shape[0]-fold fewer columns than the spec computed, tripping the active-mask check at observation_builder.py:329.

WORST-SHAPED FAILURE AVAILABLE: compiles clean, artifact valid, and whether it RUNS depends on a training hyperparameter the author may change for unrelated reasons. Any global tensor with a small leading dim (3, 4, 8 — the shapes authors actually write) sits one num_agents edit from a crash.

NOTE: the tensorNd evidence audit (B-tensornd-audit-20260821.md §9) named exactly this case as its untested information gap and flagged it as the obvious follow-up. It predicted the case 'could silently appear to work'; measured reality is a loud crash — better than silent, but the audit's boundary was real.
