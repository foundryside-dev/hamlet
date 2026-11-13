# R81 publication snippets — source-verified prose only

2026-11-13. Prepared for root integration and independent documentation review; tracked STATUS/README, source, index and Git were not changed. Scope derives from the retained five-body R81 review and these exact artifacts:

- Current API: `T18e-R0-REPLAY-FIX-A-CURRENT-API.md`, SHA256 `1c983b02f3fdd610857fc40b95eb454b5b3f701d02b869e35ea3d57e4befd63f`.
- Component receipt: `../wave35/r81-replay-fix-a-component-receipt.json`, SHA256 `71abc4a628b8a698cdb878fb71857d207ecf50fbdde3c84e90ba4ddc44564cc4` (read and hash checked).
- Independent source review: `T18e-R0-REPLAY-FIX-A-PRODUCTION3-REVIEW.md`, SHA256 `49741e76e1f77fc71ff7a176945b170eb17660a496fbd2d37613f96011b47178`.

Remote WIP14/CI state below is supplied by root. No new publication or CI result is inferred.

## A. Proposed top section for docs/remediation/bac/STATUS.md

### R81 replay repair A qualified; WIP15 publication pending

Replay repair A now revalidates owned flat/PER mutable validation DTOs against the current destination before issuing authority. Shared prepared handles contain only identity; revision, token and material stay with the issuer. Typed guards preserve required lineage and expose `PreparedReplay` results. Independent SPEC/QUALITY approval covers this finite CPU slice.

At candidate `4bcb26ec56bc2664949baab7d6b14e3c1da76b01`, root passed 53 ordinary cases plus 1 isolated poison case. Independent execution passed the same 54 controls; repeated runs are not 108 unique cases. Source/process and actual-child custody were verified. R81 global Ruff, owned Black, owned-four mypy and all-three public prepared-result assertions pass. Defaults remains 601 against 600. R79 global mypy's 15 errors (6 oracle/9 POP) and recurrent Black failures remain prior source-bound evidence, not R81 reruns.

Required work remains: recurrent mutable-DTO assessment under original B1, real scratch-stream classification/state proof, recurrent publication controls and default/style fixes; additive CUDA capability/lifecycle design and hardware qualification; caller/native integration; broader suites and final fresh reviews. These gates remain open; accounting stays 28 qualified, 38 remaining, 66 total.

WIP14 remote `678513c7` is verified. Its CI has Config PASS, Lint FAIL with 6 oracle errors, and Tests FAIL with cause still unknown. WIP15 publication is pending; no WIP15 commit or CI result is claimed.

## B. Proposed README BAC paragraph

BAC remediation remains in progress: 28 qualified, 38 remaining, 66 total. R81 replay repair A fixes flat/PER mutable-DTO authority, shared prepared-handle ownership and typed lineage/results. Root passed 53 ordinary cases plus 1 isolated poison case; independent execution passed the same 54 controls. Approval is limited to that CPU slice. Recurrent, CUDA, caller and global acceptance gates remain open; WIP15 publication is pending. See [BAC remediation status](docs/remediation/bac/STATUS.md) for exact evidence, retained WIP14 CI failures and required follow-up.
