# P0 amendment freeze v4 — independent implementation review

2026-11-14T06:21:28.204929+00:00. **PASS for the root-approved finite P0 amendment**, exact hashes below. No remaining concrete P1/P2 SPEC or QUALITY finding in this bounded implementation review. Root adoption and separately reviewed consumer integration remain required.

The freeze-v3 finding is resolved. `_layout` now requires exact output_root/attempt_id/job.id and scratch_root/attempt_id/job.id for both spec and admission-request; arbitrary descendants and wrong IDs refuse. Interface-contract-v4 publishes this same equality. Existing exclusive creation and namespace race enforcement remain P2 responsibilities. The previous review, failing results, original source snapshots and all earlier failures remain intact.

Fresh independent verification against frozen v4:

- Author's complete synthetic file: **131 passed**, exit 0, `author-suite-v5.json/.log`.
- Unchanged independent adversarial file: **48 passed**, exit 0, `independent-suite-v6.json/.log`. Includes all four previously failing layout mutations, earlier reference/state regressions and new timeout/proof/resource/evidence/disposition probes. Do not sum these overlapping selections into application coverage.

Exact argv, cwd, explicit environment, UTC start/end, exits and matching source-before/source-after hashes are in each execution JSON. Test artifacts were exclusively created under separate paths. Source, schema and interface references from freeze-v4 were independently hash/length verified. No application import, real hardware call, server action, Git operation or extra tool body was introduced. The same three-body packet totals 1363 lines; author pair 1,131/1,400 and independent probe below 500 lines.

Reviewed source identities:

- `/workspace/bac-review-2026-11-01/qualification/bac_hardware_protocol_v1.py`: 520 lines; SHA-256 `adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c`.
- `/workspace/bac-review-2026-11-01/qualification/test_bac_hardware_protocol_v1.py`: 611 lines; SHA-256 `f602359decd4a73626a737f186501f2f2e6e2a8d81f3cfdd354b4749f98f0899`.
- `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-protocol-p0/independent-review/test_independent_p0.py`: 232 lines; SHA-256 `f60c019231ef2ecf7f1a2298b97c81198e4771df5ec8a213cf5b378f411ee4a5`.

The accepted amendment is preserved: required finite timeout/grace without defaults; pinned per-instance peak CPU justification and replacement accounting; top-N CPU/RAM versus cumulative retained scratch/inodes; closed shared-lease/layout fields; child job-evidence without impossible terminal/log claims; completed-unverified for ordinary zero exit with missing proof; and actual P2 orchestration-controller source witnesses distinct from P3 job-controller custody. CPU peak settings are not inferred from inter-op width. Actual CPU-bound acceptance, root allocation/grant authority, probe reconciliation, stable leases and causal observations remain mandatory P1/P2 consumer work under their sealed private contracts.

This PASS certifies neither actual discovery backend implementation nor CUDA/child/fork/phase behavior. Structural reference validation never replaces authenticated case validators; absent validators remain unsatisfied/unrun. Source-freeze no-writer custody and root authorization are external prerequisites, not consequences of matching hashes. Actual hardware remains UNRUN.

Evidence identities (execution artifacts under independent-review; freeze/interface/schema under its parent):

- `author-suite-v5.json`: SHA-256 `435c05223f11076fc412535ab8ea4ce4a5fd34b864749bce6965e2535c2e38ca`.
- `author-suite-v5.log`: SHA-256 `73a7e99f2e467c331f26875b0340bf56e6d1b84d6c7772e1a6b082fc58b0cd9d`.
- `independent-suite-v6.json`: SHA-256 `e463c77a26009c35da955a05ab948164bde7703b6d86b163f7e39fcc317260ab`.
- `independent-suite-v6.log`: SHA-256 `67f3b2b7900905d0c1841e10fb4b57641a076975b7bdf815421056bec34c13d6`.
- `freeze-v4.json`: SHA-256 `a70793847584bafd5ef8a3ddbf71a844b92e828b850b944a4ed7a198b2c743b8`.
- `interface-contract-v4.json`: SHA-256 `0a0b4de21d8f9f168785f6b2483c7c1ad5e1ec79ec27fe56ec56838833b421b5`.
- `schema-inventory-v2.json`: SHA-256 `d6882e7ab20c788299a9c29584920bdd8a76bd503c1a4ed12a0bff48f248e63d`.
