# CurriculumDecision actual producer-domain repair

Production and tests stationary for root capture/GREEN and independent review.
Only the authorized CurriculumDecision fields in training/state.py changed this
phase. No test edits, runtime/import/pytest, guards, formatter, Git/index/commit/
push, branch/worktree/copy/deletion or subagent actions. No extra source read.

Root reports causal R3 tree 8a1cf92942c88fa394dcd3b6bc17dcf979bd5cb8:
64 collected, six failures, 58 passes, zero errors, 10.7527 seconds wall.
The exact failures were DTO validation during Static decision production: two
empty-roster, two seven-meter-roster, and custom zero/12 depletion cases. All
seven malformed depletion constructor controls passed. This is root evidence,
not execution by this author. No GREEN or global qualification is claimed here.

## Domain changes

CurriculumDecision.active_meters remains list[str], preserving typed string
elements. Removed min_length=1 and max_length=6: an actual declared roster can
be empty or have more than six names. No alternate reward mode or synthetic
meter default added. Description now identifies the actual declared roster.

CurriculumDecision.depletion_multiplier is float with ge=0.0,
allow_inf_nan=False and strict=True. It accepts finite nonnegative numbers,
including zero and 12, without an arbitrary upper cap. Strict numeric input
rejects boolean and string coercion; explicit finiteness rejects NaN/infinities.
List-shaped input remains outside the numeric domain. This aligns with the
producer's accepted finite nonnegative numeric semantics rather than dropping
numeric validation to bypass the six observed failures.

CurriculumDecision difficulty [0,1], shaped|sparse reward restriction, reason
validation and frozen configuration are untouched. PopulationCheckpoint and
every other state.py class are untouched. Optional early reward-label timing P3
is untouched. All 64 authored tests remain byte-identical to causal RED.

## Source-verified producer receipt for the bounded T21 reviewer

The reviewer need not open state.py as a sixth source. Author read exactly the
three permitted whole files before editing. StaticCurriculum's explicit
constructor validates difficulty as finite [0,1] and depletion through
finite_number plus a negative check. It rejects negative, bool, malformed and
nonfinite values before decisions; its public numeric domain includes zero and
finite 12. It accepts an explicit list of nonempty string meter names with no
length minimum or maximum and defensively copies that list into configuration.
get_batch_decisions produces CurriculumDecision from the retained difficulty,
meter-list copy, depletion and reward mode. The former DTO imposed unrelated
one-to-six meter and strictly-positive-at-most-ten depletion restrictions at that
handoff. This repair removes exactly those domain mismatches and retains
explicit numeric and string validation. Static itself was read only.

T21 declared-roster policy/EF/factory sources were not opened by this author;
their producer obligations are supplied by the designated T21 prose receipts
and the direct/EF test handoff. This receipt establishes no broader runtime,
world-binding or meter/reward-application qualification.

## Exact inventory

| File | Actual lines | Ceiling | SHA256 |
| --- | ---: | ---: | --- |
| src/townlet/training/state.py |263|350|a6f22b0b26ca6422e6a0710f9268386e8d2b7162e1a5e9a43a2decdea4c9d3e3|
| src/townlet/curriculum/static.py (read only) |64|220|22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59|
| tests/test_townlet/regressions/bac/test_curriculum_factory.py (unchanged this phase) |377|650|6e0c34ccd474f7592a6b17cdfcc8daf2d286ed7fd8b7f86f9320a0526a7c40a5|

Actual three files / 704 lines; ceiling three files / 1220 lines. Prose excluded.
Root owns capture, GREEN, fresh review, qualification and integration.
