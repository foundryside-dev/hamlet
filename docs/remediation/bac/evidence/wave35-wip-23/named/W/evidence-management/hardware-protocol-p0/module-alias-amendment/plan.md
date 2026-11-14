# Module-alias Implementation Plan

Goal: implement the adopted CUDA-HARDWARE-P0-MODULE-ALIAS-AMENDMENT-v1 proposal.
Architecture: only named-reference.name uses a new bounded reference-name scalar; id/path and all semantics stay unchanged.
Tech stack: Python, pytest, inert fixture references.
Spec: ../../../wave35-preparation/CUDA-HARDWARE-P0-MODULE-ALIAS-AMENDMENT-v1.md

Global constraints: two Q bodies only; combined <1400 lines; no application imports/runtime; no Git operations, deletion, compatibility paths or other consumers running during mutation.
Review focus: literal preservation, 128-character boundary, unrelated IDs, fixed tools, duplicate/reference rejection. All are tested in task 1.

Task 1: Add exactly the seven test groups specified by the proposal to test_bac_hardware_protocol_v1.py. Record full RED suite against frozen production bytes. Change named-reference.name to reference-name, and add its bounded scalar branch in bac_hardware_protocol_v1.py. Record full GREEN suite with no skips. Publish new schema/interface/freeze with predecessor refs, source snapshots and exact execution metadata. Root obtains independent review before adoption.

Ledger: P3 confirmed quiescence before any mutation. Root explicitly grants inline implementation and successor evidence. Root instructions supersede skill default Git/worktree/commit/deletion and full-application-suite steps. No shared implementation tasks. Final review is root-owned, pending.

Task 1: implementation complete; red01 10 failed/169 passed; green01 179 passed, no skips. Successor freeze-v5.json published. Independent review/root adoption pending. No deviations from proposed scalar semantics.
