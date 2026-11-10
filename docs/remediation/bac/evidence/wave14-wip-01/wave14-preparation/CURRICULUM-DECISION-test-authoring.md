# CurriculumDecision producer-contract tests authored

Tests stationary for root causal RED. No production edit, runtime/import/pytest,
guards, Git/index/commit/push, branch/worktree/copy/deletion or subagent action.
Read AGENTS.md and designated T21 implementation/design prose. Source inventory
is exactly three whole files; no helper, fixture, probe or other source read.

## Changed nodes and independent expected values

- `test_static_factory_transports_exact_roster_and_fixed_policy`: retains all six
  existing direct/EF cases and adds two cases using seven actual declared strings
  in this order: energy, hygiene, satiation, money, mood, social, thermal_budget.
  Both routes must produce the exact roster, difficulty 0.5, depletion 1.0 and
  shaped reward. Exact roster and difficulty remain after a completion and its
  duplicate retry. Existing checkpoint ownership and event-count assertions remain.
  Empty direct/EF cases now explicitly observe actual decision roster as well.
- `test_custom_programmatic_static_parameters_remain_meaningful`: retains 0.37
  and adds 0.0/12.0. Each explicit Static producer must emit difficulty 0.8,
  sparse reward, owned `[operator_defined]` roster and the exact supplied finite
  depletion before and after completion. No reward-mode extension is proposed.
- `test_custom_programmatic_static_invalid_depletion_refuses_before_decisions`:
  seven new constructor-boundary controls require ValueError for -0.01, True,
  False, NaN, positive infinity, negative infinity and list-shaped `[1.0]`.
  Construction must refuse before initialization, decisions or physics.

All 53 previous cases preserved; predicted collection is 64 (11 additive cases),
not executed here. Expected new causal failures on current DTO: two seven-meter
factory routes (`max_length=6`) and custom depletion 0/12 (`gt=0`, `le=10`).
Root already observed the two empty-roster failures (`min_length=1`). Invalid
producer controls should pass independently of DTO relaxation. Root owns actual
collection, causal RED classification, qualification and integration.

## Exact source inventory

| File | Actual lines | Ceiling | SHA256 |
| --- | ---: | ---: | --- |
| src/townlet/training/state.py (read only this phase) |261|350|a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0|
| src/townlet/curriculum/static.py (read only) |64|220|22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59|
| tests/test_townlet/regressions/bac/test_curriculum_factory.py (sole source edit) |377|650|6e0c34ccd474f7592a6b17cdfcc8daf2d286ed7fd8b7f86f9320a0526a7c40a5|

Actual 3 files / 702 lines; allowed 3 files / 1220 lines. Prose handoff excluded.
State-only production repair remains awaiting root's explicit clearance after RED.
