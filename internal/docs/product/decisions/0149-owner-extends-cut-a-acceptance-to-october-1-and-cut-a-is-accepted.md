# PDR-0149 — The owner extends Cut A acceptance to October 1; Cut A is accepted

Date: 2026-10-01 Australia/Canberra
Status: **accepted — owner-authorized date extension and evidence-based acceptance**
Author: Codex
Owner instruction: “yeah, but lets just extend the date instead”
Related: PRD-0002, PDR-0147, PDR-0148, implementation `hamlet-e62029114c`, acceptance `hamlet-41e79fb08b`

## Decision

Extend PRD-0002's acceptance deadline from September 16 to **October 1, 2026, end of day
Australia/Canberra**. The owner authorized the extension; the agent selected October 1
because that is the actual completion date of the verified checkpoint. The owner did not
specify a separate date. No technical criterion, hash bar, scope or evidence requirement changes.

September 16 was missed. PDR-0148 remains the historical reading under the original window;
its calendar rejection and resulting hold are superseded by this decision. This does not
assert that the original deadline was met.

Accept Cut A at engineering checkpoint **`75383d189a57546b5ae8871eb996041b742457de`**,
which completed within the revised window. This is the tested implementation checkpoint;
the date amendment changes documentation and tracker state only. It does not pretend that
older CI jobs tested a later documentation commit.

## Criterion readings

| PRD criterion | Verdict | Evidence at the implementation checkpoint |
| --- | --- | --- |
| 1: Strays loud | PASS | Original five blobs committed in a refusal fixture before live correction; public compiler names every path and line. `experiment` is consumed, as A4 establishes. |
| 2: One clock authority | PASS | L3 uses `period_of`; invalid targets and duplicated coupled facts refuse with declaring origins. |
| 3: Required declaration | PASS | Renamed/nested and multi-document witnesses compile; missing family names the declaration. |
| 4: Collisions loud | PASS | Singleton/catalog collisions at pack and level scope name both actual origins. |
| 5: Provenance | PASS | Registry-linked witnesses cover all 21 codes in the four pinned refusal families and require source/positive line. |
| 6: Hash bar | PASS | Before snapshot committed at `ee520090` before production edits; 31 cases, 884 readings, all 853 semantic readings identical, six permitted transport digests changed, zero unexpected changes. |
| 7: Gates/harness | PASS | Full local pytest: 3972 passed, 18 skipped, 84% coverage; post-integration: 38 passed. Ruff/Black/mypy/no-defaults/CLI pass; whitelist unchanged. Exact-tip CPU matrix exits 0 with ten registered CPU cells and ten CUDA skips. All three hosted workflows pass at the checkpoint. |
| 8: Hygiene/docs | PASS | Obsolete filename readers/dispatch removed; canonical authoring references corrected; remaining literals and the observer boundary explained. |

Commands and the before/after hash comparison are in the
[acceptance evidence](../evidence/declaration-cut-a/acceptance.md).
CPU run: `declaration-cut-a-cpu-75383d18`; clean source, exit 0.
DIV-013 uses only PRD criterion 7's explicit pack-drift-only allowance; no output fields or
streams are added. The earlier production-source report is banked with the evidence;
the repeated exact-tip report remains in the retained task worktree.

Every hosted row was read at `75383d189a57546b5ae8871eb996041b742457de`:

- [Tests 36743412101](https://github.com/foundryside-dev/hamlet/actions/runs/36743412101): completed/success.
- [Config Validation 36743412391](https://github.com/foundryside-dev/hamlet/actions/runs/36743412391): completed/success.
- [Lint 36743412251](https://github.com/foundryside-dev/hamlet/actions/runs/36743412251): completed/success.

Capacity review remains unchanged: ground-plus-held token headroom exceeds world-only
registry capacity; durability rows and held-item invisibility remain out of scope
(`hamlet-obs-b959ce55c0`, `hamlet-4b931faaf4`). Frozen oracle and its 108 fixture files
are unchanged. This acceptance does not claim item-cache repair, learning convergence,
browser qualification, CUDA qualification or Murk integration.

## Consequence

Close acceptance issue `hamlet-41e79fb08b` with this PDR and the recorded criterion readings.
The Cut A checkpoint gate is satisfied; Cut B can proceed under PDR-0147's existing scope.
No Cut B implementation or main merge is performed by this date amendment.
