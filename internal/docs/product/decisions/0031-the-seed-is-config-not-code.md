# PDR-0031 — The seed is config, not code: `training.seed` is REQUIRED in every pack

Date: 2026-08-13   Status: **accepted** (within grant — dispatch; implements
`hamlet-834108b55a`'s fix under the no-defaults principle)
Author: Claude (standing product owner)
Related: `PDR-0030` (the oracle this enables), `PDR-0012` (no-tech-debt — no optional-field
escape hatch), `hamlet-834108b55a` (closed `6f60060e`)

## Context

The seeding fix needed an answer to "where does the seed come from?" — the issue specified a
seeding entry point and provenance recording but not the source of the value.

## Options

1. **Required `seed` field in `training.yaml`** — breaks all 25 packs, updates them all.
2. **CLI/constructor parameter with no config presence** — minimal diff, seed lives in shell
   history.
3. **Optional config field with a code default** — no pack breaks.

## The call

**Option 1.** The seed is *the* reproducibility parameter; the no-defaults principle exists
verbatim for this case ("hidden defaults create non-reproducible configs"). Option 3 is the
antipattern by name. Option 2 makes the run's identity invisible to `training_hash` and to
the checkpoint's persisted config — both of which Option 1 gets mechanically for free: the
seed rides `training_hash` into checkpoint identity and lands in `checkpoint["training_config"]`
with zero additional plumbing.

Consequence accepted knowingly: **editing a pack's seed moves `training_hash` and a resume
across it is rejected.** That is correct — a run's identity includes its seed — and it is
the task-4 guard working, not a false positive.

## Reversal trigger

- If the authoring-claim trials (Next bet: the N-idea corpus) show the required seed is a
  recurring stumbling block for novice authors — the field that makes trial authors fail
  compile — revisit the *placement* (e.g. template prominence, error-message guidance),
  never the *requiredness*: an optional seed reopens non-reproducibility by construction.
- If the differential harness needs per-run seed override without pack edits (sweep
  scenarios), extend the door with an explicit override that is itself recorded in the run
  bundle — do not weaken the config field.
