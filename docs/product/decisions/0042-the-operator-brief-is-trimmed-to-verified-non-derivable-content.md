# PDR-0042 — The operator brief is trimmed to verified, non-derivable content; task workflows move to lazy loading

Date: 2026-08-15   Status: **accepted** (within grant — internal repo documentation, git-reversible;
owner approved the full action set in-session and committed the result themselves at `1c2ab8a0` /
`8ffca2ca`)
Author: Claude (standing product owner)
Related: `PDR-0026` (only the owner rules on lie vs unbuilt intention), `PDR-0038`/`PDR-0039` (the
documentation-truth thread this continues), `PDR-0041` (whose falsifying commit corrected the
substrate list — this trim finished the job on the rest of the file)
Tracker: `hamlet-312f75963b` (hook duplication/timeout bug, P3), `hamlet-5e2032b166` (delete
vendored axiom-* skill packs, P3) — both follow-ups filed from the same audit

## Context

A `/doctor` audit of the session tooling found that the root `CLAUDE.md` — 26,031 chars, ~6.5k
tokens loaded into **every agent session on this repo** — carried four *live self-contradictions*:
stale claims sitting in the same file as the verified corrections added over the past week.

1. The flat `configs/<level>/` pack-layout diagram, beside the corrected layout that says exactly
   that shape does not exist.
2. `drive_as_code.yaml` described as the required reward file, beside the verified warning that no
   file of that name exists in any shipped pack.
3. The "Example: L0_0_minimal" YAML showing a `multiplicative` extrinsic, beside the ⚠️ stating no
   shipped level declares one.
4. The "29→8 architecture" network literals, beside the warning that observation-dim literals were
   ~4× wrong and deliberately left unreplaced *because literals decay*.

Plus stale training commands pointing at `configs/L0_0_minimal` — a path that does not exist. The
file's own history is the argument: every derivable literal written into it eventually rotted, and
the corrections were then written *next to* the rot instead of replacing it. An operator brief that
argues with itself trains sessions to distrust the parts that are true.

## Options

1. **Leave as-is.** Preserves bulk; leaves four contradictions load-bearing in every session.
2. **Re-verify and update every stale claim in place.** Honest today; every refreshed literal
   resumes decaying tomorrow. This is how the file got here.
3. **Trim to the non-derivable stratum** — verified findings, contracts, gotchas, safety rules —
   delete what a session can re-derive from the repo, and move task workflows to lazy-loaded
   files. *(Chosen.)*

## The call

**Trim.** Owner approved the consolidated cleanup in-session ("Clean up everything") and committed
the result themselves. `CLAUDE.md` went 26,031 → 20,688 chars (−173/+20 lines). Cut: the stale
layout diagram, the `drive_as_code.yaml` remnants, the misleading DAC example, the network-shape
literals, the directory tree, the strategy-type enumerations (pointer to
`docs/config-schemas/drive_as_code.md` kept), the textbook DQN section (pointer kept), and the
standard command blocks. The training invocation was corrected against `run_demo.py`'s actual
argparse (`--config configs/default_curriculum --level <name>`) — verified, not guessed. **Every
⚠️ verified-finding block, the curriculum reality table, and all gotchas and safety rules
survive.** The two-terminal inference workflow moved to `.claude/skills/live-inference/SKILL.md`;
frontend guidance moved to `frontend/CLAUDE.md` (loads only when working under `frontend/`).

Under the same approval, machine-local tooling hygiene was executed (two plugins idle since June
disabled; seven vendored duplicate skills suppressed via gitignored `.claude/settings.local.json`;
four disposable plugin-cache temp directories deleted — the only deletion, on the owner's machine,
with explicit in-session approval). The two repo-relevant follow-ups are tracker items, not
workspace prose.

## Rationale

The documentation-truth discipline (`PDR-0038`, `PDR-0039`) says claims must be verified and must
name their scope. Derivable content is where stale claims breed — it is exactly the material
nobody re-verifies because the code already answers it. What remains after the trim is the stratum
that *cannot* be re-derived (verified findings, failure contracts, the authority notes), which is
also the stratum worth the re-verification effort when it does change.

## Reversal trigger

- **Restore a cut section (from verified source, not from git alone)** if sessions are observed
  acting on a wrong belief the cut content would have corrected — re-deriving a deleted
  enumeration wrongly, or losing time hunting for what the deleted tree showed. **Two such
  incidents against the same section** means that section was load-bearing; it comes back,
  re-verified.
- **Re-open the lazy-loading split** if the moved files fail to load when needed — frontend work
  proceeding without `frontend/CLAUDE.md` in context, or the live-inference stack being
  re-derived instead of the skill surfacing.
- This is documentation hygiene, not a north-star mover: the falsifiable condition is the
  observed-incident count above (session evidence), deliberately not a `metrics.md` row.
