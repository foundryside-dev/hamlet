# PDR-0148 — Cut A banks engineering evidence; the acceptance window was missed

Date: 2026-10-01 Australia/Canberra
Status: **superseded by PDR-0149 — original calendar rejection retained as history**
Author: Codex, engineering assessment
Related: PRD-0002, PDR-0147, implementation `hamlet-e62029114c`, acceptance `hamlet-41e79fb08b`

## Subsequent decision

[PDR-0149](0149-owner-extends-cut-a-acceptance-to-october-1-and-cut-a-is-accepted.md)
records the owner-authorized extension and accepts the verified checkpoint. It supersedes this calendar rejection and the resulting Cut B hold.
The original reading below is retained as history.

## Reading

The owner instructed the agent to continue the existing plan on October 1. That authorizes
engineering execution, verification and the planned local recovery-branch integration.
It does not alter PRD-0002's owner-confirmed September 16 acceptance window. No accepted
extension PDR was found or created. The original PRD is preserved unchanged.

PRD-0002 says: “Missing the date without an accepted extension recorded in a PDR is a
reject on every criterion.” Therefore **criteria 1–8 are formally rejected on calendar
grounds**. A green engineering gate does not waive that condition, and this is not an
accepting PDR or a retrospective assertion of owner sign-off.

## Engineering evidence

[The acceptance inventory](../evidence/declaration-cut-a/acceptance.md) records each
criterion's functional reading and reproduction commands. Production checkpoint
`144788f88b4e3c70ab0648e452672f9b61a5b7f2` preserves all 853 semantic readings over
31 cases (884 total readings). Only six raw transport digests move on the two allowed packs.
The exact clean-source CPU matrix exits 0: ten `DIVERGED_AS_REGISTERED` CPU cells and
ten skipped CUDA cells. DIV-013 is input-only; no output allowance is added.

Final executable/test checkpoint `75600ef1802007678b46edbddeb01715d365ca00` repairs
three obsolete test assumptions without changing production source or live configs.
The repaired test groups pass all 24 cases. At preparation, the complete suite and its
hosted Tests row remain running; criterion 7's functional result is therefore pending.
No “gates green” claim is made here. Final command outcomes, every hosted workflow row
at the pushed tip, and the actual local integration commit are recorded after execution
in the implementation/acceptance issues and [draft PR #40](https://github.com/foundryside-dev/hamlet/pull/40).

## Consequence

Complete the already authorized engineering plan and preserve its evidence. Engineering
completion of the implementation issue does not close the acceptance issue. Keep the
acceptance issue open without an accepting PDR. **Cut B does not start.**

An owner decision on the acceptance contract must be explicitly recorded before the
checkpoint can authorize Cut B. This assessment changes neither the deadline nor the
scope, and makes no learning, convergence, browser, CUDA or Murk-integration claim.
