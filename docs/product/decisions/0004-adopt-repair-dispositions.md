# PDR-0004 — Adopt REPAIR for all eight subsystems; the recovery is a wiring job, not a rebuild

Date: 2026-08-11   Status: **superseded in part** by PDR-0006   Author: Claude (standing product owner)   Owner sign-off: pending review of the assessment

> **Superseded in part, same session, by `PDR-0006`.** The REPAIR *dispositions* and the evidence
> behind them stand. What is superseded is the **execution model** — repair-in-place — replaced by
> a strangler rewrite behind the compiled-universe contract. Also note `PDR-0006` records that this
> PDR's claim of adversarial-verification unanimity was partly an artifact of biased prompt design;
> read that correction before citing the unanimity as evidence. The deletion rule in
> §"What closing it takes" was separately superseded by `PDR-0005`.
Supersedes: —   Related: PDR-0002 (commissioned this assessment), PDR-0003 (dogfooding rule), roadmap.md (Now), metrics.md
Evidence: `docs/product/assessments/2026-08-11-maturity-assessment.md` (run `wf_4ca82820-274`)

## Context

`PDR-0002` gated all recovery work on a macro + subsystem maturity assessment. It has landed:
three macro lenses (declared-vs-live field sweep over 322 `Field(...)` declarations, bug-corpus
freshness verification, spec/doc truth audit) and eight subsystem assessments scored across six
dimensions, source-verified, with `docs/` treated as untrusted. Twelve agents, no failures.

The result is unusually consistent, and that consistency is the finding.

## Options considered

Dispositions were assigned per subsystem by independent assessors, with any REBUILD or DELETE
routed to an adversarial verifier instructed to refute it and default to the cheaper call.

1. **Accept a mixed disposition set including rebuilds** — the expected outcome going in, given
   "buggy, underspecified, unfinished."
2. **Accept REPAIR across the board** — what the evidence actually produced.
3. **Re-run with harsher framing** because unanimity looks like assessor timidity.

## The call

**Option 2: REPAIR for all eight subsystems.** No REBUILD, no whole-subsystem DELETE, and zero
adversarial downgrades were needed — in three cases the assessor argued *down* from a harsher
verdict on its own evidence before the verifier was reached. One embedded deletion is adopted:
`src/townlet/recording/` (~1,150 LOC + ~2,600 test lines, unreachable at three independent points,
nine months stale).

Option 3 was rejected because unanimity here is explained, not suspicious: the six dimension
scores are *not* uniform. `completeness` and `correctness` vary across subsystems, while
**`specification` scored weak in all 8** and **`doc_truth` scored absent in 6 of 8, weak in the
other 2**. A codebase whose engineering varies but whose *specification* is uniformly missing is
precisely a codebase that needs specifying and wiring — not rebuilding.

**The owner's instinct is empirically confirmed.** The assessment's pattern P4 found that
inertness tracks *recency, not quality*: the oldest subsystems (feedforward network construction,
VTC passive depletion, VFS access control with real `PermissionError` raises and negative tests,
dueling/set-encoder builders) are fully live; the newest layers are declared-only. The cut line
runs along the newest work, not through the codebase. There is a great deal worth keeping, and
§5 of the assessment names it specifically so recovery cannot destroy it by accident.

### The defining finding

**~40 schema fields validate, are documented, and drive nothing** — and *in nearly every case the
inert field ships set to its no-op value*, which is why the drift was invisible. `drive.composition
.normalize`/`.clip`; `bars.recovery.natural` (shipped at `0.001` in L1 with zero readers);
`replay_buffer.min_size` (two cross-field validators; real gate hardcoded at `vectorized.py:758`);
the entire `curriculum.adversarial:` block, present in every shipped level, read by nobody; the
whole recurrent encoder specification (the factory's own docstring says so); `effects.yaml`
`scope:` (hardcoded to `AGENT`); `recording.enabled` (spawns a thread, writes zero files).

This confirms the severity ranking adopted in `PDR-0002` — declared-but-inert config is the top
defect class for this product — and adds a corollary worth recording as its own finding:
**validation theater**. The schemas enforce cross-field invariants on fields nothing consumes,
which manufactures false confidence. The stricter the validation, the more strongly an author
infers the field matters.

**The mechanism is single and structural:** there is not one test in the repository that takes a
YAML file, changes a value, and asserts the runtime behaviour changed. 139 config tests assert
only that Pydantic accepts or rejects shapes; all 53 DAC tests build config in Python. That
absence is why six consecutive declarative features shipped inert, and it is the one thing worth
fixing structurally rather than case by case.

### Two defects that change what happens first

Both corrupt artifacts *today* and are adopted as immediate work, ahead of the assessment gate's
remaining scope:

- **Compile cache is not keyed on `primary_level`** (`compiler.py:595-598`) — one
  `universe.msgpack` per pack, so requesting a different level can return the wrong artifact, and
  that artifact is what stamps checkpoint provenance (`checkpoint_utils.py:34-42`). For a product
  whose spine is content-addressed provenance, this is the most serious finding in the report.
- **The recurrent path trains a memoryless network** — `forward()` never mutates
  `self.hidden_state` and the training loop never threads it (`networks.py:271-272`,
  `vectorized.py:777-828`), demonstrated by execution. Every training timestep sees zeros. The
  LSTM does not learn, and 12k lines of training tests pass anyway.

## Rationale

REPAIR across the board is the honest reading, not a soft one. The engine half is real: a universe
compiles end-to-end in ~1.0s, emits a frozen provenance-stamped artifact, and drives a tick loop
whose observation vector is assembled purely by iterating the compiled spec. What is missing is
the *join* between the declarative front end and that runtime — plus the specification that would
have made the join checkable. That is a wiring and specification job.

Adopting the embedded DELETE of `recording/` is consistent with the zero-backwards-compat contract
and shrinks two downstream work streams; its async-queue design and versioned msgpack+LZ4 envelope
are salvaged on paper rather than in code.

The recovery shape is adopted as **work streams with dependencies, not a schedule** (§6): WS-0
unblock, WS-1 correctness, WS-2 deletion, WS-3 wiring-test harness, WS-4 close the authoring
surface, WS-5 doc and spec truth. The one genuinely sequential constraint is **WS-1 → WS-3 → WS-4**:
expanding the authoring surface on top of a training loop that does not learn, or a cache that
returns the wrong universe, compounds the damage; and without the wiring harness the next
declarative feature lands inert exactly like the last six. Sequencing and forecasting are **not**
decided here — they route to `/axiom-program-management`.

One scope correction to an existing tracker item: `hamlet-d892e161c0` targets the missing
`frontend/package.json`, but the cause is `.gitignore:94`'s blanket `*.json`. Fixing the manifest
alone reproduces the bug on the next write.

## Reversal trigger

Reopen this PDR if **any** of the following:

- The WS-3 wiring harness, once built, mechanically enumerates an inert set **substantially larger
  than ~40** — that would mean the declarative surface is not half-connected but mostly
  disconnected, and RESPEC or REBUILD becomes the honest disposition for the affected subsystems.
- Fixing the LSTM unroll (WS-1b) reveals the recurrent architecture cannot learn the POMDP levels
  even when correct. The assessment explicitly could not establish whether anything trains well;
  if the fix does not produce learning, SG6's disposition is wrong.
- Any subsystem's REPAIR exceeds the cost of rebuilding it once real work starts. Disposition is a
  hypothesis about cost; contact with the work tests it.
- A runtime confirmation contradicts a source-traced finding. Most of this assessment is traced,
  not executed (§7) — the cache/`primary_level` downstream impact on checkpoint provenance is
  specifically inferred and should be confirmed by execution before large work is built on it.
