# T18c independent review r1 — fixed-source static refresh

Verdict: no P1/P2 finding identified in the fixed source. Static contract review remains satisfactory; fixed-candidate runtime and repository gates are pending the coordinator's reruns. This is not a runtime pass or release receipt.

## Candidate and bounded inventory

Root identifies staged tree `6d27f905fac6e6942db2708db6415db3c5c8fb53`, HEAD `214408b107730b4511b8a690541569aeca4b7b67`. This refresh independently read the entire fixed ICM file and verified all five file hashes/line counts. The other four files retain the exact bytes already read whole in r0; their prior analysis is retained.

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/exploration/icm.py | 380 | 8004aec68d19c962df0cf6785b00af32c8553a3746fee95be39009555f9d44b8 |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| src/townlet/exploration/epsilon_greedy.py | 118 | f9100a2f7f6a053a06d420d850a979d1c1e4a528461727c2a1405da5daeec059 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/regressions/bac/test_icm_provider.py | 340 | 3759cd590ca7f6c348294ac6d58341cb7f7101cf25bfca7bfdeaea4ecdd645f8 |

Total: five core source files / 1,900 lines. No additional helper/probe source was opened. No runtime, project import, tests or probes were executed by this reviewer. No branch/worktree/source copy/delegation/source/index changes were made. r0 review is preserved.

## Actual fixed implementation reassessment

The checkpoint cast wraps `_owned` applied to a literal dictionary: its recursive dictionary branch returns a new dictionary, cloning tensor leaves and recursively owning policy, model, optimizer, pending and counter data. `cast(dict[str, Any], ...)` expresses that existing return structure; it does not replace runtime validation or weaken ownership.

`_model_state` now accepts and returns `nn.Sequential`, matching all three actual constructor-created networks and their off-side deep copies. The complete key, shape, dtype and finite-value checks still precede strict load into the candidate. The annotation does not bypass validation or mutate the live receiver.

The explicit `required: set[int] = set(); if updates: required = set(identifiers)` retains the cold-versus-warm Adam state rule. Zero successful updates require empty state; nonzero updates require exactly the parameter IDs, complete moments and matching step counts. Off-side optimizer creation/loading and final atomic assignment remain intact.

Re-reading the complete implementation found no change to the transition reward formula, detached successor target, weighted inverse/forward loss, eligible owned FIFO rows, drop conservation, ordinary same-tick pacing, mandatory-service accounting, or observation-only refusals. Full transported policy and inactive authoring are retained; selected active identity and numeric configuration still must match. Device provenance remains independent of receiver transport placement.

## P1 / P2

None identified by this static refresh.

## Runtime evidence attribution

The data-only artifact `count-icm-independent-results.json` was read. It identifies prior tree `01adbb21b31031df0499d7406b6ee954d59bca69`, not this fixed tree. Its separately owned independent execution reports:

- Warm Adam continuation: three warm updates, 12 parameter states, four further updates, bitwise-equal continuation.
- Restored pacing: zero same-tick updates, one next-tick update.
- Both observation-only APIs refuse without changing warm state.
- Inactive-only authoring differences load while preserving transported provenance/state.

Root additionally reports the original ICM module run as 28 PASS. This reviewer did not execute that run or inspect its runtime log. The data closes the specific r0 evidence gaps for the prior candidate; it must not be relabeled as execution of the typing-fixed candidate. Root has scheduled fresh focused/full/adversarial verification after repair work.

## Remaining gaps and optional P3

Fixed-candidate runtime, owner-suite and repository gates remain pending. Existing test-module coverage gaps for warm successful restore, restored same-tick pacing and direct protocol refusals remain optional test-hardening opportunities, with successful prior independent probe evidence now available. No production correction is requested based on this review.

## Refuted concerns / scope limits

The typing edits do not change cold/warm optimizer acceptance or strip checkpoint data. Neither idle shared-vector-tick service nor constructor ambient RNG establishes private-world semantics; later adapters/banks/private RNG/local clocks remain mandatory. No X02, GPU, cross-device bitwise, global-RNG continuation, canonical reward integration, or repository-green claim follows from this provider review.
