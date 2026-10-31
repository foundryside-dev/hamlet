# PDR-0064 — a parameter the object cannot function without is required, and the check belongs at binding

Date: 2026-08-16   Status: **accepted** (autonomous within the grant)
Author: Claude (standing product owner)
Owner sign-off: not required — an internal API signature change on a pre-release branch with zero
external callers.

Related: `PDR-0045` (behaviour comes from declared parameters), `PDR-0054` (the meter type cut),
`PDR-0061` (the same session's other delivery)
Tracker: `hamlet-9a4b3e9b73` (closed), `hamlet-45b35cfee5` (filed — the same shape in config)
Evidence: commit `e62a5e4a`; mypy clean across 168 source files

## Context

`RecurrentSpatialQNetwork.__init__` declared:

```python
observation_spec: ObservationSpec | None = None
observation_activity: ObservationActivity | None = None
```

and `forward()` opened with a raise saying spec-driven slicing is required. So the network
**constructed successfully without a spec, moved to a device, and failed on first use** — possibly
deep into a training run. The parameter was optional at the type level and mandatory in fact.

`CLAUDE.md` names this shape directly: *"field made `Optional` that should be required → make it
required, set it explicitly in every config."* The in-tree model of doing it right is
`drive_as_code.py`'s `money_bar: str` — required, no default.

## The call

**Make both required, and delete the branch that existed to tolerate their absence.** The
`_use_observation_spec` flag and the `forward()` raise it guarded are gone; the raise is now
unreachable by construction, which is the point — the failure moved from *first use* to *binding*.

Two things this surfaced that are worth recording:

1. **The same defect was one layer up, and mypy found it.** `NetworkFactory.build_recurrent` had
   the identical `| None = None` pair. Fixing only the network would have produced a type error
   papered over with a cast at the boundary; the fix went to the source. Every caller already
   passed both, so production needed no migration — the optionality was never used, only declared.
2. **A dead fixture was asserting a signature that has never existed.**
   `tests/test_townlet/_fixtures/networks.py::recurrent_qnetwork` passed `num_meters=`, which is not
   and has never been a parameter. It had zero users, so nothing ever raised the `TypeError` it
   would have raised. Deleted under zero-backcompat rather than repaired: a fixture with no users
   and a wrong signature is not test coverage, it is a misleading artifact that reads as coverage.

A new test, `test_observation_spec_is_required_at_construction`, asserts `TypeError` when either
argument is omitted, so the contract cannot regress quietly back to optional.

## Rationale

The alternative was to keep the signature and improve the `forward()` error message. Rejected: it
optimises the wrong moment. `metrics.md`'s **Failure loudness** row wants authoring mistakes to fail
at compile time with a clear error; a network that accepts an incomplete construction has already
lost that, and no error text recovers it. The distance between *the mistake* and *the symptom* is
the cost, and the only fix that closes it is making the mistake unrepresentable.

Deliberately **out of scope**, though adjacent and tempting: deriving `bars_dim` from the now-required
`observation_activity` instead of passing it separately. The issue marks it "not a decision", it is
a second change bundled into a verified one, and it can be taken on its own evidence later.

## Reversal trigger

**If a legitimate caller ever needs to construct this network without a compiled observation** — an
export path, a checkpoint-loading path that has weights but no universe (`hamlet-0cdb8a6d1a` is the
live candidate) — then required-at-binding is the wrong shape and the right answer is a separate
constructor for that case, not a reintroduced `None` default.

**If `bars_dim` and the activity ever disagree at runtime**, the derivation deferred above stops
being cleanup and becomes the fix.
