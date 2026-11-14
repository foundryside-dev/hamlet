# APP-C1 R122 independent delta and evidence review

2026-11-14, `/root/bac_astra_parent_c1_contract_review`. **No new material behavioral finding; the static ratchet regression is corrected. Full C1 acceptance remains NOT READY because required owner regression item 8 retains 215 failures, and the 15 mypy errors remain required work.** This is the exact-byte addendum to the full R121 bounded review SHA256 `98ead82e9d849cd4bf43446ba82e68e69b21e95fb23c03c5f3d1e93a5dc2a308`, not a new architectural review or a waiver of its remaining gates.

## Exact delta and source

R122 candidate manifest SHA256 `6075b1b51c3d2de05a78691fe8646963ee4bbc4b0fa22d2839ec0af91856f80e`, tree `7d3be1eeda87015e939f1dd90275b05a1586676b`, base `2f579092eae2b67eb3efd514aa7b61c909efa9f1`.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 1313 | 50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9 |
| src/townlet/exploration/scoped_curiosity.py | 1443 | 55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4 |
| src/townlet/exploration/parent_custody.py | 239 | 1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f |
| tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py | 854 | ca3b0fd10c1fb49e508237901054dd655c9df34fea3745592c216e6c4d5ad5bc |

Exact diff against the preserved R121 helper is only `_forward_bank`'s conditional assignment rewritten as explicit if/else. It tests the same `scope is None` once and calls `_record(scope)` only on the same non-None branch. Authentication, permit cleanup, lock ordering and exception behavior are unchanged. All other three APP hashes are unchanged. Reviewer source charge is four APP bodies totaling 3849 lines plus the frozen 64-line independent probe = **3913 lines/five bodies**; no sixth source body, diagnostic or tool implementation was read.

Author static record SHA256 `79f1b35d7830b1fb7dd7e701bbc69774674e044f7cc6a432a9f35ad5efa8fa0f` and root fresh static summary SHA256 `02e559593c069799e9c6f66e23f034c87d6429af2d8f2fe39fbd787ca6d6476e` agree: global Ruff PASS, scoped Black PASS, no-defaults 600/600 PASS. Logs were hash-verified. Whitelist remains `d9d66f88fc96cc117a463fff54d8349c46bc85d8dd558b64ce9fbbdbe9b98802`; ratchet remains `ab8e9a58c47abe1aeff8ae620a0ed614ee77d507ef52799d4c103d69ff35d85c`. No ceiling increase or new waiver. Mypy still exits 1 with the identical log SHA256 `ddf552be65c290932dd238ab8ad1347557d29011bdb2cacb18561db4097a6c23` classified at root as 15 oracle/POP diagnostics; it is not a passing global type gate.

## Fresh R122 execution

Root's exact C1 ordinary selection is **62 PASS/0 SKIP**, source/index/import/thread/fixture custody PASS. Five additional poison roles each have **1 PASS/0 SKIP** in distinct fresh one-node processes. This is 67 C1 cases, not broader owner acceptance. Collection is not counted as runtime evidence; prior R121 passes and overlapping controls are not added.

Reviewer independently executed only the frozen 64-line race probe through the qualified locked harness and exact fresh R122 spec: **2 PASS/0 SKIP**, launcher and verifier exit 0, custody PASS with 821 source guards, 573 config digests, 13 protected artifacts and 1 process identity. Actual outer interval 08:11:45.321147–08:11:53.858603 UTC; launcher PID 198574, verifier PID 198649. Exact argv and hashes before/after execution are retained and unchanged. No APP/source edits or hardware execution occurred.

| Evidence | SHA256 |
| --- | --- |
| E/parent-c1/independent-review/r122-independent-outer.json | f7345681c18d19ef89cded316083b4882533de48c449f4dd1e148b7f1236b95e |
| Q/wave35-r122-c1-independent-expiration-attempt-1/c1-independent-expiration-result.json | 2683dd4b63ba0406b23ccb607b185209215f8a962c5942698c05a55d9c52cd69 |
| Q/wave35-r122-c1-independent-expiration-attempt-1/c1-independent-expiration-custody.json | 032c869b0eb1d4b9a9b89e706100b08e24ff839bf80d8e6b80d7d6522f46e75b |
| Q/wave35-r122-c1-independent-expiration-attempt-1/c1-independent-expiration.log | 9ba436d6c3a5ba88ac05f6b13f2cdcc3cf2d753ebeef99dbf0c85875e08c8162 |
| Q/wave35-r122-c1-preflight-attempt-1/c1-ordinary-result.json | faa18d50a9592267fcd83989701f9a38d5cd83ccc4eef0499405b1ba373fcee3 |
| Q/wave35-r122-c1-preflight-attempt-1/c1-ordinary-custody.json | 2eb4cf033352909b3f4bb3baccd2adbeca9cb5c4347d1b4767ea00fa029fd50e |
| E/parent-c1/independent-review/r122-poison-metadata-check-v1.json | 7a15ad6d69ab98583fe71759e869bf0b833de68176d152d9685639f70b4ef017 |

The five poison records were independently metadata-checked against reviewed test semantics: exact source/manifest/spec/output hashes, actual child PID/PPID to recorded launcher, start ordering, one-node argv, five distinct child/launcher identities, actual Torch origin/version, measured intra/inter-op threads 1/5 and anomaly False, and own BANK/parent receipt/error/phase assertions. Copied-reward child False/parent True includes two actual native completion phases; child True/parent False leaves BANK uncertainty; install completion cannot heal its slot-backed latch. These are CPU component controls, not CUDA qualification. Reviewer did not reexecute poison roles.

The root ordinary command retains `--basetemp=Q/scratch/wave35-r120-c1-ordinary-attempt-1` in its actual argv. Root reports the current directory empty and the C1 test source uses no tmp_path/tmpdir/tempfile. The earlier scratch contents were not inventoried, so this review makes no assertion that historical scratch bytes were absent or unchanged. Actual R122 logs, source/custody records and poison witnesses have separate preserved attempt paths; independent race execution used no such basetemp argument. This scratch-reuse limitation is retained explicitly, not hidden by the passing tests. Root's sealed observation is `E/parent-c1/r122-scratch-reuse-observation-v1.json`, SHA256 `3396235d218de8133b748e4f9b1a023a732b513829534f08b9830be570fccca3`.

## Required remaining gates and documentation

The R121 broad owner gate remains 215 FAIL/266 PASS of 481, preserved and not rerun without prerequisites. Its required caller/managed-provider/ENV-step/replay-lineage and secondary quarantine cleanup reconciliation remains as classified in the R121 review. The R122 cleanup changes none of those interfaces. Passing 67 C1 controls does not satisfy proposal item 8's required source-matched owner regression assertions, close full C1 acceptance, or make later C2/POP work optional. The 15 mypy errors, genuine outer-owner integration, active-parent cohorts, recurrent/runner work and hardware obligations remain open.

Source-verified 96-line draft saved for root publication review: `E/parent-c1/doc-draft/CURRENT-PARENT-CUSTODY-COMPONENT-CONTRACT-v2.md`, SHA256 `6ed8321853c31f9264f02bbea1b55d8f02bc085a1341adebfe874f4d1d2def12`. It documents actual public retained/binding APIs, domain/owner order, delegated forwarding, own completion versus parent, standalone restore/bound-cohort barrier, limits and exact source hashes. It also records the requested current quarantine supplier facts: runtime forwards reason unchanged; BANK authenticates first, accepts only empty_participation/runtime_failure, and valid notification sets local failure/revision while remaining distinct from a callback-free completion consumer. String correction alone is not qualified failure-path repair. The original CURRENT filename and a separate v1-preserved copy retain exact SHA256 `b9debb77ad27bb918f3bcc4a3923c015a68a74b3fafb0971105d4f5140b537eb` for the already-pinned POP plan. The original bytes were recovered from the preceding edit/read history, hash-verified before restoration, and preserved; v2 carries only the requested readability corrections.

**Disposition:** exact static delta and bounded component behavior are reviewed without a new material defect. Required no-defaults regression is resolved at R122. Full C1 acceptance and programme closure remain blocked by required owner reconciliation and existing global gates; no release/merge/hardware approval is granted.
