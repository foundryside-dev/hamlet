# Native curriculum and persistent VFS staging

Implementation owner `/root/pw04_native_aux_state`. Five-body inventory: `curriculum/base.py`, `curriculum/adversarial.py`, `curriculum/static.py`, `vfs/registry.py`, and `test_native_aux_state.py`. No other implementation/test bodies opened. No runtime, imports, Git, branches, worktrees, execution copies or delegation performed.

The existing StaticCurriculum inherits CompletionCurriculum. Its ordinary `load_state` deep-copies and validates the full current state, then assigns the owned state, new owner token and empty transition-event list. Native preparation must own those publication objects before the BANK cut; installation must preserve the actual registered curriculum object and invalidate prior prepared completion state as ordinary loading does.

The existing VFS persistent setter validates every ID, shape, dtype and world reference before writing. Arena-backed storage is copied into its existing view; nonarena storage is cloned and rebound. Native preparation must validate the same semantics, own target-device tensors, retain actual arena views and pre-own nonarena replacement tensors. Final publication preserves registry/arena identity and performs no payload clone or device conversion. Genuine current domain/device invocation surrounds tensor preparation and publication, with terminal treatment of uncertain publication/completion.

Proposed APIs agreed with the native POP/runner owner:

- `curriculum.prepare_native_state(state, *, parent_plan)`
- `curriculum.install_native_state(*, prepared, parent_plan, attempt, restored)`
- `registry.prepare_native_persistent_state(state, *, env, parent_plan)`
- `registry.install_native_persistent_state(*, prepared, env, parent_plan, attempt, restored)`

Each returned handle is source-issued owned data, not operation authority. Real POP plan validation authenticates the exact registered curriculum or receiving ENV. The registry additionally checks that the ENV's actual `vfs_registry` is itself. C finalizer permission is checked against the genuine curriculum role or exact receiving ENV; the registry is never mislabeled as a population role. Prepared data is one-use, process/thread/receiver/revision bound and cannot carry stale RNG authority across BANK work.

Initial seven RED tests are authored and frozen; root execution is pending. Four exercise genuine standalone constructors and refusal of foreign handles/parent authority. Three use the supplied actual ParentFixture recipe and a genuine native POP plan for staging/refusal, without faking a successful C finalizer. Native end-to-end publication, populated persistent arena/nonarena content and continued learning remain required integration evidence. Empty fixture transport does not establish nonempty VFS restoration. No production implementation or passing qualification is claimed at this point.

Source-supplied external facts: root supplied the actual ParentFixture recipe and VariableDef fields; native POP owner confirmed exact plan ownership extension for curriculum/ENV; native RNG owner supplied actual admission/register/enroll/device_invocation/completion/poison behavior from its inspected core. Those external implementation bodies were not added to this agent's source inventory.

## Implemented source awaiting root execution

R163 root observed four intended missing-API failures; the three actual-POP fixtures stopped at a separate POP RNG reentry prerequisite. Root retained those failures and authorized implementation after diagnosing that prerequisite; the native POP owner reports its causal repair. No evidence is relabeled as a successful auxiliary-state test.

The agreed APIs now exist. `CurriculumManager` declares them; `CompletionCurriculum` implements both static and adversarial cases. Native curriculum input is recursively copied from ordinary portable primitive/container types, then the existing semantic validator checks it. A weak-key private record binds the actual plan (weak reference), process/thread, current state identity, owner token, generation and configuration; it owns the replacement state, replacement owner token and empty transition list. Installation checks actual plan and C finalizer, consumes once, then assignment-publishes into the same registered curriculum object.

The registry's preparation authenticates the actual ENV and verifies `env.vfs_registry is self`. Exact ordinary Tensor transport refuses per-instance overrides. Before any GPU copying, real domain admission resolves the source/destination CUDA inventory and registers or enrolls the registry's own participant. A genuine prepare invocation validates shape/dtype/reference semantics and owns target-device payload tensors. Private state records retain weak ENV/plan references, process/thread, registry revision, schema, storage identities/versions and arena identities. The genuine fixed finalizer uses actual ENV authority and a new registry install invocation. Arena-backed values copy into retained views; nonarena values use already-owned replacement storage, matching the existing ordinary setter's ownership behavior without finalizer cloning. Possible publication failure poisons the actual domain and rethrows; actual core completion remains authoritative. No RNG token survives staging.

Source inventory before root formatting: base88 + adversarial610 + static64 + registry1017 + tests94 = 1,873 lines, five bodies. Tests remain the seven authored cases; they do not establish successful actual C finalization or populated persistent storage. Root owns formatting, exact candidate capture, execution, independent verification and publication. Source is frozen for those checks. Native runner integration and applicable CUDA proof remain open.

## Independent P2 repairs awaiting R166

Independent Astra review identified two native VFS transport defects: matching sparse COO tensor payload could pass preparation and fail at the later dense arena copy, and nonexact string keys could invoke user-defined equality/hash during validation. Root R165 (`b98f9d72485851a58cfb9f406e7c3ae658c835f7`) observed both intended RED failures with custody PASS: sparse preparation did not raise, and the key equality callback executed.

The native preparation now checks exact ordinary string keys before constructing sets or performing key lookup, and requires ordinary strided tensors before any admitted materialization. Both failures remain represented by regression tests. A new positive control uses a real compiled authored config containing a persistent float scalar and persistent bool, then a genuine POP plan; it stages nonempty arena/nonarena payloads without publication and refuses a fabricated finalizer. No registered ENV/registry is replaced in the fixture. Only authored config data is copied into pytest temporary storage, never code or a checkout.

Current inventory before root formatting is five bodies / 1,992 lines: base88, adversarial610, static64, registry1026, tests204. Ten tests are authored. Root execution of the fixed candidate and the independent fixed-source review remain pending; actual successful native finalizer publication, input ownership through that publication, continued learning and CUDA remain required evidence.

## Completed curriculum tensor history repair

Root R166 observed both real runner acceptance tests reach fresh restore and fail because the native curriculum portable-copy gate rejected genuine completed metrics' Tensor leaves (`final_observation` / `final_meters`). This restriction was introduced by the new preparation code; the history is required and must not be dropped. The same R166 native component attempt passed 77 cases with custody PASS, demonstrating that those components did not establish this completed-runner path.

The narrow repair preserves the complete current history, permits only exact ordinary strided CPU/CUDA Tensor leaves without per-instance overrides, and clones them with unbound Tensor operations. A pure closed-container inventory determines every touched CUDA index before tensor work. The curriculum enrolls its own participant before the BANK cut and performs both copying and existing semantic validation inside a genuine prepare device invocation; real device completion must succeed before returning the handle. Each leaf is rechecked against that admitted inventory before cloning. The existing one-use native plan/C finalizer checks and assignment-only publication remain unchanged. Source is frozen for root's real-runner rerun; no new passing result is claimed.

Changed production body before root formatting: `curriculum/adversarial.py`, 652 lines, SHA256 `22f227d8856dbb524c62416b8945fe94625be3a5cb206d33877d8da734a94897`. The five-body cumulative scope remains below 5,000 lines. No extra implementation body, Git, runtime, checkout copy or branch was used.
