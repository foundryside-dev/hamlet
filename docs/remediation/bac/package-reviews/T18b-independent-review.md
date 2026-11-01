# T18b independent review r1 — fixed-source static PASS

Result: **static PASS; fixed-candidate runtime verification pending**. No remaining concrete P1/P2 found in the reviewed five-file COUNT scope. This refresh preserves the original r0 report unchanged and supersedes its assessment for the changed candidate.

## Correction to r0

The original required `update_stats` argument narrowed EPS's optional observation-call protocol. An inherited-protocol caller using `compute_intrinsic_rewards(observations)` would raise TypeError. Root reports an actual permanent-test RED establishing this defect. My initial static review missed that interface incompatibility; its blanket no-P1/P2 assessment was incomplete.

The fixed method at count_based.py:89 accepts the existing observation parameter plus an optional positional or keyword flag. Omission selects False and therefore a pure query. Duplicate flag binding, more than one flag positional argument and unknown keywords raise TypeError before validation/admission. A supplied non-bool flag raises ValueError before mutation. Both positional and keyword observations continue to bind through Python's ordinary function binding. The new permanent test exercises omitted positional/keyword observations, both explicit flag forms, True admissions, invalid flag values, argument rejection and checkpoint immutability after refusal. This directly addresses the demonstrated regression.

The explicit existing-key/new-key branch has the same count arithmetic as the former get(key, 0) expression and introduces no mutation on the query route.

## Verified inventory

Existing MAIN only. Exactly five implementation/test files, **1681 lines**, under the 5000-line cap. The complete changed COUNT and test files were reread; the three previously fully reviewed supporting files have identical hashes, preserving the original selected-policy/ownership assessment.

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/exploration/count_based.py | 206 | 163cb33f06799a75c887ff7beb58e4897875c94a4780ab722d019f714b33e9c1 |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| src/townlet/exploration/epsilon_greedy.py | 118 | f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/regressions/bac/test_count_provider.py | 295 | 0de2db0e0d2de868d803b97e8e8f0e277b365178dfddacaaa5825de65c5fed94 |

## Full contract reassessment

Exact finite ratios and Python integer floor division retain signed/subnormal/huge-bin semantics without float division or fixed-width overflow. Observation validation precedes all count mutation. Admissions remain stable in row order with novelty from each incremented count, bounded deterministic LRU, and cumulative reported eviction count. Explicit False and omitted flags leave counts, recency and evictions untouched, including existing-key and unseen-key queries.

Constructor selected configuration matches the immutable RP. Native tuple count keys remain valid checkpoint data. Owned state-v1 snapshots and staged restore retain complete policy provenance, validate active identity/configuration, epsilon schedule, counts, capacity, LRU and eviction totals before assignment. Different valid inactive authoring alone is not an identity rejection criterion. The zero neural-service receipt remains a no-op, avoiding a second admission. Inherited legal action selection and epsilon decay remain intact. No new scope resolver, bank or reward composer was introduced.

## Evidence and limitations

This refresh executed no project/runtime import, pytest, numerical probe or helper. No sixth probe source was opened. Root reports the r0 focused 33 PASS and separate bounded Astra probes for subnormal width, count `10**10000` and inactive-authoring restore in count-icm-independent-results.json; these are earlier root-reported evidence, not fresh verification by this reviewer or proof of fixed-candidate GREEN. Root will refresh focused/full/probe results after the source freeze.

Eligibility slicing, actual successor reward routing, single application of scale/DAC factors, and prevention of a mutating later diagnostic call remain required integration responsibilities. Instance ownership does not establish private WorldId banks, action RNG isolation, local clocks, X02, or GPU performance/correctness qualification. None is closed here.

No additional optional P3 recommendation is necessary for this adapter repair. The prior optional numerical/inactive-authoring cases now have root-reported independent runtime evidence, with fixed-candidate refresh still pending.

Only this ignored review report was written. No implementation/test/index change, source copy, branch/worktree, runtime execution or delegation occurred. Recheck candidate hashes before the authorized runtime phase; changed source requires renewed review.
