# Per-world curiosity addendum — Astra MEDIUM review r1

**Verdict: CHANGES REQUIRED.**

Exact reviewed artifacts, hashes verified before and after review:

- `per-world-curiosity-addendum.md`: `11ff44c94525b583ea003359ee32070cbd24d5402a70c86e13ebf95195cc80da`.
- `per-world-curiosity-packets.json`: `f5fd525d4807fba1e0359f4ce92bcfdf4632bd6f93348dcf3d330c0df5b79990`.

Same Astra MEDIUM planner-review loop; no plan restart. Owner choice B is explicitly authorized by `BAC-S1-PER-WORLD-B-2026-11-01` / question `call_b2b0e27039af4602b5a1c19bb3a3fc5c`. This review does not revisit that choice or select A.

## Blocking finding — preserve frozen T18 and use real source-size floors

**Locations:** addendum §6 line115 and its PW02/PW03/PW04 table rows, §7 final-lens recount; JSON `base_packet_overrides[id=T18]` starting line2238, `aliases.RND`, RND-bearing `reads`, and combined dependency/order/preflight records.

The proposal retroactively reslices T18 into five files/4900 projected lines, adds HC and dependencies T16/PW01, and places it after future POP mutations. The coordinator supplied a different authoritative execution fact for this review: T18 is already frozen with four files/3035 actual lines—POP1854, RND604, OP243 and its new test334—and its native runner smoke already passed, while package/full review remains pending. An addendum cannot silently replace that frozen packet/receipt with a future five-file job or invent prerequisites for work already performed.

The RND500 ceiling is also below the known actual604 lines before PW04 adds adapters. Substituting merely604 into the proposed T18 future inventory yields **5004 lines**, already exceeding the5000 cap. Several other packet/final-lens totals remain below the cap but are still based on that stale ceiling. The textual recount warning does not make a known-underestimated reviewed inventory valid.

**Required correction:**

1. Preserve frozen T18's exact four-file execution inventory and actual approval/pending status. Do not claim it complete from the passing smoke, and do not rewrite its historical dependency receipt.
2. Place any genuinely remaining old/new compatibility or B-specific adapter work in an explicit bounded future packet/reslice, ordered after frozen T18 and before its real consumers. Existing verified smoke evidence may be cited; it cannot replace later changed-source checks.
3. Give RND a future ceiling at least its actual604 lines plus realistic adapter growth; propagate it through every affected packet, alias, sum and original/added final lens. Split/reassign the task if any complete worker/reviewer inventory exceeds5 files/5000 lines; do not omit required source or tests to make the arithmetic fit.
4. Regenerate the combined DAG, topological order and shared reader/writer preflight against the preserved execution boundary. Keep the coherent validator/producer requirement, but attach it to the actual remaining work.

No additional blocking architectural issue was found. A revision resolving this execution/budget conflict is needed before activating B-sensitive overlays.

## Technical assessment

The ownership proposal is appropriate for strict B: private backend instances include trainable parameters, gradients, optimizers/moments, normalization, counts/LRU, adaptive history/scales, pending data, RNG and local admission/service clocks. It explicitly rules out a normalizer-only or frozen-model proof. Loss reduction/clipping/minibatches and overflow quotas are local; spectators and idle vector ticks cannot change another world's service. Shared Q/policy remains permitted and is distinguished from conditional simulator/private-reward isolation.

Stable IDs and versioned seed derivation exclude lane index, N, global ticks and other-world activity. Initialization/provider work uses an owned serialized RNG domain with normal/error global-state restoration; serving retains the process boundary. Private reward scales stay vectors into the single canonical DAC composition. Context stamps connect actual predecessor/action/successor and owned completion, including terminal-on-entry eligibility, without logging-time identity regeneration.

Same-scope restore, binding checks and off-side candidate installation are concrete. Explicit fresh-private and learned-clone conversion origins preserve source/shared access; learned clones have independent mutable state, inherited optimizer counters are named, mixed pending data is archived rather than attributed to invented private histories. Captured replay keeps its recorded reward provenance; private service consumes fresh own-world admissions instead of Q replay. Approved historical A remains distinct. Fresh/source-snapshot evaluation and read-only/statistics-only/local-learning modes are truthfully separated, with real training in required B proofs.

The finite evidence plan includes at least two actual private updates with nonzero parameter change, object/moment/RNG/queue separation, count collision/LRU and adaptive-completion contrasts, unequal lifecycles, spectators/reordering/idle service, real shared-Q updates with explicit fixed mechanics/actions, and a separate C09 own-lane application proof. The full-state helper is counted, and observation equality alone cannot close hidden-state isolation.

## Manifest checks and remaining evidence

I parsed the JSON as reference data and independently checked its declared totals, file counts and topological order: on its own stated numbers every packet is at most5/5000 and the64-node order satisfies its dependency map. I also independently checked transitive reader/writer ordering across all45 supplied new/override packet records; no unordered conflict was found. These checks do not cure the known T18/RND execution facts above; they must be repeated after correction.

Named missing evidence remains the PW12 owner inventory for item state/inventories, affordances, history, effects and every present world-owned RNG/draw cursor. The document correctly treats these as required discovery/proof inputs and blocks X02 closure if any present owner lacks an actual interface/receipt. No complete snapshot API is established by this plan review. Supply bounded owner evidence or reslice before implementation needs unlisted source; do not silently turn that into a sixth file or a narrower proof.

Nonblocking implementation precision: the PW01/PW02 receipts should publish the exact event-stamp shapes, duplicate/expired-event ordering and conversion/reset cursor initialization; the scope-selection policy and architectural ownership are already fixed. In learned-clone conversion, new local event IDs must not collide with inherited completion/dedup IDs. These are bounded acceptance details, not an additional owner policy question.

## Preserved acceptance and policy

Shared remains the existing omitted-scope default and an honestly coupled alternative. Explicit per-world mode gains strict conditional reward/state isolation; the plan does not manufacture an all-runs/default-strict guarantee. Contrary universal product claims must be reconciled visibly with the owner ruling. No shared capability/default, public API, historical artifact or working replay option is removed.

All original D01–D21/X01/G01–G09/C01–C13/K/candidate acceptance remains. X02 is added, not used to replace earlier work. Original T40 is retained with a finite additional12-run strict cohort (120000 training transitions maximum), and original17 final lenses expand to21 plus independent synthesis at one final SHA. Required repository/coverage/slow/hardware/CI gates and zero-P1/P2/zero-unapproved-gap closure remain unchanged. Neither the scope selector nor this review closes X02.

## Inspection receipt

No additional implementation/test source was inspected. Cumulative original plan-review source use remains one allowed file, `sequential_replay_buffer.py` lines160–330, conservatively charged543 lines. Current sizes/T18 status are attributed coordinator facts. Only proposal/reference metadata were parsed; no implementation, frozen plan, current task metadata or git state was edited, and no agent was delegated.
