# Current nonmodel native reset contract

2026-11-11. This contract describes the current Count and NONE native producers at qualified R22 candidate `be7e7fcc0efd1138e1d30ef69d10fa6d8cc2da52` (base `383d2ac1`). It qualifies native component behavior; BANK/parent boundary authority, RNG custody, global cadence and whole-parent transfer remain separate integration requirements.

## Concrete providers and construction

`townlet.exploration.provider_factory.make_backend(policy, *, world_id, obs_dim, action_dim, device, rng, descriptor) -> ExplorationStrategy` validates the actual resolved policy, geometry, device and scope ownership before constructing the selected provider. Its count_based branch constructs actual `townlet.exploration.count_based.CountExploration`; its none branch explicitly constructs actual `townlet.exploration.epsilon_greedy.NoneExploration` using selected epsilon_start/epsilon_decay/epsilon_end.

`NoneExploration(EpsilonGreedyExploration)` owns NONE's native preparation/reset methods. Plain `EpsilonGreedyExploration` retains diagnostic epsilon, action selection, zero intrinsic reward, no-op update, decay and ordinary diagnostic load/checkpoint; it has no native prepare_state/install_state/prepare_learning_reset methods. `make_policy_selector(policy) -> EpsilonGreedyExploration` still returns exact plain EPS for the global selector. Count and ICM retain their nominal EPS inheritance and their own family-native prepared handles. No generic inherited EPS reset or family dispatcher is used.

Shared factory construction requires world_id/rng/descriptor all None. Private construction requires the actual declared world ID, descriptor and WorldRNGState binding. Genuine private construction and current-stream custody belong to the actual owner; native private component tests do not establish them. Native reset receives an already constructed actual fresh candidate and does not construct another backend.

## Public native preparation and publication

The concrete family methods are:

- `CountExploration.prepare_state(state: dict[str, Any]) -> _PreparedCount`
- `CountExploration.install_state(prepared: _PreparedCount) -> None`
- `CountExploration.prepare_learning_reset(*, fresh: CountExploration) -> _PreparedCount`
- `NoneExploration.prepare_state(state: dict[str, Any]) -> _PreparedEpsilon`
- `NoneExploration.install_state(prepared: _PreparedEpsilon) -> None`
- `NoneExploration.prepare_learning_reset(*, fresh: NoneExploration) -> _PreparedEpsilon`

The private return types are opaque family handles for public callers. Consumers retain a handle and pass it to the same destination's install_state; handles are not portable native checkpoint data. Preparation validates off-side and owns detached candidate data. Install rejects the wrong exact handle type, foreign destination and previously used handle before changing state or consuming foreign work. A legitimate handle remains usable at its actual owner after a wrong-owner refusal. Successful install preserves destination object identity and consumes that handle once.

Publication assigns only previously prepared owned fields. Count publishes its validated policy, diagnostic triple, OrderedDict and eviction scalar. NONE publishes only epsilon/epsilon_decay/epsilon_min; it does not replace other receiver attributes. No load callback, factory/model construction, RNG activation/draw, service call, admission or epsilon decay occurs in native prepare/install/reset. Native destination/single-use checking is not a mutation-revision, copied-handle or parent-boundary authority guarantee. The outer BANK/parent producer must authenticate current revisions, actual boundary and publication permission.

## Exact native schemas and ordinary state transport

Count checkpoint schema remains `count-state-v1` with exactly eleven keys:

`schema_version`, `policy_identity`, `policy`, `quantization_width`, `max_entries`, `epsilon`, `epsilon_decay`, `epsilon_min`, `counts`, `lru`, `eviction_count`.

Complete Count validation checks the resolved policy and matching active identity; selected width/capacity; finite policy-consistent diagnostic epsilon/min/decay; bounded counts; nonempty signed-integer tuple keys; positive nonbool integer counts; exact LRU correspondence/order without duplicate keys; and nonnegative nonbool eviction count. Policy transport is independently copied and validated; count containers are rebuilt in recorded LRU order. Ordinary load_state uses the complete prepare/install seam and retains the previous active-policy/parameter acceptance semantics, including validated inactive policy provenance. It does not require whole-authoring equality merely to restore the same active selection.

NONE and plain EPS checkpoint dictionaries remain exactly `epsilon`, `epsilon_decay`, `epsilon_min`. Ordinary EPS load validates all three finite nonbool numeric values before assigning any of them. It preserves ordinary finite numeric transport without arbitrary [0,1] or selected-policy range restrictions and without float coercion. Explicit EPS diagnostic loading into a derived receiver changes only these three fields and does not virtually dispatch into Count/ICM whole-native preparation. NONE inherits that ordinary load behavior; its additional prepare_state supplies an opaque destination-bound native candidate for the same triple.

No schema adds a predictor queue, service ledger, Adam state, optimizer origin, reset generation or history archive. Count eviction_count belongs to count novelty learning, not predictor dropped-row accounting. Count's existing actual admit_and_service returns zero predictor work; NONE has no native predictor service operation. BANK service/episode lifetime, retained completions and accepted identities are not native Count/NONE learning fields and cannot be synthesized here.

## Fresh reset and retained state

Count reset requires distinct exact Count owners. It validates BOTH actual current and fresh complete native snapshots before discarding any old learning. Consequently malformed old count values/keys cannot be silently erased by reset. Fresh actual retained width/capacity must agree with its unchanged genuine policy; matching policy identity alone cannot bypass those checks. Current and fresh must match destination device, active policy identity, width/capacity and the actual cached quantization ratio. The fresh snapshot must have empty counts/LRU, eviction_count0 and selected constructor initial diagnostic epsilon; complete validation independently qualifies its min/decay.

The resulting Count candidate takes genuine fresh count-learning fields while retaining the current validated policy transport and current diagnostic epsilon/min/decay. Its installed map/LRU are empty and eviction count is0. Later genuine count admission learns anew: first visit reward1, second same-bin reward1/sqrt(2), with actual retained quantization/capacity/LRU behavior. Pure reward queries and inherited no-op update do not admit counts. Reset neither replays historical observations nor converts old evictions into predictor work.

NONE reset requires distinct exact NoneExploration owners, finite current/fresh triples, matching min/decay, and current epsilon between the selected fresh constructor's minimum and initial epsilon. It retains precisely the current diagnostic triple. NONE has no learned novelty to discard and produces no invented predictor/Adam/origin work. Repeated native resets retain bounded unchanged schemas and current diagnostics. Outer reset/history metadata remains owned by BANK.

The three NONE values cannot authenticate actual selected factory provenance or remember an original constructor start. Actual factory construction and truthful fresh-candidate provenance must be established by BANK/factory custody. Count validates observable constructor freshness and selected configuration; this also does not replace outer boundary/revision/factory authority. Native methods cannot turn an arbitrary caller-supplied object into authenticated fresh construction.

## RNG and integration limits

Current Count/NONE construction and native preparation/install contain no random primitive or RNG activation. Preparation is detached from later genuine fresh-object admissions/epsilon decay and from mutable exported input containers. Refusals leave current/fresh native state and ambient continuation unchanged in the witnessed native cases. Those observations do not establish private named-stream ownership or a process-wide shared RNG enrollment protocol. Actual private current-stream cloning, advanced candidate continuation where construction consumes draws, shared-parent custody and publication remain producer-owned integration requirements. Native methods must not reseed, invent draws or manufacture model-style learning origins for nonmodel families.

## Source receipt and qualified evidence

Exactly five owned whole sources after this correction:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/count_based.py |263|6930c2ee86364035f09fc977aa8b76ac0aa96290b8a6ab0cd917e8afb3ba3e08|
| src/townlet/exploration/epsilon_greedy.py |179|36b5bed8b13a4422764e8a108f22f9f7f2ca32a2f31ee5cc2512634c701857cb|
| src/townlet/exploration/provider_factory.py |153|dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8|
| src/townlet/exploration/base.py |118|49a9a23c2dcf3705a7712fc0bc74d11aa4b30aeee8fba1d0f87a609e05fbd1ae|
| tests/test_townlet/regressions/bac/test_nonmodel_learning_reset.py |554|6c61dd0ac7bce7676e677feb3060352cf1f3893fa72fefac277291f23d082801|

Total1267. The test uses a genuine typed selected Count width1/capacity3; seven admitted rows across four distinct bins establish repeated learning, one eviction and LRU reorder. It preserves all152 earlier semantic/negative/alias/RNG cases and adds two selector/native-class/derived-diagnostic positive controls. Its per_world cases explicitly qualify native components, not private factory/RNG ownership.

Root-reported R22 execution: coherent293 PASS in48.621755s, comprising N2 native154, N1 model61, parent47 and ENV31. Independent Astra reran the SAME154 native cases:154 PASS in8.935267s; this overlap does not establish447 unique cases. A separate basic Count/factory/EPS selection passed182 cases in9.680415s. The two-line factory expected-None class alignment received Astra SPEC+QUALITY approval (`c11da651`) and is covered by that actual182-case pass. Each run's named full802-source/573-config/13-artifact/controller/index/import/thread/14-registry MAIN1 custody checks passed with zero errors/skips/warnings. The five native source/test hashes above are unchanged from R21.

R21 global Ruff/Black/Expr/NoDefaults600 passed; R21 mypy reported only six older oracle errors, with all eight new family override errors fixed. Root verified that R22 source/config/scripts/ratchet hashes are identical to R21: R22 changed only the factory test's two expected-class lines. These are retained R21 static results on identical static inputs, not a claimed R22 static rerun. Owning Astra source/API review approved the concrete-none correction and marked P2 addressed. All execution/review results here are attributed to root and independent reviewers, not execution by this prose author.

Required BANK selection84 stopped with34 PASS/1 FAIL; restore selection147 stopped with0 PASS/1 FAIL. Both fail in the old shared fixture Rig's ENV.step call missing vector_step, before their intended assertions. Exact source custody passed. The known older150-case Rig module was not repeated. These failures remain required caller/fixture work: source-owned readiness identifies authentic pre-first-step B retirement, actual destination/action geometry, and canonical reward/service exactly once as prerequisites for the shared Rig repair. Adding only a keyword or directly mutating dones cannot establish the missing authority or current flow.

Actual DemoRunner, full D/B1/F, private/shared RNG custody/enrollment, stable role publication and all remaining final gates are still required. Original28/38/66 acceptance remains unchanged. This native contract does not claim whole N2 package, BAC transfer integration or release closure.
