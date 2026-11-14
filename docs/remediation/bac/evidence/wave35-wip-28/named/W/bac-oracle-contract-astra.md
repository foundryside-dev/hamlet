# BAC oracle contract review and bounded decision

Preparation only. No producer/source/test changes, Git commands, runtime checks, branches, worktrees, or source copies were made. This is a new design record; it changes no prior hash-bound record. It does not authorize an implementation decision.

## Finding

The six reported oracle type failures expose two independent changes. Explicit per-side trace-driver artifacts can solve the historical interpreter/API mismatch without an application fallback. They cannot make the existing arbitrary-action, fixed-step experiment executable through the current manual physical protocol. The latter is a real capability decision, not a typing repair.

The current plan's three-file implementation scope is insufficient for the cross-version part: `harness.py` hardcodes the same new-tree driver path for both subprocesses. Rewriting that driver to import the current manual protocol will break historical interpreters that lack it. Merely preserving the self-containment prohibition on `townlet.oracle` imports does not solve absent current ENV APIs.

## Inspected source and exact contracts

Source-body budget charged at full file sizes even where only relevant regions were read: `driver.py` 202, `harness.py` 682, `manual_physical.py` 293, `vectorized_env.py` 3183, `trace_io.py` 354: five bodies, 4714 lines. No manual regression body was opened. AGENTS and the existing oracle plan and C API prose were also read. Root supplied the real LocalTemporalController/BANK activation fact; this review does not independently qualify its entire lifecycle.

* `driver.run_trace` promises integer scripts of exact `(steps, num_agents)` shape with every value in `[0, action_dim)`, stepped verbatim. Random mode draws one CPU `torch.randint(0, action_dim, ...)` per step. The loop always requests exactly `steps` vectors and records `steps + 1` observations.
* `harness.run_cell` constructs `new_src / townlet/oracle/driver.py` and passes that same path to both `run_side` calls. The selected code and pack roots differ through explicit subprocess inputs. Scripted mode records the old actions and replays them into the new side. A script that is legal on one side is not thereby legal on the other.
* `ENV.bind_manual_execution` (713 onward) requires the exact freshly bound population owner, no existing manual/exploration binding, an issued boundary authority, no bootstrap yet, and no retained custody scope.
* `ManualPhysicalSession._current` validates active phase, genuine accepted token, committed participation, authentic activation with this population owner, and current owned physical state. `_step` rejects an all-terminal vector (`not bool(active.any())`) and any illegal active-lane action (`not bool(legal.gather(1, actions[:, None]).flatten()[active].all())`). These are explicit refusals before physical work.
* `ENV.step` (1399 onward) requires the actual exploration/POP runtime binding and invokes its genuine prepared-vector claim callback. The shared private kernel is not an alternative public authority: a manual binding requires its issued decision and exact session claim. Calling it directly or fabricating a PreparedVectorStep would evade the contract.
* `ENV.activate_episode` (2896 onward) validates both population and curiosity activation receipts against bound owners and the exact accepted token. Closure validates actual positive step-count participants and genuine BANK disposition receipts. Stop/reset/close cannot be invented to fill a trace horizon.
* `Trace` records format 4, exact fixed shapes, and `RunParams` containing pack, level, agent count, steps, seed, and device. `action_source` is deliberately reported but not compared. A new sampling/episode policy cannot become a verified scenario merely by changing that string.

These facts establish incompatibility with the existing public routes. They do not establish that no future authenticated physical protocol could ever support the old experiment.

## Smallest additive work that does not need capability reduction

Add explicit side-driver selection at the harness boundary, with an immutable artifact identity/digest and declared ENV protocol for each side. Keep shared-driver selection available for compatible interpreters; support choosing distinct artifacts deliberately. The historical artifact is a test instrument against its named frozen code, not a legacy application path. Never select a fallback after ImportError, inspect API presence to silently change behavior, or retain old ENV API branches in the current application driver.

Every run must bind each driver artifact to the declared source root and scenario. Validate each trace's actual code root against its own declared side, not only that the two roots differ. Record driver paths/digests, protocol IDs, scenario policy and selected pack roots in report provenance. Preserve existing pack-drift gates, exact stream comparison and registered-divergence rules. A missing historical artifact is a preflight failure, not SKIPPED or a registered application divergence.

This is a finite harness feature: explicit selection, propagation to all ordinary/registered-crash/scripted call paths, provenance, and focused selection/injection tests. It is not a new oracle programme. It can be planned and implemented independently of deciding the current physical policy, subject to root's execution release and source ownership. Its success alone does not resolve the six current-driver errors.

No historical driver bytes or checkout are available/qualified in this review. Root reports one available checkout and 14 preserved registry entries, with no permission for another worktree. Cross-version execution therefore remains blocked separately from source design; do not create a checkout or source copy to conceal that limit.

## Decision required for the current driver

The bounded viable current-protocol implementation is an explicit legal-action, single-episode scenario using the genuine manual session. It must NOT be called preservation of the original unrestricted scenario.

| Surface | Existing experiment | Proposed bounded current scenario |
| --- | --- | --- |
| Random | CPU all-vocabulary randint each vector | Explicit deterministic sampling among legal actions; sampling algorithm and RNG consumption specified and identified |
| Script | Every in-range integer script executes verbatim | Same shape/range validation plus actual predecessor legality; legal scripts replay verbatim, illegal scripts fail clearly without rewriting actions |
| Horizon | Exactly requested physical vectors, including vectors after all lanes finish | Exactly requested physical vectors only while at least one lane is active on entry; early all-terminal state makes this requested run fail, with completed-prefix diagnostics but no successful truncated format-4 trace |
| Episode | Old implicit reset and stepping | Real authored world IDs, reservation/reset/accepted token, genuine activation, owned results, and established completion/disposal |
| Cross-version | Same injected driver | Explicit artifacts using each side's native public protocol; comparison only for the same declared action/horizon experiment |

A successful step that terminates every lane exactly on the final requested vector is valid; refusal applies to a subsequent requested vector. Finished lanes remain represented as provided by the authentic physical result. Never pad frames, repeat the last result, silently cap `steps`, reset mid-trace, replace an illegal action with a no-op, or emit a rejected request as if physics executed it.

For a historical side participating in the new legal-action experiment, its explicit driver must actually implement that declared policy. An existing old all-vocabulary trace cannot be relabelled legal. In scripted comparisons, a legal old-side script can still be refused on the new side; report that as a real failed comparison with the exact rejected step/lane/action, not agreement or an automatically registered divergence. Do not silently change old-to-new replay direction to find an easier witness.

The policy identity must be checked by the harness before applying existing comparators. It may live in a required scenario declaration/report binding for this bounded change; format-4 arrays need not be widened merely to add protocol provenance. Random generation versus replay may legitimately differ between sides, as today, while the semantic action/horizon policy remains the same. Merely relying on `action_source` is insufficient.

Alternative: retain the existing arbitrary-action/fixed-step requirement and leave the current-driver repair blocked. A future additive authenticated execution primitive might preserve it, but no such public supplier has been identified. Designing one needs a separately bounded ENV/session protocol review proving real ownership, participation, attempted-action semantics, terminal-clock semantics and genuine receipts; it is not authorized here as an invariant exception or a shortcut around the six diagnostics.

## Exact approval question for root to put to the owner

“May I change the current-protocol oracle to sample only legal actions, reject scripted actions that are illegal in their actual predecessor, and fail a run if all worlds finish before its requested final step, while preserving cross-version comparison through explicitly selected per-side drivers?”

Why approval is needed: this removes current-side coverage of arbitrary in-range actions and post-terminal fixed-horizon vectors. The owner's instruction requires approval for capability removal/degradation. AGENTS' prohibition on application backwards compatibility does not itself authorize that reduction. Adding side-driver options is already within additive scope; the question concerns only the concrete lost experiment coverage. Do not ask for permission to continue unrelated authorized work.

## Finite handoff after that decision

1. Root records the owner's decision and releases execution. Keep the existing plan immutable; supply an additive amendment identifying the selected semantics and expanded harness ownership. If declined, preserve the open six-diagnostic blockage explicitly and implement no reduced substitute.
2. Obtain the remaining finite supplier facts from current owners: authored roster/lane input for actual callers, genuine BANK/owner setup, and supported one-episode completion/disposal. A test-local controller is evidence of a viable public composition, not permission to copy receipts or omit real consumer effects.
3. Add explicit harness driver/artifact/scenario selection and its focused tests. Preserve shared-driver selection and all divergence adjudication behavior. Do not modify matrix expectations or register a protocol ImportError as a successful divergence.
4. Under approved semantics, replace the current driver's obsolete calls with that exact public lifecycle; add explicit scenario inputs to its CLI and actual callers. Preserve format-4 full-trace shapes and owned stream capture for successful runs. Require named policy values; no hidden sampling fallback.
5. Execute the existing driver and RNG integration tests as pre-change evidence. Preserve format/provenance, identical-seed equality, script-shape/type/range and verbatim replay assertions. Adapt tests only where the owner approved a contract change, and retain a distinct regression that demonstrates the former unrestricted script is now refused. Add real legal progression and terminal-boundary controls, including completion exactly on the horizon versus one requested vector beyond it. Test genuine accepted/activation records and failure behavior, not a mock of physics.
6. Verify explicit old/new driver dispatch, missing/mismatched artifacts, each trace's declared source root, same-policy comparison, policy mismatch rejection, and the old-action replay path. Run finite type/style checks and current-side tests after source repair. Historical execution awaits an authorized actual historical environment; no current/current self-comparison can substitute for it.

Acceptance must separately report current-driver typing, current-protocol physical tests, harness selection tests, and historical cross-version execution. No checks were run by this reviewer. No broad BAC acceptance follows from this design.
