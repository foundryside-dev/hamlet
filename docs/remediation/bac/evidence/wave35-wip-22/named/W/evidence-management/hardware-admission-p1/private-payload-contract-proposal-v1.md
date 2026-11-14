# P1 private payload contract proposal v1

Finite current-only payloads, not changes to P0. All objects reject unknown fields,
wrong exact types, duplicates, unsafe paths and nonfinite numbers. All references
use P0 path/bytes/sha256. A structural pass is never observation or authority.

1. Candidate.registry references UTF-8 `git worktree list --porcelain` exact stdout.
   Capture issues that read-only command under the authorized root and compares
   exact bytes. No subprocess shell, Git mutation, tree writing or staging.
2. Candidate.availability references JSON with exact fields:
   `{schema: "bac-hardware-availability-v1", worktrees: [{path: absolute path,
   directory_exists: bool}]}`. Paths/order derive exclusively from the observed
   porcelain `worktree ` lines; existence comes from current filesystem metadata.
3. source-freeze.grant references an out-of-band root-authored JSON declaration:
   `{schema: "bac-hardware-source-grant-v1", authorized_root: path, head: git-id,
   tree: git-id, import_roots: [path], inputs: [reference], start: UTC,
   end: UTC|null, no_writer_barrier: true, includes_untracked: true,
   authority: nonempty text}`. Inputs are the exact flattened candidate inventory,
   unique across categories. Root authorizes this grant reference out of band;
   its hash does not authenticate its author. Capture checks exact candidate
   bindings and active start/end at both source samples. An open end means root
   still maintains the barrier, not that capture prevents writes. P2/P3 must
   recheck through their last witness. A candidate reference inside the grant
   would create a reference cycle, so head/tree/import/input bindings are explicit.
4. Private discovery JSON (`bac-hardware-discovery-v1`) has exact fields: schema,
   profile(cpu|cuda), identity(P0 identity), at(UTC), argv([text]), interpreter(path),
   cwd(path), inherited_visibility(string|null), effective_visibility(string),
   tmpdir(path), cgroup_root(path), cgroup_leaf(path), ancestry_complete(bool),
   cgroups([{path,cpu_max:string|null,cpuset:string|null,memory_max:string|null,
   memory_current:string|null}]), affinity([uint]|null), meminfo(string|null),
   scratch_free_bytes(uint|null), scratch_free_inodes(uint|null),
   cpu_topology/numa_topology/gpu_topology/torch_build/cuda_runtime/driver(string|null),
   competing_workloads([text]|null), devices([P0 device minus mapping_provenance]),
   probe_errors([text]), commands([{argv:[text],exit_code:int,stdout:string,stderr:string}]).
   Observation references are attached to derived P0 facts; nested parent memory
   headroom remains visible in raw observations. Missing controllers, hidden
   ancestors, unsupported mapping, nonempty competing GPU workload and failed
   required probes refuse. Synthetic fixtures have no actual-hardware standing.

Derived budget: floor(min(affinity∩all cpusets, each finite quota/period)) minus
CPU reserve; min(host MemAvailable, each finite ancestor limit minus its current
usage) minus RAM reserve; scratch available bytes/inodes minus reserves. Refuse
if minima or the sum of the N largest job budgets for any resource exceeds that
budget. Each job reserves all role counts plus replacement_limit. Keep intra-op=1;
inter-op configuration alone is not a measured extra concurrency reservation.

Normalized spec uses identical admitted_budget; jobs preserve argv/env/seeds and
CUDA visibility. CUDA currently requires an exact whole-device mapping in every
CUDA job (logical index, UUID, model, VRAM, parent); MIG is explicitly unsupported
and refused. CPU jobs hide CUDA. requested visibility must equal inherited CUDA
visibility when inherited is set; no implicit expansion. Device UUIDs must be
within authorization and both Torch enumeration and driver inventory must agree.

The request has no attempt_id field. Derive one common ID from the first relative
component of every job.output under output_root and job.scratch under scratch_root.
Require job directories strictly beneath those attempt directories. P2 exclusively
creates those directories. P1's capture destination is separate, exclusive, and
outside source/output/scratch; it holds capture start, raw discovery, admission,
normalized spec (only when admitted), source samples and capture result. Refusals
retain reasons and observations and never emit a runnable spec.
