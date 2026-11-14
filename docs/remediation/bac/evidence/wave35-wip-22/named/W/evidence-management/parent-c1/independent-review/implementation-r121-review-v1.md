# APP-C1 R121 independent source and evidence review

2026-11-14. Reviewer `/root/bac_astra_parent_c1_contract_review`. **The bounded implementation has no remaining identified P1/P2 behavioral defect; full APP-C1 acceptance is NOT READY.** Required owner regression acceptance (proposal item8) fails, and R121 has a new no-defaults ratchet failure. Neither is waived by the passing C1 cases. This report does not close the packet, qualify broader POP/ENV/runner integration, or certify hardware.

## Exact scope and custody

Approved design remains P/T18e-R0-PARENT-INTEGRATION-PROPOSAL-V2.md SHA256 `45801f6d05a751b4fa7458278f2c781290c094eafa267a65479efb34d9c427c6`, with independent contract review `a8cb7f8d403740f1b938f31734cdf54698779b75911eca4ca95c497290fe760e`. R121 candidate manifest is W/wave35/r121-candidate.json SHA256 `9fe86fd0968fd5059590e3ef88ed4069575e3232f1677e2cf1e3810e11dc1305`, tree `b429489ce4f6226b03e8f1a4971bd49861f9f2d5`, base `2f579092eae2b67eb3efd514aa7b61c909efa9f1`. Handoff implementation-v3-handoff.md SHA256 `ccd6f7869430d1df97dae49527dcc526d775ae35b41a81e2edc9f3614826b1ef`.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 1313 | 50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9 |
| src/townlet/exploration/scoped_curiosity.py | 1443 | 55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4 |
| src/townlet/exploration/parent_custody.py | 236 | 5b592ac955d8e45b3369d4dac3a1bc2996093dfaa8427d732183d321aada801a |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 854 | ca3b0fd10c1fb49e508237901054dd655c9df34fea3745592c216e6c4d5ad5bc |
| E/parent-c1/independent-review/test_scope_expiration_race.py | 64 | 774219868be84b1f9d07f66a9edb9d677d97883cd8d7071f8f162fdeef188c87 |

Four APP bodies3846 plus one explicitly authorized independent probe64 = **3910 lines/five bodies** for this reviewer. No diagnostic, core, native, CP, ENV, POP, fixture, launcher or verifier implementation body was added. Supplier capsules and evidence metadata remain attributed; failure exception/frame summaries were read as evidence, not used to claim whole-owner source review. Writer's separately charged diagnostic112 is not part of this reviewer's source custody.

No APP edit, Git write, branch/worktree/checkout, source execution copy or hardware action by reviewer. Root-authorized independent execution was restricted to the frozen two-node probe through the exact locked launcher and verifier. Other tests are root-executed evidence independently inspected as metadata and against reviewed C1 assertions. Source/probe hashes were checked before/after independent execution and unchanged.

## Behavioral review of the complete finite contract

This reassessment covers the full finite mechanism, not only earlier fixes. Domain admission precedes runtime and BANK locks for ordinary and retained routes. Public scope binding authenticates an actual RNGOperation through domain admission, never ambient/private active state. Retention is separate from runtime `_operation_active` and BANK `_entered`; those guards remain active during their actual methods. Wrong-thread/PID/forged/expired scope use refuses before owner-lock waiting, while ordinary foreign-thread work does not inherit scope authority.

The runtime-owned BANK guard is delegated-only. A private single-use intended-method/current-call permit is consumed before public BANK body/admission/callbacks; callback peers cannot borrow a scope-wide binding. The internal public-call identity survives standalone preparation's operation-idle registration gap, while nested public calls refuse. Genuine direct BANK controllers remain supported outside runtime delegation. Harmless epsilon remains observational and grants no forwarding authority. Existing view/revision/receipt/phase checks are preserved.

BANK's own fresh invocation uses its exact existing `_devices` tuple. Its entered invocation exits and its sealed outcome is consumed while BANK exclusion remains held. True sets slot-backed monotonic `_completion_uncertain` without CUDA, callbacks or newly acquired locks; False cannot heal existing body/publication failures. `_entered` and `_lineage` are also outside `__dict__`, so prepared dictionary installation cannot resurrect execution authority or reset the completion latch. Scope/permit records remain nonrestored issuer state, active scopes pin actual owners, and expiry clears their strong execution references.

Runtime/BANK retained locks outlive child return, parent completion and the owning consumer cut. Native own completion remains actual, not deferred. Copied ordinary reward and public stamp properties do not create an inferred live-native-storage exposure; no blanket native quarantine is added. Exact BANK declared inventory is preserved, without falsely claiming complete foreign-source/rejected-prefix inventory or a CUDA hardware pass.

Standalone restore/private initialization/install remain implemented, including real idle cohort registration and original currency/correlation checks. Active-bound cohort routes refuse before parsing/copies/callbacks/registration pending the explicit later packet. Final runtime installation now uses the same authorized `_forward_bank` seam directly and then only its prepared assignments; ordinary postpublication invalidation has been removed. No compatibility fallback, forged authority, automatic recovery or scope removal was introduced.

The two earlier P2s are resolved: foreign lookup can tolerate a scope expiring before registry access without KeyError; final installation no longer performs ordinary revision invalidation after BANK publication. Intended RED records are preserved at root; durable controls and independently authored race controls now pass. Prior static-v1.md remains historical, not silently rewritten.

## R121 test corrections and owner lifetime

The original R120 ordinary run was58 PASS/4 FAIL, not complete acceptance. Two failed assertions expected RuntimeError where public admission correctly raises ValueError for forged/expired lineage. R121 preserves that real refusal and additionally proves failed binding grants no authority before a subsequent genuine binding. Scope/PID/reentry RuntimeError assertions remain precise.

The CUDA sentinel failure occurred during monkeypatch installation's `__class__` introspection. R121 installs it through the module dictionary while retaining the all-attribute trap during the actual CPU scope/refusal/operation test. This fixes setup without relaxing the tested CUDA-laziness requirement.

Root's sealed diagnostics establish that the original full POP fixture remains alive even without C1 retention, with both C1 registries empty; the observed make_parent return-frame reference does not establish its external root cause. R121 therefore constructs an additional real isolated runtime/BANK using the real ENV validator, WorldReceiptIssuer and actual parent callbacks, with no reverse POP ownership of that new runtime. Baseline collection, live retained pin and post-expiry collection with the expired handle retained are all asserted. This supplies the C1 lifetime control without pretending to resolve the separate full-fixture frame-retention question or weakening collection assertions. No diagnostic body was read here.

## Executed evidence and independent checks

- Root R121: all **67 C1 cases pass**:62 ordinary cases within the combined481-node owner run, plus five separately launched one-node poison roles, each1 PASS/0 SKIP. The four targeted repaired-test passes overlap these cases and are not additional coverage counts. Collection486 is not a runtime result.
- Reviewer R121: exact independent probe **2 PASS/0 SKIP**, launcher/verifier exit0, source/index/import/thread/fixture custody PASS (821 source guards,573 config digests,13 protected artifacts,1 process identity). This is separate causal evidence, not a replacement for the owner regression gate.
- Root's five poison roles were independently checked against actual recorded child PID/PPID, launcher identity/start ordering, one-node argv, role gate, source/manifest hashes, actual loaded Torch origin/version, measured intra/inter-op1/5 and anomalyFalse. Exact own/parent receipt values, exception identity/aggregation assertions and expected BANK/native/parent phase sequences match the reviewed source. Each role has a distinct child and launcher. Specs have scheduler capacity2 but exactly one job and no xdist; actual process evidence is one process per role. An initial overstrict metadata assertion expecting capacity1 was corrected explicitly in the record; no poison execution was repeated by reviewer.

Independent R121 evidence under E/parent-c1/independent-review:

| Artifact | SHA256 |
| --- | --- |
| r121-independent-outer.json | c98ec5f5ffbd3eee41a5f67b5c52df5ade127e22d8fe2b3dc5c67e4f0c8bdfd3 |
| r121-poison-metadata-check-v1.json | a401f5032e7095db9c846e0f13d078f203c89da487d4c224e0369aa3e6c3563f |
| Q/wave35-r121-c1-independent-expiration-attempt-1/c1-independent-expiration-result.json | 9bdf54474d9802b495e078eb624f642f94ee4c82524b6185eb45ecc8258ddc63 |
| Q/wave35-r121-c1-independent-expiration-attempt-1/c1-independent-expiration-custody.json | 75727b0e2c803b383264e88b2d35a6b75dd5e0cf78ffd491429e3fb4357a75e4 |
| Q/wave35-r121-c1-independent-expiration-attempt-1/c1-independent-expiration.log | d7affd5acc6e708af6fbe9ac6edfb39a6e331e855203802b3f938b18200c8567 |

Actual outer observation interval08:00:42.978810–08:00:51.878916 UTC, launcher PID196317, verifier PID196423; exact argv and before/after hashes are retained. Both stderr files are empty. These actual outer observations supplement the older inner harness's limited identity/timestamp schema; no unobserved pytest PID is invented for the independent probe.

## Blocking gates: full acceptance remains owed

**Required owner regressions fail:** combined run481 selected, **266 PASS/215 FAIL**, zero skips. Its failure index SHA256 `98759129f50eae5a60158ab4dc4d599542f1d958209a0f487229d73247bea38d` and negative custody SHA256 `8cfb916742b1defc1660df4d2e156ab0062cd2909080a17e141c8bd58aed38e7` preserve the failed gate. Failures affect four existing owner files, not the new C1 test file. The62 C1 ordinary passes are included in266 and must not be added to it.

| Observed failure family | Unique cases | Source-qualified implication |
| --- | ---: | --- |
| ENV.step missing required vector_step | 59 | Existing caller/fixture does not earn current ENV/POP step authority; repair genuine caller protocol, not a compatibility default. |
| SharedWorldBackend treated as raw provider (checkpoint_state37, encoder35, predictor_network17, rnd15, validate_state7) | 111 | Current supplied managed-owner interface requires its real call/snapshot/prepare APIs; wrapper is not the native provider. |
| OwnedWorldBackend.call missing required lineage | 22 | Current native supplier requires explicit authentic lineage or standalone None. |
| Other missing replay lineage | 6 | Current replay contract requires the producer's admitted caller protocol. |
| Quarantine cleanup note | 17 | All17 worker records also show the original missing-lineage TypeError at POP `_learn`800; unsupported quarantine reason is secondary and also requires caller cleanup reconciliation. |

These signatures agree with unchanged source-qualified ENV/native/replay interfaces and previously identified pending POP migration. That establishes finite caller/contract gaps, not execution of their intended later assertions, not a blanket statement that every owner behavior is correct, and not an exemption from proposal acceptance item8. Bounded owner/caller reconciliation must reach and execute the original continuation, archive, restore, shared/private and lifecycle assertions. Do not relabel these required failures optional or erase modes to make the first slice green. Later C2/POP work remains required in its own bounded packets.

**Required static gate fails:** R121 global Ruff and scoped four-file Black pass; mypy retains15 oracle/POP diagnostics (root classification; no C1-file diagnostic reported). The no-defaults ratchet fails601>600 due to the newly introduced conditional expression at helper201 (`record = None if scope is None else _record(scope)`). Static summary SHA256 `036c6a87ff10a80216e753a1e92c7cbadcbe6b115f7f9e9c8e4e7762e72b51c0`; no-default log SHA256 `71e27611b77daf66e54145576854e8ca771e4bd5d2f9940d422ce941f6acb7df`. This is a mandatory new gate failure, despite the whitelist; the ceiling must not be raised. Root's proposed explicit if/else with identical branch evaluation is semantically adequate. Exact repaired source and fresh limited gate verification remain owed under R122; this report does not preapprove unobserved bytes.

## Disposition

The approved design and bounded four-body implementation remain coherent, with the two independently found behavioral defects repaired and the new67-case component suite plus independent race evidence green at exact R121 bytes. No further material behavioral finding is identified within this source boundary. **Full C1 acceptance stays open** until the new static ratchet regression is corrected and required owner/caller regression coverage is reconciled and qualified. Existing mypy, dependent ENV/POP/cohort/recurrent/runner, outer-owner and hardware obligations remain explicit. No package/programme release, merge, or hardware approval follows from this review.
