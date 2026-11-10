# World identity actual-source R1 independent review

Candidate: root-pinned tree `2ab1dfdc105a9ae3e559c829096c1e50ca3860a7`.

**Spec verdict: CHANGE REQUEST. Quality verdict: CHANGE REQUEST.** The declaration and broad lifecycle placement follow the approved design, and the implementation honestly excludes real consumer/native/simulator qualification. The issues below are narrower than a design restart. No P1 runtime defect is established by this static review; P2 issues require repair or a precise contract ruling before producer handoff acceptance.

## Scope and evidence

Read the requirements/review briefs, author report, supplied actual diff package, approved design/amendments and previous closures. Actual implementation inspection stayed within the same five-file inventory: ENV2278/2442, WS734/734 readonly, RP768/768 readonly, test701/715, roster291/341: **5/4772 actual, 5/5000 ceiling**. No sixth source/helper/probe/fixture, imports, runtime/tests, source/test edits, Git/index operations, copies, branches/worktrees, deletion or subagents. This ignored report is the only write. Read root's supplied mypy log as evidence; its diagnostic source paths do not constitute inspection of those other sources.

Root reports owned45 PASS, 0 warnings,17.798s wall and custody PASS. These are attributed root results, not independent executions. Root also reports global mypy FAIL75 errors in7 files; the raw log was inspected. At review time Ruff/defaults/expression were root-reported PASS; Black/CLI were still pending. No passing global or integrated acceptance is inferred from the owned45.

## Findings

### F1 — P2 confirmed defect: duplicated native closure integers accept bool/float values

`config/world_roster.py:282–288` compares last_closed_episode's batch and sequence fields with already-validated integer history using Python equality, without applying exact_integer or validating their serialized types. For a genuine first completed snapshot, replace only `last_closed_episode.batch_episode=1` with `True`, or its `world_episode_seqs=[1,1]` with `[True,1]` (similarly1.0). These pass equality against batch1/history[1,1]/cursor1. The returned prepared state preserves the invalid types. ENV2262–2267 then installs those values in the restored WorldAcceptedEpisode. This violates the exact non-bool integer native contract before any later owner validation is considered. Existing corruption tests cover bool in accepted_bindings, not these duplicated fields.

Remedy: validate last-closure batch and every sequence independently with the exact type/range checks and validate its sequence/ID container shapes before semantic equality. Add isolated malformed-last tests, asserting pure refusal and unchanged destination. Avoid accepting contradictory duplicate representations merely because Python considers them equal.

### F2 — P2 confirmed producer-contract gap: child effect issuer checks validate against themselves

`environment/vectorized_env.py:158–163` invokes `WorldReceiptIssuer.validate(child, name, child.owner)`. This proves that some issuer issued the receipt, but does not prove the child came from the actual sink for that role. A bound boundary owner can unintentionally insert a receipt from a separate `_Sink()` with matching accepted token/boundary in the population_commit_receipt slot; the code accepts it although ENV already knows the activated population owner. The current test at the end of the test file rejects a foreign **outer** boundary_effects owner; it does not test foreign **child** receipt custody. The same self-owner validation pattern appears in initial owner preparation at ENV190–193.

This is cooperative custody correctness, not a security claim against Python introspection or an accusation that a trusted T26 owner is malicious. A missupplied child from the wrong actual owner must fail rather than becoming a valid completion release/initial proof. The approved contract explicitly requires correlation and issuer custody, and the additive generic issuer vocabulary does not settle which actual owner is authoritative for each role.

Remedy: bind/freeze the expected owner or accepted issuer for every effect/initial-state role through the concrete T25/T26 handoff, using known activation owners for applicable roles. If T26 is deliberately the certifying owner for some normalized child role, specify that distinction and require that bound owner, rather than a self-referential check. Validate the role's required correlation/content fields under that frozen contract. Test a valid outer proof containing a foreign child and a same-boundary wrong-content child; both must refuse before release/state installation. This does not require inspecting or implementing real consumers in this slice.

### F3 — P2 confirmed intervening-state gap: prepared closure survives further rollout

ENV2094–2125 validates participation at preparation, but leaves phase active. `step` at ENV1247 permits more rollout; it does not update the lifecycle generation. `close_episode` at ENV2127–2143 checks only the capability/current accepted token, then installs its earlier payload without rechecking current participation or a pinned live-state revision. Concrete witness: participate only A, prepare its A-completed/B-retired closure without committing it, then step B as well, then pass the old preparation to close_episode. The old prepared token remains generation-valid and can close with B retired despite actual B participation. The current _Run.close helper prepares and commits immediately, so tests do not exercise the gap.

The design's single runtime owner prohibits intentional interleaving, but also explicitly promises destination/generation protection against intervening-state misuse. A producer receipt should not claim the latter while only relying on the caller convention.

Remedy: pin a rollout/state revision in prepared close and refuse it after any step, or introduce an explicit precommit boundary freeze that blocks stepping after successful full preflight, or revalidate exact pinned participation/content at commit under an equally precise owner protocol. Preserve pure whole-sink preparation and equal closure retry. Add the prepare/step/commit refusal witness without changing existing genuine completion assertions. The committed-disposition prerequisite of prepare_episode_close also needs an explicit earlier pure-preflight route in the T23/PW05 handoff if that handoff promises that every expected ENV refusal is checked before any sink commits; do not silently treat the postcommit check as whole-boundary preflight.

### F4 — P2 confirmed quality gate failure: owned typing regressions and immediate caller seams

Root's actual mypy log reports three new owned errors in roster112,250,291 (Any returned from dict-returning methods). Repair those within the owned module without ignores. The log also reports `has-type`/derived-return diagnostics in existing action/reward helpers, originating from ENV attributes now inferred through the changed dependency graph. Root should verify/recover stable ENV attribute typing within the counted producer rather than open those helpers opportunistically or suppress their checks. Causality of the individual helper messages remains diagnostic evidence, not independently executed analysis.

Separately, missing required constructor arguments in EF/compiled/oracle and reset-return/signature mismatches in oracle/POP are real current-only caller maintenance obligations shown by the root log. Their sources were not opened. They need named immediate serial inventories and exact new protocol receipts; no no-ID/untokened fallback is acceptable. These integration seams may be recorded in an explicitly incomplete WIP, but cannot qualify a coherent runtime tree or be waved away because owned45 pass. Global mypy remains failing until root's fresh verification says otherwise.

## Accepted behavior and remaining integration scope

The additive roster is authored, owned and exact; constructor validation precedes existing construction randomness. ENV retains the live authority/cursor/reset owner; roster contains data/codec/validation only. Pure repeated reservations, accepted reset observation ownership, preactivation step refusal, late-reset quarantine, explicit abandonment, save-independent releases, required INITIAL/COMPLETED kinds, fresh restore capabilities and per-batch binding history are represented concretely. No extra lifecycle coordinator, historical format adapter or supported-family removal was identified.

The direct from_universe constructor route is an explicit implementation choice with the prior EF forwarding/normalization receipt. It does not establish that the standalone EF path or actual runner is updated. WS/RP remain unchanged; actual WS descriptor/bank ID routing and current-only RP consumer cleanup remain their named obligations.

The tests correctly label opaque local sink content as producer-interface evidence. They exercise actual ENV reset/step and binding preservation, but do not prove real canonical EP fingerprints, bank disposition/native equations, actual nested NN/provider initial restore, on-disk manifest custody, T25 retained-reference union, sink/epsilon interruption semantics, or VFS/simulator independence. Existing VFS autonomous scalar increment/row-key draws remain a specifically required direct-consumer repair; ambient spawn/layout RNG remains unqualified. These are disclosed integration dependencies rather than newly discovered local defects, and no integrated/family/learning guarantee is accepted here.

Installation interruption still needs executable fail-closed evidence: reset/restore use multiple assignments within try/except quarantine guards; closure/release/activation have ordinary multi-assignment transitions. Do not describe those assignments alone as proof of arbitrary interruption atomicity. The current45 do not cover every post-install/pre-ack interruption promised by the handoff. Root can allocate a finite adversarial packet after exact runtime/CPU-slot clearance; this reviewer has not run one.

## Proposed finite adversarial follow-up

In the same counted test file and pinned environment, test F1's bool/float last-closure duplicates; F2's bound outer proof with wrong-role owner/content; F3's prepare/step/commit misuse; and interruption immediately after closure installation/before acknowledgement followed by equal retry. Snapshot all observable lifecycle/live state before each expected refusal. Real consumer/native tests remain with their named owners, not substitute sinks. Repair/review and root rerun the owned packet plus required global checks at the final fixed source before claiming producer acceptance.
