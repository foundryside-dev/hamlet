# Independent Astra supplemental reviews

These are separate prospective method/checker/fence and R1 repair reviews.
They preserve the interim58a refusal and supply no final implementation acceptance.
Their dated information gaps describe the point of each review; subsequent gate
receipts and the final criterion review are recorded separately.

## Prospective method review

Original artifact: `runs/episode-lanes/2026-10-02/implementation/review/inherited-terminal-adjudication/review.md`. SHA256: `c012e3d331e0f060bff22cbb61495aec73ba8d18045d8249b03ddc0545d9682d`.

```markdown
# Astra prospective review: PDR-0161

**Decision: method APPROVED; inspected draft checker NOT YET APPROVED for qualification.** The proposed exact-coordinate adjudication is legitimate under the approved plan. Before GO, implement and freeze the safeguards below. No acceptance gate was run by this reviewer, and no implementation acceptance follows.

The E4 policy at `docs/plans/2026-10-02-truthful-episode-lanes.md:305` explicitly directs retention and scoped comparator/PDR adjudication of an inherited recipe's legitimate terminal difference. Its final gate policy at line 1044 permits independently qualified exact newly observed boundary differences. `docs/oracle/known-divergences.md:1691` preregistered the earlier-death/false-retirement cause and requires exact adjudication without matrix or stream allowances. PDR-0161 follows that process; it does not change the policy to accommodate an unrelated defect.

The seven coordinates are a finite instance of the already registered correction. I independently read the original failed reports and recomputed all ten direct-parent raw trace comparisons. Only items row99 agents0/1/3 and effects row99 agents0/1/2/3 change float32 bits `0x3f800000` → `0x00000000`. All other reward bits and all observation/action/done bytes agree. Independent sticky-done counts are `[49,51,100,54]` and `[65,67,62,60]`. Both static and frozen-action four-cut bridges agree with their original traces; E2 contains all changes and E3/candidate add none. All three raw DAC contributors are zero at each changed coordinate. Items lane2's genuine retirement retains `0x3f8147ae` (`1.0099999904632568`). These independent checks are retained in `evidence_audit.py` and `evidence-audit.json`; they are forensic checks, not execution of the proposed acceptance gate.

Source identity at review: HEAD `58a7048eca23a6c8c5d9d509ab6f8459cc91ee45`. `git diff 8e3ca306..HEAD -- src scripts configs` is empty. Original gate source remains `8e3ca306d6f615bd272bb1c8d51b071b74686877`, static `qualified=false`, standing `new_dirty=true`; neither is relabelled. Exact reviewed PDR, draft checker/spec, plan, findings and original-report hashes are in `evidence-audit.json`.

## Confidence Assessment

**Overall Confidence: High** for method authorization and bounded causal explanation; checker readiness is presently insufficient.

| Finding | Confidence | Basis |
|---|---|---|
| Plan authorizes independent narrow adjudication while preserving literal failures | High | E4 lines305–312 and final policy1044; DIV-016 scope and standing-harness paragraph. |
| Seven differences are dead-entry false bonuses, not changed live behavior | High | Independently recomputed raw arrays, eligibility, counts, causal bridges and component values; retained audit. |
| Original frozen action stream was truly bridged | High | Read actual standing parent/E2/E3/candidate NPZs and compared frozen rewards/actions/dones against parent, then parent/candidate unchanged streams. |
| Draft checker does not yet enforce complete PDR | High | Read `causal/inherited-terminal-streams/scoped-comparison.py` and `proposed-spec.json`; gaps below. |

## Risk Assessment

**Implementation Risk: Medium** until checker safeguards are complete. **Reversibility: Easy**, since adjudication is external and artifacts are retained.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Narrow success conceals a missing/different cell or reset/inventory failure | High | Medium in current draft | Assert complete named inventories and exact original-report invariants and verdict sets. |
| Correct arrays attributed to wrong source/config/candidate | High | Medium in current draft | Validate pinned source/config/import closure, report/trace provenance and candidate equivalence. |
| Value equality hides undesignated signed-zero or nonfinite differences | Medium | Medium | Finite validation plus byte-exact reward residual comparison after removing only seven literal coordinates. |
| Candidate ledger alone obscures causal source or erroneous components | High | Medium | Validate parent/E2/E3/candidate ledgers and components against independent events and raw driver streams. |
| Final summary says inherited gates passed | High | Low with PDR | Preserve actual nonzero exits/dirty flags and separately label scoped adjudication. |

## Information Gaps

- Revised checker and complete adversarial controls are not yet available; no passing qualification receipt exists.
- Full source/config closure records were read structurally but not all rehashed in this bounded review; the checker must perform these checks.
- Final candidate-wide suite, lifecycle comparisons and PRD1–8 acceptance are outside this method review and remain pending.

## Caveats & Required Follow-ups

Required before GO with the checker:

1. Assert exact ten-cell static inventory, 31 inventories/884 readings/11 reset recipes, no identity/stale-attribution/unattributed/reset errors, and only the declared two reward mismatches. Check the complete standing cell-ID/verdict set: eight existing registered CPU outcomes, exactly two declared failures and ten explicit CUDA skips.
2. Pin/verify original failed reports and source/config/import closures, full causal SHAs, authored pack/level/action identity and complete trace inventories. Preserve `new_dirty=true`; separately demonstrate committed source equivalence. Final acceptance must bind to its actual candidate identity, not merely inherit the older receipt label.
3. Require explicit shape/dtype and finite numerical checks. Compare every undesignated reward byte exactly, including signed zeros. Require all and only the seven literal changed coordinates with exact old/new float32 bits. Preserve every live reward and the genuine retirement bit pattern.
4. Consume parent/E2/E3/candidate lifecycle and component evidence, not only the candidate ledger. Independently derive eligibility and survival from full sticky dones and assert one-shot events, no dead-entry retirement, raw zero components, actual count behavior and no post-E2 stream changes.
5. Implement every PDR corruption control: wrong live reward, false bonus retained, missing/stale/unused expected delta, swapped coordinates, changed action/obs/done, nonfinite reward, wrong eligibility/survival and genuine retirement corruption. Also test corrupted source/config/inventory/report identity and undesignated signed-zero changes. Mutate private copies only.
6. Freeze/hash checker and prospective specification after those changes; retain actual qualification/negative-control results and both original failures. The seven-coordinate adjudication must not broaden matrix/register/harness allowances.

The method is approved now. The inspected draft is not authorized to produce an acceptance claim until these prerequisites are satisfied and its actual behavior is checked. No further policy amendment is needed merely to implement these already required safeguards. Implementation acceptance, CUDA, convergence and recovery exit remain separate.
```

## Strengthened checker review

Original artifact: `runs/episode-lanes/2026-10-02/implementation/review/inherited-terminal-adjudication-strengthened/review.md`. SHA256: `54f654ed85149452ff04ff7047587ca1f4edf4f25d9c1266fce41a4f6376e444`.

```markdown
# Strengthened E4 checker prospective review

**Decision: approve the checker safety structure; qualification GO remains pending final source binding and specification freeze.** This is not implementation acceptance. No qualification gate was executed during this review.

Reviewed checker SHA256 `05fa08a7d36fdc0222339fc23f867c971d221a0270b41ab0784f21ca86397a27` and prospective structure SHA256 `741d045071fce7df46b8733c036ce6cac7ea364d63a0f7b2ec783c020e8598ca` at HEAD `58a7048eca23a6c8c5d9d509ab6f8459cc91ee45`.

The full source enforces all ten static and frozen CPU cells, the 31 inventories/884 readings and eleven reset recipes, all twenty standing verdicts, and exact original failure/dirty metadata. Literal substitutions cover only seven float32 coordinates; the entire remaining reward array must match byte for byte, including signed zero. Every affected causal bridge validates parent, E2, E3 and retained candidate actions, dones, observations, lifecycle counts and raw/published components. The final candidate must match those retained executions. Source/config closures and forty-two private-copy corruption controls cover the previously identified gaps.

Independent read-only checks verified all 157 original artifact digests, inclusion of all thirty frozen NPZ files, 434 config bindings, forty-two declared controls and parser validity. I inspected the complete comparator, mutation controls and specification builder. No new concrete method blocker was found.

Before GO:

1. Commit the custody repair and bind the exact final source SHA, full committed source closure and verified physical import root. Retain the exact allowed two-file source difference fence.
2. Capture four actual final driver/collector bridges across both affected recipes and both action modes.
3. Complete the final fields and add hashes for the final closure and all new driver/collector NPZ and ledger JSON files. Preserve all existing 157 original artifact and 434 config bindings.
4. Register the completed specification hash before executing qualification. Re-review any checker logic change.

## Confidence Assessment

High confidence in the narrowly scoped method and static source inspection. Actual comparator and corruption-control execution remains pending.

## Risk Assessment

Medium execution risk until final binding and all controls succeed. Low scope-expansion risk: exact-coordinate and complete residual-byte checks cannot authorize a stream-wide reward exemption.

## Information Gaps

Final repair commit, four final bridge receipts, completed preregistered specification hash and executed control results remain outstanding.

## Caveats & Required Follow-ups

This does not qualify CUDA, learning, convergence or production RNG isolation, and does not replace either original nonzero gate result. The separate 58a implementation review remains NOT ACCEPTED pending custody repair and all final gate receipts. Prior reviews were preserved.
```

## Final committed source fence review

Original artifact: `runs/episode-lanes/2026-10-02/implementation/review/inherited-terminal-adjudication-strengthened/final-fence-review.md`. SHA256: `306c5cd948175293042669b52ca631bef05cc1b0e593e526ea55e1169337e6ff`.

```markdown
# Final E4 fence review

**GO for the exact scoped checker after root registers completed specification SHA256 `471412bcd3016b9a76bc739caf455386b3214729734b7229fb29fc403ea512da`.** Checker remains the reviewed `05fa08a7d36fdc0222339fc23f867c971d221a0270b41ab0784f21ca86397a27`.

Independently verified all 182 artifact and 434 config digests, final commit `462e8a3980845d76e7987cfea67fb63432bcb847` archive/full source closure and physical source equality, and the exact permitted two-file difference fence. All four final driver/collector bridges have identical array dtype, shape and bytes (including metadata), and identical ledger JSON, to the retained candidate.

## Confidence Assessment

High confidence in the completed source/specification fence. No qualification gate was executed by this reviewer.

## Risk Assessment

No new method blocker. Actual comparator execution can still expose an error; all forty-two corruption controls must reject.

## Information Gaps

Actual qualification receipt, full suite and final numerical/lifecycle evidence remain outstanding.

## Caveats & Required Follow-ups

Register the exact completed spec before execution. This GO authorizes that execution only. It does not accept the implementation, qualify CUDA, claim convergence, or replace either original nonzero gate result.
```

## Exporter custody repair review

Original artifact: `runs/episode-lanes/2026-10-02/implementation/review/implementation-candidate/r1-repair-review.md`. SHA256: `11759a470ecfe106ab761300de53bad20047218bbc24079848a3c0a9193c06be`.

```markdown
# R1 repair review

**R1 verified repaired at `462e8a3980845d76e7987cfea67fb63432bcb847`; ready for the full suite.** Reviewed both production files, all new custody regressions and the two updated real current-schema fixtures.

The original closed legacy WAL reproduction now raises `ValueError: Unsupported demo schema version: 0` while preserving every original family member, including absence, bytes, device, inode, size, mtime and ctime. The new thirty-one custody cases independently pass in 0.63 seconds. They exercise accepted current WAL files, malformed/legacy/missing/empty/companion cases, late TensorBoard failure, both actual exporter entrypoints and external family mutation. SQLite never opens the original. The context retains custody checks through SQL and TensorBoard reconciliation and closes all private connections.

## Confidence Assessment

High: inspected actual production paths and reproduced the original failure condition against the repair.

## Risk Assessment

The supported mode still requires exclusive custody of a stopped, companion-free database. Fingerprints detect external changes and leave them intact; they do not implement concurrency control.

## Information Gaps

The final full suite, E4 and numerical/lifecycle receipts remain outstanding.

## Caveats & Required Follow-ups

Original failed evidence and the 58a review remain unchanged. This closes R1 only; full implementation acceptance remains pending.
```
