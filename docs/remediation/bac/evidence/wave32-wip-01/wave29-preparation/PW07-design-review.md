# PW07 independent finite ABI/specification/quality review

SPEC: APPROVED for tests-first component implementation.
QUALITY: APPROVED for tests-first component implementation.

Reviewed proposal SHA256 f749261e772840f7045a5a477e584f8269d1f49ccd96e7d8bd5b51b84fcf36e0 and author-report SHA256 6489d252e02ea0867e0ed6b1017375fa746617c2db6fdf1351d35f4863e0c03a. Both supplied hashes matched the actual files. This is an independent other-model review of the Astra-medium design, not implementation approval, runtime verification, or programme completion.

## Finite findings and dispositions

Confirmed design defects requiring revision: none. No capability weakening, fallback, source-format compatibility adapter, simulator-scope expansion, or scope waiver is accepted by this review.

1. The proposed composite ledger satisfies the actual inspected ICM v2 constraints. At initialization A0=C+D, C0=C=U*B, D0=D, Qn=[], position=A0, budget0, and retained Adam step=U are mutually consistent. Later nonnegative differences satisfy a=c+d+len(Qn), c=u*B and m<=u. Native clocks advance at A0+a+1 while the public BANK-local clock advances at a+1. This preserves actual inherited Adam state without presenting inherited work as this world's activity. ICM.py:333 validates actual Adam steps against successful updates; :429 validates consumption/update and admission conservation; :441 validates private position/admissions. RND/adaptive signed optimizer offsets and absence of a cumulative mandatory-native counter are handled according to the supplied source-verified contracts. No new native producer schema is required by these equations.

2. The epoch/origin/phase changes are necessary and explicitly covered. Current CP preflight/event decoding require epoch0 (:179/:311); BANK stamps, context checks and export currently use epoch0. The proposal identifies all these seams, preserves origin-less epoch0, requires converted epoch=source+1, preserves it through subsequent ordinary resume, and prevents archived source events from becoming active dedup state. The new private_initialized phase carries real source/parent episode baselines without manufacturing private completion, disposition, accepted tokens or closing receipts. Genuine next ENV acceptance must be baseline+1. This is compatible with current begin_episode's actual sequence/closure gate (:361), which needs the proposed narrow boundary seam.

3. The INITIAL/COMPLETED conversion boundary is acceptable against the supplied original requirement and governing clarification. A completed shared source may contain the required mixed pending native queue; accepting that queue only as a complete inactive source archive satisfies the pending requirement. The supplied scope does not require an active simulator ownership switch. Ordinary live same-scope restore and current active captured training replay remain required; K01's existing exact-stochastic/mid-simulator qualification is unchanged. A later proposal that removes either required capability would need a new review.

4. Strict compatibility and ownership are adequately specified. Actual RP couples scope to captured authoring and derives different shared/private capacities, so the proposed independently resolved target policy and active selected-parameter comparison are appropriate; simply editing scope fields would be insufficient. The explicit path validates the source with its shared policy, then validates transformed payloads with actual receiving native validators/loaders. Count/ICM policy replacement follows that compatibility check. Independent private RNG continuations are declared fresh, source gradients are separately transported and attached after final native copying/loading, and the full source archive remains independently owned. None/Count do not acquire fictitious predictor ledgers, and the actual global selector remains separate.

5. The allocation/publication design preserves the current transaction boundary. Admission precedes owned input/native/callback allocation; the source validator uses disposable RNG custody; complete target owners, origin/archive/runtime and callback views are prepared off-side. Existing destination/revision-bound handles and single preallocated __dict__ publication are retained (BANK.py:998/:1109). Archive storage is charged on initialization and subsequent export/restore. Expected refusal must preserve live source/destination values, storage, gradients, RNG and revision; whole-parent final freshness/publication remains the actual parent owner's obligation.

## Required evidence still missing, not design blockers

G1 — No authored test, implementation, collection, RED, GREEN or independent execution evidence exists yet. Required disposition: implement the proposed three exact named test families under the baton, with all five actual providers, both initialization selections and selected service modes; establish genuine updates/tails/Count evictions/adaptive history, direct live optimizer/gradient/storage witnesses, archive nonrouting, negative custody, report/late-allocation refusal and healthy retry. In particular, next-update equality alone must not substitute for residual-gradient equality, and native counter assertions must distinguish inherited totals from future-local differences.

G2 — BANK v2/current diagnostic owner migrations and actual parent/native/runner/sampler/T26 integration are unimplemented. Required disposition: update current supported emitters/callers/tests/docs together, keep obsolete native BANK v1 training state an explicit refusal under AGENTS.md, preserve external historical artifacts, run current owner suites, and complete actual full-parent/captured-replay/private-counter/next-update gates separately. Minimal HC/replay fixtures cannot establish actual sampling or production parent publication. These obligations are retained by the proposal and are not closed here.

Refuted hypotheses: retaining learned ICM requires independently zeroed native update counters; a new ICM offset schema is inherently necessary; mixed archived pending must be routed into a private active queue; preserving current capabilities requires a BANK v1 compatibility loader. None follows from the actual contracts or accepted governing clarification.

Optional extensions: none required. This review does not request new live scope-switch or exact simulator continuation features.

## Bounded inspection and custody

Read review brief, original task, main brief including governing zero-compatibility clarification, AGENTS.md, the actual proposal/report, and the brief-named current public contracts/source-verified dependency capsules. Current facts supersede explicitly historical statements in older capsules. No underlying unlisted implementation, helper, fixture or old-test source was opened.

| Whole semantic source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/curiosity_checkpoint.py | 901/1400 | d0e63d86e154866656db0047194048420c2a7220a2b5958de59d524cafeb8e4c |
| src/townlet/exploration/scoped_curiosity.py | 1122/1250 | 5ad7ca86549c886f3dc587535ba321df5a1a6737097af38a803cea41051938cc |
| src/townlet/exploration/icm.py | 481/550 | eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f |
| src/townlet/config/exploration_policy.py | 768/800 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| tests/test_townlet/regressions/bac/test_pw_scope_conversion.py | reserved0/1000 | not read/authored |

Actual whole-source inventory 4/3272; five named ceilings total5000. All four sources were read in full; final line-count check remains3272. No sixth source, runtime/import/test/compile/index/commit/branch/worktree/source-copy/subagent action. The only write is this ignored review file; git check-ignore confirmed its exact path before writing.
