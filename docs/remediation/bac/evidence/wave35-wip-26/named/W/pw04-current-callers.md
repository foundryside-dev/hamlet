# PW04 current production callers — bounded migration handoff

2026-11-14. Read-only inspection by `/root/pw04_current_callers`; this document is the only write. No production edits, imports, tests, formatters, Git operations, branches, worktrees, execution copies or deletions. Root approved roster transport conceptually and deferred implementation until the current runner lifecycle/native slice. This is a durable planning handoff, not package qualification or execution evidence.

## Exact inspected source

Five whole bodies, 3,010 lines. Hashes rechecked unchanged before writing this handoff:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/demo/unified_server.py` | 616 | `626634171c744ecac9ac825f5db5727e3407031efd6c8fe0dcac5a1058e2a02c` |
| `scripts/check_episode_lanes.py` | 1,036 | `19e0b83130f2467a2bfd890dc79e95de6d7694e79f7fa996fa16c66b43e62eb7` |
| `scripts/l2_baseline.py` | 279 | `d282c731005614fea047bfb265774cbbb640be9aa0a66f950df5c578065e4c76` |
| `scripts/l2_token_regression.py` | 767 | `3dcca153423a484e4934194ccfbf7ec29836b44241d49fbb3d18dadf0d1509cb` |
| `src/townlet/config/world_roster.py` | 312 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |

Read repository AGENTS.md and the current world constructor/identity contract prose. No runner, ENV, POP, compiler, manual-session implementation or external CLI body was opened. Runner's new required declaration and immutable manifest behavior are integration-owner supplied facts, not an independent source audit here.

## Six actual DemoRunner call sites

None currently supplies an authored world roster, and none exposes a roster authoring input.

| Current call site | Finite transport proposal |
| --- | --- |
| `src/townlet/demo/unified_server.py:418`, `_run_training` | Add required keyword-only `world_roster: WorldRosterDeclaration` to UnifiedServer's constructor, validate/retain the supplied declaration and forward it unchanged. Do not infer IDs from population size or agent names. |
| `scripts/l2_baseline.py:133`, `cmd_train` | Add required `--world-roster` JSON input. Parse the exact declaration before creating run artifacts. Pass it to DemoRunner; record declaration and canonical manifest digest in run metadata. |
| `scripts/l2_baseline.py:158`, `cmd_eval` | Load the existing run's canonical `run-world-roster.json` and pass its exact declaration. Missing/invalid/noncanonical manifests refuse; evaluation must not allocate replacement identities. |
| `scripts/l2_token_regression.py:456`, `cmd_train` | Add required `--world-roster`. Bind declaration/digest into `prepare_run`, `validate_resume_run` and normalized command provenance, before recording a training attempt. Forward the validated declaration to DemoRunner. |
| `scripts/l2_token_regression.py:507`, `cmd_eval` | Validate the existing canonical run manifest and forward its exact declaration. No generated IDs or compatibility fallback. |
| `scripts/check_episode_lanes.py:814`, `run_producer` budget-six branch | Author a literal pair of stable world IDs for the already fixed two-lane recipe. Use the same declaration in its direct ENV and actual runner paths. Keep world identity distinct from lane index and display agent names. |

The source-verified declaration decoder is `WorldRosterDeclaration.from_dict`: exact fields `schema` and `world_ids`, current schema `world-roster-v1`, a serialized list of unique nonempty exact strings. The immutable declaration exposes `to_dict`, `semantic_identity` and `manifest_digest`; the latter hashes canonical bytes plus newline. A launcher may parse a user-authored JSON file and pass the declaration, while the persisted run manifest must satisfy runner's exact-byte contract. Reading an existing run's authored manifest is transport, not identity inference.

## Consumer work beyond roster transport

1. **External UnifiedServer CLI is owed.** Its constructor migration is incomplete until its real launch caller accepts and forwards explicit roster authoring. `scripts/run_demo.py` is a likely entry point from repository guidance, but was not opened or freshly confirmed as the caller. A separate bounded source inspection must identify and migrate the actual call chain and affected tests. This handoff does not claim all production entry points are covered.
2. **Both greedy evaluation loops use obsolete manual ENV APIs.** Baseline `cmd_eval` and token `cmd_eval` restore through a shutdown-marked runner, then call bare `env.reset()` and `env.step(actions)`. They require a genuine supported manual lifecycle/session owner, preserving greedy masked-action evaluation and recurrent hidden-state behavior. Actual current manual-session API availability, signatures, restore ownership and completion/retirement semantics are unknown in this inspected scope. Do not invent a session API, synthesize receipts, or remove evaluation to claim caller coherence.
3. **Episode-lane producer has multiple current interface mismatches.** Its direct ENV constructor omits required world declaration/seed/binding; its POP/exploration construction is old; its reset wrapper accepts no reservation/retired-world inputs and returns no authentic reset result; its budget-six branch patches the removed runner `AdaptiveIntrinsicExploration` seam. Current policy authoring and genuine lifecycle transport must replace these together while retaining all independent lane/budget assertions and recipe functionality. Roster-only edits cannot qualify the producer.
4. **Current test callers remain separate.** No test body was inspected. This is the four production caller files requested by root, not the broader reported 24-file caller migration.

## Finite implementation and verification order

After the current runner lifecycle/native slice stabilizes: identify the real public launch chain in a separate bounded assignment; establish the genuine manual evaluation/session API; implement explicit roster transport and resume identity checks across the relevant coherent consumers; migrate manual evaluation and lane-recipe choreography using actual current owners; then run focused caller/CLI/identity-refusal tests and the applicable owner gates against the exact integrated candidate. Root owns runtime, source freezes, Git and publication. Source budgets remain at most five whole bodies and 5,000 lines per assignment, including growth.

Required negative cases include missing/malformed/duplicate-ID declarations, cardinality disagreement, changed authored order or membership on resume, and missing/tampered persisted manifest. Required positive cases include unchanged explicit declaration transport, actual training/resume, and preserved greedy/manual and budget-six behavior. These are proposed checks, all unrun in this handoff.

No new owner decision is identified for additive explicit authoring under the existing no-backwards-compatibility instruction. Any proposed removal, degradation or consolidation of evaluation, recipe or launch capabilities must be surfaced rather than silently accepted. No such reduction is proposed here.

Status: **paused pending root scheduling; no production edits authorized by this handoff; no package closure claim.**
