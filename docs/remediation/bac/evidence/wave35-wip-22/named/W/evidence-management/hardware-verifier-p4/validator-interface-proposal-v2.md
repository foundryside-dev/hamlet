# P4 finite common validator proposal v2 — ROOT DECISION REQUIRED

Finite built-in ID `p4-common-v1`; exact kinds process-custody, source-freeze,
required-cases; pure-data entrypoint internal `_common_validation(kind, checked)`.
No dispatch by file path, module name or supplied entrypoint. No imports/execution
of validator references. Other IDs/kinds remain unimplemented and unsatisfied/unrun.

Root writes external inventory AFTER final P4 source freeze (acyclic), then seals
its reference as one job.prerequisites entry in the exact root-authorized spec.
Exact schema `bac-hardware-validator-inventory-v1`, fields schema, authority,
validators. Each entry exact fields id, kinds, validator (exact P4 source ref),
dependencies (exact protocol ref), contracts (accepted case-contract refs),
witness_schemas (accepted schema refs), evidence_classes (exact [cpu,cpu-standin]).
No arbitrary inventory search: inspect only spec.job.prerequisites parsed JSON;
exactly zero or one inventory; malformed/duplicate inventory refuses. Zero means
unimplemented validators, never satisfaction. Root's exact-spec invocation and
no-writer custody authorize this dependency; text/hash alone cannot establish
root authorship. Unknown extra keys/IDs/kinds reject inventory. P5 and real CUDA
are not members of this common inventory.

P4 must parse every common contract and bind exact kind/cases/roles/class/minimum,
validator source, witness schema and inventory. Each required case must have exact
passing setup/call/teardown P3 reports, linked actual process-start identity and
lifecycle, source observations within freeze and delegated P3 runtime. Evidence
references must bind exact obligation/case/process. Built-in validation recomputes
common verdict, never trusts supplied payload/verdict. Dedicated payload exact
schema bac-hardware-common-observation-v1 with fields schema, kind, case_id,
reports([P3 report refs]), processes([actual start/end refs]),
source_witnesses([P0 source-witness refs]). Exact case report membership and exact
process/source sets required. Empty generic envelope cannot satisfy these.

P4 emits per-obligation immutable validator receipt to destination-derived
exclusive directory, then final P0 receipt. Closed proposed v1 receipt envelope
retained with validator_id=p4-common-v1, source/dependencies/spec/job/obligation/
contract/schema/class/cases/evidence/payload/process/related_attempt links.
Observed validation_process from actual /proc/self/stat+pid/ppid/host/boot, start/
end UTC; only actual passed common checks produce satisfied verdict. Final receipt
still custody unsatisfied unless ALL required obligations satisfy; hardware unrun
on CPU and unsatisfied/unrun on CUDA with unimplemented hardware validators.

Receipt publication reserves destination exclusively and preserves incomplete
artifacts/failures; second verify requires a new destination. No P5 or hardware
acceptance is implied. This is a proposal, not source/validator self-adoption.
