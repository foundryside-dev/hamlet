# WIP19 documentation proposal — linked version 3

2026-11-13. **INERT PROPOSAL ONLY.** No published document or application file changed. Proposed interval R99–R108; base/current reported remote `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`; terminal execution tree `fa1c6804fcff475f5652e5f5f357468e2d931c0d`. Publication identity remains separate. Clone repair independent SPEC/QUALITY verdict: **PASS for the bounded repair; concrete P2 addressed under the adopted ordinary native runtime profile.** Terminal evidence review, publication and new remote/CI verification remain pending.

Linked predecessors preserved unchanged: V1 `633f4fe7f154f4a3c9ac6c733454bfdfdfda49e2b74494a49836fde1df98410f`; V2 `c5a1797dbba07d968d56d2f719109490a22555c5164c0bc6c195935b109b14d2`. V3 supplies the final atomic checkpoint document bytes: README/core unchanged from V2; STATUS/index use continuing evidence scope and planned WIP19 navigation without stale pending-publication prose. Root verifies those destinations after assembly and before commit/push. No successful terminal review, new remote identity or successful current CI is asserted.

Read current CORE contract, current README/BAC status/index paragraphs and EVIDENCE-PROCESS. Only this proposal is authored; no new implementation body, application execution, test, Git mutation, branch/worktree/copy or delegation. Root owns application of the replacements, final reviewed document hashes, exact source equivalence, evidence assembly and publication.

## Frozen document inputs

| Path | SHA256 before proposed edits |
| --- | --- |
| `README.md` | `fe172c53b4e34beb9723698d9b827e3cbb9175fdf498c63851216d5ec0f5c70a` |
| `docs/remediation/bac/STATUS.md` | `d7ef31d33a56ce6203582c5558c84bcee0177166550c4380a7e8302f2b4002c4` |
| `docs/remediation/bac/EVIDENCE-INDEX.md` | `72b86c0763dc8e297efcc5cd5988b5b37fad28d91a436d61ae166af575698b7e` |
| `docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md` | `259f78f91209cd917412941a7f60e3eef557899414110306ac4d9f75bfa9a9a7` |

Exact replacement/insertion blocks follow. All text outside these anchors stays unchanged. Historical R89/R98 evidence remains dated and source-bound. The planned WIP19 links below are part of these final document bytes; root verifies their destinations after assembly and before commit/push without a post-seal document edit.

## CORE contract replacements

1. Replace the paragraph starting `Current [rng_custody.py]` under `## Current source and qualification scope` with:

```markdown
The implemented invocation-outcome core [rng_custody.py](../../../src/townlet/exploration/rng_custody.py) is 948 lines, SHA256 `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`. Its initial [CUDA admission regression](../../../tests/test_townlet/regressions/bac/test_rng_cuda_admission.py) packet is 1681 lines, SHA256 `ccc74e6bac55f322d3363ac1e19c820b2b97b0d86839b392dfabedb452647a38`.

R106 has independent initial-source SPEC/QUALITY approval and 76 exact-candidate passing controls: 66 nonisolated and ten existing isolated cases. These establish the initial API/lifetime/authentication packet and retained regressions, not the new nonempty own-phase failure, nested failure, invocation fork, direct state or numeric-ID alias qualification. Those second-phase controls remain owed. The ten old children do not qualify new invocation outcomes. R108's extended public-consumer type probe passes for the required factory, `RNGDeviceInvocation`, `AbstractContextManager[RNGOperation]`, bool getter and `Literal[False]` exit; owned typing/style and unchanged defaults600 also pass. The [evidence index](EVIDENCE-INDEX.md) separates these exact candidates and remaining gates.

### Historical R89 qualification

R89 used core821 SHA256 `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477` and test1409 SHA256 `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`. The following results retain those historical source bindings.
```

The existing R89 paragraphs immediately following this insertion remain unchanged beneath the explicit historical heading, including their original source-specific counts, type failures and hardware limits.

2. After the existing `domain.device_operation` API table row, insert these exact rows:

```markdown
| `domain.device_invocation(*, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation \| None, cuda_devices: tuple[int, ...])` | returns opaque single-use `RNGDeviceInvocation` |
| `invocation.__enter__()` | yields the authentic `RNGOperation` |
| `invocation.__exit__(exc_type: type[BaseException] \| None, exc_value: BaseException \| None, traceback: TracebackType \| None)` | `Literal[False]`; preserves failures |
| `invocation.completion_failed()` | immutable historical `bool` after an entered invocation exits |
```

3. Immediately before `## Lazy resolution, READY and enrollment`, insert:

```markdown
## Single-use invocation completion outcome

`device_invocation` binds the explicit participant, kind, lineage and immutable device tuple without CUDA work, owner pinning or domain exclusion. Actual entry repeats admission through the same operation implementation and yields its genuine lineage; nested contexts can yield the same parent operation while retaining distinct invocation identities. `TracebackType` is from `types`; `Literal` is from `typing`. All inputs are required, and normal exit returns False rather than suppressing errors.

The opaque source-issued handle cannot be copied, serialized, reused or moved to another thread. Every handle method checks actual process PID before registry, thread, lock or CUDA access, then authenticates the exact issued identity and issuing Thread object. The lifecycle is issued → entering → active → exited, or entering → entry_failed. The getter refuses before completed exit, including entry failure. Historical reads require no active operation, membership, domain/owner lock or CUDA access and remain valid after poison, unrelated work and participant retirement. They grant no draw, token, publication or parent authority. Termination releases execution bindings; retaining the completed handle does not retain its owner, operation, original errors, traceback or generator through the outcome record.

The result describes only this invocation's own required completion phase. False means its actual completion returned successfully, including an empty phase that touches no CUDA attribute. True means that phase failed or remained uncertified. Body errors, reported gate errors, shared poison and exception identity do not determine the result. Nested completion uses its admitted subset; outermost completion uses the final union including descendants. A child's False remains unchanged if later outer completion fails. A failed child can be True while a parent's own successful union phase is False, although poison and error propagation remain in force.

Certification occurs at the actual completion call, and exit seals the result before outward error delivery. A body error E and synchronization error using that same E can still propagate as exactly E while the result is True; body-only E with successful completion yields False. The receipt adds no retry or second synchronization pass. Generic completion retains its current implementation; its early-stop tail is not a new permanent outcome guarantee. Local completion retains its separate all-declared-devices rule.

The producer must retain actual owner exclusion through completion, result read and any justified uncertainty transition. The core boolean neither proves lock custody nor identifies affected owners/devices. Parent integration must designate the consumer of the outer outcome and justify owner transitions from actual reachability before releasing the relevant locks; it cannot reinterpret a child's immutable receipt or infer blanket quarantine. The implementation and initial CPU controls do not close these producer or second-phase qualification obligations.
```

4. In the paragraph starting `New gate entries and every gate method`, append this sentence, preserving the existing scope restrictions:

```markdown
An exited RNGDeviceInvocation's historical getter is the explicit post-exit exception; it does not revive any expired synchronous operation or gate.
```

5. Replace the sole paragraph under `## Subsequent producer checkpoint boundary` with:

```markdown
R99–R108 retains staged flat/PER producer work and the newly implemented core invocation outcome. R106 source review approves the initial core implementation; second-phase own-invocation failure/fork/state/alias qualification remains open. R108's reachable CPU selection passes 507 distinct controls, with 836 collected and 329 UNRUN, including ten producer poison children. The clone repair has independent fixed-source SPEC/QUALITY PASS; concrete clone-stability P2 is addressed under the adopted ordinary native runtime profile. Production local-contract activation, actual producer children, parent outcome ownership/handoff and recurrent integration remain required; no B acceptance follows. See the [evidence index](EVIDENCE-INDEX.md) for exact candidate and scope.
```

6. In the final sentence of `## Remaining integration and hardware obligations`, replace the exact substring `the deselected required ordinary-runner case,15 global type errors` with `the deselected required ordinary-runner case, global typing`. Historical R89 and older dated type-error counts remain untouched; this current obligation does not assert a newly rerun global result.

## README replacement

Replace only the paragraph starting `Subsequent flat/PER CUDA producer work is staged and incomplete.` with:

```markdown
The R99–R108 checkpoint adds an implemented single-use RNG invocation outcome and a bounded clone repair. Initial core source review and 76 R106 controls pass; R108 separately passes 507 reachable controls, with 329 focused cases UNRUN. Independent clone-source SPEC/QUALITY review passes the bounded P2 repair under the adopted ordinary native runtime profile. Own-invocation failure/fork/state/alias qualification, production CUDA contract activation, producer children and parent/recurrent integration remain open. See [BAC status](docs/remediation/bac/STATUS.md), the [core contract](docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md) and the [evidence index](docs/remediation/bac/EVIDENCE-INDEX.md). This remains unreleased work in progress; accounting stays 28 qualified / 38 remaining / 66 total.
```

Preserve the preceding dated R85/R89 paragraphs and broader README review stamp.

## STATUS insertion

Immediately after `# BAC implementation status`, insert this section; retain every existing dated section unchanged:

```markdown
## 2026-11-13 — WIP19 checkpoint: invocation outcome and clone repair through R108

The R99–R108 checkpoint ends at execution tree `fa1c6804fcff475f5652e5f5f357468e2d931c0d`, based on `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`. R106's initial single-use invocation implementation has independent source SPEC/QUALITY approval and 76 exact-candidate controls PASS. The new handle supplies an immutable own-phase completion result without changing genuine lineage or granting producer publication authority; its second-phase failure/fork/state/alias qualification remains open.

R108 records 507 distinct reachable PASS, 836 collected and 329 UNRUN. It covers the bounded clone repair's causal/preservation and native/opaque boundary controls; independent fixed-source SPEC/QUALITY review passes, addressing clone-stability P2 under the adopted ordinary native runtime profile. Owned typing/style/defaults600 and the extended invocation public-consumer type probe pass. Global mypy16 is historical evidence, not a fresh global result; owned typing does not establish global success or reduce the historical count to15. R106's 76 belong to a separate exact candidate and are not added to 507 or described as an R108 run. Collection is not execution, and these results do not accept B activation or the unrun producer cases.

Production local-contract activation, ten producer poison children, actual parent outcome ownership/lock handoff, recurrent integration, real CUDA and remaining runner/full-suite/coverage/slow/learning/final-review gates remain open. WIP18 remote is reported at `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`: Config PASS, Lint FAIL with 16 known errors, and Tests FAIL in the fast suite; test-log retrieval was unavailable, so no detailed Tests cause is inferred. Publication identity and CI are verified separately; this checkpoint makes no successful-current-CI or full-BAC acceptance claim. **28 qualified / 38 remaining / 66 original packages** is unchanged. See the [core contract](CURRENT-RNG-CUSTODY-CORE-CONTRACT.md) and [evidence index](EVIDENCE-INDEX.md). This is an unreleased evidence checkpoint; full A/B/component/programme acceptance remains open.
```

## EVIDENCE-INDEX insertion and heading change

Before `## Current checkpoint: WIP18 / R98 — work in progress`, insert:

```markdown
## Current checkpoint: WIP19 / R108 — work in progress

The [manifest](evidence/wave35-wip-19.json) and [selection plan](evidence/wave35-wip-19/selection-plan.json) record the finite R99–R108 interval, ending at executed candidate `fa1c6804fcff475f5652e5f5f357468e2d931c0d`, base `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`, candidate-manifest SHA256 `27b28f930659b690c55db0a0e4a2edc97155210ce0c9bf1f0e38738e4f85bdce`. Execution identity and publication identity are distinct; publication does not turn bounded component evidence into full programme acceptance.

R106's independently source-approved initial invocation implementation has 76 exact-candidate PASS. R108 separately records 507 distinct reachable PASS, 836 collected and 329 UNRUN, with owned typing/style/defaults600 and the extended public invocation type probe PASS. The clone repair's other-model fixed-source SPEC/QUALITY review passes: concrete P2 is addressed under the adopted ordinary native runtime profile; full A/B qualification remains open. Global mypy16 remains historical, not a new global check. These are bounded source/custody results; the two candidates' counts are not summed. The archive preserves failed, interrupted and unrun interval attempts.

Core own-invocation failure/fork/state/alias qualification, production local-contract activation, ten producer poison children, actual parent handoff and recurrent integration remain open. Tooling protocol reviews or synthetic controls do not qualify those application paths. Real CUDA and final repository/coverage/slow/learning/review/CI gates remain required. **28 qualified / 38 remaining / 66 original packages** is unchanged.

WIP18 remote is reported at `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`: Config PASS, Lint FAIL with 16 known errors, Tests FAIL in the fast suite. Test-log retrieval was unavailable; no detailed cause or equivalence with local typing errors is inferred. Publication identity and CI are verified separately; this checkpoint makes no successful-current-CI or full-BAC acceptance claim.
```

In the same atomic edit, change the exact existing heading `## Current checkpoint: WIP18 / R98 — work in progress` to `## Historical checkpoint: WIP18 / R98`. Preserve every WIP18/R98 and earlier historical paragraph. The planned manifest/selection-plan links above are final bytes, not a later edit; root verifies both destinations after assembly and before commit/push.

## Source/evidence mapping and publication conditions

| Proposed claim | Binding and limit |
| --- | --- |
| Exact API, identity/thread/PID, lifecycle/release, own-phase certification and union semantics | Previously reviewed core948 SHA256 `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`; independent source review `P/T18e-R0-CUDA-INVOCATION-OUTCOME-IMPLEMENTATION-REVIEW.md`, SHA256 `841eb6bc15a15161a970fb306d427f36c6a3b167d9c73fc73e16ab22b0a8789f`. No new source read or execution here. |
| R106 76 disjoint current-node passes; second phase still open | `W/wave35/r106-root-checks.json`, SHA256 `803d831ae57fbc8fd46963be58ee095301895beb6c4fcc88fb572aa6a4b05570`; separate tree `ab46784efc86bab95b031494529e06871a12f1ff`, manifest `12e5609bf4f300e608ebd6f94297fd0f2496bf95169e757864cb6ad50fbd0970`. |
| R108 507/836/329, owned guards and exact public typing | Freshly read `W/wave35/r108-root-checks.json`, SHA256 `500a588b4c6af705cf7f824b0bbc1d1953b67efe2cb0beb99a8d38672c959dec`; candidate manifest `W/wave35/r108-candidate.json`, SHA256 `27b28f930659b690c55db0a0e4a2edc97155210ce0c9bf1f0e38738e4f85bdce`. Root-executed evidence, not a documentation-author rerun. Distinct groups are 436 prior reachable +8 clone fixtures +34 native controls +21 classifier +8 causal plans. |
| Clone fixed-source review PASS | `P/T18e-R0-CUDA-ARCHIVE-CLONE-STABILITY-OTHERMODEL-REVIEW.md`, SHA256 `eaf6b4b20eb37d4bbc7056d91d04c0c0d4d34fedbf61c060a32d7fc1f7345213`. Reviewer inspected actual three-body source/full deltas; bounded P2 addressed under adopted ordinary native runtime profile; no new probe requested. No full A/B or hardware acceptance. |
| WIP18 exact-head remote/CI | Root-supplied status in this task: df8dcebc; Config PASS/Lint FAIL16/Tests fast-suite FAIL/logs unavailable. Root must bind the actual immutable remote/CI receipt in WIP19; no receipt path or SHA is invented here. |
| Counts, retained failures and current/future publication distinction | EVIDENCE-PROCESS requires one authoritative exact-candidate record, immutable attempts, independent terminal review, overlap-aware accounting, separate execution/publication identity and postpublication remote/CI checks. Accounting remains 28/38/66. |

Before application, rehash the four document inputs and reconcile any legitimate intervening edit; do not overwrite unrelated text. Before publication, root must bind the actual clone verdict, required terminal review, complete R99–R108 failed/unrun attempt inventory, selected dependencies and final document-review bytes. The sealed clone PASS closes only that bounded source gate, not terminal evidence review or full A/B acceptance. Final source-equivalence and remote/CI checks belong to root; this proposal supplies no publication or acceptance receipt.

## Final expected document identities (in-memory only)

Computed from the hash-verified frozen live inputs by applying these exact eight blocks, the core current-obligation substring replacement and the WIP18 historical heading change. No live document or evidence destination was written. README/core identities match V2. Root can bind these final bytes in the receipt before assembly, then verify planned destinations before commit/push; no later navigation edit is needed.

| Final proposed document | Lines | SHA256 |
| --- | ---: | --- |
| `README.md` | 551 | `efed71def427225be84e0d6f9e67d6f87df4401df392907de2195d195d3e36a3` |
| `docs/remediation/bac/STATUS.md` | 300 | `52d5261a3b7eb5f8f36286ab2c7e5aa5b13abcaf8764147dcfeb21fe32c4affe` |
| `docs/remediation/bac/EVIDENCE-INDEX.md` | 45 | `9646ff5b9672b505943d2a3c335b01d8662253f8b92358aee16ad0b050ef6fad` |
| `docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md` | 232 | `553a840a6b54c28763cec8a1e2e84f8161f9aa67832b2d3e1b07bf90c0eb7aab` |
