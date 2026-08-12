# PDR-0030 — The oracle is pinned: `oracle-2026-08-13` at `0e875d7a`

Date: 2026-08-13   Status: **accepted** (within grant — dispatch/accept; the GPU-first
sequencing was proposed to the owner this session and explicitly endorsed: *"yes, your rec
is endorsed, it would be a shame to lose that when it 'should' be cheap"*)
Author: Claude (standing product owner)
Related: `PDR-0006` (the strangler this enables), `PDR-0028` (the register the tag depends
on), `PDR-0029` (WS-1 close — its first reversal trigger binds to this tag)
Tracker: `hamlet-e3af412673` (WS-7), `hamlet-834108b55a` (seeding, closed `6f60060e`)

## Context

The strangler's every knockdown is judged against a frozen reference. Pinning it is the
single most load-bearing call in the programme: the tagged commit *becomes the spec* for
preserved behaviour. Preconditions per `PDR-0006` and the WS-7 stream: WS-1's defects fixed
(else frozen as requirements), the known-divergences register standing (else intended
diffs are indistinguishable from rebuild defects), and determinism exposed (else the
differential harness cannot compare traces at all).

## Options

1. **Tag at `6f60060e`** (seeding landed, CPU determinism verified) — earliest eligible.
2. **Verify GPU + TorchScript-JIT determinism first, then tag** — one more session-hour;
   closes the "both untested" gap in WS-7 content 1 before the freeze depends on it.
3. **Defer the tag until the differential harness exists** — tag and harness co-designed.

## The call

**Option 2 — taken, owner-endorsed.** GPU determinism was cheap to verify (this machine has
CUDA) and load-bearing to know *before* the freeze: if GPU traces were nondeterministic, the
harness design would change (CPU-side comparison). Option 3 inverts the dependency — the
harness needs a fixed old side to be written against.

Verified: same seed → bit-identical 40-step env trace on CUDA, through the
`@torch.jit.script` vtc kernels (unconditionally on the step path, so JIT is covered by the
same trace). Tag pinned at `0e875d7a` with one clean full-suite run at that exact commit
(2992/16/0) and all static gates green.

## Scope honesty

The tag's determinism claim is **env-step trace determinism** — what the harness consumes.
Training-loop determinism on GPU (cuDNN backward) is explicitly unclaimed and unverified;
`ORACLE.md` says so in its own section. Claiming it would repeat the Gates-green lesson:
a recorded property nobody measured.

## Reversal trigger

- **`PDR-0029` trigger 1 was tested and did not fire**: every WS-1 pinning test is green in
  the full run at `0e875d7a`.
- **Move the oracle forward** (new tag after the fix lands, old tag retained, register
  re-stamped) if a pre-tag defect is found that fails `PDR-0028`'s carry test — i.e.
  freezing it would freeze artifact corruption rather than a known quirk. The oracle is
  never mutated and never silently re-pointed.
- **Re-open this decision** if the differential harness, once built, cannot reproduce the
  oracle's traces from the recorded seeds on either device — that would mean the
  determinism evidence was insufficient and the tag was pinned on a false floor.
