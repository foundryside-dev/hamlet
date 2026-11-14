# WIP28 independent terminal evidence review

Disposition: **APPROVE BOUNDED PUBLICATION** of the already-in-flight paused durability checkpoint only. No new qualification or package acceptance is authorized.

Reviewer: /root/pw04_native_replay_astra_review; producer: /root/bac_wip28_evidence_preparation. Separate delegated evidence reviewer; did not produce qualification artifacts, execution commands, document postimages or publication. Previously authored bounded NR2 source reviews, expressly not substituted for this independent terminal evidence assessment. Only this review pair is authored in the present durability task.

Terminal candidate: `7333be02ae881c800884c52bb2bec71053fcae4c`; base `af212f0b06041ee98ddf89c502e3c772c286c658`.

- contract: `wave35/WIP28-CHECKPOINT-CONTRACT-v1.json`, SHA256 `226d8a186e51842a3013bb59c5c5d437cbd17fa0a55790df478cf446b935e110`, 10360 bytes.
- reviewed_subject: `wave35/WIP28-QUALIFICATION-SUBJECT-v1.json`, SHA256 `c89a51d98d09cc126a3720a3a8b872559c10056f1a0a3a2f76c571cdff230d69`, 595265 bytes.
- pre_review_receipt: `wave35/WIP28-PRE-REVIEW-RECEIPT-v1.json`, SHA256 `e5668ad3d54864d0bcc3effe6b7d0d8c6ae47fd9f86185c221e6e3a8d5079e57`, 595482 bytes.

EVIDENCE-PROCESS.md guidance was read earlier in this review session and applied. Read-only JSON/hash/inventory inspection is evidence checking, not application execution.

Frozen contract, qualification subject and pre-review receipt match the supplied hashes. Every shared subject field except descriptive status equals the receipt. Contract required components equal receipt component receipts.

Independently checked 257 unique explicit rooted references in frozen inputs, all sizes and hashes matching; additionally checked 84 catalog/component/preexecution reference occurrences, all matching. Exact Q R169–R175 top-level membership and every declared attempt descendant file/directory match.

47 semantic attempts retain 21 PASSED, 12 FAILED and 14 UNRUN. Every UNRUN has a reason and null execution facts. R169 failed capture/missing-manifest launcher, R173 failed capture and R172 verification-only view remain retained; no later manifest substitutes for nonexistent execution.

R175 raw result/log/custody and controller/gw0/gw1 witnesses support 19 PASS on tree7333be02ae881c800884c52bb2bec71053fcae4c, wall64.0804913059983 seconds (pytest56.17), two workers, source/config/protected guards843/573/13. This is the only qualifying terminal-source runtime.

R174 raw result/log/custody and witnesses separately support 540 PASS with four workers, wall151.92298274699715 seconds (pytest146.64), plus isolated poison1 PASS with zero workers, wall30.518681432993617 seconds (pytest13.97), on tree80b518716d7b49a4e0dde6bb40273ea8ea698cc0. These required components retain their own source and are not summed or relabelled terminal-source tests.

Named runtime result records agree with candidate manifest hashes, trees, base and wall durations. Actual witnesses use /workspace/hamlet/src/townlet/__init__.py and threads1. Original witnesses lack literal attempt IDs/PIDs and job UTC; those disclosed limitations remain, with outer timestamps separately attributed.

Raw R175 static logs retain Ruff PASS and Black PASS (747 unchanged), mypy6 errors in oracle/driver.py FAIL, and defaults601 against600 FAIL. The incorrect PER.get causal guess is explicitly corrected in paused handoff and status documents.

Four exact document postimages are hash-bound. STATUS/EVIDENCE-INDEX distinguish terminal19 from earlier540/poison1, retain causal failures and unchanged28/38/66 accounting. CURRENT RNG contract and paused handoff preserve CPU-only limits, open PW04/package gates and the explicit pause until John resumes.

This is an independent evidence review, not reuse of the reviewers prior NR2 source disposition as terminal approval. No additional implementation body was inspected and no application runtime, tests, Git, branch/worktree operation or source edit was performed.

No blocking evidence finding identified. Final sealed receipt must preserve every frozen subject field and contract binding, adding this immutable review and seal metadata only. Independent exact final-receipt comparison remains required before publication.

Required next:

- Complete only final receipt comparison and already-in-flight checkpoint durability; then remain paused until John explicitly resumes.
- On resume diagnose actual defaults601 delta without raising600 ceiling; oracle capability decision and six mypy errors remain open.
- PW04/full/default/coverage/slow/remaining mode-fault/fresh final review and hardware gates remain open; original package accounting28/38/66 unchanged.
- CUDA unqualified, CI lookup blocked; root owns exact eventual remote identity and CI verification, no merge authority inferred.
