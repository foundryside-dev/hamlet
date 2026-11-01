# Review provenance

Historical finding/review; see the final implementation receipt for repair and qualification.

Original artifact: `PW02-astra-review-r3.md`; SHA256 `9f36256cb69b37a649c33b64a5a167bcd7c790d3a86dffba04bd2754e6afcfa9`. The original is retained unchanged. This portable rendering normalizes execution paths; it does not alter the review verdict or source binding. This artifact describes its recorded earlier source. The repaired implementation and final review are linked from the package receipt; final qualified release `eb73173496a7955b30a6fea4b65ccae8cc615b87` has sum tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`. Historical findings below are not current unresolved findings.

# PW02 fresh independent adversarial review R3

Verdict: **BLOCKED — one confirmed P2 in the finite PW02 ownership primitive.** No P1 found. This is a static source/spec review, not a new executed reproduction or runtime qualification. Repair and fresh review are required before PW02 dependency release. Root continues the full BAC implementation; this report neither closes X02 nor authorizes early stopping or a capability reduction.

## Scope and immutable candidate

Reviewed existing `/workspace/hamlet`, HEAD `23755537926c2808c8b312f4f5b52ad76ab594ab`, staged candidate tree `f372de50f0efce29229855eb9fe4b6d09bff5d53`, against `wave05/green-r3-candidate.json`. Exactly five complete implementation/test files were read, 2750 lines total; no sixth source/helper/probe was inspected:

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/exploration/world_curiosity_state.py | 734 | 3cc53945442d15066aadb4d5e3eb985a9daba1b23094c1c741df6e6a35028bac |
| src/townlet/exploration/rnd.py | 661 | 3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72 |
| src/townlet/exploration/icm.py | 380 | 8004aec68d19c962df0cf6785b00af32c8553a3746fee95be39009555f9d44b8 |
| src/townlet/exploration/adaptive_intrinsic.py | 226 | 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9 |
| tests/test_townlet/regressions/bac/test_pw_rng_domains.py | 749 | a16a6d621fb4dd4f3b9dfce496795a0ed2bad2fa87d4ccb0dc44169c4c38d627 |

Read root AGENTS.md and the PW02 interface capsule, task brief, and relevant per-world curiosity addendum contracts. The using-superpowers skill explicitly excludes dispatched subagents; verification-before-completion evidence discipline is applied to snapshot/report verification, without overriding the direct ban on runtime execution. No project imports, tests, runtime experiments, subdelegation, source edits, source copies, branch/worktree creation, deletion, tracker writes, or index edits occurred. Only this ignored prose report is written. Git tree identity was read through write-tree; no staged entry changed. Existing authority and actual tool approvals govern; no failed governance rule or user-only fallback is adopted. Higher user preservation instructions supersede the root blanket deletion rule.

## P2 — Mapping keys leak live parameters through the owned callback boundary

**Exact production location:** `src/townlet/exploration/world_curiosity_state.py:248–249`, reached from `OwnedWorldBackend.call` at lines 654–656. `_owned` returns `{key: _owned(item) for key, item in value.items()}`. It recursively owns values but reuses every original key. Tensor handling at lines 242–243 therefore never runs for a tensor used as a key.

**Contract:** PW02 capsule states that returned receipts/tensors cannot expose internal mutable storage and requires recursive detached tensor clones/copied containers at the owned boundary. It does not limit valid callbacks to numerical scalar keys or forbid exporting native optimizer diagnostics. No such narrowing has been approved.

**Concrete static counterexample using a real inspected backend:** Construct an owned RND backend and perform one genuine minibatch update (RND Adam is attached to predictor parameters at rnd.py:175; zero_grad/backward/step occurs at 382–385). Then call `owner.call(lambda backend, sources: backend.optimizer.state)`. PyTorch Adam's native state mapping is keyed by its live Parameter objects. The returned dict has copied moment values but the exact original live Parameter keys because of WS:249. Take `parameter = next(iter(exported))`; performing `parameter.zero_()` under `torch.no_grad()` mutates the owned predictor outside the owner guard. A later ordinary checkpoint/reward sees changed weights, although no owned callback ran for the mutation and the wrapper's revision/quarantine machinery never observed it. The same pattern applies to ICM Adam (icm.py:93, 157–161), or adaptive via `backend.rnd.optimizer.state` (adaptive_intrinsic.py:59–68, 130). Even an untrained backend can expose the same defect through a dictionary keyed by a parameter; native learned Adam state makes a custom invented container unnecessary.

**Impact:** Core callback result ownership is violated. A caller can unknowingly corrupt live network state while handling what the API promises is an owned result. Revision-bound prepared state can also remain apparently current across an escaped-key mutation. This is not a claim of malicious callback sandboxing; the callback simply returns ordinary backend state and the mutation happens later through the returned result.

**Required repair direction:** Deep-own mapping keys as well as values, retaining supported callback capability and detached tensor semantics. Add a regression in the already counted PW02 test using real learned optimizer state: mutate an exported parameter key outside the callback, then assert the live network and optimizer continuation remain unchanged; retain a positive check that the exported key actually changed. Check composite keys containing tensors as appropriate. Do not repair by imposing an unsupported numerical-only callback contract or deleting general result support. Recount the same five files after repair. No runtime reproduction was executed by this reviewer; the counterexample follows directly from the unmodified key expression and real Adam ownership.

**Why current green tests miss it:** `_mutate_arrays` traverses only mapping values (test:394–396). Existing snapshot/restore mutation tests at 403–458 cover state_dict integer/string keys, tensor values, moments, pending rows and adaptive history. Object-array tests at 688–710 correctly cover array payload ownership but do not exercise mapping keys.

## Independently checked paths and refuted hypotheses

- Previous object-array value alias defect is repaired for both plain and structured object-bearing dtypes: WS:244–247 branches on `dtype.hasobject` and uses deepcopy, with genuine adaptive-history regression at test:688–710. That repair does not cover the independent mapping-key hole above.
- The healthy native OrderedDict/plain-dict false rejection is repaired by owning readbacks before strict comparison (WS:708, 712, 715). `_same` still checks exact types/dtypes/devices/shapes, rather than weakening equality globally. The learning fixture canonicalizes only mapping representation (test:187–196).
- The versioned seed recipe uses exact world identity/provider/training seed/component and distinct Python, PCG64, legacy NumPy and declared CUDA domains (WS:416–444); creation uses local generators. Spectator order is excluded from component identity. Python's activation-bound facade delegates to installed globals (372–387), avoiding two independently advanced Python representations.
- Genuine A→B→A now reuses the suspended A frame (548–552), captures suspended ambient state (558–559), advances it (572–576), and restores the current outer frame (584), rather than the stale initial saved copy. The actual regression at test:713–734 compares both streams and whole resulting snapshots. Cross-owner nesting refuses before swaps (542–543); one RLock covers lifecycle and TLS stack state.
- Cleanup catches BaseException and attempts every captured global restoration (349–369, 567–589). Capture failure marks the private owner broken; restoration failures poison the process coordinator and retain failures. The isolated failure-injection regression is source-inspected only (test:598–685), not run here. It asserts Python/NumPy restoration after a failed Torch restoration and refusal without additional swaps.
- Factory outputs are cloned; ICM's MappingProxy-bearing resolved policy is reconstructed via its portable API before deepcopy (WS:620–628). There is no need to strip the policy or change shared constructors. Real providers remain read-only in this packet.
- Saved continuation RNG and disposable construction/load streams are distinct (WS:692–718). Destination identity, revision, quiescence and one-use checks precede the reference swap (720–734). Failed live calls quarantine (647–661); failed diagnostic snapshots also quarantine (663–679). No automatic retry after a real optimizer step is introduced. Restore preparation is off-side and readback is exact; provider validation is mandatory but remains a supplied pure contract, not complete semantic validation inferred from equality.
- The tests exercise real RND/ICM/adaptive learning, nonzero parameter and Adam-moment changes, fixed-target preservation, tail conservation, post-update failures, independent same-WorldId instances, and continuation after restore. The transparent random-consuming callback is honestly labelled (test:163–180); deterministic current provider updates alone are not presented as native random-service proof.

## Evidence and required open gates

Root-owned log `qualification/wave05-green-r3/PW02.log` was read: 26 collected, **25 passed / 1 skipped in 8.67s**. Root reports 15.83s wall time. This is attributed root evidence, not reviewer execution. The single CUDA skip is a hardware qualification gap, not a CUDA PASS. No test was run by this reviewer while root qualification was active.

PW04 complete backend semantic validation (especially adaptive config/history), actual target/predictor constructor hooks, and native local eligible-admission service clocks remain REQUIRED OPEN. Current RND target/predictor construction still shares ordinary ambient constructor order (rnd.py:166–175); ICM initialization uses its existing constructor order (icm.py:86–93); adaptive delegates to current RND. This finite primitive does not prove those future integration obligations. PW03 actual backend-factory/bank integration and subsequent bank/runtime quiescence/routing gates remain REQUIRED OPEN. T24/T25 native admission/loader qualification remains OPEN. X02, broad strict-B completion, shared-Q independence, whole simulator state, old-artifact acceptance and the final support matrix are not closed here. Existing shared alternatives and defaults must remain available.

Additional finite coverage gaps, without elevating unproved implementation failures into findings: inner malformed RNG state canonicality cases, failed entry installation/private capture, and combined primary-plus-cleanup failure are less directly exercised than envelope rejection, healthy continuation and restoration poisoning. These do not erase the direct P2 above. No separate optional P3 is asserted.

## Final stationarity receipt

Before and after review, HEAD and staged tree equal the candidate identities above; all five SHA256 values equal the manifest. Index byte SHA256 is unchanged at `874cc5c96a2a93f116fe3c87ef080eac92d856ca0152b23820f2270fc01bd5cb`. `git diff --name-only` is empty both before and after (no unstaged tracked drift). The same 13 staged paths remain present; existing staged work was not modified. `git check-ignore` confirms this report is ignored. The five-file whole-source inventory remains 734+661+380+226+749 = 2750 lines. Review/report is complete and stationary; no further action by this reviewer is pending.

## Root-executed causal evidence addendum

After this review, root reports an actual causal reproduction of the P2: after a genuine RND Adam update, the key returned by `owner.call` exporting native optimizer state was a `Parameter`; mutating that exported key changed only live predictor `net.0.weight`. The intended ownership assertion failed. Root reports all 49 guarded source hashes, HEAD and index unchanged through its before/finally guards. Evidence: `qualification/wave05-r3-key-red-and-remaining/mapping-key-red.log` and its accompanying result JSON. This paragraph attributes root's execution report; this reviewer did not execute the probe or inspect its source (which would be a sixth source file). The original five-file review inventory remains unchanged. This strengthens the causal evidence for the existing P2, not a broad PASS. A repaired counted regression, repaired source, and fresh final candidate review remain required before release.
