# P1/P2 allocation and CPU-bound private addendum v2

Supersedes the resource/path paragraphs of private-payload-contract-proposal-v2.
P0 additions remain exactly the independent review v1 list; no extra P0 fields.
All payloads are closed/current only. Root's out-of-band authorization applies to
exact source-grant bytes and their subordinate referenced contracts; it is not
inferred from authority strings, matching hashes or samples. P1 owns validation;
P2 independently rechecks bindings and enforces reservations/leases.

`bac-hardware-source-grant-v1` gains required `allocation_grant: reference` and
`cpu_reservation_evidence: [reference]` (unique exact accepted role-bound inventory).
Existing head/tree/import roots/inputs/time/barrier fields remain exact.

`bac-hardware-resource-allocation-v1` exact fields:

- schema (literal above), allocation_id:id, pool_id:id, host:text, boot_id:text,
  lease_root:path, capacity:P0 budget, overhead:P0 budget,
  partition_basis:enum(exclusive-pool,root-proven-disjoint),
  partition_evidence:[reference] (0 for exclusive-pool, 1 for root-proven-disjoint),
  authorized_cpu_ids:[uint] (nonempty, unique), authorized_devices:[text] (unique),
  start:UTC, end:UTC|null, authority:text, no_writer_barrier:true.

A shared stable lease_root is root-owned/no-writer and disjoint in both directions
from source/output/scratch/capture roots. host/boot must equal actual discovery.
Actual capture/discovery/runner/job affinity must exactly equal authorized_cpu_ids
(set comparison). Refuse any mismatch before work; these tools do not implicitly
expand or restrict affinity. Actual inherited affinity is reobserved after spawn.
Only those CPUs contribute to measured capacity. Allocation
capacity caps observations; admitted budget is max(0,min(measured available,
allocation capacity) - request reserve - allocation overhead), per dimension.
Overhead explicitly accounts for runner/capture/discovery/controller/log retention;
unknown overhead refuses rather than inventing zero. Output, capture and scratch
must share the measured filesystem/capacity pool; P1 refuses unsupported separate
pools. The resource grant bounds root-authorized usage, not physical exclusivity
against arbitrary noncooperating processes.

One runner holds an exclusive allocation lease throughout its active attempt.
exclusive-pool additionally acquires its canonical pool-wide exclusive lease;
root-proven-disjoint acquires a shared lease on that same canonical pool lock,
so exclusive and partitioned claims cannot coexist. root-proven-disjoint requires the exact root-authorized partition payload below.
Every allocation and every pool on the same host uses one identical root-authorized
lease_root; host-wide timing/physical-parent GPU/RNG keys are shared across pools. Timing leases are
host-wide, GPU leases physical-parent-wide and RNG leases domain-wide, not narrowed
by allocation_id. Multi-device leases use stable ordering. Shared timing leases
for ordinary jobs exclude host-exclusive timing jobs. Source/namespace no-writer
custody must cover capture through all final required witnesses; inode drift fails.

`bac-hardware-capacity-partition-v1` exact fields: schema, pool_id:id, host:text,
boot_id:text, lease_root:path, pool_capacity:budget, allocations:[{allocation_id:id,
capacity:budget, authorized_cpu_ids:[uint], authorized_devices:[text]}], start:UTC,
end:UTC|null, authority:text. IDs, CPU sets and device UUIDs are pairwise disjoint;
capacities summed across rows cannot exceed pool_capacity. The current allocation
must match exactly one row. All cooperating allocations must bind this same exact
root-authorized partition reference; independent self-issued pool aliases are
outside authorized scope. Root owns actual full pool coverage and exclusivity from
unlisted allocations; P1/P2 cannot establish that external authorization by hash.

`bac-hardware-cpu-bound-v1` exact fields: schema, basis:enum(accepted-case-contract,
measured-bound), role_id:id, role:P0 role enum, observer:P0 observer enum, intra_op:1, inter_op:positive-int,
debug:bool, torch_policy:P0 role torch_policy enum, cuda_policy:P0 role cuda_policy enum, peak_cpu_slots:positive-int,
argv:[text], environment:env, required_cases:[text], head:git-id, tree:git-id,
inputs:[reference], justification:[reference] (nonempty), authority:text,
bound_statement:text. Cases and inputs are nonempty and unique. All private payload fields inherit
P0 exact types/enums where named; grants/partition times are ordered and must be
active at every use. All role/config/argv/env/case/source fields equal the sealed
job/candidate. inputs exactly match flattened candidate inventory. Bound reference
must occur in source grant's exact accepted cpu_reservation_evidence inventory;
no opaque unaccepted measured sample can authorize a bound. Root authorizes the
upper-bound justification for that complete workload, never merely a point sample.

Job CPU reservation is at least sum((count+replacement_limit)*peak_cpu_slots).
CPU/RAM admission uses the N largest simultaneous job reservations. Scratch bytes
and inodes charge every retained job plus the overhead already deducted above.
P2 never releases retained scratch simply because a process finished. No assumed
worker count, idle inter-op pool width or implicit default controls reservations.

P0 request carries explicit attempt_id and lease_root; spec copies both exactly.
Fixed layout is output_root/attempt_id/job_id and scratch_root/attempt_id/job_id.
P1 capture destination is separate and exclusive. P2 exclusively creates both
attempt directories. Environment/argv/seed contents are retained exactly; role
CPU bound controls declared concurrency without changing one-thread custody.
