# Hardware verifier P4 author freeze v1

The bounded P4 implementation is frozen for fresh independent review. Final
packet-only validation is **73 synthetic tests passed**, Ruff passed and Black
passed. This is not full P4/P5 toolchain qualification, application qualification,
actual-server admission, or CUDA execution evidence. Root review/adoption and an
authorized concrete validator inventory are still required.

Files in `/workspace/bac-review-2026-11-01/qualification/`:

| Body | Lines | SHA-256 |
|---|---:|---|
| historical `verify_bac_run.py` unchanged | 33 | b00f16ec8666f475805399e80e7f4c2e335f8c6170c18cb705c22f8d6725c91d |
| adopted `bac_hardware_protocol_v1.py` unchanged | 520 | adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c |
| new `verify_bac_hardware_v1.py` | 1127 | 029274afdf79d51b8c02c6b1f2bd2e72a0946cdee708a1604b10e48afb324961 |
| new `test_verify_bac_hardware_v1.py` | 1196 | e2d17f43a0066f7a9f4a3788a9542efc2d59cd0b832ea607f6f0ac5004bde7a5 |

Total: **2,876 lines / four bodies**, below the 3,800-line packet cap. No other
helper/application/test source body was imported or inspected; P1/P2/P3 were
consumed through their sealed metadata. Standard-library, pytest, formatting and
lint tooling imports were used. P2's frozen output metadata remains subject to
its separate review; P3's adopted interface v2 preserves v3 authority and retained
v2 observations. Existing historical helpers were not modified.

`verify(spec_path, job_id, destination)` independently checks closed P0 records,
all referenced bytes, exact capture terminal admission, command/environment/seed,
candidate/dependency/source-freeze bindings, device mapping, parent launch/wait
identity and actual exit/signal/time, complete sealed inventories, and terminal
precedence. It checks P3 raw observation/policy/runtime/source linkage, imports,
roles, actual full environments, complete starts/ends, controller/worker ancestry,
replacement/down/configure links, role limits and nonoverlapping PID reuse.
It compares actual collection/report membership and per-case setup/call/teardown
phases rather than reading pytest log counts. Skips, xfail, xpass, missing phases,
collection-only output and hidden reports cannot satisfy required cases.

The finite built-in `p4-common-v1` validates exactly process-custody, source-freeze
and required-cases against accepted contracts, a parsed closed witness-schema
identifier, and actual case/process/source observations. An external root-authored
inventory pins exact verifier/protocol/contracts/schema bytes **after** verifier
freeze and independent review; its reference is supplied in the exact authorized
spec's job prerequisites. It never dispatches executable paths, imports provided
modules or accepts an adjacent file's verdict. Validation receipts contain the
verifier's actual PID/PPID/Linux start token/host/boot and UTC observations.
Synthetic fixture inventories exercise this behavior; they are not root adoption.

Successful, failed, interrupted, refused, unrun and completed-unverified terminal
classifications remain distinct. Missing process completion/end yields explicit
unqualified terminal evidence, with no invented witness. Invalid references or
contradictory observations refuse. Receipts and their component directory are
exclusive, including concurrent-write tests; failures and partial outputs remain.

The adopted P0 receipt requires every obligation satisfied before its aggregate
custody/hardware may be satisfied. Root approved preserving that invariant plus
a private closed component-classification receipt. Thus common source/process
custody can independently satisfy while a required P5/hardware obligation remains
unrun/unsatisfied; the P0 aggregate stays unsatisfied with an explicit explanatory
reason. A CUDA-profile job's CPU common proof never satisfies actual device work.

P5 strict child/producer/RNG/fork-three-trial/phase-pair, all six actual CUDA groups
and application B/parent/recurrent validators are **unimplemented required
semantic dependencies**, never generic pass-through. Direct arbitrary child or
observer contexts remain refused until accepted owner delegation exists. Root
must reslice P4 before integrating P5's separately reviewed pure-data entrypoint;
there is no P5 import in this packet. Worker argv records actual execnet startup
and matches start/end; it is not falsely compared with controller job argv.
Worker mainargv binds across lifecycle/raw/context as the actual pytest sys.argv,
not interpreter/-m/job.argv. Full producer/toolchain/server integration remains owed.

Evidence lives in `evidence-management/hardware-verifier-p4/`. Every executed
source version was retained as non-executable `.txt` bytes with exact source
hashes and command/PID/UTC/exit records before later edits. Initial collection
passed at 30 cases and the missing verifier produced 30 failures. Preserved later
RED records cover common payload omission, parent exit/collection/report mutation,
worker down links, incomplete process termination, hardware-class separation,
PID reuse, seal disposition and witness-schema parsing. Early generic implementation
errors (primitive P0 validator misuse), capture-seal interface reconciliation and
lint failures are retained, not relabeled as feature failures. No overlapping
selections are added: **the final observation is one 73-case pass**.

The final execution source snapshots/log/argv/PID/times/exits are
`green-final-v4/{pytest,ruff,black}.{json,log}`. Final fixture artifacts and recent
RED fixtures are explicitly retained under their attempt directories. Earlier
synthetic temporary payload directories used pytest's default temporary retention;
those payloads were not separately frozen, while their exact test/verifier source,
failure output and process records are retained. No claim of complete earlier
fixture-directory retention is made.

Preflight confirmed existing Python3.13.5, pytest origin in the existing venv,
five affinity CPUs, cgroup quota400000/100000 and memory17179869184. Only this packet
was collected/run with application conftest disabled, plugin autoload disabled and
pytest-cov explicitly loaded for --no-cov. No APP/Torch/CUDA/server execution,
installation, Git/index write, source checkout/copy, branch/worktree creation,
deployment, remote access or deletion was performed. No self-adoption is claimed.
