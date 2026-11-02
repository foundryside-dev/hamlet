# T19 R4 independent core runtime

**PASS: all24 owned cases, no failures/errors/skips.** Independently executed after root's explicit one-CPU runtime clearance against candidate tree4bf7dab98a9baa1140380e13d8230ddcb445076a/basebc47e44662f7bea953156a668610a20e6bced9f2. Normal pytest and wrapper closure observed; this conclusion is based on the actual pytest log/result and both process identities, not outer exit alone.

Exact authorized outer command, cwd /workspace/hamlet:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave12-r4-independent-main-spec.json
```

Actual subprocess command:

```text
/workspace/hamlet/.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_outcome_clocks.py --no-cov -p no:cacheprovider -p bac_source_identity -q -n 1 --dist worksteal --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave12-r4-independent-main
```

Actual collection:1 worker [24 items]. Pytest:24 passed,2 warnings in135.38s. Actual job exit0; wrapper exit0; job wall147.667254447937s. Warnings originate from the two deliberate optimizer-step spies installed after scheduler construction in the schedule witnesses; those tests independently assert actual optimizer/target/LR counts and values. Benchmark disabling under xdist is also disclosed in the log, not a missing T19 benchmark requirement.

Artifacts under /workspace/bac-review-2026-11-01/qualification/wave12-r4-independent-main:

- independent-main.log, SHA2567cb95673ba55b651bdb412db4b53ecb5e5dbefd4e46029caa4db7407173cc32e
- independent-main-result.json
- independent-main/identity-controller.json
- independent-main/identity-gw0.json

Both controller and gw0 independently recorded basebc47e44662f7bea953156a668610a20e6bced9f2, candidate4bf7dab98a9baa1140380e13d8230ddcb445076a, import /workspace/hamlet/src/townlet/__init__.py, torch2.11.0+cu130 and threads1. Result binds manifest SHA256ba430b5e0c12dcc31b082250b94d2384ad804c12244fe900e6519f25cdf7c03e and harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. Wrapper/plugin implementation was not opened as extra source.

Post-run five-file hashes independently checked and match the reviewed R4 source:

| File | SHA256 |
| --- | --- |
| POP |629efddfd259aa5bc39f8c4c119b506f1c1eeb17b338c564751dc0ddc820cd92|
| EP |5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9|
| CL |117caf9f2dfcc486d71284e6d9206f351eef690b6acf425f841beb3b3ba52571|
| RC |3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| owned test |66069b051f1165ee50a15cc106aac0919f3447f9ef0ed1395aeaaa70e5dc21e9|

## Actual proved outcomes

- Real2/5 authored lanes in both orders/two measured resets retain7 eligible transitions/5 vector ticks/2 lane events and frozen scalar/reward/entropy snapshots. Batch commitment increments once and reordered replay adds none.
- All four cap/budget/shutdown/checkpoint cuts retain actual nonterminal successors/masks and explicit reason; repeated flush does not duplicate completion.
- Six mutation cases verify separate public tensor readings and publication-time authority for observations/meters/scalars before and after first commit. Changed content refuses without counter mutation; original content remains committable.
- Two delayed/partial cases verify accepted reset, retained original events, lane reversal, later valid commitment and reordered replay, changed old-event refusal and no adaptive replay. Subsequent batch commits independently.
- Actual compiled legal WAIT-only width1 world executes physics and publishes finite exact-zero entropy. NaN/+inf/-inf Q variants refuse before physics with clocks/episode counts unchanged.
- Actual unconfigured POP service observes short-tail0 updates followed by real predictor updates and parameter changes, retaining the single-minibatch route and authoritative before/after counter deltas. Direct legacy one-minibatch control passes.
- Both configured overflow variants exercise actual predictor receipts, mandatory overflow or explicit drops,7 admissions, vector ticks6–10, Q attempts6/8/10 versus successful8/10, target10 and two LR advances to initial*0.25. Adaptive completions remain[2,5] despite duplicate commits.
- Binding negatives, duplicate begin, ordinary DTO-only reset and historical ledger-accessor diagnostic pass; held immutable clock readings remain unchanged.

The previous static disposition is supported by this independent runtime: all three material findings addressed, no unresolved in-scope P1/P2/gap found. This24-case execution is scoped package evidence, not repository-green or a replacement for root's mandatory full gate. Separate producer evidence remains its owner's review/runtime; root owns remaining consumer/full gate, final evidence, commit/push and requested halt.

No production/test/tracked-document/index/branch/worktree/source-copy/deletion/subdelegation action. Only this new ignored report written; all14 worktrees preserved. Runtime closed normally; stationary, no next packet.
