# CUDA core issuing-PID guard and transparent probe facts

2026-11-13. Source-owner prose only. Retained core is371 lines, SHA256 `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`; no additional source body, runtime/import, source/test edit, Git/index action, copy or delegation. Tests835/b0f9e154 remain frozen. Read proposed `T18e-R0-CUDA-CORE-CHILD-QUALIFICATION-PROTOCOL.md`; genuine fork execution remains UNRUN.

## Exact existing refusal and issuing state

`AmbientRNGDomain.__init__` stores `self._pid = os.getpid()` on construction of the sole module-owned `_PROCESS_DOMAIN`. This is actual process identity, not a participant identifier, thread identifier, configurable value or test-supplied identity.

The first branch of `_usable()` compares that unchanged `_pid` with actual `os.getpid()`. Mismatch raises **exactly built-in `RuntimeError`**, with exact text **`RNG custody cannot be inherited by another process`**. It does not add a cause or mutate domain state in that branch. The later poison branch has a different diagnostic (`Ambient RNG domain is poisoned after failed restoration`) and must not count as PID proof. Neither a missing API, unrelated RuntimeError, lineage/thread refusal, fixture failure nor timeout is an acceptable witness.

Current `_usable()` itself has no lock acquisition or CUDA access. Current public `register`, `unregister`, `operation`, `current_token` and `validate_current` enter `with self._lock` before calling `_usable()`; thus **the original core does not establish pre-lock inherited-process rejection for those public paths**. `status()` does not call `_usable()` and is diagnostics, not an inherited-PID guard. `_authenticate()` checks operation identity/thread/generation rather than PID and is not a substitute.

No `RNGAdmission`, `LocalCUDAGate`, `admission`, `local_cuda_access` or their methods exist in this source. Their required implementation must preserve the exact built-in RuntimeError/text above while checking actual PID **before lock acquisition and before scope/thread/contract/CUDA work** at each proposed inherited entrypoint. This is an intended new-gate requirement, not a claim that unimplemented methods already pass. The PID-only guard must be callable without poison rejection so a valid READY qualified local gate remains expressible after common poison; that does not relax PID checking.

## Plain state observation

Existing scalar lifecycle slots are `_pid`, `_generation`, `_revision`, `_currency`, `_ambient_revision` and `_poison`. Capture their values directly before each fork action and compare afterward; compare `_poison` by object identity to preserve first cause. Existing `_members`, `_operations` and `_tokens` are the actual membership/operation/token registries; their direct lengths/identity contents can supplement scalar observations without calling an API. `_local` is genuine `threading.local`; `_lock` is the actual `threading.RLock` constructed by this domain. `_retired` is the weak-retirement SimpleQueue; do not drain it in the guard grandchild.

`_cuda_ready` and gate registries/state do not yet exist in the current core. The tests propose `_cuda_ready` as the controlled runtime-readiness slot; future implementation must publish its actual gate registry/open-scope/thread/binding fields and update the finite state observation if names differ. Tests must not forge these fields or `_pid` to create a witness. Any counter created by a forwarding probe is observation, not domain issuing authority.

## Transparent actual-lock probe coverage

Every current acquisition of this domain lock is syntactically `with self._lock`; there is no cached alias, direct `.acquire()`, Condition path, `_acquire_restore` or owner lock inside this371-line domain body. A test-only wrapper installed around the **existing actual RLock**, before genuine gate entry, can observe current paths through `__enter__`/`__exit__` while delegating to the same RLock. If it also exposes `acquire`/`release`, count one actual acquisition attempt per delegated entry/acquire, avoiding double counting its own forwarding implementation. It must preserve real reentrancy/exclusion and any future ownership inspection by delegation, never return a fabricated ownership result.

This coverage statement applies to the retained source only. Final new-gate source must be checked for direct/cached raw-lock bypass, any added acquisition routes and when it checks PID. Its fork witness must demonstrate zero actual probe acquisition attempts in the grandchild; holding a real parent gate is not enough to infer that count. A new implementation that caches the raw RLock outside the probe would invalidate the observation and require correcting the fixture before acceptance.

The core currently never acquires an owner's private lock. The fixture owner has a real `threading.RLock`, available for an independent forwarding probe in the authored test. If that owner lock is not used by a particular guard path, report measured zero under the installed probe, not invented coverage. A separate finite forbidden-access CUDA seam must count any CUDA attribute access without invoking Torch/CUDA. Precreate device/error/action descriptors before fork; do not call Torch, NumPy, bootstrap, importlib, RNG snapshots, domain diagnostics or queue helpers inside the guard grandchild.

All exact fixed inherited actions in the proposed protocol must match the RuntimeError/text above and leave acquisition/CUDA/body counters zero plus state unchanged. The proposed ninth role, real OS ancestry, single-thread precondition and two sequential admission/local fork trials remain subject to consolidated test-fix authorization, independent protocol/source review and actual root execution.
