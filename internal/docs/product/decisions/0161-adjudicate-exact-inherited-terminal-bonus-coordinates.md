# PDR-0161 — Adjudicate exact inherited terminal-bonus coordinates

Date: 2026-10-02 Australia/Canberra. Status: **accepted — bounded E4 qualification**.
Related: PRD-0005 criterion seven, PDR-0158/0159/0160, preregistered DIV-016,
execution `hamlet-78ad37dd49`. The owner requested implementation of the reviewed
plan and an independent Astra implementation review.

## Retained failure and cause

The unchanged static-access command at source
`8e3ca306d6f615bd272bb1c8d51b071b74686877` returns nonzero:
31 inventories/884 identity readings and eleven reset recipes agree, as do all
observation/action/done streams. Two reward streams differ. The unchanged frozen
`--scripted` harness also returns nonzero: eight CPU cells retain their registered
verdicts; the same two cells are DIVERGE, with ten explicit CUDA skips. Preserve
both original reports, logs, traces and dirty flags unchanged. Neither literal
command is a passing gate at this source.

Exactly seven reward coordinates change. Coordinates are zero-based trace
row/agent, with 100 world ticks and four agents:

| Cell | Row | Agents | Parent/frozen reward | Candidate reward |
| --- | --- | --- | --- | --- |
| items_smoke:L0_smoke:cpu:seed42 | 99 | 0, 1, 3 | 1.0 | 0.0 |
| effects_smoke:L0_effects:cpu:seed42 | 99 | 0, 1, 2, 3 | 1.0 | 0.0 |

Both packs declare lifespan 100. Those lanes had already completed at ticks
49/51/54 and 65/67/62/60 respectively. The parent increments completed lane
counts to 100 and manufactures a retirement reward. E2 freezes their counts at
actual survival and removes that reward; E3 adds no further stream differences.
The items lane two genuinely retires at tick 100 and retains its exact reward
`1.0099999904632568`. No live reward, action, done, world input or reset changes
are admitted by this decision.

This is the earlier-death/later-retirement defect whose correction was recorded
in DIV-016 before the runtime cut. The E4 plan explicitly requires retaining an
inherited command's failure and adjudicating a legitimate terminal boundary
through a scoped comparator/PDR. The format-four standing harness can observe
these lifespan-100 packs, even though it cannot qualify the configured 1000-tick
boundary or replay/RND/completion accounting. Its existing registered observation
ABI differences remain separate from these seven reward coordinates.

## Proposed bounded qualification

Keep the static-access tool, frozen source/fixtures, matrix and existing register
allowances unchanged. Do not add a reward-stream allowance or reinterpret either
original nonzero exit as zero. Preregister a separate exact-coordinate
adjudication before executing its acceptance gate:

1. Require complete declared inventories and retained valid source/config/import
   closures. The static comparison must still report zero identity changes,
   exact resets and only the two specified reward mismatches. All ten raw CPU
   trace inventories must remain present.
2. Compare entire raw observation/action/done arrays exactly for the direct-parent
   bank; compare entire reward arrays except for the seven literal old/new values
   above. Require equal shape and dtype, finite numeric values and exactly the
   specified seven coordinates, including rejecting a missing or unused expected
   change. Equal aggregate totals do not qualify substituted coordinates.
3. Independently derive entry eligibility and survival from the full sticky-done
   trajectory. Each changed coordinate must be dead on entry, have true survival
   below 100 and no retirement event. Bind the actual E2/E3 lifecycle readings
   and reward components to those independently counted events and full causal
   commits. Require the genuine retirement row and every live reward unchanged.
4. Bridge frozen → preserved parent → E2 → E3 → candidate with the actual frozen
   recorded actions and unchanged authored config bytes. Keep the existing
   frozen observation/provenance registrations; compare all other streams in
   full, allowing only the same seven reward coordinates. Record the unchanged
   action-array equality rather than assuming the two action recipes coincide.
5. Retain the standing report's other eight CPU verdicts and ten explicit CUDA
   skips. The separate adjudication may qualify the two concrete DIV-016
   corrections only after every exact input/value/event check passes; it does
   not accept CUDA, learning, convergence or the broader recovery exit.
6. Demonstrate failing corruption controls for a changed live reward, a retained
   false bonus, a dropped expected difference, swapped lane coordinates, changed
   action/observation/done, nonfinite reward, wrong eligibility/survival, stale
   allowance and corruption of the genuine retirement reward. Originals remain
   byte-identical; mutations are made only to private copies.

Independent Astra review must approve this concrete instrument adjudication
before its qualification gate is executed. Freeze the checker and prospective
coordinate specification before that execution. If a check fails, retain the
failure and return the candidate unaccepted; no broader allowance may make it
green. Final verification reports must list both original literal gate failures
and the independently approved narrow adjudication, with their actual exits.

No runtime, scheduling, RNG, artifact, oracle-harness or matrix repair enters
this decision. Criteria one through eight, actual sample/target evidence,
ordinary persistence and the unfiltered full suite remain required. This
decision itself supplies no implementation acceptance or publication claim.

## Prospective review and registration

Independent Astra review approved the plan-authorized method, required a stronger
checker, then approved the completed checker and final source fence before GO.
The final candidate is `462e8a3980845d76e7987cfea67fb63432bcb847`.
Exactly two source files change from the retained gate candidate: the separately
reviewed database/exporter private-read repair. Four actual final driver/collector
bridges match the earlier candidate exactly, including lifecycle/components.
All 157 original evidence bindings and 434 configuration bindings remain; 25
additional final files produce 182 evidence bindings. There are 42 required
corruption controls, including signed-zero and provenance/inventory controls.

The [complete prospective specification and checker](../evidence/episode-lanes/inherited-terminal-registration.md)
were frozen at `2026-10-01T23:34:54.541302Z`, before qualifier execution. Checker
SHA256 is `05fa08a7d36fdc0222339fc23f867c971d221a0270b41ab0784f21ca86397a27`;
completed specification SHA256 is
`471412bcd3016b9a76bc739caf455386b3214729734b7229fb29fc403ea512da`;
registration SHA256 is
`92db55423cff0faa4a43be8bd0083ad4adf6a7e51a8676f5b0e3cce346ae6a75`.
The root issued GO only after the independent final fence check and registration.
The first actual qualifier execution returns 0 and rejects all 42 controls.
Its result SHA256 is
`de959b9badd4b76ed85c3658dd9913c4ad778c2313e97ca72aaec4d81b772b2a`.
The retained attempt is
`causal/inherited-terminal-streams/qualification-attempts/20261001T233600045324Z/`
under the implementation artifact root. Source/artifact/config snapshots are
unchanged before and after. Independent Astra audit verifies the prospective
timeline, actual output/exit, exact controls, full fences and both preserved
original failures. This qualifies bounded E4 only; PRD implementation acceptance
still requires its remaining gates and final criterion review.

## Options and reversal trigger

Keep the two literal gates failed and the candidate unaccepted indefinitely;
broaden their reward-stream allowances; or use the reviewed exact-coordinate
consumer while retaining those failures. Select the third under the existing E4
policy because it adjudicates the already registered defect with complete raw
evidence and falsifiable controls. Broad allowances would conceal live changes.

Reopen this decision and refuse acceptance if any original input/report digest,
source fence, undeclared reward byte, event/component check or required corruption
control fails. A new coordinate or changed cause requires another prospective
review; it cannot be absorbed into this seven-coordinate decision.
