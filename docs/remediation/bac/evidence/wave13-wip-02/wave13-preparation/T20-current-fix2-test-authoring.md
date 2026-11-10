# T20 current-only fix round 2 — tests-first handoff

Stationary, tests only. Read the complete `T20-current-only-independent-review-r7.md` before writing. Root supplied prior R7 custody/local159 PASS/owned four guards PASS601, with global six unchanged factory-call errors remaining T21-owned. Runtime was closed. No test/import/collection/runtime/guard/git/index, branch/worktree/source copy, cleanup or subagent operation occurred. Only the owned test and this ignored prose report were authored; production remains exactly R7. Owned-test-only formatting was expressly authorized and is recorded below.

Root approved the finite test projection1000 before authoring; same five-file projection2520, hard5/5000. No sixth source/helper/probe inspected or authored. No architecture, native schema, journal, compatibility or caller work proposed.

## Actual inventory

| Whole file | Actual lines | SHA256 | Ceiling |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` |66|`d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268`|150|
| `src/townlet/curriculum/adversarial.py` |516|`ba79f1e650ac33180088475c7e3b94d92dbff083fdd6410308ef40ccbc4174cf`|950|
| `src/townlet/curriculum/static.py` |64|`22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`|220|
| `src/townlet/training/episode.py` |176|`53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf`|200|
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` |967|`e6d3b7ad72c102175d4ed4cc1541e6fa4edbce6a164012936dc5059d2e194e0e`|1000|

Total actual5/1789. Test headroom33 lines. Formatter `.venv/bin/ruff format tests/test_townlet/regressions/bac/test_curriculum_events.py` reported `1 file reformatted`, exit0. This is source formatting evidence only, not test/collection evidence.

## Causal negative witnesses and arithmetic

Added `test_latest_rate_interval_or_zero_rate_corruption_refuses_with_prepared_owner_intact`, eight parametrized cases using genuine completion histories. Each changes only stored difficulty within the existing band, expects ValueError at load, compares the full snapshot including state/telemetry/decisions/lane info/RNG, then accepts a receipt prepared before the attempted restore and compares its future effects against an uncorrupted genuine control. Thus refusal must preserve owner-token usability as well as visible state.

For bounds L/H, latest eligible steps S, rate r, budget B=r*S and target T from the **new committed stage**, any prior difficulty in [L,H] maps into `[min(T,L+B), max(T,H-B)]`.

| History | Current target/budget/interval | Damaged difficulty |
| --- | --- | --- |
| Saturated: rate1, dwell10, two full10/10 completions | First event advances to stage2; second keeps stage2 with zero progress. T=.25, B=10, interval[.25,.25]. |0 and.9, both in[0,1] but outside the singleton reachable result.|
| Interior: rate.01, dwell10, full10/10 then2/2 completion | Stage2 retained; T=.25, B=.02, interval[.02,.98]. Genuine difficulty is.12. |.01 below and.99 above.|
| New advance: rate1, dwell8,8/10 then10/10 | First event advances to stage2; second fraction improves.8→1 and advances to **stage3**. New T=.5, B=10, interval[.5,.5]. |.25 (old-stage target) and.9.|
| Zero rate: band[.2,.8], two full10/10 events | Initial difficulty.2 must remain.2 under immutable rate0. The generic B0 interval alone is[.2,.8], so a separate zero-rate invariant is needed. |.3 and.79.|

R7 currently accepts each modified lane state: they remain finite, within band, and pass existing stage/count/signal checks. Intended RED is `DID NOT RAISE` at the actual malformed-load assertion, not a missing interface or fixture error. No rate0 capability is removed to avoid its invariant.

## Genuine controls and future continuation

Added `test_genuine_latest_rate_endpoint_interior_and_new_stage_native_future`, seven parametrized genuine histories with literal expected stages/difficulties:

- Saturated stage2/.25; nonsaturated interior stage2/.12; newly advanced stage3/.5, as above.
- Lower endpoint: rate.01, full10/10 →10/20 retreat to stage1/difficulty0 →full10/10 advance to stage2. Latest T=.25, B=.1, interval[.1,.9], genuine output exactly.1.
- Upper endpoint/new retreat target: rate.01, fractions.75/.8/.9/1 using30/32/36/40 eligible steps of horizon40 reach stage5 and difficulty1. A10/20 completion retreats to **stage4**, new T=.75, B=.1, interval[.1,.9], genuine output exactly.9. This tests the post-retreat target and a valid upper endpoint without fabricating unavailable historical payloads.
- Zero-rate band[.2,.8], stage2/.2; singleton band[.6,.6], stage2/.6.

For each history, drain already-published source telemetry, load a genuine current-native snapshot, compare the complete snapshots and literal expected stage/difficulty, then commit the same fresh future event to uninterrupted/restored instances and compare complete resulting snapshots. Endpoint/interior/singleton controls protect representation-aware validation from rejecting genuine current states.

All159 previous substantive cases/values remain. No old-format helper, compatibility fallback, production edit or extra probe was introduced. Newly authored cases were not collected or run here; root must capture actual causal RED before production repair. Same Astra fix review and independent verification, focused/local/full outstanding gates and existing WIP-not-release status remain root-owned. All factory/caller/provider/world/native-boundary integration obligations remain unchanged.
