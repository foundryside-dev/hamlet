# Allocation/CPU private addendum — targeted independent review

2026-11-14T06:06:28.382506+00:00. **PASS for exact v2 metadata contract**, subject to implementation and independent synthetic verification. No remaining concrete P1/P2 SPEC or QUALITY finding in this bounded contract review. This does not approve consumer code or actual hardware execution.

Reviewed root's accepted amendment decision, private addendum v1, and the owners' v2 resolution. No source edits, new tool/application body reads, imports or runtime operations. Existing P0 reviews and historical frozen bytes remain unchanged.

Three v1 gaps were sent once to both P1/P2 owners and resolved in v2:

1. Partitioned runners now hold the shared canonical pool lock; exclusive-pool runners hold that same lock exclusively. The per-allocation exclusive lease permits one active runner, while admitted jobs within it remain parallel. Exclusive and partitioned claims therefore conflict through the same lock, rather than unrelated lock names.
2. Every pool/allocation on a host shares the identical root-authorized lease_root. Host timing, physical-parent GPU and RNG domains remain shared across pools. Ordinary jobs participate in shared host timing ownership; host-exclusive timing work conflicts with them. Stable namespace custody/inode checks remain mandatory.
3. Actual capture/discovery/runner/job affinity must equal the root-authorized CPU set, reobserved after spawn; mismatch refuses. Capacity arithmetic alone cannot enforce a disjoint CPU partition. The tools make no implicit affinity expansion/restriction. Root must arrange authorized affinity before use; later observations and execution controls must preserve this exact contract.

V2 also closes CPU-bound role/config enums under P0 types, requires unique nonempty cases/input inventory and ordered active grant/partition intervals. Per-instance peak_cpu_slots is justified by a root-accepted exact workload bound, bound to role/config/argv/environment/cases/head/tree/inputs and accepted source-grant inventory. Inter-op width and idle OS thread count never substitute for an active CPU bound. Unknown/unaccepted bounds refuse. Job reservation includes count plus all permitted replacement overlap; orchestration/storage overhead is explicit.

The source grant remains acyclic: explicit source identities and input references, not a candidate self-reference. Its allocation and CPU-bound references have out-of-band root authorization; authority text/hashes are not cryptographic proof. Actual host/boot/resource/source and active source-freeze bindings must be checked by both consumers. Partition rows are disjoint and capacity sums bounded; root owns coverage and exclusion of unauthorized aliases/unlisted allocations.

CPU/RAM account for admitted simultaneous jobs. All retained scratch bytes/inodes remain charged, with separate explicit overhead already deducted from available allocation capacity. Output/capture/scratch must occupy the measured supported pool. Admission caps actual measurements by authorized capacity before reserves/overhead; a reference alone cannot supply an observation. Unknown overhead or unsupported separate pools refuse.

No extra P0 fields are needed beyond the already-approved consolidated amendment. Root's hold on P0 edits remains in force until WIP21 publication, followed by a linked revision, red/green synthetic tests and independent review. P1/P2 implementation must validate and enforce this metadata exactly; this PASS does not waive their source/test review or P3–P5 behavioral obligations. Hardware remains UNRUN.

Exact reviewed metadata identities:

- `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-protocol-p0/root-interface-amendment-decision-v1.json`: SHA-256 `5b23d1616de3b2857026f315bbc4ad6b17a4017ad2d766ad78bf08d98d21bb4c`.
- `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-admission-p1/allocation-cpu-private-addendum-proposal-v1.md`: SHA-256 `4910f23f041a5bc721872d915450849d7871b60202aaea58e1a20c2a06dbf970`.
- `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-admission-p1/allocation-cpu-private-addendum-proposal-v2.md`: SHA-256 `1509c1e66049b36b6917890979f6bc24fa7aa5a2f3e71a84325b25d28f542fc2`.
