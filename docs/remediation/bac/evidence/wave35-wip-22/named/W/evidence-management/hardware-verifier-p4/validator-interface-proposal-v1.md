# P4 case validator interface proposal v1 — ROOT DECISION REQUIRED

No executable dispatch from spec/reference paths. Initial authorized inventory is
empty: all obligation validators remain unimplemented/unrun or unsatisfied even
when generic transport, process, collection and source checks pass. Generic checks
never create case validator receipts or satisfy P5 obligations.

Before any supported validator is integrated, root must authorize a finite entry:
{validator_id, obligation_kinds, exact validator source reference, dependency
references, contract references, witness_schema references, accepted evidence
classes, entrypoint interface, independent qualification reference}. The inventory
must be a fixed root-pinned implementation dependency, not supplied by an attempt.
A future separate bounded packet may expose a pure data validation entrypoint;
P4 must not import arbitrary modules, exec code, or shell out based on references.

Proposed receipt envelope exact fields:
schema="bac-hardware-case-validator-receipt-v1", validator_id, validator(reference),
dependencies([reference]), spec(reference), job_id, obligation_id,
contract(reference), witness_schema(reference), evidence_class, cases([text]),
evidence([obligation-evidence reference]), payloads([reference]),
producer_processes([P0 process-start reference]), related_attempts([reference]),
validation_process(P0 identity), start(UTC), end(UTC),
verdict="satisfied"|"unsatisfied"|"unrun", reasons([text]).

Every set/list has exact required membership and no duplicates; all evidence must
cross-bind attempt/job/spec/contract/validator/case and actual producer lifecycle;
validation process/start/end must be observed by trusted entrypoint, not a field
assertion supplied by the attempt. P4 recomputes verdict from finite authorized
validator on parsed pinned observations and emits its own immutable receipt; it
never accepts verdict from an adjacent file merely because hashes match.
P5 must validate the existing strict child/RNG/fork/phase semantics, and real CUDA
owners their actual work/device/storage/event/RNG transitions. CPU/mock/device
presence cannot satisfy real CUDA. Missing witness schema, unknown/unimplemented
validator, absent observations or failed validation never become satisfaction.

No generic PASS route is implemented until concrete root inventory and supported
bounded semantic implementation are reviewed. This proposal does not authorize
P5/source body reads, arbitrary dispatch, APP imports, or real hardware runs.
