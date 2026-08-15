# PDR-0008 — WS-1 is verified by execution; scope corrected, fix order changed by reachability

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: n/a (within grant — prioritization and acceptance criteria)
Related: PDR-0006 (oracle freeze precondition 2), PDR-0007, metrics.md (Provenance integrity, Failure loudness), tracker `hamlet-67ffbd282a`

## Context

`current-state.md` opened this session with an explicit qualifier on WS-1(a): the
cache→checkpoint-provenance link was **source-inferred, not executed**. `PDR-0006` precondition 2
makes that distinction load-bearing — a defect must be *fixed* before the oracle freeze or
*entered in the known-divergences register*, and you cannot classify a defect you have not
established. Three further WS-1 defects carried the same unverified status.

So the session ran the verification the brief asked for: every claim established by execution,
then two independent adversarial lenses per verdict (reproduce-from-scratch, hunt-for-confound),
then a completeness critic. The instrument was deliberately **not** given the "default to refuting
unless the evidence is overwhelming" instruction that `PDR-0006` identified as having corrupted
the maturity assessment's unanimity into an artifact of prompt design.

## Options considered

1. **Accept the assessment's WS-1 write-up as-is and dispatch the fixes** — pro: fastest. Con:
   `PDR-0006` precondition 2 requires a real classification, and the write-up's own text flagged
   (a)'s downstream impact as unverified. Freezing against an unverified defect list is the
   failure mode the precondition exists to prevent.
2. **Verify by execution, single verdict per defect** — pro: cheap, resolves the qualifier. Con:
   a single verifier produces exactly the unchallenged-verdict problem `PDR-0006` criticised,
   just with the ratchet pointing the other way.
3. **Verify by execution, then adversarially test each verdict on evidence, then hunt for more
   defects of the same family** — the option taken.

## The call

**Option 3.** WS-1 defects (b), (c), (d) and the two session findings are **confirmed by
execution**. The fix order within WS-1 is changed on reachability grounds, and four claims are
retired as false alarms.

### What was established

- **(a) compile cache not keyed on `primary_level`** — CONFIRMED, and worse than written. The
  guard that should catch it is neither missing nor bypassed: `assert_checkpoint_vfs_hash` is
  **satisfied by a corrupted comparand**, because it compares the checkpoint against
  `self.compiled` and never against the level the caller requested. End-to-end through the real
  `DemoRunner.run()`, an L0-trained network silently resumed into a correct L2 run; the corruption
  is *hybrid* — the right level's physics with the wrong level's weights — and no shape check can
  see it, because L0 and L2 share a deliberately identical 124-dim/15-action ABI down to identical
  `observation_field_uuids`. The L2 run then wrote a checkpoint stamped with L0's identity, so the
  mislabelling is **inverted and permanent**: a later honest L0 run accepts it, a later honest L2
  run rejects it.
- **(b) recurrent path trains memoryless** — CONFIRMED [2/2 lenses]. `lstm.weight_hh_l0` received
  exactly zero gradient across 231 real training updates.
- **(c) subsequence boundary treated as terminal** — CONFIRMED [2/2]. 448/448 mid-episode window
  boundaries lost their bootstrap term; bites 1-in-8 transitions at the shipped `sequence_length: 8`.
- **(d) live `apply_interaction` weaker than `apply_instant_interaction`** — CONFIRMED [2/2] but
  **narrowed**: carried entirely by the *affordability* leg. The clamp leg is largely an artifact
  of comparing against a hand-chosen alternative and must not be specced as independently established.
- **New: four per-level content hashes stamped by nobody** (`hamlet-ae6601e463`) — `bars_hash`,
  `affordances_hash`, `curriculum_hash`, `training_hash` are computed, serialized, round-tripped
  through the cache, and read by zero consumers. They move on exactly the divergences that load
  silently today. Folds in `brain_hash` certifying the *pre-override* brain.
- **New: the serving path runs zero identity guards** (`hamlet-1029f99f4b`) — A/B verified:
  `DemoRunner` raises on a mismatched checkpoint; `LiveInferenceServer` loads it with no exception
  and no guard invoked. This is the tech-demo path.

### Four claims retired — recorded so nobody re-files them

1. `observation_schema_hash` "compared nowhere" — technically true, practically a non-finding: it
   is an input to `compute_vfs_hash`, so it is transitively validated.
2. Same for `variable_schema_hash`, `action_schema_hash`, `transition_graph_hash`.
3. `config_mtime` "never compared" — it is, at `compiler.py:131`, via `>=`.
4. "A poisoned `.compiled` cache ships to every clone" — **wrong**; `.gitignore:126` has
   `*.msgpack`. Verified directly with `git check-ignore`. The poison is confined to a working tree.

### The fix order changes

(b) and (c) are correct and **unreachable on all 21 shipped packs** — zero packs configure a
recurrent architecture. Their pre-freeze case is *config-reachable*, not *config-reached*.
Recommended order: **(a), (d)-affordability, the four-hash stamp, then (b), then (c)** — with
(a) and (d) first because they are live today. (b) and (c) still land before the freeze:
an unreachable-today defect becomes a frozen requirement the moment `PDR-0009`'s work makes a
recurrent pack possible.

One implementation hazard is recorded on the tracker rather than here: **(c)'s spec does not
compile against (b)'s**, and (c)'s pinning-test mitigation is void once (b) deletes
`self.hidden_state`. It must be rewritten against (b)'s post-fix API, not extended.

## Rationale

Option 3 beat option 2 because the adversarial pass changed four substantive things a single
verdict would have shipped wrong: it narrowed (d) to one leg, overturned a verifier's downgrade of
the `config_hash` finding *toward greater severity*, killed four false alarms, and found the
(b)→(c) API incompatibility. Option 1 was excluded by `PDR-0006` precondition 2 on its own terms.

The reachability finding is the result that most changes what happens next, and it came only from
the completeness critic — the stage whose job was to ask what had *not* been checked.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **A WS-1 fix lands and the differential harness (WS-3) shows no behavioural change** where one
  of these verdicts predicted one. That would mean a probe measured something the product does not
  do, and the verdict rests on an artifact.
- The four-hash stamp (`hamlet-ae6601e463`) turns out to require widening an existing hash rather
  than stamping an existing one. The claim that it is the cheapest fix in the set is load-bearing
  for its priority; if it is not cheap, it re-sequences against (a).
- A recurrent pack is authored (per `PDR-0009`) and (b)/(c) prove to have *additional* unverified
  consequences beyond zero-gradient and lost-bootstrap. The verdicts were established on
  hand-driven paths; first real recurrent training is the honest test.
