# T21 fresh independent spec and code-quality review R4

## Exact candidate and review boundary

Base commit: `02d1f614bfbf603b9742d8fea60984b7b7e1b568`.
Candidate tree, supplied by root and recorded in `wave14/r4-candidate.json`:
`b7a8c6778ef1dc61e0865c8136ad073eafcfb255`.
Scoped diff: `wave14/r4-T21-review.diff.txt`, SHA256
`c7243bf99eed73ece4ee89fc901791b0b007ef5a1ba8bf2c2eb7fb9e17510969`.

Reviewed the execution brief, FINAL source-verified component refinement in
T21-DESIGN-RULING.md, T21-implementation.md, the scoped diff, and the supplied
CURRICULUM-DECISION-implementation.md producer receipt. The final refinement,
not the earlier roster argument on OP option resolution, is the governing spec.

Whole source inventory is exactly these five files, read in the existing checkout:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/bac_options.py | 323 | cc0b2b9cfbbfd6396a9080b90bd65692f964e04c75693a164408f59f0dab3ee6 |
| src/townlet/config/training_v2_config.py | 435 | 2803a9572b9836e857815c734b15f47ae20f2bb65b490f639be49b7fa49bd863 |
| src/townlet/config/effective_run.py | 371 | 9ec1ddfa5259e9d5ffa2880e2cf65dab1e22b939aae50f80d1396f307fba8999 |
| src/townlet/curriculum/factory.py | 58 | 10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71 |
| tests/test_townlet/regressions/bac/test_curriculum_factory.py | 377 | 6e0c34ccd474f7592a6b17cdfcc8daf2d286ed7fd8b7f86f9320a0526a7c40a5 |

Actual 5 files / 1564 lines; projected 3450; within 5 files / 5000 lines.
No sixth implementation, helper, fixture, probe, or test source read. In
particular STATE, static/adversarial strategy implementations, EP, RP, compiler,
and parent validators were not opened. Their facts below are explicitly supplied
contracts or separate-owner obligations, not independent source review here.
No runtimes, imports, pytest, formatter, git write-tree, index/source/test edits,
subagents, copies, branch/worktree, commits, cleanup, or push were performed.
Only this ignored prose report was written.

## Verdicts

**Spec verdict: ACCEPT the bounded direct/EF producer and factory implementation
on static evidence; runtime acceptance remains pending root's exact-candidate
results.** No confirmed new owned P1/P2 defect was found. This does not accept an
integrated T21 release or close the required compiled route. The externally
supplied DTO repair still needs its own independent review and root GREEN.

**Code-quality verdict: ACCEPT the scoped change on static evidence.** The
factory is a small explicit consumer, the named baseline has one semantic owner,
and the change removes the obsolete factory/configuration API and EF old-payload
branch without adding a replacement adapter. Existing EF projection complexity
is not multiplied by a second curriculum policy resolver. No speculative
refactor or compatibility mechanism is required for this handoff.

No GREEN is inferred from test names, collection, earlier RED counts, or prose.
Root reported R4 joint T21/T20 collection of 239 with test and guard runs in
progress at dispatch; this reviewer did not execute them or observe their final
results. Earlier R2/R3 failures are causal history and not current failures.

## Concrete spec checks

1. **Semantic ownership and absence:** OP61-93 restricts authored commit mode to
   completion, retains authored None markers, and owns the finite immutable
   static-baseline-v1 policy separately. OP201-323 keeps the pure options-only
   resolver signature, so component callers need no invented level roster.
   There is no factory-local omission resolver. Factory29-32 refuses either
   unresolved mode even for static; omitted authoring is resolved before that
   boundary rather than interpreted as a compatibility request.

2. **Actual roster and fixed policy:** OP's strict tuple[str,...] field plus
   nonblank/unique-name validation accepts empty and arbitrary ordered unique
   rosters while rejecting mutable list authoring and malformed names. No
   familiar six-meter roster is synthesized. Constants are fixed to difficulty
   .5, shaped reward label, and depletion 1, with no new authored feature knob.
   The tuple and strings are immutable; factory39 creates a fresh constructor
   list. EF153 calls this same baseline resolver with its required argument.

3. **Current factory transport and units:** Factory14-58 requires resolved
   curriculum_options/static_policy/device, forwards all five required static
   inputs and all ten accepted adversarial inputs, and returns the manager
   uninitialized. It supplies no obsolete episode-horizon constructor argument,
   configure_from_training call, or alias/probing branch. TC224-248 describes
   rate movement per eligible transition, completion survival/planned horizon,
   and eligible-transition dwell. Authored rate remains strictly positive and
   singleton bounds remain permitted. Programmatic T20 zero rate is outside
   TC authoring and is not removed by this change.

4. **Truthful identity and activity:** EF258-259 makes adaptation_rate inactive
   for stage_band; EF285-286 makes difficulty_mode inactive under static while
   commit_mode remains the common active/derived contract marker. EF335-355
   uses effective-run-v2 and includes the entire static declaration only when
   static is selected. Reward and meter application remain explicitly
   unqualified; their inclusion is documented as selected policy-context
   identity, not a claim of implemented application mechanics. Under adversarial
   the static declaration is an inactive preset and omitted from execution
   identity. Authored training and exploration identity remain separate.

5. **Portable current validation and ownership:** EF117-133 requires the static
   declaration, explicitly converts a portable list roster to a typed tuple,
   validates its finite fixed schema, resolves authoring, and checks the whole
   canonical payload. EF108-115 no longer accepts the historical missing-scope
   variant. Missing/extra/tampered fields cannot be hidden merely by adjusting
   one execution hash because validation compares the complete reconstructed
   payload. Models read from EF are defensively copied; static_policy itself is
   immutable, and serialized static data is newly materialized.

6. **Preservation:** The diff changes exactly the three authorized YAML
   legacy_step selectors to completion while retaining rate_limited and their
   other options. It does not remove strategy, network, provider, replay,
   serving, checkpoint, or exploration choices. Existing supported custom direct
   StaticCurriculum difficulty/sparse reward/roster/depletion choices are
   retained by the supplied constructor receipt and tested via the fifth file.
   Their DTO-domain repair is separate: the receipt states empty/arbitrary
   rosters and finite nonnegative depletion including 0 and 12 are now accepted,
   while shaped|sparse reward and strict finite validation remain. This review
   neither reopens that source nor substitutes for its designated review.

## Confirmed open gates, not new scoped defects

**Required integration gap; blocks integrated release:** The real compiler and
compiled factory path has not been established here. The required EF argument
and factory interface are intentionally breaking current API changes. Root's
reported remaining compiled EF argument failure must be closed by the named
serial compiler/compiled maintenance owner using the actual declared level
roster, then witnessed through the real compiled artifact into this factory.
The YAML-roster direct/EF test is useful but is not that compiled witness.
Do not restore old signatures, fabricate empty rosters, use a stand-in compiled
object, or mark integrated release GREEN to avoid this obligation.

**Required parent binding gap; blocks broader native acceptance:** EF.from_dict
can establish internal current-payload consistency only. A fully self-consistent
payload for a different roster/world is not proved to match the caller's actual
world. The parent/current-native owner must compare expected effective/world
inputs before installation and provide negative controls plus unchanged-state
proof. This is an explicit final-ruling limitation, not a newly discovered EF
vulnerability or justification for weakening current portable validation.

Full owner/native/learning/final gates remain open as applicable. A passing
bounded root run plus independent scoped reviews can support a producer handoff;
it cannot waive those gates.

## Refuted concerns and optional strengthening

- Requiring declared_meter_names on resolve_bac_options would contradict the
  FINAL component refinement. Its absence there is correct; EF and the separate
  static resolver require the roster.
- Including reward/meters in selected static identity does not falsely label
  their mechanics active: the explicit policy-context projection and
  unqualified roles satisfy the ruling together.
- Empty/>6 rosters and 0/12 depletion were real prior producer/DTO mismatches,
  but the supplied precise DTO repair addresses them. They are not asserted as
  current defects without the designated fresh review and runtime.
- Rejecting unresolved modes for static is intentional boundary validation,
  despite static difficulty_mode being an inactive preset after resolution.
- The original custom_reward fixture was outside the supported shaped|sparse
  domain. The current sparse control preserves the supported capability without
  inventing a new reward feature.

Optional low-priority test strengthening: a direct adversarial retreat-threshold
control and a nonsingleton changed-bound comparison would complement existing
advancement/dwell/entropy/rate controls. The factory forwards both threshold and
bound fields explicitly, and current native future/singleton tests already cover
part of this surface; this is not a confirmed transport defect or a condition
for bounded static acceptance. A portable adversarial EF roundtrip with a
nonselected static roster would similarly strengthen coverage beyond the
existing static roundtrips and adversarial identity exclusion test.

## Existing fifth-file adversarial execution selection

Sent to root for another model to execute later, with no new test source:

```text
-k 'static_factory_transports_exact_roster_and_fixed_policy or invalid_declared_rosters_refuse or factory_refuses_unresolved_modes_even_for_static or custom_programmatic_static or actual_completion_demonstrates_stage_and_rate_choices or static_roles_are_truthful or inactive_presets_preserve_authoring_but_not_selected_execution or adversarial_rate_identity_tracks_only_selected_semantics or static_execution_binds_actual_roster_while_authored_training_does_not or adversarial_execution_excludes_inactive_static_roster or portable_effective_current_roundtrip or forged_or_obsolete_effective_payload_refuses'
```

This exercises arbitrary/empty roster transport and ownership, malformed roster
and unresolved-mode refusal, custom supported static domain, direct/EF actual
completion effects, truthful activity, selected/inactive identity, portable
roundtrip, and forged/obsolete-payload rejection. Execution remains root-owned
until explicit clearance; selection is not an assertion that these tests pass.

## Cleared independent execution addendum

Root subsequently explicitly cleared the single-CPU independent packet and
verification, with source/test/tracked docs/index frozen and root abstaining
from concurrent Git/source/index work. Executed exactly the supplied locked
packet command for `wave14-r4-t21-independent-spec.json`, then exactly its
`verify_bac_run.py` command. Both sessions exited 0 and are closed. No additional
helper source, probes, tests, or implementation were read or written.

Actual independent result: **48 PASS, 16 deselected, 0 skipped, 0 xfailed,
0 xpassed, 0 warnings** from 64 collected existing fifth-file cases. Pytest
reported 0.54 seconds; measured packet wall time was **4.22620415687561 seconds**.
The selected expression is the one above. Log:
`/workspace/bac-review-2026-11-01/qualification/wave14-r4-t21-independent/t21-independent.log`,
SHA256 `911f16d0eb552dba8362f9cf9a50508f293182ee1f269771f989ae72c949c6ce`.
Manifest SHA256:
`fc0fecc1a11edb136fbc9a758a2245df0c38bd518be27664ae6ab5e7202d1d6d`;
harness SHA256:
`180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.
Verifier confirms the exact base and R4 tree at the top of this report.

Custody verification: **PASS**, covering 176 source guards, 573 configuration
digests, 13 protected artifacts, 1 process identity, 14 worktree registry records,
and 1 available worktree. Its source/index/import/threads/fixture custody verdict
is PASS. After execution, direct SHA256 inspection of all five allowed files
matches every hash in this report's source table, including the 377-line test.

Root additionally reported joint T21/T20 **239 PASS, 0 warnings, 18.69 seconds
wall**, and current Ruff/Black/mypy/default checks **601 PASS**; those are supplied
root evidence rather than this reviewer's own executions. Root supplied the
separate DTO review execution as **23 PASS, 41 deselected, 0 warnings**, both
sessions closed and custody PASS. This addendum does not independently review
STATE or expand the five-file source inventory.

**Updated spec verdict: ACCEPT bounded direct/EF T21 producer and factory
handoff, supported by this exact-candidate independent execution. Updated
code-quality verdict: ACCEPT.** No new confirmed owned P1/P2 arose. Earlier
pending-runtime language records the pre-execution review state; this addendum
supersedes it for the specifically executed independent selection.

The globally remaining real compiled required-argument path remains REQUIRED
and owned by the next serial compiler/compiled maintenance slice. Bounded
acceptance does not close compiled integration, actual-world parent binding,
full owner/native/learning/final gates, integrated release, or whole-BAC
qualification. Both authorized execution sessions are now closed; root can
release this review barrier and continue planned delivery.
