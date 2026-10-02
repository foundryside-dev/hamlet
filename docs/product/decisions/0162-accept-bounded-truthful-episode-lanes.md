# PDR-0162 — Accept bounded truthful episode lanes

Date: 2026-10-02 Australia/Canberra. Status: **accepted — local implementation**.
Owner instruction: implement the reviewed plan and have Astra review implementation.
Related: PRD-0005, PDR-0158/0159/0160/0161, DIV-016,
execution `hamlet-78ad37dd49`, engine bug `hamlet-d6fc84d147`.

## Decision and evidence

Accept [PRD-0005](../prds/0005-truthful-episode-lanes.md) at
`7dc1d02e78d8b70bd096fc4c84b4d95a9822c94f`, tree
`6551ba43c94a2a942ea0ecf04e3e3f8b8659cba1`. The independent
[Astra implementation review](../evidence/episode-lanes/implementation-review.md)
accepts all eight criteria, with no remaining blocking finding. The complete
[verification record](../evidence/episode-lanes/verification.md) and
[receipt](../evidence/episode-lanes/verification-receipt.json) retain commands,
source/environment identity, actual results, causal cuts and artifact digests.

Authored survival is `[2,5]`, seven eligible transitions and five world ticks:
accounting error zero. Terminal experience is retained once; standard/PER and
recurrent replay, novelty statistics and actual predictor training exclude later
dead rows. Canonical retirement reward occurs once, authored death wins boundary
coincidence and completed outcomes own their snapshots. Explicit cuts preserve
MDP bootstrap semantics. Ordinary persisted DB/TensorBoard/curriculum/indexed
recording/replay/observer and both actual exporters reconcile eligible outcomes.
Nested population checkpoint format6, recording format2 and database schema1
refuse unsupported artifacts without compatibility paths or migrations.

Astra's original implementation review rejected58a because curve exports opened
an original historical WAL-mode DB and created sidecars before refusing it.
The repaired production candidate462e validates raw custody/schema and reads an
isolated snapshot; real refusal/success/late-event controls preserve originals.
The original failed probe and NOT ACCEPTED review are retained. Astra independently
reproduces the repaired scenario and all31 custody cases; R1 is resolved.

At production source `462e8a3980845d76e7987cfea67fb63432bcb847`, the unfiltered
full suite collects4,670: **4,652 passed,18 skipped,31 warnings,85% branch
coverage**, exit0. Ruff/Black/mypy/no-defaults/compiler/33-pack gates also pass.
All individual skips remain reported. Allocation-traced RED identifies16 SQLite
warnings in five test validation reads. Final7dc1 changes only two imports and
five `contextlib.closing` contexts. The other1,059 execution files of the1,061
inventory remain byte-identical, including production/config/scripts/lock and
all other tests. Owning and independent strict30-case affected/pipeline gates
pass with zero warnings and forced collection after every call and teardown.
Plan F expressly permits affected gates during receipt preparation; this exact
reviewed closure carries the complete462e evidence forward. There is no fresh
full suite at7dc1 and the original31-warning reading remains unchanged.

## Qualified attribution and limits

Six frozen lifecycle recipes verify799 declared changes and4,008 other exact
parent readings. Eight final learned numerical recipes match complete earlier
controlled payloads and perform actual Q/predictor updates. PDR-0160 prospectively
qualifies CPU-controlled reset comparisons only; the natural-reset bank remains
unqualified and production RNG isolation is excluded.

Both original inherited static-access and scripted frozen commands retain exit1.
PDR-0161 qualifies exactly seven earlier-dead false retirement-bonus removals with
a prospectively reviewed frozen checker, full source/input closures and42 rejected
corruption controls. Every other reward byte and genuine retirement remains
exact. Original reports, dirty flags, frozen fixtures and register/matrix allowances
remain intact. This bounded qualification does not relabel either literal gate
passing and does not satisfy PDR-0058's recovery exit.

Choose accepted local bounded implementation over indefinite rejection of the
already attributed boundary correction or broadening inherited allowances. The
first ignores independently verified intended behavior; the second would hide
unrelated changes. Close the verified engine bug and implementation task through
their normal tracker transitions, anchored to the final local documentation
commit. Preserve the owner-selected feature branch and all worktrees/artifacts.

Local branch integration is separate from a future main merge, push, PR and
hosted CI. There is no CUDA, convergence, public release or recovery-exit claim.
Effects reset, initial-item fidelity, RNG isolation, warmup redesign and full BAC
remain separate work. Do not reopen a learning campaign from this receipt alone.

## Reversal and backout

Reopen acceptance if an eligible terminal row is lost, later dead row admitted,
completion/reward repeated, outcome aliases mutable state, persisted consumers
disagree, a refused original family changes, or any frozen/source/control binding
fails. A new unexplained boundary needs prospective adjudication rather than a
broader allowance. Further executable changes require affected gates and renewed
independent review. Documentation-only landing must preserve all accepted
execution bytes.

Backout restores the prior source checkpoint with fresh run/database paths while
preserving every historical and newer artifact. Old source must not consume newer
formats. No artifact deletion, migration or oracle re-freeze is authorized.
