# WIP16 metadata fix1 — frozen for scoped re-review

Finding W16-E1 in T18e-R0-WIP16-TERMINAL-EVIDENCE-REVIEW.md (SHA256 4fec8c8f6eeb78ddf84a01f9f47f481ff1898928e682e8e4b8d85c96ac0991e5) identified seven missing mandatory top-level dependency roles. This correction starts from root's frozen input, not an earlier draft.

Input: evidence-management/wip16-r85-terminal-review-input-v1.json, SHA256 23b035938c7db22766ad5fbe357ccc90cf947035252366b9ab1c5accb09fa512, 287239 bytes.

Output: evidence-management/wip16-r85-terminal-review-input-v2.json, SHA256 184d37936d6be46f056bf7a09ca86dd60fe8fe922f63aacadd5882c79e6d1cee, 287533 bytes.

Only these seven JSON fields were added, in the existing dependency order:

| JSON path | Dependency | Added role |
|---|---|---|
| /dependencies/0/role | run_bac_packet_checks_locked.py | qualification_harness |
| /dependencies/1/role | verify_bac_run.py | runtime_custody_verifier |
| /dependencies/2/role | verify_bac_failed_run.py | failed_runtime_custody_verifier |
| /dependencies/3/role | verify_bac_static_run.py | static_custody_verifier |
| /dependencies/4/role | verify_bac_replay_spawn_identity.py | replay_child_identity_verifier |
| /dependencies/5/role | capture_wave14_round.py | candidate_capture |
| /dependencies/6/role | bac_source_identity.py | pytest_source_identity |

Verification: parsed the written v2 JSON, removed exactly the seven added role fields, and asserted deep equality with parsed frozen v1: PASS. Checked seven unique expected dependency paths, absent prior role fields and exact supplied role values: PASS. Rehashed v1 after writing: unchanged. All hashes, references, required_by arrays, execution facts, status, ordering and other fields are preserved. Existing drafts, v1 and independent review remain untouched.

No selector, receipt validator, assembler, application or helper runtime was invoked. No tool/source read or edit, Git/index operation, source copy, branch/worktree or delegation occurred. Metadata parsing/hashing only. No final-schema validation or publication PASS is claimed. Root must freeze the matching v2 subject, obtain scoped independent re-review, then seal the final receipt and perform actual final selection/publication checks. Metadata author relinquishes writes at this handoff.
