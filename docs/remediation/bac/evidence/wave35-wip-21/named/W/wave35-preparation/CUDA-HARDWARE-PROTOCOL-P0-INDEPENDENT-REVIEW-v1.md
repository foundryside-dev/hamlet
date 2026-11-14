# Independent Astra review — hardware protocol P0 v1

Reviewed at 2026-11-14T05:46:28.507417+00:00. Disposition: **changes required before consumer adoption**. Review is of the frozen common transport only; neither synthetic pass nor reference shape proves hardware, child, fork, phase, or BAC behavior.

## SPEC / QUALITY findings

1. **P1 QUALITY — reference path substitution is accepted** (`bac_hardware_protocol_v1.py`, `file_reference`, lines 155–185). A parent directory is renamed after the file opens, then a different directory/file is installed at the original path. The final leaf stat is relative to the retained old directory descriptor, so the function returns the original digest with a path that already names different bytes. The independent test deterministically performs this during the first read; rejection fails. Verify the observed directory chain still binds the original absolute path before returning (with the existing honest no-writer limitation). This is narrower than preventing arbitrary future writes and belongs to the existing reference operation.
2. **P2 SPEC — nonexecution dispositions permit completed-success fields** (`_semantic`, job-result, lines 387–413). An otherwise successful record can become `unrun` or `refused` by changing only disposition and reason. It retains exit 0, measured completion/duration and passed outcomes. Both independent mutation tests are accepted. Define and enforce a closed local shape for unrun/refused (at minimum no execution exit/signal or executed outcomes); preserve genuinely available wrapper timestamps distinctly if needed. This is local consistency, not downstream evidence authenticity.
3. **P2 SPEC — impossible source-freeze interval is accepted** (`source-freeze` schema, missing semantic interval check). A measured end earlier than its start passes. Enforce chronological order as already done for job-result. Root's actual no-writer barrier remains downstream proof.

No broad case validator expansion is requested. The explicit pinned contracts, fixed role/obligation taxonomy and metadata obligation owners preserve the agreed finite P0 boundary. P1–P5 must still parse and authenticate referenced records/validators; missing validators remain unsatisfied/unrun. These three findings are local invariants/reference binding gaps, not a request to implement behavioral validators in P0.

## Evidence and scope

- `/workspace/bac-review-2026-11-01/qualification/bac_hardware_protocol_v1.py`: 448 lines; SHA-256 `aaa0a2b7efc22aba0bc9fe6f581a4788c1617b44b406e580485db1ff2dd6b053`.
- `/workspace/bac-review-2026-11-01/qualification/test_bac_hardware_protocol_v1.py`: 379 lines; SHA-256 `4375fc1c24e62438695eff860faf6f0197adfffefbb550b3fcbbbd98199a85d9`.
- `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-protocol-p0/independent-review/test_independent_p0.py`: 124 lines; SHA-256 `dc17ff2ac3ef7f21716eb78cc561c9c08fc771fe20c1b34f54d5aa467e718bf2`.

Three bodies / 951 combined lines inspected or authored, below five/5,000 and author two-file 1,400 caps. No other helper/application body read or imported; no hardware, server, checkout, branch, source copy, deletion, push, or Git operation. Reviewed AGENTS.md, root grant, accepted plan/readiness, freeze/interface metadata and author's test command metadata. Interface gap declarations remain explicit; server availability is not assumed.

- `author-suite-v1.json/.log` and `independent-suite-v1.json/.log`: preserved initial interpreter failure, pytest absent, exit 1.
- `author-suite-v2.json/.log`: **85 passed**, exit 0, independently rerun frozen author's suite with external plugins disabled and conftest disabled.
- `independent-suite-v2.json/.log`: preserved pytest setup refusal, exit 4; inherited project addopts referenced disabled coverage plugin. No application test ran.
- `independent-suite-v3.json/.log`: **18 passed, 4 failed**, exit 1; exact local review cases above. Explicit `-o addopts=` cleared inherited options. Test source does not import author's fixtures; it creates literal inert records and file fixtures and directly loads frozen protocol.

Each JSON records exact argv, cwd, explicit environment overrides, UTC start/end, exit and source SHA-256 before/after; all tested source hashes remained unchanged. Outputs were exclusively created with distinct test temporary directories; failed logs and fixtures retained. Reproduction command is in `independent-suite-v3.json` (use a fresh distinct basetemp for a new attempt). Independent fixture bytes and source hashes suffice to reproduce without application runtime.

No success claim is made for malformed-path/race handling until finding 1 is fixed and rerun. No P1–P5 adoption is authorized by this review; root owns integration.
