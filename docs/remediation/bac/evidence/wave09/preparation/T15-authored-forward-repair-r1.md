# T15 authored forward repair r1

Stationary authoring handoff. Root cleared this write after both R1a causal runtimes closed. This round modifies only tests/test_townlet/integration/test_authored_episode_lanes.py, plus this requested ignored report. Prior lane-population supplier remains stationary at SHA-256 5c306090ecdf7ec50c699ffb48913376a40fd12e58feb682bfc1ceb514ecd4f8.

## Scope and exact census

Exactly FOUR implementation/test/helper sources read cumulatively: src/townlet/population/vectorized.py (2128 lines at initial read), tests/test_townlet/regressions/test_episode_lane_population.py (406 before/413 after prior correction), tests/test_townlet/regressions/fixtures/episode_lanes.py (157), tests/test_townlet/integration/test_authored_episode_lanes.py (57 before/66 after this correction). No fifth implementation source or dependency/conftest opened. Current source census at handoff: 2764 lines using the initially read POP count; plus AGENTS.md79/CLAUDE.md605 =3448 lines, below5000. Main owner's concurrent POP edits are disjoint and were not reopened for this round.

Authored integration test before SHA-256: 3b46b8ae90da5827b5f6d46c0ce644df36beabde502d0c90776e76f23e2abb91; after SHA-256: 1aa95fc7764c9e85dfdc16d8f1d43f4014d86fedc18c7bcfdc627bf8779c56ac. Diff11 additions/2 removals; 57 to66 lines. Two test functions retained. Prior three source hashes and instruction hashes are recorded in T15-lane-supplier-repair-r1.md; no other source authoring performed by this owner.

## Causal correction and retained evidence

Root reports R1a owner causal12PASS1FAIL, with test_authored_pack_compiles newly reaching the obsolete full-N forward versus eligible-K provider equality at original line38. This is the bounded witness correction, not a product runtime change.

The real q_network forward hook now captures both the entire detached full-N output and actual entry eligibility (~env.dones & ~population.episode_completed). For each actual step, the test requires full-N/A output shape and finite values including inactive Q rows, cross-checks captured eligibility against independent observe_environment_steps tick.active_before, and requires exact equality between eligible forward rows and provider-K Q values. The full forward is retained; no actions are fabricated and no network/selector/environment execution is replaced.

All original checks remain: compiled feedforward architecture, hidden-layer widths, initial energy, five real forward/provider calls, exact selected-Q equality for actual eligible rows, independent survival counts[2,5], one terminal event per lane, terminal coordinates at steps2/5, global_tick5; the separate survival test's independently counted and published[2,5] totals, total7 and tick5 are unchanged. Full-N shape/finite and eligibility-cross-check assertions are additive controls.

No shared helper changes, production changes, authored pack changes, runtime imports, pytest, index operations, commits, worktree operations, deletions, source-checkout copies, or delegation.

## Verification and runtime owed

Passed exit0: owned .venv/bin/black --check; .venv/bin/ruff check; git diff --check. Standard-library AST parsing/census completed:14 Assert nodes before,17 after; two test functions before/after. Runtime qualification remains owed to root after all owners are stationary; no runtime pass claim is made here. Root should re-run the previously reached authored-pack case and its full causal12PASS cohort against the final integrated source.
