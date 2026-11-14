# C1 core completion seam — root source capsule

2026-11-14. Root inspected rng_custody.py (1195 lines), SHA256
6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8.
Source-only; no core edit or new execution claimed. Writer consumes capsule,
not another source body within its four-body packet.

AmbientRNGDomain._complete is staticmethod _complete(devices: tuple[int, ...])
-> None (line525). It only loops calling torch.cuda.synchronize(index). Empty
tuple performs zero CUDA attribute lookups. _finish(operation,devices,failures,
completion) always calls self._complete(devices), including empty tuple. A
raised BaseException goes through real self.poison(operation=operation,error=error)
and is appended to failures. Only successful completion sets the own completion
record failed_completion=False. Tests must not mutate poison or outcome records.

Nested _operation finally calls _finish(active,devices,failures,completion);
outer finally uses tuple(sorted(record.devices)) accumulated union. Both run
inside common lock. _exit_invocation seals exited in finally and releases its
execution references despite raised completion. _raise preserves a single real
error object, identity-deduplicates repeated same objects, and aggregates distinct
remaining errors in BaseExceptionGroup.

Permitted transparent CPU failure seam: retain actual domain._complete callable,
wrap it on that actual domain, call original(devices), record exact argument and
causal event, then raise chosen error at intended observed phase. Assert complete
expected schedule; do not guess BANK phase by ordinal when native phases may
intervene. Real begin_episode validator-failure can avoid native phases only if
actual producer ordering establishes that prefix. Copied-reward controls must
record nested phases. Do not wrap _finish or manufacture completion outcomes.
This tests CPU completion failure, never real CUDA qualification.

register(cuda_devices=(0,)) genuinely calls torch.cuda.is_initialized() and
device_count(); device_invocation rechecks nonempty initialized enrollment.
Empty CPU controls need no fake CUDA registration. Nonempty CPU instrumentation
must explicitly observe CUDA APIs/synchronize as a separate protocol-only seam;
actual hardware remains UNRUN. Never reset common poison or fabricate participants.

Existing node names observed as metadata, not newly reviewed test bodies:
test_existing_cpu_registration_and_completion_query_no_cuda,
test_device_invocation_nonempty_completion_matches_existing_operation,
test_device_invocation_nested_siblings_keep_lineage_and_receipts,
test_mixed_operation_completion_union in test_rng_cuda_admission.py.
Root owns fresh execution and any further CUDASeam helper supplier.
