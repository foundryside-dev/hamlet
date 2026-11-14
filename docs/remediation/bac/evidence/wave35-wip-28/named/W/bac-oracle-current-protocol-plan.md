# Oracle current-protocol repair plan

> Execution remains blocked on root's R170 release. Use the existing delegated execution method; no Git, test/runtime execution, branches, worktrees, or source copies in preparation.

**Goal:** Restore the existing oracle physical trace caller against the current ENV protocol while preserving deterministic random and scripted traces.

**Architecture:** The trace producer must own a real manual physical session and use genuine reservation, accepted reset and activation lifecycle records. It must supply explicit authored roster, lane order and training seed, and consume owned manual step outputs. No ENV private guard bypass, fabricated authority, old-API fallback or ignored type error is a repair.

**Scope:** Modify only `src/townlet/oracle/driver.py`, `tests/test_townlet/unit/oracle/test_driver.py`, and `tests/test_townlet/integration/test_oracle_rng_stability.py` after release. Read-only references are `src/townlet/environment/manual_physical.py` and `tests/test_townlet/regressions/bac/test_manual_physical_session.py`.

## Evidence and finite cause

Five whole source bodies have been read: driver 202 lines, manual helper 293, oracle unit tests 123, oracle integration 48, manual regression 801; total 1467. No ENV body or other implementation body was opened. AGENTS.md requires current-only APIs with no compatibility arrangements or hidden defaults. Root reports six remaining mypy errors at the old ENV interface calls; exact diagnostic text is requested, not independently reproduced.

The driver currently constructs ENV without world roster/training seed/lane IDs, calls `env.reset()` without a reservation and treats its return as a tensor, then calls obsolete `env.step(actions)` and unpacks a tuple. The manual helper instead exposes an ENV-issued `ManualPhysicalSession.step(accepted=..., actions=..., depletion_multiplier=...)` returning owned `observations`, `rewards`, `dones`, `info`, physical tick and receipt. It authenticates genuine activation, refuses illegal active-lane actions and refuses a vector with no active worlds. These are causal protocol differences, not typing-only errors.

Existing tests require valid format-4 trace shapes/provenance, same-seed exact streams, scripted actions stepped verbatim with matching dynamics, and clear rejection of malformed scripts. The integration caller uses 25 steps and two agents. The current source self-containment check forbids importing townlet.oracle from the driver; preserve that constraint. Its old frozen-tag compatibility prose cannot justify a fallback or forged protocol.

## Supplier facts required before implementation

Root must supply bounded current ENV/compiled-contract facts, without another source-body read:

1. Exact authored roster/lane source for both existing pack callers and production CLI; whether the compiled contract authors deterministic lane membership for requested num_agents. If not, required explicit input changes and all actual entrypoint callers must be coordinated; do not fabricate fallback IDs.
2. The supported genuine physical-only boundary owner and activation route, including whether a real CuriosityBank is required. The manual regression's LocalTemporalController uses a real bank plus a WorldReceiptIssuer bound to its actual controller, so copying a curiosity receipt is not permissible.
3. Completion/disposal obligations for a one-episode trace and behavior when all lanes finish before requested steps. Do not pad synthetic terminal frames or silently reset.
4. How seeded-random policy is expected to respect current action masks. The old all-vocabulary randint recipe can produce illegal actions; changing the random distribution is a trace-policy decision that must be explicit, not a hidden fallback.

Public lifecycle established by the existing regression: bind_boundary_authority(owner, role_owners), bind_manual_execution(population_owner), authority.bootstrap(first_batch_episode=0), install_boundary_release, prepare_episode(batch_episode=0, release), reset(reservation), retain reset.accepted/reset.observation, then activate_episode with genuine population and curiosity receipts. Public get_action_masks is available. This sequence does not establish authority to invent role effects.

## One repair task and RED/GREEN evidence

- [ ] Obtain root's finite supplier contract and R170 runtime release. Record the exact source/process provenance for each subsequent check using the existing BAC evidence process; no execution is claimed here.
- [ ] Run the existing loadable-trace test and same-seed integration representative unchanged as meaningful current-caller RED evidence. Preserve exact failure output, rather than replacing them with mocked ENV failures.
- [ ] Add focused assertions in the existing two test bodies for authentic manual progression, explicit authored identities and unchanged script replay/RNG reproducibility. Observe real session calls/receipts; do not replace physics, weaken existing shape or equality assertions, or import a broad fixture body.
- [ ] Implement the smallest current-protocol lifecycle in driver.py using only established public APIs and explicit inputs. Preserve format-4 metadata and action provenance. Resolve legality/horizon semantics explicitly from the supplied contract before coding.
- [ ] Run those two existing test files after repair, then finite mypy/format checks authorized by root. Acceptance requires all original random/scripted correctness tests plus the current-caller regression, not merely removal of the six diagnostics.
- [ ] Hand root exact changed paths, source hashes, immutable attempt records, observed counts/failures and remaining limitations for independent review. Do not claim broad acceptance from this slice.

## Review focus

Authored ID order must match trace lanes; same seed must preserve all four streams; replay must execute recorded legal actions verbatim; early all-terminal episodes must not invent physical work; genuine owner/activation and failure quarantine must survive without private mutation. Source remains capped at five bodies and 5000 lines including growth.

Status: preparation only. No APP or test source writes, no runtime/test commands, no source copies. The remaining supplier questions are deliberately explicit; this document does not pretend the missing authority/identity contract is established.
