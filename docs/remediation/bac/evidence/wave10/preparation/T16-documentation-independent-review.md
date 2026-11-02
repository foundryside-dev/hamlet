# T16 documentation independent review

Disposition: **PASS for bounded source accuracy and qualification limits, with one low-severity wording tightening recommended before application.** No blocking false ownership, new capability, native-resume or release promise found. No runtime was executed for this review. G2 is root-reported RUNNING;25/66 qualified and41 remaining stay current. T16/native qualification is not established by this documentation review.

I read the complete ignored `T16-documentation-draft.md` and checked its claims against the same five complete sources already reviewed, with freshly recomputed matching hashes below. I also checked the expressly referenced T15 flat-contract/interface prose for the external buffer RNG roles; no linked implementation was opened. Existing R2/R3 review/runtime reports were not modified.

## Concrete wording gap and replacement

**Low severity — standalone options paragraph should distinguish saved owned state from an external-global role.** The proposed options.md addition says: “Saved sampler state is restored through the existing validated path, rather than replaced with a fresh stream on resume.” In context the draft correctly qualifies external-global/current formats elsewhere, but this independently applied paragraph can sound as though every resumed buffer serializes/restores its RNG state. The supplied T15 flat-contracts prose explicitly says buffer load does not overwrite global NumPy state or promise its exact continuation; captured PER5 retains an external-global adapter, whereas PER6 can restore its private state. POP's fresh configuration cannot fill missing historical RNG state.

Recommended replacement for that sentence:

> For supported current payloads, existing validation/adoption preserves the saved sampler descriptor and any recorded owned RNG state; it does not force a fresh PCG64 stream on resume. External-global sampler roles do not gain an exact RNG-continuation guarantee.

This is precision tightening, not a discovered production defect or a new gate. Retain the following uniform RNG-role sentence and all existing native-resume limitations. The BAC bullet already says “saved sampler ownership” and “existing supported loaders,” and the draft explicitly denies exact stochastic continuation; those statements are appropriately bounded.

## Checked source claims

- **Fresh PER versus uniform:** RR492 supplies an explicit training-seeded PCG64 Generator. POP469–506 actually gives that owned policy to selected flat PER/recurrent PER, while flat uniform remains its ordinary buffer and recurrent uniform uses `for_replay` without that Generator. The draft correctly limits fresh ownership to PER. The external Torch-uniform and Python-random statements are supported by the attributed T15 prose, not by new buffer source inspection here.
- **Canonical forwarding:** RR401–454 takes learner inputs from effective training; RR461 forwards the canonical effective brain; RR462–497 forwards the complete resolved replay object, declared minimum and required factory inputs. BC534–568 identifies the five brain overrides, and POP325 preserves zero gamma. There is no claimed second local resolution/default table. Canonical per-leaf roles remain distinct from the sampler's authored seed-policy label. POP453/641 supports the explicit warning that the factory's optional provenance tuple remains None.
- **Horizon and origins:** RR464–470 names the executed override or declared episode field and declared cap/declaration origin; RR494 is exactly executed episodes times cap. The wording correctly states upper-bound vector ticks, not actual completed ticks, summed transitions, N-scaled ticks or successful optimizer updates. The launch override is a runtime source name; the cap retains its authored absolute origin.
- **Construction/load boundary:** RR474–497 runs before RR522 load, with fresh tick0. No post-load reset/reseed was introduced. POP2033 onward restores state and invalidates binding; POP595 onward distinguishes loaded from pristine and adopts it. The draft appropriately presents this as static preservation evidence, not an actual fresh-only runner-resume PASS. Ordinary constructor/inspection/serving implementation is unchanged; fresh caller policy does not overwrite the separate external-global role.
- **Tests and observers:** The test anchors354/389/416/456/492,529-line size,12 parameterizations, N1/seed42/explicit episode override, fresh-only load assertion and distinct reported runtime scopes match the inspected file. A factory name is not presented as sole behavior proof: the draft names actual sample/finite optimization/weight-change evidence. Warmup1000, all-family and adaptive counterpart are correctly excluded from my three-case R3 execution claim.
- **Qualification:** R2's11PASS/1FAIL and correction are retained; R3 is not relabeled R4 and overlapping selections are not summed. Root-attributed R4 consumer results/G2 selection are labeled as such, outside this source/runtime review's independent proof. Earlier T15 native captures are not reassigned to T16. Conditional26/66 is gated on actual qualification and does not close the final54 requirements/22 lenses.

## Required boundaries preserved

The draft explicitly retains broad dated README source/CI and BAC review stamps, T15's separately dated correction, native10/7/T24/T25 continuation/resource/RNG atomicity, private-curiosity/X02, ICM full reward/update/continuation/T18e–f, final common-source learning/E2E/T40, coverage>=70%, slow/applicable hardware, fresh final reviews/synthesis and exact-tip CI. The shared AdaptiveIntrinsic/RND arrangement and its N1/world-binding limitation remain explicit; no strict per-world isolation or provider-precedence qualification is inferred from options parsing.

I did not reread the target README/BAC/CLAUDE/options/STATUS/ledger documents in this task. Therefore exact destination line numbers, existing surrounding wording, existing ledger-row linkage and claimed preservation of their current bytes remain documentation-author/root application responsibilities. The draft's scoped text itself preserves these boundaries. No destination text was applied or source qualification count changed.

## Source identity

All fresh hashes match the unchanged R3 five-source context; the broader R4 tree has separate consumer edits and is not independently attested by these five hashes.

| Complete source | Lines already counted | Fresh SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |529|`2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`|

Total5 sources/4422 physical lines; no sixth implementation/helper/provider/buffer/network/environment/conftest/probe source. No project imports, runtime, pytest/collection, linter, compiler, source/test/tracked-doc/index operation, commit/push, branch/worktree/checkout/copy/deletion or subdelegation occurred. This new ignored report is the only write; ignore status was verified. Existing G2-pinned reports remain untouched. Return stationary for root's actual G2/native results and eventual qualified documentation application.
