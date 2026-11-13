# R0 replay child verifier — independent source and synthetic review

2026-11-13. Reviewer: independent other-model agent; producer: Astra. Scope is the three frozen source bodies below and the stated brief, report, diff, AGENTS.md and BAC evidence process. No application source body or producer implementation was inspected. No application command, real child, Git/index command, or qualification attempt was run.

| Source body | Lines | SHA-256 |
| --- | ---: | --- |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_publication_spawn_identity.py` (read-only comparator) | 102 | `8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209` |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_replay_spawn_identity.py` | 154 | `0986a6f3edebc0a208da073eda849ccb8f9d867a330fe1c2848ac38158e6f868` |
| `W/evidence-management/test_replay_spawn_verifier.py` | 234 | `3f01b82ca3f5c3c2cb5629d11aa398e611efcbe2bbc0f736d41ee64261f44633` |

Total: exactly 3 bodies, 490 lines, under the brief's ceilings. These hashes independently match the author report and root synthetic observation.

## Verdict

**SPEC: bounded pass with one evidence-process defect. QUALITY: acceptable synthetic logic coverage; real-use approval remains with root.** The verifier seals the replay role and exact message/pytest args; checks a zero parent result exit and a zero child exit; pairs positive exact integer child, Process, queue, parent, and PPID readings; checks the old three import paths and four separately named replay import paths against the source inventory; rehashes source/config/artifact inventory; and retains HEAD, index tree, unstaged diff and worktree registry guards. It binds hashes of the input records, itself and the fixed harness label in an exclusively created receipt. Wrong role, message, PID/PPID, parent exit, missing records and changed source values refuse in the reviewed logic. The new PPID and parent PID checks are applied only to new producer fields, with no claim that historical receipts had them.

**Defect D1 — parent elapsed duration is accepted without validation.** `check_bindings` requires a `seconds` key but never checks its type or value. A result with `seconds: null`, `0`, or a negative value can produce the positive custody receipt when the other bindings agree. The BAC evidence process requires positive recorded elapsed seconds for a qualifying runtime claim. The receipt itself omits elapsed seconds, so downstream publication must validate duration independently. Before treating this tool's output as complete qualifying runtime evidence, root should either require a positive finite numeric `seconds` from the parent result or enforce and record that guard in the authoritative attempt review. This is a process-completeness gap, not evidence that the PID or source guards can be bypassed.

The actual producer's `_child_identity('replay_poison')`, multiprocessing parent assertions, and source import readings were described in the brief but were outside this source packet. The verifier accepts JSON record provenance from the sealed root execution context; input hashes establish byte bindings, not independent JSON authorship or actual child execution. The pinned harness digest is compared to the result's `harness_sha256` field; this verifier does not independently hash a harness source file. The root must validate actual producer and candidate provenance separately before real use. No broader suite, CUDA, restoration, historical PPID, or whole-package conclusion follows.

## Independent test receipt

Command from `/workspace/hamlet`:

`/workspace/hamlet/.venv/bin/python -B /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py`

Observed exit: `0`. Combined captured output:

```
............
----------------------------------------------------------------------
Ran 12 tests in 0.059s

OK
```

Captured log: `W/wave35-preparation/T18e-R0-REPLAY-CHILD-VERIFIER-INDEPENDENT-TEST.log`, SHA-256 `7648ba9b8e06fc2670e0273e7d293585d6af926f24760546722dd3d9ca0543d3`. Exit file: `W/wave35-preparation/T18e-R0-REPLAY-CHILD-VERIFIER-INDEPENDENT-TEST.exit`, SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`, containing `0`. UTC start/end times were not captured. This is a separate run from root's recorded 0.041 s observation. Tests used temporary synthetic DATA fixtures and mocked external metadata; they prove only the tested verifier behavior.
