# P1 pinned real discovery backend contract v1

Actual probe implementation is mandatory; qualification executes only stubbed
synthetic tests. Actual hardware execution remains UNRUN. No new P0 fields.

Environment dependency inventory is exact. Ordinary entries name Python installed
distributions and bind their unique dist-info/METADATA file and observed version.
Two reserved exact names specialize CUDA discovery: `torch` binds the actual
`torch/__init__.py` file in its installed distribution and actual distribution
version; `nvidia-smi` binds the explicit authorized driver-query executable and its
observed NVIDIA-SMI version from `--version`. CPU profiles need no driver entry.
CUDA profiles require both. Duplicate, missing, unknown origin or version mismatch
refuses. Torch import origin is checked against the pinned reference before import
and rechecked against actual module.__file__ after import; actual torch.__version__
and torch.version.cuda separately bind environment torch_build/cuda_runtime facts.
No application or unrelated Python package is imported for dependency discovery.

The existing private discovery payload gains `torch_origin: reference|null`.
Each raw `commands` entry has exactly argv:[text], executable:reference,
identity:P0 identity|null, start:UTC, end:UTC, exit_code:int, stdout:string,
stderr:string, errors:[text]. executable is pinned before/after command execution.
Parent observes actual spawned PID/PPID/proc start token/host/boot before reaping;
missing identity is retained and refuses admission. No shell/default executable.

Only these fixed nvidia-smi argv tails are supported:

- `--version`
- `--query-gpu=index,uuid,name,memory.total,driver_version,mig.mode.current`
  `--format=csv,noheader,nounits`
- `--query-compute-apps=gpu_uuid,pid,process_name`
  `--format=csv,noheader,nounits`
- `topo -m` (optional topology observation; unsupported topology is explicit)

CSV parsing uses exact column counts, unique indices/UUIDs, exact numeric types,
nonempty model/driver and finite positive MiB memory. Only known Disabled MIG mode
(or explicit driver N/A whole-device mode) is supported; enabled/unknown MIG,
unknown UUIDs and unproved shared parents refuse. Requested numeric or full GPU
UUID visibility is mapped against this actual driver inventory, then compared to
Torch logical enumeration and actual per-device UUID/model/VRAM observations.
Torch UUID must be an exact string or 16-byte UUID; other representations refuse.
Driver total memory is an upper bound on observed Torch total memory. No guessed
physical identity, inferred GPU count or visibility expansion is accepted.

Only the separate pinned discovery process imports Torch/queries CUDA. CPU profile
never imports Torch or calls the driver executable. Capture binds actual discovery
PID/PPID/start/host/boot/argv/interpreter/cwd/profile/TMPDIR/visibility/time and raw
stdout/exit; rereads all source/dependency/tool references afterward. Later test
processes remain separate and uninitialized. All unavailable or unsupported
required facts produce retained refusal and no normalized runnable spec.
