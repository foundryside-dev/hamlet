# Direct world-identity VFS ABI review R1

Verdict: **APPROVE** the exact proposal identified below for the bounded direct VFS consumer. No material contract gap or required design change found. This is static ABI approval, not implementation, runtime qualification, or final BAC approval.

## Custody and exact read inventory

Whole existing sources read; SHA256 and lines independently checked:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/environment/vectorized_env.py | 2343 | f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784 |
| src/townlet/vfs/random_draws.py | 218 | e9cb4a885c70ef72282841d26c95c3a11e5208657e814faf4ea16b1821f9e490 |
| src/townlet/config/world_roster.py | 299 | e2627284a192920211429c77f5a806c0032e17071eedbd0877f95f4d7df4c461 |

Same three existing sources, 2860 lines. Reserved tests/test_townlet/regressions/bac/test_world_vfs_identity.py was neither created nor opened. Future complete inventory remains exactly four files/4900 maximum: ENV2600, VR700, ROSTER400, new test1200.

Other files read, with whole-file SHA256:

- AGENTS.md: 2db4cc23dbf6e2890c3279ea34a068c38f4ee1c8dfd5ecf838541dd93586672e.
- docs/remediation/bac/CURRENT-WORLD-IDENTITY-CONTRACT.md: af69d3e613df4611355b3432e3fcc59ce508806bc0e99a72d75e2521b669a204.
- .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave17-preparation/CURRENT-WORLD-CONSTRUCTOR-TRANSPORT.md: 703cb0f1eadb065271e939b446ed889b83f3238c1ca5af58a3951bf6ead1b635.
- This directory's WORLD-VFS-ABI-REVIEW-brief.md: beb02bb81f8486934ae10b83f15f343fb446fe1b6c3c62a88d933906875780ca.
- This directory's WORLD-VFS-brief.md: 4a866798dc1c25d3ff13618bcce4c336f0a0bad4733b53411e95449686a19f9b.
- Reviewed WORLD-VFS-ABI-PROPOSAL.md: 16c334d0d1917d663d2f2f87796c6821b11b649628efb3886c5415c7b1fc5419.

A file-name search located the named contract and AGENTS.md; no additional implementation/test bodies were opened. The subagent-exempt using-superpowers instruction was read via the skill tool. Only this ignored review prose was written. No imports, runtime, tests, formatters, Git/index, branches/worktrees, source copies, deletion, or subagents were used. Constructor R1 source remains frozen. Execution receipts in the briefs/contracts are attributed, not independently rerun here.

## Findings and source-grounded assessment

No material findings.

1. **Ordering and sole identity authority are coherent.** ENV initializes authoritative identity before subsystems (289, 1917 onward), builds old VFS at780, and performs old scalar reset before instant-zero evaluation (1020 onward). Public reset accepts only after `_reset_world_state`, then updates cursors (2086–2109); duplicate accepted retry returns before reset work (2083–2085). Therefore the proposed validated candidate producer installation before reset work is necessary and correctly placed. Installing only after acceptance would miss reset-time expressions. Candidate projection does not itself accept an episode; failure quarantine and export refusal preserve that distinction. No second sequence counter is needed or proposed.

2. **Per-world KDF is concrete and sufficient for the stated domain.** Exact framed seed/ID/sequence hashing excludes row, N, order, authored membership hash and other-world context. Independent tuple projection supports unequal pure contexts without fabricating unequal currently reachable ENV history. Tick/site/ordinal/element mixing and the 24-bit conversion are specified sufficiently for independent Python vectors and a device-local tensor implementation. A 64-bit output key is expressly not collision-free; that is an acknowledged finite random namespace, not a contradicted isolation promise. The recipe deliberately changes old draw values; no compatibility contract requires retaining them.

3. **Existing shape and shared-prefix mechanics can survive directly.** VR141–218 contains the complete joined/broadcast shape, ordinal, two-lane normal and shared-prefix behavior. Replacing the scalar/row contribution with lane-ordered per-world keys does not require changing these interfaces or normal/broadcast rules. ENV1449/1477/1547 already uses the preserved DrawInstant seam. Shared prefix must keep its original prefix ordinals, while write-local ordinals restart after the prefix exactly as proposed. Normal outputs retain float64 intermediates/float32 results and device semantics; cross-device bit-identical transcendental results are not newly promised.

4. **The v4 parent/child correlation is correctly defined.** ENV2260–2280 exports actual destination lanes independently of historical saved binding. ROSTER223 onward validates original accepted-history/closure bindings; ENV2316–2333 restores those histories unchanged. Consequently a snapshot taken after a restore permutation must bind its VFS child to that snapshot's destination_lane_binding, not saved_lane_binding. The proposal explicitly does so, then separately derives a context for the fresh restore destination by exact-ID cursor lookup. INITIAL seq0 and COMPLETED current cursors remain distinct. The proposed pure validator must run for INITIAL before its current early return at ROSTER246, as well as COMPLETED; this follows the proposal's entire-v4 preflight requirement.

5. **Prepared state can remain owned without serializing capabilities.** Existing `_record`/frozen_value/owned_value accept data mappings, lists and tuples, but reject a raw new VFSWorldContext dataclass (ENV1982 onward; ROSTER128–156). Implement the proposed preconstructed destination context in the prepared record as owned portable context data/tuples and reconstruct the immutable context when needed; do not insert a raw producer or context object into the current generic receipt serializer. This is an implementation watchpoint within the specified data-only ABI, not a need for a fourth implementation source or serializer redesign. The candidate producer can be built locally before mutation. Complete validation before installation and guarded quarantine remain the existing failure model; rollback is not asserted.

6. **Native entry points do not create lifecycle authority.** Strict expected-current validation/reinstallation cannot import a different seed/cursor or authorize rollout. Joint restoration remains the prepare/attest/install route. Exact producer lane order on standalone native state and explicit destination remapping through joint preparation are compatible; an old source-ordered standalone child cannot simply be fed into a permuted destination as though already remapped. The proposal states that distinction and correctly assigns outer parent updates separately.

## Acceptance limits and handoff

The reserved test scenarios are meaningful: actual compiled construction/reset/step, reset-time candidate observation, reference vectors, identity-preserving permutation/spectators, independent unequal pure sequences, broadcast/normal/shared-prefix controls, accepted retries, late quarantine, deep pure refusals, and genuine producer INITIAL/COMPLETED permutation histories. They can establish the direct VFS contract using explicitly local owner receipts. They do not establish real bank/learner/parent behavior.

The schema bump is approved within the three production sources. If existing owned world-native tests require their v3 expected-payload/fixture updates, schedule that as a separate bounded maintenance task with its own inventory; do not open/edit that old test here as a fifth source and do not weaken v4 checks to keep it passing.

Ambient Torch placement paths at ENV557,975/980,1871,1900/1911 remain separate required qualifications. No inspected dependency makes changing substrate, shared affordance mechanics, provider RNG or real learner behavior inseparable from this VFS consumer. Preserve those capabilities and qualify them in their existing scopes. Root may reconcile these implementation watchpoints and clear the authorized tests-only phase; no new user routine permission or expanded design programme is required.
