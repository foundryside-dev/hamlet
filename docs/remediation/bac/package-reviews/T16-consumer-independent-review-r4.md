# T16 consumer repair R4 — independent bounded static review

2026-11-02. Reviewed in existing `/workspace/hamlet`, candidate tree `51c6d53eb2a815257b7eab4bffa800fb54d8a2a2`, base `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`, as recorded in `wave10/r4-candidate.json`. Exact review artifact: `wave10/r4-consumer-review.patch`. This is a fresh source/spec and quality review of the two consumer fixture repairs, not a rerun or a new main-production qualification.

**Verdict: static spec and quality approval for this bounded repair; no introduced blocking defect or hidden assertion/scenario weakening found. Runtime remains unverified here.** The patch changes only the two named tests; production RR/POP and LANES hashes match the audit and supplied R3 context. The larger candidate manifest also names the main RR/readiness work; that is not misrepresented as part of this two-file repair.

## Independent custody and inspection

Read the complete failure audit and repair receipt, complete exact patch, selected candidate manifest fields, and all five complete sources below, without following imports. Optional T16 brief/readiness/implementation prose supplied contract context; a combined prose read was output-truncated, so no claim is made to complete independent re-review of all those optional documents. All source reads were complete and untruncated in separate bounded chunks. Independently counted and hashed at entry and exit; all five remained identical and match the candidate manifest:

| Whole source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` |312|`e6631eb7e2375165a1e1131eaf88999e8debb024d37ef736bf9eadcdacd3fbde`|
| `tests/test_townlet/integration/test_runner_hyperparams_v21.py` |126|`237ca50b9deb1e585c7d37d1134896b4fe1a29dde12b4de7a401210e317c4db0`|
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` |157|`9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f`|

Total: exactly five whole sources / 3758 physical lines. No sixth source, helper, environment, artifact payload, network implementation or test was read. Manifest artifact/config names and hashes are metadata, not payload reads. The candidate tree was read from the supplied manifest, not regenerated through the index.

## Repair reasoning and preservation

RR401–426 binds one effective training view, binds its loop, then passes that same training object to build_curriculum. The SINKS observer stores precisely that loop, calls its imported real build_curriculum once with the unchanged positional/starred/keyword arguments, and returns the real result. The runner contains one such construction call. The imported function binding is independent of the patched runner-module attribute, so this does not recurse through the mock. No curriculum result or completion is fabricated.

The cap assignment still occurs after the real population reset and before RR593 reads max_steps. LANES still authors lifespan10 and two agents; SINKS still asserts the real environment lifespan10 before assigning cap3. Curriculum, exploration, population and the beta upper-bound horizon have already been constructed using10. The fixture does not pretend that a late loop cap recomputes their construction-time settings. It mutates the local runtime training view, not runner.training_config, compiled configuration or an identity/hash field. Owned-copy isolation of the effective carrier is an existing prose contract, not independently re-inspected sixth-source evidence.

The two end-tick permutations still create lane counts [2,3] and [3,2], three vector ticks and five eligible rows. POP stores actual eligible transitions and successor masks before finalizing authored terminals; RR flushes the surviving nonterminal lane with reason cap before constructing the curriculum publication. POP flush does not turn the stored done flag true. The original assertions retain one actual terminal, a live final replay row, exact DB values and completion-before-publication. No budget substitution, authored-lifespan shortening, expected-five-tick relaxation or acceptance of two terminals appears.

The exact patch touches no SINKS test-function body or decorator. All seven bodies, both permutations, no-cap/two-episode, budget6, zero-work budget1, real-DAC and owned-final-meter scenarios remain. Independent textual counting finds67 assert statements in current SINKS; the patch adds exactly the capture assertion and removes none, consistent with66 original assertions. The implementer's AST-equivalence check is separately reported evidence, not rerun here.

HP's observer keyword-only names/order match POP.for_training, including explicit replay/horizon inputs and no invented defaults. Installing it as classmethod supplies cls normally. The same7/5/3.5 authored values and all three numerical assertions remain, with the same stop sentinel. POP.for_training uses __new__ then _initialize, which explains why the previous __init__ spy failed to intercept. Moving the observer to the actual public construction boundary preserves its narrow runner-forwarding purpose. It does not qualify internal factory forwarding or real population initialization; those remain separate production evidence.

No named public per-episode cap constructor/setter exists in complete RR. Its documented max_episodes, max_environment_steps, level and force-new-VFS controls remain. Direct mutation of runner.training_config stopped steering the runtime loop in the main canonical-copy change; this observable behavior difference must not be denied. Within the supplied contract it is fixture plumbing, and root's audit addendum explicitly accepts that classification. This review supplies no approval to remove a stronger external runtime-mutation guarantee if an owner supplies one later. The repair itself removes no production API or capability.

## Cleanup, geometry and remaining gaps

The new SINKS patch is context-managed alongside the existing observers. All patches unwind on normal completion or exceptions; the DemoRunner context exits first and performs resource cleanup. The original curriculum update function is captured before the inner patch, preserving the outer completion-order and owned-meter observers. The loop capture is local to each helper invocation, so one test does not retain another test's cap target. The source still resolves action names from compiled IDs and checks eligible Q/state/action/mask geometry; no fabricated token schema or relaxed action dimension was introduced.

Two pre-existing limitations are worth keeping visible, not treating as repair blockers:

- HP constructs DemoRunner without a context manager. Its expected sentinel occurs before RR's training-loop try/finally, so explicit DB/TensorBoard cleanup is not exercised on this test path. Monkeypatch restores both classmethods, but runner resources and installed signal handlers have the existing lifecycle limitation. The old successful spy also stopped at this early location; this patch does not introduce the leak. A separately authorized cleanup improvement could wrap that test runner in its context manager without changing forwarding assertions.
- SINKS's cap test directly asserts replay cardinality and nonterminal done state, not numerical TD bootstrap values or exact successor-mask contents. POP source preserves real successor-mask admission, but these five sources/tests alone do not constitute a runtime legality-target proof. HP likewise proves boundary values only. Neither limitation justifies weakening existing tests or manufacturing wider coverage.

The observer forwards once per runner construction call by source structure; it has no separate mock call-count assertion. That is adequate for the stated preservation repair and is not a new production single-construction guarantee. Main-policy identity isolation is source/prose-grounded, not newly asserted by these consumer tests.

## Execution and scope limits

No imports, project runtime, pytest, collection, AST probe, compiler, linter, formatter or diagnostic test ran in this review. Root reports the prior affected result4FAIL/261PASS/1SKIP and main selected3PASS; those are attributed context, not this review's executions. R4 exact-four runtime and later affected/static/full gates remain root-owned. Static approval does not close T16 release, any of54 final requirements, any of22 lenses, or any package beyond the root's current25/66 qualification.

Only this ignored report was written. `git check-ignore -v` confirms `.git/info/exclude:7` matches `/.superpowers/`. No source/test/tracked-document/index/commit/push change, branch/worktree/checkout/project-source copy/deletion, artifact mutation or subdelegation occurred. All14 checkouts were left untouched. Stationary pending explicit root assignment.
