# P4 common validator interface v3 — root-approved additive correction

Read proposal-v2 for the finite p4-common-v1 dispatch and exact inventory/common
payload/causal validator receipt contracts. Root approves these within P4.

Common CPU/cpu-standin evidence can prove common custody on a CUDA-profile job;
it never satisfies real-CUDA work or any P5/application obligation. The common
validator does not restrict the enclosing profile to CPU.

Adopted P0 receipt semantic invariant requires every obligation satisfied whenever
custody or hardware is satisfied. Preserve that conservative aggregate gate and
frozen P0 bytes. When common custody passes but a required P5/hardware/application
obligation is unrun/unsatisfied, P0 custody remains unsatisfied with explicit reason
"aggregate obligation gate incomplete; common source/process custody independently
satisfied". This does not report observed source failure or overall qualification.

Add a private closed component receipt, included in final P0 receipt.inventory:
schema=bac-hardware-component-classification-v1, spec(ref), job_id,
common_custody=satisfied|unsatisfied|unrun,
strict_custody=satisfied|unsatisfied|unrun|not-required,
test_outcome=P0 disposition, hardware=satisfied|unsatisfied|unrun,
overall=satisfied|incomplete, reasons([text]), validator_receipts([ref]).
Common custody requires satisfied process-custody/source-freeze/required-cases.
Strict custody kinds: strict-child-core, strict-child-producer, rng-custody,
fork-three-trials, phase-pair. Unimplemented strict requirements remain unrun or
unsatisfied; hardware is independent and actual CUDA work cannot be inferred.
Actual P4 self-identity and start/end observation remain in each common validator
receipt. Source snapshots and root frozen inventory precede exact spec execution.
