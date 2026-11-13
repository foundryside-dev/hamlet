# R0 replay child verifier interface — source-factual handoff

2026-11-13. Source review only; no execution, import, probe, Git/index operation,
or implementation edit. Read repository AGENTS.md and
T18e-R0-QUALIFIED-CHILD-CUSTODY-API.md. The sole implementation body read was
`/workspace/bac-review-2026-11-01/qualification/verify_bac_publication_spawn_identity.py`:
102 lines, 5057 bytes, SHA256
`8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209`,
measured before reading. Root clarified the <=5000 bound is source lines.

## Actual accepted interface

CLI arguments are `SPEC JOB_INDEX CASE EXPECTED_MESSAGE` (exactly four after
script name). SPEC is JSON; `jobs[int(JOB_INDEX)]` selects a job, whose `name`
sets the evidence directory. There is no explicit nonnegative index check.
Required spec fields read here: `root`, `manifest`, `output`, `jobs`; required
job field: `name`. Root resolves via Path.resolve(); manifest/output paths are
used as supplied. The script first reads SPEC, then checks argument count.
EXPECTED_MESSAGE is caller-supplied exact text; no case-to-message map is imposed.

CASE has a hard-coded allowlist:

- `binding_poison`, `domains_poison`
- `bootstrap_poison_setter`, `bootstrap_poison_cleanup`, `bootstrap_poison_completion`
- `owner_capture_poison_setter`, `owner_capture_poison_cleanup`, `owner_capture_poison_completion`
- `bank_restore_poison_setter`, `bank_restore_poison_cleanup`, `bank_restore_poison_completion`
- `bank_install_poison_completion`

A new `replay_poison` role or distinct replay-domain role is **not admitted**.
Do not rename replay evidence to an old BANK/core case to pass this verifier.

Files consumed are `output/<job-name>-result.json`, and under
`output/<job-name>/`: `identity-controller.json`, `spawn-identity-<CASE>.json`,
`spawn-observation-<CASE>.json`. Child `worker` must equal CASE; controller
`worker` must be `controller`. The result's manifest hash, candidate tree and
base commit must match the actual manifest; its exit_code is copied into the
receipt, **not asserted zero**. Parent pytest success remains a separate result.

## Import and process pairing contract

Child `imports` must equal this complete dictionary, with these unqualified keys:

- `world_curiosity_state`: `<resolved-root>/src/townlet/exploration/world_curiosity_state.py`
- `rng_custody`: `<resolved-root>/src/townlet/exploration/rng_custody.py`
- `rnd`: `<resolved-root>/src/townlet/exploration/rnd.py`

Extra entries in `imports` fail equality. Extra top-level child fields are not
rejected, so a separate replay-import map and `ppid` could be recorded there,
but this verifier would ignore them. Merely adding paths does not verify replay
source custody. Both identities' package `module` paths are resolved and checked
against root/src/townlet/__init__.py; the three imports above use string equality.

Observation keys must be **exactly** `process_pid`, `queued_pid`, `exitcode`,
`qualified`, `message`, `manifest_sha256`. Adding parent `parent_pid` currently
fails. Child pid must have exact type int and be positive. The verifier checks
`observed.process_pid == observed.queued_pid == child.pid`, exitcode == 0,
qualified is True, exact message, and shared actual manifest hash. It does not
independently type-check the two observation PIDs. It reads JSON; it cannot
inspect a live multiprocessing Process object or prove how observation values
were acquired. The supplied custody prose establishes the existing parent wrote
actual Process.pid and compared it to the successful child's queued PID.
That existing pairing supported the existing custody; those records did not
contain PPID. No parent os.getpid/child os.getppid pairing is checked here.

Other enforced child facts: debug is True; interop_threads exact int == 5;
Torch version equals controller's; both identities have matching commit/tree and
threads == 1. The verifier checks current HEAD, locked git write-tree, clean
unstaged diff, hashes of manifest source_files/configs/artifacts, and exact
worktree-registry text. These are source facts, not operations performed in this
review. Root owns execution authorization and manifest/tool sealing.

The output `spawn-custody-<CASE>.json` refuses a preexisting destination by
assertion before write_text (not exclusive-create). It hashes the child record,
parent observation and verifier itself and reports only the named child scope.
No runtime conclusion or replay poison correctness follows from this review.

## Minimal separately named extension proposal — not authorized to edit

The existing generic verifier is incompatible with the proposed new role,
expanded imports dictionary and parent PID field. Propose a new narrowly scoped
`verify_bac_replay_spawn_identity.py`, leaving historical verifier and evidence
bytes intact. Root must seal its exact new role/message(s) before execution;
`replay_poison` is a proposed role, not an admitted role today.

Retain the current source/manifest/controller/child/Process/queue/exit/message
checks and explicit scope. Change only the new contract as needed:

1. Admit only the exact fresh replay role(s), with their agreed exact success
   message(s); do not extend or reuse old receipts.
2. Check the exact replay import keys and expected paths in the child-owned JSON,
   in addition to the existing bootstrap probes. Root supplies the actual module
   inventory; this review did not read replay source and cannot invent it.
   Prefer a separately named `replay_imports` map if retaining bootstrap's map.
3. Require observation `parent_pid`, child `ppid`, exact positive integer types,
   and `child.ppid == observed.parent_pid`; preserve the independent
   `child.pid == observed.process_pid == observed.queued_pid` pairing and reject
   parent/child PID equality. The parent must record os.getpid and actual
   multiprocessing Process.pid; the child must record its own os.getppid.
4. Keep parent-job success separately checked by root, or explicitly assert
   result.exit_code == 0 if the new receipt is intended to require it. Do not
   silently describe the present verifier as enforcing that condition.

The proposed child can call existing bootstrap._child_identity(role), enrich its
own emitted spawn identity with real replay module paths and os.getppid before
queuing success, while the parent records the actual Process and its own PID.
This describes the proposed producer/verifier contract, not observed replay
execution. Root owns the new sealed run and final verification. No broader new
evidence programme or additional helper/source read is required for this narrow
interface conclusion.
