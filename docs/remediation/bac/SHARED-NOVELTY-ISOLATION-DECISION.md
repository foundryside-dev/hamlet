# X02 — Owner decision: independent worlds and shared novelty

**Status: John selected OPTION B. Implementation and qualification remain pending; X02 is OPEN.**

Decision owners: **John / Emmy**. Prepared by Astra, 2026-11-01, from the retained differential evidence and the existing S1/r2/P5a contract context. John explicitly selected B in reply `call_b2b0e27039af4602b5a1c19bb3a3fc5c`, approval `BAC-S1-PER-WORLD-B-2026-11-01`. The [original reviewed proposal](plan-reviews/shared-novelty-options-reviewed.md) is preserved byte-for-byte at SHA256 `cb23ae28696259123b2b16b27e0f29b8d6740900b51bad56f387765c6877e701`. The preceding clarification request selected nothing; this later explicit answer supplies authorization. No implementation is claimed by this decision record.

## Decision and required implementation

John selected B: add strict per-world curiosity while retaining the explicitly qualified shared alternative.

The original implementation already violates an all-output reading of S1: changing only world0's action changes world1's canonical intrinsic and total reward, while the measured world1 successor observation, done, extrinsic and shaping values stay equal. This is a reproduced cross-contract issue, not merely a concern about the planned CountExploration provider. It is **X02**, separate from the original defect/gap inventory and X01.

**Pre-decision technical recommendation (A was not selected): Option A is coherent with the explicitly shared learner and accepted P5a ownership, provided John/Emmy approve the exact scope qualification below.** Option B is appropriate if independent intrinsic reward is part of the intended experiment guarantee. Neither recommendation constitutes owner approval or lets this review silently weaken S1.

## Retained evidence and limits

Evidence: [shared-novelty-differential.json](/workspace/bac-review-2026-11-01/qualification/isolation/shared-novelty-differential.json).

- Original immutable source SHA: `4aa5363b5de54d9a112977c32c2975f37627197f`.
- Imported package recorded in the artifact: `/tmp/hamlet-bac-4aa5363b/src/townlet/__init__.py`.
- Two authored two-lane runs execute one environment step with actions `[0,0]` versus `[1,0]`. The coordinator confirms these are the first versus second legal action only for world0, with the same seeds; world1 takes the same first legal action.
- The JSON records equal initial observations and equal initial Q, RND fixed-network and RND predictor digests. Q digest: `4e7c4e06dfedc29b5c20384895ccaa3d5723d41748e4ffb8d28119e2b5ef872b`; RND fixed: `c887af716200eaba4d52e0927c3bd4a9c807f082266c222b493d958ac590bdec`; predictor: `adedae7ba46e2b660887d6afca9b200164cd6e4eb7d91ad77708183828d52b32`.
- Both runs record zero Q updates, zero predictor optimizer state entries, two pending predictor rows, and active normalizer admission with count `2.0001`. The coordinator additionally confirms runtime intrinsic scale1, drive base1 and no intrinsic modifiers. Those configuration/control assertions are coordinator-supplied; this decision review read the JSON, not the probe implementation or pack files.

| Measured quantity | Actions `[0,0]` | Actions `[1,0]` |
|---|---|---|
| World0 successor observation | Changed between runs | Changed between runs |
| World1 successor observation | Exactly equal between runs | Exactly equal between runs |
| World1 done | `true` | `true` |
| World1 extrinsic | `1.9925000667572021` | `1.9925000667572021` |
| World1 shaping | `0.0036754447501152754` | `0.0036754447501152754` |
| World1 canonical intrinsic | `1.7587649822235107` | `1.7606741189956665` |
| World1 canonical total reward | `3.7549405097961426` | `3.756849527359009` |
| Shared reward RMS mean, as serialized | `0.012112318` | `0.012376724` |
| Shared reward RMS variance, as serialized | `5.011925e-05` | `5.001061e-05` |
| Shared reward RMS count | `2.0001` | `2.0001` |

All seven top-level comparison checks are recorded in the JSON: world0 changes; world1 successor/done/extrinsic/shaping equal; world1 intrinsic/total unequal. This is a one-step, original adaptive-RND witness with no Q or predictor optimizer update. Shared normalization therefore cannot be dismissed as a hypothetical effect requiring later policy training.

**Limits:** the measured successor observation is not the entire hidden simulator state. This witness does not establish all world-state/RNG isolation, all substrates, future timesteps, CountExploration behavior, LRU eviction effects, annealing coupling, exact stochastic resume or learning quality. It establishes the specific reward differential above. Root reports original source files unchanged. Astra performed no new source inspection or probe execution for this decision.

## Current guarantees and unresolved intersection

- **S1, existing owner rule (STATUS §3):** the batch is N independent single-agent worlds; global state is per world, relevant storage/references/RNG are world-local; the world0 differential must leave worlds1..N−1 bitwise identical. The retained wording does not explicitly exclude intrinsic or total reward.
- **PRD-0005:** shared model updates from valid experience may continue, while lane eligibility and owned completion outcomes remain exact. That permits shared learning; it does not itself settle intrinsic reward's place in the S1 comparator.
- **r2 BAC-C05:** the transition owns canonical reward and terminal/successor meaning. **C08:** exploration/normalization/predictor admission has explicit ownership and eligible samples. **C09:** each world's curriculum decision must reach its own dynamics. None contains an owner-approved general exemption for cross-world intrinsic reward coupling.
- **Accepted v3 P5a, as supplied by the coordinator:** CountExploration counts/LRU are deliberately shared learner state. Original RND already shares normalization/predictor state. This makes the ownership question concrete but does not independently amend S1.
- **Adjacent C09 interface, supplied by the coordinator:** the approved adversarial curriculum consumes each lane's Q-values/entropy from the shared Q network. A shared Q update could therefore change another lane's later controller decision even when its actions are scripted. This is an interface-level possibility, not an effect reproduced by the retained one-step witness. Simulator isolation and correct ownership of controller decisions require separate comparisons; fixed actions alone do not control every explicit mechanics input.

The unresolved issue is therefore **the isolation boundary**, not whether the observed values differ. The difference is confirmed. Calling the present behavior “S1 compliant” by silently dropping reward fields would change the guarantee without approval.

## Option A — Not selected: qualify S1 to world-owned simulator outputs

**Unselected proposed scope change (not authorized):**

> Under identical world initialization, changing world0's actions must not alter any other world's simulator-owned state, simulator RNG progression, observations, termination, extrinsic rewards or shaping rewards when that other world's full explicit action and mechanics-input traces are held identical, including authored curriculum/depletion decisions where applicable. Shared learner state is a distinct, explicitly identified owner: Q-learning, curiosity normalization, novelty counts/LRU, intrinsic annealing and predictor learning may aggregate eligible experience across worlds. Their shared state may consequently change another world's intrinsic and total training rewards. Those rewards are not claimed to satisfy all-output independent-world isolation in shared-curiosity mode.

This authorizes **no domain-state, simulator-RNG or physics sharing**. It does not authorize lane0's curriculum decision to govern other worlds, nor shared curiosity to mutate another world's simulation parameters, observation facts or extrinsic/shaping rules. Shared Q updates may affect future chosen actions and the explicitly contracted C09 controller inputs; the simulator comparison holds the resulting explicit action/mechanics-input traces fixed. Separate C09 qualification must prove that each controller uses its own lane's inputs and applies its decision only to that lane, with shared-learner feedback declared. Any additional feedback from learner state into world mechanics needs its own explicit contract and qualification.

This is a conditional simulator guarantee, not a promise of identical complete closed-loop physics when explicitly contracted controller decisions differ. The controlled mechanics inputs must be named and recorded at the real interface; arbitrary changed simulator state cannot be reclassified as an input to hide a leak. This precision is part of the proposed owner-approved scope qualification, not an already-approved exception to S1.

Required qualification and reporting after approval:

1. Maintain a world-owned-state/RNG/observation/terminal/extrinsic/shaping differential with curiosity **active**, not disabled to make it pass, holding each unperturbed lane's full explicit action/mechanics-input trace identical. Extend beyond this one-step observation witness to the actual affected state owners and reset/lifecycle boundaries. Separately exercise C09 with lane-distinct Q/entropy/controller inputs and decisions: verify correct lane ownership/application, absence of lane0 broadcast, and the declared shared-learner feedback path. Do not use the controlled simulator comparison as proof of closed-loop controller independence.
2. Retain a separate intentional shared-curiosity contrast: normalizer admission, real predictor updates, shared Count key collisions/LRU effects and shared annealing where supported. Show precisely which intrinsic/total outputs may change and which world-owned outputs do not. Eligibility and once-only completion still apply.
3. Record shared versus per-world ownership, provider identity and applicable reward-isolation guarantee in the effective run description, checkpoint/provider state ownership and telemetry. “Independent worlds” must not be presented as “independent total training rewards.”
4. Keep reward components and canonical total truthful. Do not remove intrinsic from stored reward, hide the difference, loosen bitwise checks on world-owned outputs or relabel the old all-output S1 test passed.

**Effect on P5a:** its shared counts/LRU direction remains viable with this explicit scope. **Tradeoff:** cross-world novelty history can change intrinsic reward targets even under fixed actions and no optimizer update; changing population composition can therefore change the learning signal. That is accepted shared-learner semantics under A, not isolated-world reward equivalence. Approval changes the normative scope; it does not by itself prove the strengthened ownership checks pass.

## Option B — SELECTED: retain strict intrinsic-reward isolation; add per-world curiosity

**Owner-approved direction:** retain strict reward comparison, including intrinsic and canonical total reward for unchanged worlds under identical full explicit action/mechanics-input traces. Require an additive per-world curiosity capability before this seam qualifies under that guarantee. The same explicit C09 boundary and separate ownership/application qualification described above apply; this comparator does not promise identical closed-loop physics when contracted mechanics inputs differ. If the owner instead intends independence of those controller decisions despite shared Q updates, that is a further requirement to resolve explicitly, not an exception granted here.

The finite design amendment must identify every state dependency that can change intrinsic reward: normalization, novelty counts/LRU, annealing/completion history, pending predictor data, predictor parameters/update ownership and any RNG. Per-world counts or normalizers alone are insufficient if a shared predictor update still changes another world's novelty reward. The shared Q learner can remain; controlled action/mechanics-input traces isolate its explicitly contracted downstream effects from this comparator. Curiosity state itself must evolve through the tested admissions and updates; freezing that state would not demonstrate intrinsic-reward isolation. No exact algorithm or provider-state layout is selected by this decision record.

Preserve the existing/planned shared-curiosity capability as an explicitly labeled alternative; do not delete it or silently claim it satisfies strict S1. Any advertised S1-qualified execution must pass the full world0 differential including intrinsic and total rewards. A shared mode must carry its explicit non-isolated-reward qualification; adding a strict mode does not make the shared mode pass. If the product is to promise strict S1 for every supported run, the owner must resolve that universal promise against retaining shared mode—technical reviewers cannot exempt it silently.

Required qualification after the additive design is implemented:

1. Repeat the retained two-run contrast with the strict mode, equal initial provider state, identical unperturbed-lane action/mechanics-input traces and all provider admissions active; world1's intrinsic and total reward must remain bitwise equal. Record the controls and resulting curiosity state instead of forcing post-admission curiosity state equal.
2. Exercise all supported curiosity admission/update states, including admitted and ineligible samples, pending and real predictor updates, normalization updates, count collisions, LRU capacity pressure, annealing, lane completion/reset and restore. Preserve world-specific state identity across the supported lifecycle. Separately qualify C09 controller ownership/application and its declared shared-Q dependency.
3. Retain shared mode's contrasting evidence and ownership/provenance so it remains available without a false strict-isolation claim. No capability removal or default substitution is inferred from selecting B.

**Effect on P5a:** shared provider work can remain, but it cannot close strict S1 qualification. A bounded additive amendment is needed for per-world curiosity before this seam is accepted. **Tradeoff:** additional provider state, update accounting and checkpoint qualification; sharing a novelty learner remains an explicit alternative rather than an accidentally isolated one.

## Implementation disposition and work boundary

**Selected option: B — add strict per-world curiosity. Owner: John (explicit user answer), 2026-11-01. Approval: `BAC-S1-PER-WORLD-B-2026-11-01`.**

John selected B. X02 remains open until the bounded additive design is technically approved, implemented and independently qualified across actual curiosity updates; shared parameters must not be frozen to fake independence. The decision itself and implementation acceptance are separate receipts. No approval of A, capability removal, implicit default substitution or complete closed-loop learner independence is inferred. The shared alternative remains available with truthful reward-isolation qualification. The shared Q learner may remain; its policy/controller effects are separated through the specified controlled traces.

Continue unrelated authorized work, including T01 and T02 qualification repairs, without changing their evidence or claiming this seam resolved. Curiosity integration may retain its approved shared-state implementation direction while this decision is pending, but must not claim S1 acceptance or silently change the isolation invariant. If dependent work would assume one option's semantics, keep that dependent qualification open rather than making an unapproved choice.

This record proposes no algorithm changes, capability removal, frozen-plan edits or broad redesign. The user's approval rule applies because Option A qualifies an existing guarantee; Option B preserves that guarantee while adding capability and explicitly retaining the shared alternative.
