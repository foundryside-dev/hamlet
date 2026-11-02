# T15 fixture independent review R1

Reviewed 2026-11-02, statically, in existing `/workspace/hamlet`. Candidate attribution: HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, frozen tree `096cdb7d98a9725181658c44b3ed84a6d0d72e82`, manifest `wave09/r1a-candidate.json`, diff `wave09/r1a-fixtures-review.diff`. HEAD and all five source hashes/counts below were independently measured. Tree attribution is from root/manifest; no tree or index was created. A later production optimizer repair outside this inventory does not invalidate these unchanged source findings, but requires its own candidate-bound execution evidence.

## Verdicts

**Spec: PASS for the two bounded fixture repairs, by static inspection.** The edits implement Q7's eligible projection and synthetic collector maintenance without restoring an inactive provider call, inventing production legality, changing public APIs, or weakening the intended existing assertions. This does not certify production Q4 alignment or complete T15/BAC acceptance.

**Quality: acceptable narrowly scoped repairs; runtime qualification OPEN.** No blocking defect found in the two-file change. Assertions were assessed by what they distinguish, not their count. Root reports collection 319 PASS; that is collection evidence only. Neither active runtime job was executed or inspected by this reviewer, and no behavioral GREEN is claimed.

## Exact source inventory

Exactly five whole implementation/test/helper sources, 3313 lines. No sixth source, POP, buffer, provider, conftest, imported implementation or scratch probe was opened. Imports were text only.

| Source | Lines | SHA256 |
|---|---:|---|
| `tests/test_townlet/unit/population/test_vectorized_population.py` | 1884 | `9e0b50095cd29470afc92d42a740a800e34c731aea12abfa96a7d60d89b1015c` |
| `tests/test_townlet/unit/population/test_recurrent_training.py` | 573 | `32f3a4e7996a5798c17b10a1ae69ad6d22631a2421549c33501f3764560325f9` |
| `tests/test_townlet/unit/population/test_double_dqn_algorithm.py` | 324 | `b9b12150109541ed53f75fc692661c305f075b616827bac4c37a83afbe859e5a` |
| `tests/test_townlet/unit/population/test_action_selection.py` | 375 | `81ffc9ef6390f2a64471f3e9daf3ea77c751d1bc0e97ff6cbd5b03eede65b2b1` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

Read repository AGENTS/CLAUDE, supplied fixture audit/repair and interface proposal prose, candidate manifest and complete fixture diff. The using-superpowers skill explicitly exempts dispatched subagents from its workflow. No subdelegation was used.

## Preservation and independence

At helper lines 104–120, `nonzero(~env.dones)` supplies ascending original-world indices independently of the selector's supplied row count. Q geometry and finite values remain checked; observation row count now correctly requires K. The entire authored name schedule still resolves through the compiled action map and must have N entries. Indexing that full schedule by the independent eligible indices preserves original world identity in returned K actions. Mask presence, exact K-by-A geometry, and legality of each selected action remain required. No mask-derived membership, new randomness, second selector, or forced full-N provider call is introduced.

`SelectionWitness.actions` retains full-N authored schedules, whereas `q_values` retains actual K provider outputs. Those are different domains, now documented; authored inactive actions must not be mistaken for actual inactive transport. `observe_environment_steps` (lines 138–157) remains unchanged and wraps the original ENV step. Its full-N action copies, predecessor eligibility, newly terminal rows, sticky dones, canonical returned rewards/info and actual world tick remain independent real-transition observations. Thus the change preserves the means to check seven transitions and lifecycle behavior, without fabricating an environment transition or replacing those observations with schedule data. Consumer assertions outside this five-file inventory were not independently re-reviewed.

At recurrent-test lines 232–262, the original five synthetic observation/action/reward/done/successor rows remain. Each loop iteration creates a fresh bool[A] one-hot successor mask permitting `(i+1)%A` and a scalar bool True recorded bit on the same device. All five pairs are appended in the same order as their original rows. The explicit synthetic label is accurate: these masks declare unit inputs, not recovered ENV history. The test preserves successful store, observation collector reset and positive replay occupancy; it additionally requires both legality lists to contain five rows and both replacement lists to be empty after reset. No all-legal historical substitution or production relaxation occurs.

Other original purposes remain: empty episodes are rejected; real three-step cap flush stores once and records survival; per-agent hidden reset leaves other agents unchanged; adaptive completion records survival once; snapshot/curriculum controls retain their assertions. The unchanged action-selection module retains mask validity, epsilon behavior and recurrent output-shape checks. The unchanged DD module supplies manual calculation/flag/inspection controls, not production legal-target or actual optimizer evidence. The unchanged VP module retains constructor/configuration, scheduler persistence, checkpoint validation/nonmutation and low-level replay inspection roles.

## Gaps and severity

- **No P0/P1/P2 defect established in these repairs.** Static coherence is not execution proof.
- **Evidence gap, acceptance-blocking if these fixtures are used alone:** helper observation row count cannot distinguish a permuted or wrong K-row state, wrong per-row epsilons, false done bits, or same-shaped wrong masks. The selector is intentionally patched and therefore cannot establish actual provider candidate/epsilon RNG behavior. Q4's real aligned state/mask/epsilon and eligible-empty/no-draw proofs must come from the independently owned production/provider tests. This is a scope limit, not a new demand to broaden this helper repair.
- **Evidence gap, acceptance-blocking if unit storage is promoted to capture proof:** the manual collector test checks construction alignment/reset and positive occupancy, not exact stored mask/bit values after serialization or sampling. Independent actual capture/learner tests must prove successor legality survives storage and is consumed correctly. Do not cite these synthetic rows as authored ENV evidence.
- **P3 existing descriptive debt, optional cleanup separately:** recurrent lines 331–386 still describe twenty maskless ten-row episodes as enough to trigger learning, but the final assertion only checks recurrent mode after one step. This 200-row maskless smoke remains a low-level archival/step smoke only and is explicitly excluded from acceptance learning evidence. No change to it is required for the two observed repairs. VP scheduler lines 680–798 checks restored equality and cannot establish scheduler progress merely from 110 opportunities. DD manual target shapes/flags similarly do not prove production target semantics. None licenses training on unknown legality or lowering readiness.

## Executable proof owed to root

1. Execute the repaired manual buffering case and the recurrent unit module on the qualified candidate; retain empty collector, real flush, hidden-state and exactly-once completion behavior.
2. Execute all B03 shared-helper consumers, including authored lanes, population lanes and lane learning, through the existing identity/import harness. Require actual full-N ENV transport and seven real eligible transitions, correct terminal/cap lifecycle and independent row/curriculum/entropy evidence. Match K provider receipts to original eligible world identities rather than zipping K Q rows with N witness schedules.
3. Independently establish actual provider K-state/mask/epsilon alignment, zero eligible selector bypass, inactive RNG preservation and nonselection service behavior; controlled scheduling cannot prove these itself.
4. Independently establish real captured masks/recorded bits, qualified warmup and genuine optimizer/network change, including exact-prefix/BPTT controls. Neither the old maskless smoke nor manual target math nor scheduler equality substitutes for this proof.
5. Bind runtime outcomes to the exact candidate being released. Root's separate optimizer ownership repair and other T15 repairs, affected consumers, full G2/BAC acceptance and final gates remain open. Successful collection or static format results cannot close them.

## Custody

Only this ignored prose report was written. No source modification, project import, test/collection, linter, compiler, probe, branch/worktree/source copy/deletion, index/tracker/commit or publication operation occurred. Root retains source integration and runtime custody. Return stationary.
