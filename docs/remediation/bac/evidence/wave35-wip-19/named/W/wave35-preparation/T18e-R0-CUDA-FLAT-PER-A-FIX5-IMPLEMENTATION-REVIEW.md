# Packet A FIX5 implementation review — R104

**SPEC: PASS for this bounded repair. QUALITY: PASS for this bounded repair. F1: ADDRESSED. F2: ADDRESSED within the adopted ordinary-metadata/opaque-protocol boundary. No material actionable source finding established.** This is source-stage disposition, not A/B acceptance, complete I5 runtime qualification, or programme acceptance. The required final other-model adversarial gate remains open.

## Candidate and scope

Reviewed frozen R104 tree `e206288d4f6eee330e3fcb8114a47af3002eecb1`, manifest `90534e49a82821c82df027828e1ed85037ed7d5cb98d723250584e75a9e5672a`, on existing branch `project-recovery-bac-2026-11-01`. Read repository AGENTS.md; no nested AGENTS.md was found under the admitted source/test/preparation directories. Read the FIX5 brief, FIX3 full F1/F2 definitions, FIX4 review, I5 matrix and binding interpretation review, relevant final author-report sections, and root R104 check record. Reviewed the complete R102→R104 shared/test diff and relevant source/test sections.

| Admitted implementation body | Lines | Personally verified SHA256 |
| --- | ---: | --- |
| src/townlet/training/replay_contract.py |842|`3fd73601d1ec9110a7ca03157d452827e0fc1d8249f0c3a86a18cad364c8b23c`|
| src/townlet/training/historical_checkpoint.py |675|`74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`|
| tests/test_townlet/regressions/bac/test_replay_cuda_producer.py |2204|`d178bb0a40340292e3b06328438ec2d825378d9464df8bf600873d3c7e2fce9b`|

Retained scope3721 lines in3 bodies. Flat/PER implementation bodies were not read; their unchanged family validation order and prefix call sites are supplied by the prior scoped review and binding matrix. No application execution/import, source/test edit, new checkout/worktree/branch, source copy, delegation or Git mutation occurred. Only this review report was written.

Personally verified diff `T18e-R0-CUDA-FLAT-PER-A-FIX5-R104.diff` SHA256 `269d2c9aba57214aa9c0121c9496e34b2b918eca26b43a4a4517830abbc80ab7`; final author report SHA256 `ac27c6965cf7f5c4e3d5be0196db01f9a6ea3eb40d39f6941812789032c67aad`; root check record SHA256 `f2f93e2193ecd2e837b67a5bec4438c692196cf7d31f3fd6f3d6585824f53717`. The author records retained preappend report snapshot `16ebe09b1ebd376bbbac82bc850744657e7da62d43be0f9cf9d65bd91c6911ce`; that snapshot was not independently rehashed in this review.

## F1: finite known schema refusal is separated from opaque continuation

At shared72–81, planning first retains all reached keys. With opaque keys present, unknown continuation now requires both equal cardinality and no ordinary unexpected key. Against the supplied all-string expected sets, membership of exact primitive values does not dispatch opaque key comparisons. Consequently both the original extra-entry class and FIX4's equal-cardinality ordinary-unexpected-plus-opaque class stop with key sources and earlier effects retained. `_transport_inventory`305–316 does not add the whole state, installed archives or selected destination for this definite stop.

Equal-cardinality opaque keys without an ordinary impossibility still receive possible continuation. The `_OpaqueSchemaKey` positive control demonstrates accepted nonplain string equality rather than imposing a new plain-key policy. The real validator remains responsible for comparison and rendering; `keys` is inert when not planning. Flat schema-before-kind and PER kind-before-schema remain supplier-qualified unchanged behavior. Archive schema refusal remains before constructor values, with earlier records already retained.

The appended paired tests cover top-level, archive and later-archive equal-cardinality refusal, plus true opaque success at both schema locations. They keep live rows nonempty and valid so later row rejection does not mask the tested boundary. Mixed-key error assertions allow the original sorting TypeError as well as schema ValueError. No exception rewrite is introduced.

## F2: actual archive count relationship is represented

The helper source independently confirms the sequence: `HistoricalReplayArchive.__post_init__`295–304 owns/clones mappings, obtains owned state/formats, evaluates reward then approval, validates archive state, compares its returned count with exact-int/nonnegative archived count, then computes/compares digest. `_count`157–166 returns the exact declared `size`, `size_current` or `num_transitions`; `_validate_archive_state`199–262 returns that count after its internal checks. Tensor reduction results do not replace it.

Shared109–118 preserves clone-source inventory, ordinary semantic short-circuit and fixed-diagnostic count type/range refusal. Shared119–136 reads the Mapping items used by the actual clone implementation51–62. With exact-string keys, exact supported kind and exact-int declared count, an unequal archived count proves the digest cannot be reached: preceding validation either refuses or returns that same declared count. The new check retains earlier mapping/record effects without running archive validation, reductions, digest, Tensor comparison, repr or clones during planning. It handles all three kinds and arbitrary unequal ordinary counts, including empty archives. Real restoration remains the unchanged callback at99–100.

Nonplain keys or kind/count metadata do not receive this exact-metadata deduction. Their clone behavior can change the owned metadata. `_ArchiveCountOnClone` and MappingProxyType controls specifically preserve a clone-changing accepted count and a supported Mapping view. The patch does not impose new runtime accepted types or suppress constructor work.

The earlier F2 semantic and operator cases remain covered: ordinary wrong reward excludes approval/digest, wrong approval excludes digest, and reached nonplain semantic/digest operands are retained. Tensor archived count remains an exact-type refusal without a fictitious comparison effect. The FIX5 fixtures exercise count mismatch above/below/zero, an unreachable digest operand, a later-record boundary, matching count, clone-changing count, and Mapping views across all supported archive kinds and both replay families.

## Examined composition boundary and test limits

I explicitly traced an additional composition rather than merely checking the supplied last witness: put the existing `_ArchiveComparison(torch.tensor(0), 1)` in reward_semantics, ordinary archived count5 against exact declared4, an opaque digest on5, and valid live rows3/selector4. Shared112 calls `opaque`, which stops at66–70 with unknown=True before the new count predicate; inventory consequently includes later5/3 and preparation4. For this particular side-effect-free test class (`__ne__`1948–1952), actual construction performs the semantic operator on1 then refuses on count, without digest or live-row work. No test currently combines these two dimensions.

This is **not classified as a material F2 defect under the adopted scope**. The binding matrix expressly makes nonplain scalar protocols a stop of the safe predicate path, retaining protected evaluation and possible continuation; FIX3 excludes a requirement to resolve arbitrary custom comparisons. The planner has no certificate that a supplied nonplain comparison/truth hook is side-effect-free. Arbitrary supported hooks are executable Python and could alter archive fields or reachable state before the subsequent comparison. Conversely the existing `_ArchiveComparison` does not do that: its observed simplicity is a source fact about this fixture, not a general production type contract. Advancing the ordinary proof across that protocol boundary would need a separately justified stability rule; inspecting or special-casing this test class would be inappropriate. The same distinction applies to clone-mutating nonplain metadata. Thus source-stage PASS does not claim minimal inventory for every actual execution of opaque user protocols.

Other limits: the MappingProxyType control is positive only; no negative Mapping-view count pair or clone-changing key/kind pair was added. The source checks cover their corresponding ordinary/unknown branches, so these are finite coverage limitations, not independently established defects. Existing opaque semantic fixtures and the new count fixtures separately prove their intended effects; pure planning checks1394–1400 assert no Tensor/runtime events. They do not establish authentic public producer completion or hardware behavior.

## Quality, preservation and evidence

The production delta is20 net shared lines, with no helper/family edits. It adds a small successful-return relationship rather than duplicating the archive validator. Its comments explain the clone-stability boundary. The existing real-validation callback and family predicates preserve original runtime errors/order. No changed-code regression in DTO ownership inventory, issuer-held additive inventory, reentry ordering, mask handling, sampling or publication was established. Those unchanged components and excluded consumers are not independently requalified here.

Root's read/hash-verified R104 record reports757 collected IDs,436 unique reachable PASS in disjoint10+129+69+24+16+4+40+28+44+72 selections, zero errors/skips/warnings. It reports the72 causal RED cases now passing; author history preserves prior attempts rather than adding them to436. Owned-four Ruff/Black and unchanged default600 pass. Owned-three mypy still fails with the one missing B `AmbientRNGDomain.device_invocation` at shared464. These are attributed root results; this reviewer did not execute tests or independently verify every referenced log/custody file.

321 focused nodes remain UNRUN, including216 new B-dependent public cases and10 isolated children. Core invocation/outcome integration, authentic B activation, producer/parent/recurrent completion, real one-/two-device CUDA, final other-model adversarial verification and whole-programme gates remain owed. Package accounting remains28 qualified/38 remaining/66 total. This same-model scoped review closes neither those gates nor the residual execution obligations of I5.
