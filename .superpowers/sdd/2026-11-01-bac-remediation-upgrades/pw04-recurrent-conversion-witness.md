# PW04 recurrent conversion witness

Tests-only authored candidate, frozen for root R172 RED observation. No runtime,
tests, imports, Git operations, source copies, branches, or worktrees executed by
this author. Root owns integration and execution; no passing result is claimed.

Finite selection:
`tests/test_townlet/regressions/bac/test_population_recurrent_conversion.py::test_nonpristine_captured_uniform_to_per_preserves_rows_and_masks`

The witness compiles the authored recurrent pack and a temporary DATA-only copy
with PER enabled. The real uniform parent enters an episode, runs three actual
population steps, and completes it. Its captured format-6 replay is cloned using
public sequential preparation/load with explicit `lineage=None`. That genuine
buffer is supplied to a fresh target before its ENV role binding. Real
`POP._bind_training` must convert it to PER, preserving all captured episodes,
successor masks, geometry, replay options, archives, and active row count. The
result must be ready to sample, and a second bind must retain the same owner.
The ENV boundary then binds the converted owner. No credential is fabricated;
no already-bound ENV role is replaced.

Counterfactual: omitted ordinary-operation lineage arguments in POP's conversion
prepare/load prevent the conversion. Lost rows/masks, wrong priority adapter
initialization, or non-idempotent owner installation also fail the assertions.

Supplier: SEQ owner supplied the public constructor, transport preparation/load,
serialization fields, and captured6 priority adapter facts. Root supplied the
compiler recipe and actual parent rollout recipe. Historical inspection/archive
branch tests are not yet authored; SEQ supplied a public construction recipe for
a later bounded follow-up. This candidate covers current captured conversion only.

Budget: 3 whole implementation/test bodies, 4,556 lines including new growth:

| File | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 3571 | `ee3aa7d0d37f07fae221217fd4b5fb24f873ad39371eb06954f7b719301bc2c8` |
| `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` | 900 | `bbfdc1e8d60a609de6dacf7b68c0d6cb7e014df308dddddde5698ad2bf7fd673` |
| `tests/test_townlet/regressions/bac/test_population_recurrent_conversion.py` | 85 | `0e0e531ee15137606ebabc4ca0c304bc5c223705f97ff17acf90dd8b0eae60c0` |

Hashes describe authoring-time bytes, not a qualification result. POP production
repair belongs to a separate owner after root observes the RED.

## R174 inspection branch extension

Root reported R172 reproduced the intended missing-lineage failure, followed by
R173 passing the captured conversion after the separate producer repair. Those
execution claims belong to root's custody records; this author ran no runtime.

The test file now adds two parameterized inspection cases:
`test_inspection_conversion_preserves_archives_without_training_historical_rows[archives-only]`
and
`test_inspection_conversion_preserves_archives_without_training_historical_rows[transport-and-archives]`.
Finite selection for R174 is the complete three-case conversion file.

Actual recurrent rollout episodes supply historical writer tensors. Public
unconfigured sequential store/serialize and load create the genuine archival
record. One case leaves its legacy transport empty; the other stores two real
episodes as a distinct nonempty transport. No archive object or authority is
fabricated. The actual POP conversion before ENV binding must preserve archived
original tensors, row counts, and source digests. The nonempty case checks the
transport archive first and the existing archive second, as supplied by SEQ's
existing-first merge contract. Both cases require zero active rows and false
learner readiness, then bind the converted owner through the actual ENV boundary.

New frozen test hash:
`d906430c1aa1557947d60c447b187153c9779e2d089c856cc6f3c50a0562be4f`
(148 lines). Current POP is 3576 lines with hash
`c95cbda0192d2d33a604d6aedb56e0000611bcb5dbb759f14da7f88d7b6ff764`;
parent fixture remains 900 lines. Three-body total including all growth: 4624.
No additional implementation/test bodies were read. This extension remains
unexecuted by the author and frozen for root verification.
