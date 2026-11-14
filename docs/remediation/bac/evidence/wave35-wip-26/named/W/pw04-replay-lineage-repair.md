# PW04 standalone replay restore repair

Source-only repair; execution and qualification remain root-owned. No native bound-controller or PW04 closure is claimed.

Measured three-body inventory before work: POP 3169 lines, replay_contract 881, test_parent_intrinsic_handoff 900 = 4950. Final POP 3181, total 4962. Final POP SHA256: ff8828ab4ae966e7ac0a7b482102b060293cc247043686e4f5d9b818339e4408.

Replay contract source proves each PreparedReplay is registered to its actual destination owner and carries that owner's revision plus a core currency token. The old POP sequence omitted required lineage, materialized on the live owner, then deep-copied that owner and attempted installation on the copy. Replay custody owns a lock and opaque registered RNG authority. Root independently confirmed that none of the three concrete buffers provides an owner deepcopy implementation or a safe owner-clone API.

The repair uses POP's existing selected replay factory at the restored ledger tick. When the old validation target was the live replay, the new destination first restores the complete current serialized transport, preserving retained receiving archives. It then materializes and installs incoming validated state on that same genuine offside owner. Each immediate prepare/install pair explicitly requests standalone lineage=None; it does not adopt ambient authority or refresh a token. Already-offside targets retain their existing path. Existing fresh-unbound and bound-owner replacement guards remain unchanged.

Concrete buffer transport/archive behavior is attributed to root's source-qualified inspection; those implementation bodies were not opened in this bounded packet. The inspected replay contract verifies custody and token semantics, and the inspected POP verifies factory/setup selection and ordering.

Required root verification is the three existing failed R148 nodes in test_parent_intrinsic_handoff.py:
- test_current_initial_transport_has_complete_exact_ledger
- test_initial_pop_roundtrip_preserves_ledger_and_next_real_update
- test_initial_install_refuses_roles_bound_after_preparation

No tests, imports, formatters, Git operations, branches, worktrees or execution copies were performed by this worker. The final source remains frozen for root formatting and exact-candidate execution. Native stable-owner continuation and composed runner save/restore remain separate required work.
