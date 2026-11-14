# PW04 C3 packet A independent implementation review

2026-11-14. Reviewer `/root/pw04_restore_env_a_review`, independently assigned Astra medium. Static review of fixed r156 candidate, base `f2bfae2ee6fbeca120754eefa7e32cb2442c3c9e`. No P1/P2 finding or material A specification gap identified. This is bounded A source approval; execution qualification remains root-owned. No B/C, native-owner, continued-learning, PW04 or package closure is claimed.

## Reviewed bytes and bounds

The following SHA256 values were computed from the existing checkout and match `wave35/r156-candidate.json`:

| Whole body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/environment/vectorized_env.py` | 3041 | `c362c37649e4e5f2a8b3cd910e4cc9ba34b665fcf0429c166e15abaab9f29b37` |
| `src/townlet/environment/parent_custody.py` | 418 | `fe0490b6a998fc73787bef36ef39230265bc1203079b2690c205200a597c927a` |
| `src/townlet/config/world_roster.py` | 312 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |
| `tests/test_townlet/regressions/bac/test_prepared_world_currentness.py` | 301 | `e28fc2310597e4585e3f92bc6e0718f80c8fb94f4c6d6c7fa3ef03ae5b7b7998` |

Four whole-body inventory entries / 4072 cumulative lines. Relevant sections inspected within those bodies; this is not a claim of exhaustive review of unrelated ENV physics. AGENTS.md read. No Git, source copy, worktree, imports, test execution, formatter, deletion or delegation. Manual implementation was not opened: its real field mapping is attributed to the implementation supplier `pw04-restore-env-a-api.md`; ownership and approved predicate semantics are checked against restore-correlation `producer-facts-v3.md`, `ownership-capsule-v1.md`, and `env-independent-design-review-v3.md`.

## Source findings

1. **Issuance and authenticity:** ENV `prepare_world_restore` seals the genuine `_record` before returning (ENV 2972–2991). Helper 143–170 captures original payload identity and receiving metadata; 176–191 authenticates exact concrete record and ENV weak registry before inspecting authority fields. Equal-content and copied records cannot substitute. The seal is frozen and keeps no direct strong reference to its weak key.
2. **Pure retained validation:** helper 78–93 authenticates process, creating thread, live exact scope and retained pins before the check. Operation-bound scopes and active/reverse work refuse. Helper 172–275 performs metadata checks only: no public payload accessor, Tensor work, `same_value`, encoding, RNG admission, new lock, issuer work or callback. Refusal does not poison the receiver or consume the preparation. Existing retain 278–287 establishes exclusion; validation reuses it.
3. **Receiving identity and ownership:** helper 193–252 covers fresh-bound phase, exact integer zero generation/revision/cursors, original roster/seed/lane IDs/semantic identity, authority/owner and role/runtime/callback identities, empty accepted history and absent pending effects. ENV `bind_boundary_authority` builds an owned immutable MappingProxyType role mapping, so the mapping identity plus ordered value pins do preserve the actual original role associations under the cooperative API. Reacquiring a later scope cannot erase the separate issuance-time pins.
4. **Manual capability:** helper 253–275 accepts the actual healthy fresh manual session and checks its population binding, authority, PID/thread and idle/no-pending/no-failure state. It neither calls a manual callback nor demands a runtime. Exact mapping to the manual implementation is supplier-qualified as stated above.
5. **Payload and lifetime preservation:** WorldRecord public accessors defensively copy mutable leaves; the check never asserts that Tensor or opaque capability leaves are primitive immutable content. Ordinary payload schema remains unchanged. Weak seals retain original payloads, not their own keys; an opaque older record legitimately retained by a live later preparation is not itself a leak. Abandoning the later key should release that graph. Multiple prepared records and an issued uninstalled bootstrap remain permitted.
6. **Scope of terminal inputs:** ENV initializes weak revocation and terminal predicate fields; helper 180–182 checks them. A does not implement attempt transitions, terminal ingress enforcement or child outcome truth. Those remain C/B obligations, not missing A functionality or an A closure claim.

## Assertions and evidence limits

Writer tests use real compiled ENV and genuine prepared records with authored INITIAL/COMPLETED parser inputs. Role owners only establish component identity. The eight kind/manual/bootstrap combinations, nested Tensor/accessor-copy checks, multiple preparations, forbidden-path sentinels, 30 receiving-field changes, eight manual state changes, copied/foreign/replaced payload checks, scope/process/thread/operation refusals and weak-key lifetime check target the declared A contract. These tests do not establish real native-owner save/load or learner continuation. I did not execute them.

Additional finite independent assertions proposed to root: issuance-time owner/runtime/authority pins must still reject after scope reacquisition; recorded terminal/revoked inputs reject without consuming unrelated records; nested opaque preparation references must release when their outer prepared record dies. These are focused evidence additions, not discovered implementation defects. Probe writing awaits root's source-freeze release.

## Independent probe handoff

Root released the source freeze after R156 custody verification. Authored `tests/test_townlet/regressions/bac/test_prepared_world_currentness_independent.py`, 87 lines, SHA256 `5f26fc72e217040d80caa7d2fc9c5e95f447d909c37db115ab472775608b8e92`. It reuses the already-reviewed component fixture and adds nine cases: five seal-time binding replacement cases after scope reacquisition, two authority-internal identity cases, exact revocation/global terminal input refusal, and nested opaque preparation weak lifetime. The source inventory is now five whole bodies / 4159 lines. No implementation source change or execution by reviewer. Root owns collection, execution and any formatting/candidate recapture.

Root reports R156 A selection 52 passed; affected owner selection 279 passed / 20 failed / 7 skipped. The 20 reported failures occur in the bound-component reward service retry fixture at unrelated same-thread RNG admission reentry. I have not opened that sixth body or independently revalidated baseline attribution. These failures remain unresolved owner-gate evidence, not waived by the A source review and not converted to passes. B/C and package acceptance remain open.

## Current disposition after corrected independent execution

Root reports R159 candidate `b2aa0e47fc230dd314a0ff1b3216000d55f45b83`, positive selection **12 passed in 23.19s**, exact source/process custody **PASS**. This selection comprises **nine independent packet-A probes and three separate POP initial regression nodes**; the twelve are not all A cases. The corrected independent probe is 91 lines, SHA256 `40633f471d55e087b2596d4460c9cda712968895b9d95184674a5450126b24a7`. Its production A dependencies remain byte-identical to the r156 hashes above. The final measured reviewer inventory is five bodies / 4163 lines.

Root's named execution evidence is `Q/wave35-r159-restore-positive-attempt-1/{restore-positive.log,restore-positive-result.json,restore-positive-custody.json}`. Execution and custody results here are explicitly root-supplied; this reviewer performed no runtime/import/test execution. Together with the separately reported R156 writer selection **52 passed in 13.11s**, the nine independently authored R159 cases support the bounded A currentness/seal assertions. These selections are stated separately, not summed into package acceptance.

Historical attempts remain failures/unrun as recorded. R157 failed static checking before collection/runtime and remains UNRUN. Root's Black/import cleanup re-exported `compiled as compiled` without changing assertions. R158 then produced **eight independent passes and one failure**: this reviewer's final exact-membership assertion compared a WeakSet directly with an ordinary set. The rejection and healthy-continuation checks before it passed; Python WeakSet cross-type equality made that final assertion invalid. I corrected only that assertion to `set(env._world_restore_revoked) == {first}`, preserving the requirement for precisely one revoked record and no extras. R159 supplies the passing execution of those corrected bytes; it does not rewrite R158 as passing.

The R156 affected owner selection's **20 failures** also remain preserved historically. Root reports the separately owned current-custody fixture repair passed its R158 owner selection: **133 passed / seven skipped in 36.77s**, custody PASS. Those seven are explicit required poison-child cases, not CUDA skips. The repair and owner-body implementation are outside this reviewer's five-body inventory and are attributed to root/their separate owner, not independently source-approved here.

**Current disposition: packet A source and its bounded currentness behavior approved; no P1/P2 finding.** This approval covers the exact original A production bytes and corrected independent probe above. It does not approve unseen B/C source, certify actual child publication or attempt transitions, waive required poison-child evidence, establish real native-owner continued learning, or close PW04/package acceptance. Future C changes to ENV/helper currentness or ingress require fresh review of the actual integrated candidate.

## Type-only helper follow-up before R160

Re-read the existing helper body after root's static repair. Current `src/townlet/environment/parent_custody.py` is 421 lines, SHA256 `03f96c2d935e8e7342387ad78b4f4db3aadb331b52d7e77e2052128f4d602014`. The change imports `TYPE_CHECKING`, places the `VectorizedHamletEnv` import inside that guard, and annotates the `_seal_prepared_restore` local as `env: VectorizedHamletEnv = self.owner`. The type-only import does not execute a circular ENV import; the function-local annotation does not add runtime validation or evaluate the annotation. The issuance, scope authentication, pure predicate, refusal and lifetime behavior reviewed above remain unchanged. **Bounded source approval extends to these helper bytes; no new finding.**

No new body was opened and no code/test/probe was written or run. The cumulative current inventory is five bodies / 4166 lines. R156/R159 results retain their original byte identities; they are not relabeled as execution of this new helper hash. Root's planned R160 rerun remains pending at this addendum. Root's global mypy/defaults progress and runner edits are outside this bounded source review. All B/C/native/package limitations remain in force.

## Final R160 packet-A disposition

Root reports candidate `39f5b5c3ca7688b29ccc1fbe501b826ebae4f2ee`: **61 packet-A cases passed in 15.37s**, comprising 52 focused cases and nine independent probes, with source/process custody PASS across four processes. This execution binds the type-only helper SHA256 `03f96c2d935e8e7342387ad78b4f4db3aadb331b52d7e77e2052128f4d602014` and independent probe SHA256 `40633f471d55e087b2596d4460c9cda712968895b9d95184674a5450126b24a7`. Named root evidence: `Q/wave35-r160-env-currentness-attempt-1/{env-currentness.log,env-currentness-result.json,env-currentness-custody.json}`. The separate three POP regressions passed in 6.90s with custody PASS for one process; they are not added to the A count.

**Final bounded packet-A source and runtime approval: no P1/P2 finding.** Runtime results are root-executed and root-supplied. Earlier failed/unrun attempts remain preserved above; repeated selections are not aggregated. No B/C, actual native-owner continuation, PW04 or package closure is claimed. Future integrated C changes require fresh review. This report is now frozen for root's WIP26 evidence sealing; no further reviewer prose writes are planned.
