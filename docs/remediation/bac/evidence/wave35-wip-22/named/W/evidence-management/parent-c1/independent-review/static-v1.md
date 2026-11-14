# APP-C1 frozen implementation v1: independent static findings

2026-11-14, `/root/bac_astra_parent_c1_contract_review`. **NOT READY at these bytes:** two finite P2 implementation/contract findings require resolution. This is a preliminary static review; final independent review must revisit repaired actual bytes and all nine contract groups, with separately authorized executable evidence.

| Frozen body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 1311 | b3101198bad2eb73a5b9678ec4ca5007465f91f3650a043be3b6674dae86cff3 |
| src/townlet/exploration/scoped_curiosity.py | 1443 | 55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4 |
| src/townlet/exploration/parent_custody.py | 234 | 80bb75a9a1ef819e55d79d50e90ad9f592cec91b18563e12ec0d8f622a03c681 |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 740 | 17ed9a6086bccf6dbca4195b8ad824ae7a60ba97338d37a35d2d52cf39defef1 |

Current four source bodies total3728. Root explicitly authorized one additional independent causal probe body <=450 lines; authored64, total3792/five. No other implementation body was opened. The earlier reviewed runtime/BANK are the same logical bodies, now remeasured. Supplier/fixture/helper contracts are prose/metadata only. No APP execution, import, test or compile was performed by this reviewer. Production/test bytes remain frozen; only this report and the root-authorized auxiliary probe were written. Root owns R118 and all qualification/execution.

## P2-1: ordinary ingress can index an expired scope record

`parent_custody._local` obtains a genuine scope using `_lookup(owner)` before acquiring domain admission, then separately indexes `_records[scope]`. The issuing thread can exit its legitimate retained scope between those operations. `_expire` removes that record while the contender still holds its local scope reference. The contender's subsequent indexing raises KeyError instead of continuing through ordinary domain admission.

Causal schedule: A retains real runtime/BANK; B's ordinary runtime or BANK method enters `_local` and captures actual scope; B pauses; A exits actual context and expires records; B resumes `_records[scope].thread`. This requires no forged scope, raw owner mutation, domain bypass or unsupported callback. It violates the explicit ordinary-other-thread waiting/admission requirement. Weak dictionary references do not serialize the compound lookup/delete sequence.

Required correction: make foreign-thread scope observation safe across expiration without acquiring owner locks before common admission or weakening same-thread live-scope authenticity. A missing record from an already expired foreign observation must not make ordinary work fail. Preserve current wrong-thread handle misuse refusal as a separate operation.

Root-authorized deterministic probe: `independent-review/test_scope_expiration_race.py`,64 lines, SHA256 `774219868be84b1f9d07f66a9edb9d677d97883cd8d7071f8f162fdeef188c87`. Nodes `test_contender_lookup_survives_issuer_scope_expiration[runtime]` and `[bank]`. Each first creates actual make_parent(compiled) and successfully calls the real ordinary owner method. A transparent real `_lookup` wrapper pauses the contender after genuine lookup; real issuer context exit performs expiration; then the contender resumes. No positive authority is manufactured. Probe is authored, **UNEXECUTED by reviewer**; root will seal exact auxiliary bytes and run the intended RED. Writer concurred statically and remains frozen pending root release.

## P2-2: final runtime install adds ordinary invalidation after BANK publication

`ExplorationRuntime.install_restore` now calls `_bank_call("install_restore", ...)`. That ordinary wrapper's finally compares BANK mutation_revision and invokes `_invalidate` after successful BANK dictionary publication and completion. `_invalidate` increments runtime revision and clears its restore registry; final install then overwrites revision and registry with the already-prepared publication values anyway.

The original final-install boundary deliberately permits only preallocated runtime assignments after BANK return. Its retained comment still says no fallible work, callback, loader, allocation or corrective check follows publication. New ordinary invalidation introduces an unnecessary revision check, integer update and registry clear in that cut, contrary to the accepted publication constraint. This is a source-visible contract regression; no fabricated runtime failure is claimed.

Required correction: route final install directly through the same finite private `_forward_bank` authorization seam, without the ordinary revision/invalidation wrapper, preserving the prepared runtime assignment sequence. This is not permission to bypass the delegated guard or add a compatibility route. Existing ordinary forwarders still need their invalidation policy.

## Other acceptance observations

The A-only selector component test currently passes full-roster successor masks to runtime.select_actions, including inactive rows without legal actions. Root already identified this fixture issue. The production method deliberately requires a legal action per presented row. Repair the test with genuine active-row data/masks from the earned handoff; do not relax production validation or invent legal inactive actions. This is an invalid positive acceptance setup, not evidence that valid C1 selector behavior fails.

The inspected implementation otherwise places BANK invocation exit and its own sealed-outcome read inside actual BANK/domain exclusion; keeps the monotonic completion latch and `_entered`/`_lineage` in slots outside restorable dictionaries; uses producer-private scope/permit records; consumes exact runtime forwarding permits before public BANK body/callback/admission; retains the public-call guard across standalone preparation's operation-idle cohort gap; and rejects bound cohort routes before effects. Genuine parent lineage comes from public admission, not core-private ambient discovery. Native own completion and copied-output attribution remain as supplied, without blanket native quarantine.

All nine contract groups remain owed in final qualification, including actual healthy fixtures, domain/runtime ordering, retained consumer lifetime, callback authority and permit cleanup, owner pin expiry, same-object and distinct completion failures, child/parent phase independence, standalone modes/restore and dictionary lifetime, declared-device controls and empty CPU laziness. Five poison roles require one-node fresh root-qualified processes and actual self-witness; skips cannot qualify them. CPU seams do not qualify CUDA hardware. Final approval cannot be based only on confirming the two edits above.
