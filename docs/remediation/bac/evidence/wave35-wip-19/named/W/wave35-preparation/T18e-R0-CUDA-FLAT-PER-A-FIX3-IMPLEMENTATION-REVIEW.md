# Packet A FIX3 implementation review — R100

**SPEC: CHANGES REQUIRED. QUALITY: CHANGES REQUIRED. Original normative I5: NOT ADDRESSED in full.** The structural traversal repairs the ordinary tested metadata prefixes and later-field boundaries, but two finite boundary classes remain. This is a source/test-stage verdict, not A/B acceptance or CUDA runtime qualification.

## Exact reviewed candidate

Root tree `0b17ef1e48a6efc6e52bc814812439d4035e5447`, manifest `59d925fcef3c60cff1da69b01edd297b968588fd15320a8c33807ffa7d64e4ca`. Combined R98→R100 diff `T18e-R0-CUDA-FLAT-PER-A-FIX3-R100.diff`, SHA-256 `b5585af90f485540fb082a9f22e6ba78ddbff11e213266360c1b6a6657050167`, checked directly. New FIX3 report sections read; supplied report seal `1e644587cf1da79759c3c180155177e7fd555de3c91cd55a85724c49d24e3c15`.

| Retained body | Lines | Personally checked SHA-256 |
|---|---:|---|
| replay_contract.py |799|`f4b4c02e35df0e72a57987a5768dc32e0462c582d440f219c476c6b1fa68f63e`|
| replay_buffer.py |817|`7521a532ef7eda914138efefdc23743a34abd95747bd6c67397fb6d7e3894ad3`|
| prioritized_replay_buffer.py |1311|`9206411c38990efccb0284d504222be162bf460448369fb8b3a1d1326728487e`|
| test_replay_cuda_producer.py |1945|`a03cf0833addc329b3e3347a2f04ff0113757a3311fd910aed915eb6102eb3b3`|

Total 4872 in four bodies, within the current grant/hard5000. No additional implementation body, helper/core/recurrent/parent read, application execution/import, delegation, source edit or Git action was used. The archive facts below are explicitly supplier-qualified.

## F1 — known schema refusal is conflated with possible continuation

Affected: shared `ReplayPrefix.opaque` lines66–70 and `_transport_inventory` lines265–274; flat key prefix562–567, PER966–971; archive key prefix92–96.

`opaque(key)` sets `unknown=True` for a Tensor key and stops traversal. `_transport_inventory` interprets that flag as possible successful validation: it adds the entire transport, and preparation adds installed archives and may select the replay destination. This loses the distinction between protected key diagnostics on a known schema failure and an unknown comparison that really might continue.

Concrete paired-family witness: supported current version and correct kind, the complete required key set plus one CUDA Tensor key on device2, with an unused CUDA observations value on device3 and selector4. The extra entry count already guarantees schema mismatch; no Tensor/string comparison prediction is needed. The actual key-set failure operates on keys and its diagnostic, never row values, installed archives or materialization. R100 instead inventories the whole input, and preparation selects4. The same issue applies to a seven-entry archive record (six expected keys plus a Tensor key): the constructor is unreachable, but the planner may scan record values and the surrounding transport.

Required correction: represent a protected diagnostic-only stop separately from genuinely possible continuation. Inventory all actual key/diagnostic sources and preserve original family order/error rendering; do not execute sorting/representation or Tensor predicates during planning. Do not suppress unknown-continuation coverage where the predicate actually can succeed. This is the approved R1/R5 boundary, not a new requirement to resolve arbitrary custom comparisons.

Regression obligation: paired flat/PER top-level and archive schema controls with key-source2, untouched value3, target4 and no prepared handles. Pure planning should retain only reached diagnostic/earlier-effect devices and no destination; authentic public execution later must show the original refusal and protected key work without value3/target4. An earlier archive-record effect must remain covered when a later record has malformed keys. B-dependent public observations remain staged.

## F2 — archive recorder models initial copies but not the subsequent semantic boundary

Affected: shared `ReplayPrefix.archive` lines87–97, consumed at flat598 and PER archive iteration. After exact keys, the planner appends only source_formats/original_state, returns None, and continues through later records and rows. The real path instead completes constructor semantics and ownership before proceeding.

Two consequences of that incomplete boundary require one coherent correction:

* **Unused continuation:** an exact-key record with ordinary wrong `reward_semantics` copies its source2 mappings and then deterministically refuses before later records or live rows. R100 continues planning. With otherwise valid nonempty CUDA3 rows, it inventories3; preparation can also select target4 and installed archives. Earlier source2 copies must stay covered, but later3/4 work is unreachable. Existing `semantics` controls use an empty transport with a non-null row; that later empty-row refusal prevents continuation independently and therefore does not expose this gap.
* **Omitted reachable operator operands:** reward_semantics, approval_reference and source_digest participate in real inequality/truth evaluation after the initial copies, but none is retained by `archive`. Supported nonplain operands can dispatch their comparison/truth hooks. The recorder must include those reached operands at the appropriate boundary rather than assume the initial two cloned fields are the complete effect inventory. Source reachability is established; this review does not claim an executed CUDA witness or that every ordinary Tensor-versus-string inequality launches a kernel.

Exact supplier: `T18e-R0-CUDA-ARCHIVE-SEMANTIC-FIELD-FACTS.md`, SHA-256 `8868f5a2a4a4fa591d68462d375bd38b7f3c37c302f29760638a2b5f9a0e019a`, with unchanged helper identity `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`. The constructor copies the two mappings, then checks reward semantics followed conditionally by approval, then validates cloned state, then checks count, then evaluates source digest against a computed digest. The digest calculation itself reads the already covered cloned Tensor contents. Tensor archived_row_count is rejected by an exact-type guard with a fixed diagnostic before comparison/repr; **do not add a false claim that that operand itself performs GPU work.** Earlier constructor effects still occur.

Required correction: carry that finite semantic/operator sequence through archive planning while retaining clone-before-refusal and actual short-circuit order. Known ordinary semantic refusal ends continuation after the copies. A reached opaque semantic/digest operator requires protected operand coverage and any genuinely possible later continuation; do not eagerly evaluate it, impose a new type policy, blanket-scan every field on an earlier schema refusal, or skip actual constructor copies.

Regression obligation: nonempty valid later rows on another device behind ordinary semantic refusal, plus a later-record variant; and a causal supported nonplain operator fixture whose genuine comparison/truth work is observable on its own device. Pair reward failure with an unused approval/digest operand to prove short-circuit exclusion. Keep the count fixed-diagnostic negative control distinct. No authority fabrication or policy bypass is authorized by these tests.

## What the refactor and tests establish

The single family validation traversal is a substantive structural improvement. Ordinary raw scalar/configuration and row metadata now use the real predicates; push order remains family-specific. Later row and optional-component metadata can stop destination/later-source inventory while retaining earlier action/reduction/clone sources. The approved flat-versus-PER retained-width distinction is preserved. Recorded entry guards and shared successor-mask behavior preserve original ordering; known-vocabulary plain allocation is retained as an earlier effect. No additional changed-body sampling-law or state-publication regression was established by this bounded source review.

Binding interpretation1 is substantially implemented for row/component continuations; F2 identifies the remaining archive continuation hole. Interpretation2 requires F1's diagnostic-only distinction and F2's opaque operator coverage. Interpretation3's initial Mapping/six-key/copy order is present but its full boundary is incomplete as described. Interpretation4's shared mask extraction preserves the original checks and duplicate later validation at source level; excluded recurrent bodies were not re-reviewed or qualified. Interpretation5's full DTO clone-source traversal, accepted Mapping traversal, initial diagnostic protection, issuer-held additive inventory and pre-admission reentry guard remain intact in the reviewed delta. F2 is a new narrowed archive-operand inventory issue and must not be masked by those prior dispositions.

The all-Tensor-CUDA2 raw positive correction is justified by actual validators: mixed row devices are rejected after cloning and cannot prove target4 reachability. Marking all actual raw Tensor fields consistently CUDA2 preserves data and reaches the possible materialization branch. Root ruling `r99-fix3-positive-fixture-ruling.json` was read. The two superseded R99 preparation-positive oracles remain historical evidence; their PASS is not acceptance. The corrected controls test metadata inventory, while actual public completion remains separately owed.

## Evidence and staged limits

Root check record `wave35/r100-root-checks.json` was read and its SHA-256 checked as `0c500bb9df422ff277344568b24dee525fcc1761a5d8aac6c9a77ca59cc85259`. It records393 collected IDs preserved,232 unique reachable PASS in disjoint10+129+69+24 selections, with zero skips/warnings; owned-four Ruff/Black and unchanged defaults600 PASS. Owned-three mypy still has the one missing B `device_invocation` error. These are root-run, custody-verified results, not reviewer execution.

The broad reachable matrix is meaningful evidence for its actual cases, but lacks the two boundary classes above. It does not justify original normative I5 closure. 161 focused nodes remain unrun, including56 new B-dependent public cases and ten producer children. B activation/outcomes, full final-source producer behavior/completion, child execution/verification, parent outer-failure ownership, hardware and programme gates remain explicit. Existing independent child-verifier qualification is unchanged. A finite repair and new frozen review are required before proceeding as though packet A source is accepted.
