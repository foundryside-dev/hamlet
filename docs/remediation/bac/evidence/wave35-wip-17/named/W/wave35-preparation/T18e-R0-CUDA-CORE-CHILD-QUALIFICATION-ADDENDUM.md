# CUDA core child qualification — finite protocol addendum

2026-11-13. Prose-only clarification of T18e-R0-CUDA-CORE-CHILD-QUALIFICATION-PROTOCOL.md (b9b90d05bc2abdf8f1c10fff9111f9a3e742a95c906543b7a5baa5e489341c37). Preserve that original proposal. This addendum resolves its supplied diagnostic, tenth mapping and admission calling convention; it does not claim implemented source, frozen final test bytes, verifier readiness or actual child execution.

Authority inputs, all public prose:

- PID-PROBE-FACTS: 114fab3a801f198db385f6a54b34fea6e5a9a4fc88baca9bfc41ed5676dd6de7.
- CHILD-PROTOCOL-REVIEW: f19ae10f27a57f1c4df868e6d8269dba6e66b2a768199c8ea73ef15f3fefc2f2.
- TESTS-FIX1-GRANT: 2078a7f89a4d730a1f2011b5d53df72221e59d850084c0aa842eeff57286a0bd.

All names above carry the T18e-R0-CUDA-CORE- prefix and .md suffix in this directory. No sixth implementation body was read; retained five-helper budget unchanged. No source/tool edits, imports, tests, runtime, Git/index action or delegation.

## Exact tenth ordinary spawn mapping

Keep the original eight ordinary mappings and ninth inherited-PID mapping unchanged. Add precisely:

| Field | Exact value |
|---|---|
| Job | cuda-core-local-completion-duplicate-parent |
| Node | tests/test_townlet/regressions/bac/test_rng_cuda_admission.py::test_isolated_poison_protocol[local_completion_duplicate_parent] |
| Case | local_completion_duplicate_parent |
| Role / Process.name | cuda_core_local_completion_duplicate_parent |
| Success message | cuda core local_completion_duplicate_parent fail closed |
| Target | cuda_core_child(queue, case), case exactly local_completion_duplicate_parent |

The target follows the existing ordinary-case target described in the author report; the final author CHILD-API must confirm the resulting frozen source. The job has the same exact -m pytest NODE --no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q arguments and one-controller CPU profile. No general case-prefix acceptance.

This case preserves the distinct-error controls and adds the same exception identity through body, multiple completion attempts and retained-poison unwinding under a genuine active parent. All synchronizations, unique final exception order and first cause must be observed. It uses the full ordinary qualified spawn identity/observation schemas, original bootstrap imports, actual Torch/intraop1/interop5/debug profile, two actual core/test imports and actual test-source hash. It is not a fork guard-only profile.

There are now ten top-level job mappings: nine ordinary/full-profile spawn cases including this addition, plus one full-profile spawn coordinator for inherited PID. The two admission/local fork grandchildren remain fixed nested trials of that coordinator, not extra top-level jobs or substitutions for the new repeated-error case.

## Exact inherited-PID refusal

Supplier source facts resolve the expected outcome: require type(error) is built-in RuntimeError and str(error) exactly RNG custody cannot be inherited by another process. The existing _usable mismatch branch supplies this diagnostic without locking, CUDA access, state mutation or added cause. The inherited domain's genuine _pid originates from constructor os.getpid(); never rewrite it. The poison diagnostic Ambient RNG domain is poisoned after failed restoration is different and cannot satisfy the control.

Do not accept subclasses, generic errors, missing methods, fixture/introspection errors, wrong-thread/scope/contract refusal, hangs or timeout as PID proof. The grandchild's actual PID must differ from unchanged inherited _pid, which must equal actual spawn-parent PID.

The original371-line public register/unregister/operation/current_token/validate_current paths lock before _usable; they do not prove pre-lock rejection. New admission/local entries and every tested inherited gate method must independently check PID before lock acquisition and before other scope/thread/contract/CUDA work. These gate APIs are not implemented in the supplied core. Source review and actual future execution must demonstrate their ordering; the existing diagnostic alone cannot qualify it. A PID-only authentication branch remains necessary so qualified READY post-poison local access is not incorrectly prohibited by a combined poison guard.

## Invocation and observation corrections

Admission trial calls inherited_gate.resolve_cuda(precreated_cuda_device) positionally. Local trial calls inherited_gate.resolve_cuda(device=precreated_cuda_device) by required keyword. The original admission keyword example is superseded, with no new keyword-only admission requirement.

Other calls remain enroll(participant=..., cuda_devices=()), report_failure(error=...), complete(cuda_devices=()), completion_failed() and the specified domain-entry keywords. Fresh context-manager rejection must be tested at actual __enter__, including complete entry; mere lazy context-manager construction proves nothing. Never exit/unwind an inherited parent gate in the fork grandchild.

Direct pre/post state observations use supplied existing scalar slots _pid, _generation, _revision, _currency, _ambient_revision, with _poison compared by object identity. Registry lengths/identity contents of _members/_operations/_tokens may supplement them without domain APIs. Do not call status or drain _retired. Future _cuda_ready/gate-registry/open-scope/thread/binding fields are not established by the original core: the implementation owner must publish their real state and extend observation where needed, without forging authority.

Current lock routes are exclusively with self._lock; no cached/direct/raw-acquire route exists in the supplier's retained371 body. A transparent probe wraps that same actual RLock before genuine gate entry, delegates ownership/reentrancy/exclusion, and counts each attempted underlying acquisition once. The fixture owner's real lock and forbidden CUDA-access seam must also be observed, with zero counts measured rather than assumed. The fixed test must permit required Python introspection without allowing actual CUDA access; the original NoCUDA __class__ fixture failure is not a PID failure.

Future new-gate source must be reviewed for cached/raw lock bypass and every new acquisition route. If it bypasses the probe, observation must be corrected before any pre-lock claim. No Torch/NumPy/CUDA call, importlib/bootstrap/queue helper, RNG snapshot or domain diagnostic may run in the guard grandchild. Keep the original actual /proc task-count1 precondition, two real forks, pipe/waitpid ancestry, exclusive child identity/parent observation, bounded owned cleanup and os._exit protocol unchanged.

## Final schema and handoff

Ordinary full-profile identity/observation shapes remain unchanged; tenth case adds only one exact finite configuration. Guard-only schema remains separate with explicit null Torch profile/reason, actual OS task count and inherited-module origin/file hashes. Its guard_results now require the exact built-in exception class and diagnostic above for every fixed action. No optional relaxation for missing observations, alternate errors, wrong roles/messages or fake inherited thread counts.

The final author CHILD-API after tests freeze must bind the actual complete test hash, ten names/targets, profile/schema and gate action map. That frozen capsule supersedes provisional835-line test identity for future qualification; preserve old bytes as historical evidence. Root's fix1 ceiling is test1800 + projected core1200 = two-body3000, below hard5000, superseding this protocol's prior test1200/two-body2400 planning limit. This changes no actor's retained source-body permissions.

Remaining gates are finite: review the actual fixed test/source probe, implement and review genuine gate ordering later, grant a separate verifier extension with strict synthetic negatives and independent review, then root executes source-qualified ordinary/fork evidence. Actual hardware and B6/package/programme acceptance remain open. No verifier work starts under this addendum.
