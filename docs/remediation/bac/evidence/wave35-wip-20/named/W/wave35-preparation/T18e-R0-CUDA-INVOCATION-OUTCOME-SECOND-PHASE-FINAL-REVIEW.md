# Invocation outcome — final bounded source/design/execution reconciliation

2026-11-13. Reviewer `/root/bac_astra_invocation_source_review`.

**SPEC: PASS. QUALITY: PASS. Bounded CPU pre-B invocation prerequisite: PASS.** The unchanged implementation, independently reviewed second-phase assertions, qualified tooling and actual R109 executions reconcile with the adopted invocation design and finite qualification protocol. No remaining material core CPU gap or concrete P1/P2 is identified in this packet. Root may use this disposition for its next bounded B decision; this report does not itself grant a producer write or accept B, parent integration, hardware or whole BAC.

## Exact subject and independently inspected evidence

The implementation scope remains exactly core948 + test2166 =3114 lines/two bodies. Fresh current hashes are core `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e` and test `780b1464c258d0a0162f9f0983be079b869c3868b4d24fbbc029afa154218b36`, matching the previously read source and authored protocol. No verifier, synthetic-test, helper or producer implementation body was inspected. Tool hashes were checked as bytes only. No application import/execution, redundant runtime rerun, source/test/tool/index mutation, branch/worktree/copy or delegation occurred. This is the sole authored artifact.

R109 base is `0597715b8d59ab3bdda41ef5521b9772aaa9c436`; actual execution tree `35ba7e44c6be2516da6a39422376c26bdf993127`; manifest SHA256 `798f7964b2513168b58a3cb46d29b626cd57e5541eb2d738c568141aee1df781`. Runtime is root-executed evidence, not a second reviewer execution.

| Exact record | SHA256 |
| --- | --- |
| `wave35/r109-root-checks.json` | `87320230075f8299f55d974be77b5057f679fcc922c9ee6e06d7681228407903` |
| `wave35/r109-isolated-and-phase-pair-checks.json` | `906231432c0f1950ae5e2650726ca6c35c0cca2fea1c93aa6ad96f6022dfb97d` |
| `wave35/r109-invocation-verifier-qualification-and-runtime-grant.json` | `eaecc6674e385612813ba036711d7952d74048bcfcbdac71d74317faffb747e7` |
| `Q/wave35-r109-invocation-phase-pair-custody.json` | `7072ea4b2648a2a4f2c1a7519afe50f77db2636b99dd4492c3beca8936539b6e` |
| `P/T18e-R0-CUDA-INVOCATION-VERIFIER-IMPLEMENTATION-REVIEW.md` | `16d1f4a30e3169173c1007a859df7621404b1097034cbed6231f8f8f822a4fa2` |

Here W is the existing `.superpowers/sdd/2026-11-01-bac-remediation-upgrades`, P its wave35-preparation directory, and Q `/workspace/bac-review-2026-11-01/qualification`. Previous actual source review `P/...-SECOND-PHASE-REVIEW.md` is `7aea3ba6b7fd450afa4c9de7146e0f41cdc0cd31c7fdfcefe6e0c8ca3d602bca`; authored protocol is `57d2984443217a1f31ae468173bf4d21333d5828ee3cf1df550f9963cf3414c3`.

Personally rehashed 94 distinct directly referenced subjects from the healthy, isolated, tool-adoption and pair records, verifying their declared byte lengths and SHA256s. This included result/spec/custody/phase/source metadata and the tool-byte identity; it was not recursive unrelated evidence discovery. Also checked all16 actual result-log hashes, all16 one-job integer-workers1 specs, exit0 and one passing case per generic receipt, common candidate/manifest bindings, strict verifier identity and each child's own PID/PPID correlation. Healthy custody records report66+4+1+1 passes with zero skips/xfails/xpasses/warnings and source/index/import/thread/fixture custody PASS. Fork identity/observation hashes and phase artifact/parent/strict hash linkage were checked directly.

The earlier healthy record's isolated-held status remains historical to that stage. The later separately sealed isolated record closes those16 executions; neither record is silently rewritten.

## Reconciliation with the accepted behavior

| Adopted obligation | Actual source and qualified evidence |
| --- | --- |
| Exact all-required opaque single-use API; genuine operation yield; no suppression or fabricated authority | Unchanged core59–79/675–753 and the retained initial API/auth tests run in R109's66 prior-healthy selection. Constructor/copy/subclass/forged identity, lifecycle/reuse and retired-member refusal controls remain intact. Existing signatures/defaults/local manifest are not weakened. |
| Historical result without operation/member/owner lifetime or lock/CUDA dependence | The prior historical/token/retirement, unused-owner and completed-body-error weak-reference controls pass again. New state/lifetime job passes actual issued/entering/active/exiting/exited/entry_failed observations, zero read/refusal acquisition counts, cleared execution fields, live generator completion identity and weak-key expiry. The source retains only finite outcome/thread provenance after release; the getter never calls `_usable` or CUDA. |
| Genuine Thread-object identity and refusal before exclusion | Prior wrong-thread-under-held-lock tests plus the new real-thread-alias job pass. The alias fixture forwards real current_thread and aliases only the custody numeric dependency, while real A/B objects and actual locks remain genuine. This proves the stated controlled alias resistance, not actual OS-ID recycling. |
| Successful/empty completion and existing currentness/union semantics | Healthy parity/nested/currentness instances pass; empty-path NoCUDA controls remain. Actual nonempty success vector [0,1,2], nested/sibling union [1,2,0,1,2], genuine token behavior, independent historical False values and shared-operation lock parity are asserted by the reviewed tests. |
| Own-phase result independent of body/poison/exception identity | New same_error and reported_failure isolated cases pass. Same E produces False after body-only completion and True after same-E sync failure while outward E identity is preserved. Reported poison with successful own completion stays False. Valid factory issuance followed by invalid-subset entry has no body/sync/outcome; poison-refused entry remains unreadable. Other entry-error reasons retain the same source exception/release path; no claim is made that each has a separate new node. |
| Nested failure versus outer completion; immutable child/sibling outcomes | Qualified child_failure proves child True/parent False with one-shot child fault and successful outer union; a later sibling is poison-refused, not a fabricated success. parent_failure proves both child/sibling False survive parent True. Completion/read/competitor order occurs under the actual owner lock. This qualifies core attribution/read custody, not a production owner-quarantine policy. |
| Completion certification before outward deduplicated error; no extra retry or changed cleanup policy | Unchanged `_finish` certifies only actual own `_complete` success; `_exit_invocation` seals before outward delivery. Same-E and ordered distinct E/F controls pass. The explicit separately revalidated pair agrees on observed [0,1] for reference and invocation. [0,1] is this implementation's actual trace, not a fixed public tail requirement. Local all-device behavior remains separately preserved and its existing isolated cases pass. |
| Real inherited PID guard before lookup/locks/CUDA/state mutation | The actual third invocation fork trial passes all five adopted actions, exact RuntimeError/diagnostic, zero integer acquisition/CUDA/body counters and unchanged expanded state. Genuine active/completed handles were prepared before fork; the reviewed guard observes all eight registry fields and active context/frame completion linkage. The old admission/local trials also pass. |

Actual invocation fork grandchild PID150159 has parent/inherited-domain PID150063 and single-OS-task profile. Its five action keys are exactly active_enter, active_exit, active_completion_failed, completed_completion_failed and domain_device_invocation. These are guard-only Linux observations; no Torch/CUDA work or inherited-scope unwind is implied.

The phase reference subject has child/parent149940/149857 and null outcome; failure subject149965/149859 and True outcome. Both bind this same source/manifest and observed [0,1] vector with ordered body/synchronization labels. The actual assertions establish E/F object identity before serialization. Pair references bind exact individual strict receipts and parent-read phase hashes; process identities remain per subject rather than being compared across independent jobs.

## Tooling and count boundaries

Strict verifier SHA256 `311f32e05522e1f81b7c2e130f95483568eb642a88b12ed44e7b3188084c7cd0` has independent frozen implementation review, root75 synthetic PASS and7 independent adversarial probe PASS. This reviewer read that prose/result metadata and checked hashes, not the tooling bodies or a redundant synthetic rerun. The independent review confirms closed role/trial admission, exact typed schema/receipt checks, exclusive individual writes, full per-subject revalidation and side-effect-free pair receipt construction. Its qualification supplies the tooling premise; actual child/fork/phase records supply application evidence separately.

Root collection is88 with all prior76 retained. The72 healthy nodes and16 isolated nodes are disjoint, giving **88 unique R109 PASS**, not88 plus R10676 or R108507. Each isolated case used its own one-job/worker1 fresh child. Three fork trials are witnesses within the inherited-PID node; the pair comparison and tooling probes are not additional application tests. The initial V8 orchestration syntax rejection occurred before dispatch and is preserved without inventing an application retry.

R109 Ruff/Black pass. R108's extended public invocation type probe and owned type/defaults600 evidence are reused only for identical core bytes; they are not described as new R109 typing/default execution or proof that unrelated changed files inherit qualification. No current global type/CI success is inferred.

## Remaining boundary and recommendation

The finite CPU pre-B core prerequisite is now supported by accepted design, exact source, reviewed causal assertions and actual qualified runtime, including the previously held new children/fork/pair. No routine rerun or new probe is requested without a new concrete concern or changed subject.

Production local-contract activation remains absent. Actual B/public producer invocation integration, ten producer poison children and the producer329-node unrun scope are separate from these16 core children; they are not closed here. The designated parent-outcome consumer, actual owner/device-effect reachability and justified transitions before real owner-lock release remain required. A child's False still cannot authorize or explain a later parent union failure. Recurrent/current-parent integration, real one-/two-device CUDA, global typing, runner/full/default/coverage/slow/learning/final reviews and exact-final CI remain open. Original package accounting remains28 qualified/38 remaining/66 total. Root retains the next bounded B grant and publication decisions.
