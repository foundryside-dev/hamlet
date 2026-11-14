# BAC runner handoff — pending hardware availability

John expects a server with 16 workers and CUDA later this evening. Access and
hardware have not yet been verified. Continue authorized CPU work meanwhile.
This is an execution handoff, not a qualification result or a scope change.

## Admission before costly runs

- Use the existing authorized checkout and exact integration candidate. Do not
  infer permission for new branches, worktrees, source copies or deployments.
- Verify the remote commit/tree and local source hashes; check for local changes.
  Every controller, test worker and subprocess must identify that same candidate.
- Measure actual CPU quota/affinity, RAM, GPU model/count/VRAM, CUDA driver and
  PyTorch capability, dependencies, and competing workload before choosing jobs.
- Verify collection/imports and the causal fixture controls before broad runs.
- Use the available workers for independent selections with distinct output paths.
  Isolate process-global poison tests. Bound GPU concurrency using actual memory
  and shared-device constraints; do not assume 16 concurrent GPU jobs are safe.

## Required evidence

Run the still-open CUDA cases, supported slow/hardware and end-to-end acceptance
scenarios from the current ledger against the qualified candidate. Preserve the
finite accepted learning matrix, provider/scope coverage and checkpoint/replay
obligations. Do not substitute unit counts or skipped CUDA tests for behavior.

Retain source/process identity, command, seed, hardware profile, exit status,
assertion outcome and immutable output for each attempt. Publish new exact bytes
and verified existing references under docs/remediation/bac/EVIDENCE-PROCESS.md.
Report unsupported or blocked checks explicitly. Hardware availability alone
closes no package, requirement or final acceptance gate.
