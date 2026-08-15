# Docs Reconstitution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Archive the current `docs/` tree wholesale to `docs-archive/2026-05-16-pre-reconstitution/`, rebuild `docs/` as a small, source-derived set of 13 files (1 index + 12 pages), **and refresh the root-level project docs** (`README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`) so they cite live code anchors and link into the new `docs/current/` tree — never copy claims from the archived tree.

**Architecture:** Single physical move (`git mv docs docs-archive/2026-05-16-pre-reconstitution`) preserves history while removing every stale doc from search results. The new `docs/` is built file-by-file from source (`src/townlet/`, `configs/default_curriculum/`, `tests/`, `pyproject.toml`), not from the archive. Root docs are refreshed *after* the new `docs/current/` set exists, so they can link into the canonical pages rather than re-stating facts. Each new or refreshed doc must pass a "no stale claim" grep gate and an "anchors compile" verification command before its task closes.

**Out of scope (no edits):** `LICENSE` (legal text), `CODE_OF_CONDUCT.md` (standard Contributor Covenant — no project-specific drift). `DEPENDENCY_ANALYSIS_SUMMARY.md` is treated as a historical analysis artifact and moved to the archive rather than refreshed (Task 14).

**Tech Stack:** Markdown (CommonMark). Verification uses `uv run python -m townlet.universe validate`, `uv run pytest`, and `rg` (ripgrep) for stale-claim gates.

**Writing contract (binding on every task below):**

1. Source is authority. If `src/` and the archived docs disagree, source wins; the archive is never consulted as evidence.
2. Every factual claim cites a live anchor (`path` or `path:LN`) per the Source-anchor preference rule below.
3. Every page lists a verification command the reader can run, and the expected outcome.
4. No backwards-compatibility framing, no "supports old and new," no migration prose. Pre-release; zero users.
5. **Banned stale terms** (must `rg` to zero hits in the new `docs/` tree before closing the doc tasks):
   - `seven-stage` / `seven stage` (compiler is no longer described that way; see Task 7)
   - `drive_as_code.yaml` (the per-level file is `drive.yaml`; see `configs/default_curriculum/levels/L0_0_minimal/drive.yaml`)
   - `variables_reference.yaml` (replaced by shared `vfs_profiles.yaml` at the pack root)
   - `RewardStrategy` and "reward_strategy field" as a config concept (gone; reward is composed under DAC, but DAC is not a peer subsystem — it is a reward composition layer)
   - Any specific coverage percentage; coverage is measured per run, never hard-coded in prose
   - `src/hamlet/` (obsolete; package is `src/townlet/`)
6. The frontend is partially scaffolded: `frontend/` has `index.html`, `vite.config.js`, `src/`, but **no `package.json`**. Any `npm run dev` mention must be qualified as conditional on hamlet-d892e161c0 landing.
7. **Stale-callout marker.** When a doc legitimately names a banned term in a "this is gone" context (Task 2's "Where not to look" paragraph, Task 5's replacement notes, Task 17's CLAUDE.md edits, Task 20's CHANGELOG entry, the docstring of an archived module reference), prepend the line with an inline HTML comment exactly: `<!-- stale-callout: <term> -->`. The master sweep uses this marker as the only allow-list signal. No prose narrowing.
8. **Pytest-output marker.** When a doc legitimately includes pasted `pytest` or `coverage` output that contains a percentage, wrap the fenced block on its own preceding line with `<!-- pytest-output -->`. The coverage-percentage gate uses this marker as the only allow-list signal.
9. **Archive exclusion.** Every `rg` sweep must pass `--glob '!docs-archive/**'` so that intentionally stale archived files cannot satisfy or trip a gate. The archive is reference-only and exists outside the verification surface.
10. **Source-anchor preference.** When citing live source, prefer stable symbol references over line numbers. Choose anchors in this priority order:

   1. **Stable symbol** — `UniverseCompiler.compile` in `src/townlet/universe/compiler.py`. Survives unrelated edits anywhere in the file.
   2. **Path-only** — `src/townlet/universe/compiler.py`. Use when the entire file is the unit of reference (e.g. "the compiler is implemented in...").
   3. **Path + line** — `src/townlet/universe/compiler.py:92`. Use only when the cited content has no nameable symbol (e.g. a specific `raise` inside a method body, a constant inside a dataclass field). Append a `<!-- anchor-drift-check: <YYYY-MM-DD> -->` HTML comment immediately after such anchors. These comments are **manual re-verification reminders for the executor**, not gate-enforced — there is no automatic 30-day flagging in Task 21. Anyone editing the cited file should refresh the date when they confirm the anchor still points where the doc claims.

   Task 21 (Step 21.10) verifies anchors by file existence, not line accuracy and not comment freshness. An executor who picks a stable symbol anchor (priority 1 or 2) protects the doc from silent drift; an executor who picks priority 3 accepts the cost of manual re-verification when the dated comment becomes old.

---

## File Structure

**Archive (one move, no edits):**

- Move: `docs/` → `docs-archive/2026-05-16-pre-reconstitution/`

**New docs tree (14 files, all created fresh):**

- Create: `docs/README.md` — index, source-of-truth policy, what is and is not authoritative
- Create: `docs/current/project-brief.md` — what the project is today, in one page
- Create: `docs/current/architecture-map.md` — subsystem map, the compact "new HLD"
- Create: `docs/current/config-model-v21.md` — pack layout (shared root + per-level)
- Create: `docs/current/universe-compiler.md` — compiler stages as they exist in source
- Create: `docs/current/runtime-environment.md` — `VectorizedHamletEnv` construction and golden path
- Create: `docs/current/actions-and-observations.md` — ActionCompiler output, observation construction
- Create: `docs/current/vfs-vtc-dac.md` — VFS profiles, VTC transition schedule, DAC reward composition
- Create: `docs/current/training-checkpoints.md` — DemoRunner, replay buffers, checkpoint provenance
- Create: `docs/current/demo-frontend.md` — CLI demo flow and frontend state
- Create: `docs/current/testing-quality-gates.md` — test layout, markers, canonical commands
- Create: `docs/current/glossary.md` — one canonical vocabulary
- Create: `docs/current/known-gaps.md` — generated from live Filigree only

**Root docs (refreshed in place, after the new `docs/current/` tree exists so they can link to it):**

- Move: `DEPENDENCY_ANALYSIS_SUMMARY.md` → `docs-archive/2026-05-16-pre-reconstitution/DEPENDENCY_ANALYSIS_SUMMARY.md` (Task 14 — historical analysis artifact, not a maintained doc)
- Modify: `README.md` (Task 15) — rewrite body; preserve title/badges/license link
- Modify: `AGENTS.md` (Task 16) — de-duplicate against `CLAUDE.md`; keep agent-facing operational rules only
- Modify: `CLAUDE.md` (Task 17) — strip stale claims (mandatory `variables_reference.yaml`, unverified `drive_hash`, `src/hamlet/` mentions); align with new `docs/current/` anchors
- Modify: `CONTRIBUTING.md` (Task 18) — update dev commands and link to `docs/current/testing-quality-gates.md`
- Modify: `SECURITY.md` (Task 19) — verify each policy claim against current state; light edits only
- Append: `CHANGELOG.md` (Task 20) — one entry under `## [Unreleased]` recording the reconstitution. Do **not** rewrite historical entries.

**Plan self-preservation:** This plan lives at `plans/2026-05-16-docs-reconstitution.md` outside `docs/`, so the archive step does not consume it. Do not move this file.

---

### Task 1: Archive the existing `docs/` tree

**Files:**
- Move: `docs/` → `docs-archive/2026-05-16-pre-reconstitution/`

- [ ] **Step 1.0a — Remote-branch sweep for docs/ changes**

Fetch all remotes and check whether any remote branch carries `docs/` or `scripts/docs_gate.py` changes relative to `origin/main`. If any branch does, it must be coordinated, frozen, or merged before Step 1.3 proceeds — this is an operator decision and cannot be automated.

Run:

```bash
git fetch --all --prune

git for-each-ref --format='%(refname:short)' refs/remotes/ \
  | grep -v '/HEAD$' \
  | while read branch; do
      diff=$(git diff --name-only "origin/main..$branch" -- docs/ scripts/docs_gate.py)
      if [ -n "$diff" ]; then
        echo "=== $branch ==="
        echo "$diff"
      fi
    done
```

Expected: No output (no remote branch touches `docs/` relative to `origin/main`). If any branch produces output, stop and document a coordination decision for each one before continuing to Step 1.3.

DoD: Paste the full output of the sweep into the execution log. For every branch with non-empty output, document the chosen resolution — one of: (a) rebase the branch onto the post-move tree, (b) freeze the branch and coordinate with the PR author, or (c) merge the branch before this task runs. Do not proceed to Step 1.3 until all affected branches have a documented decision.

- [ ] **Step 1.0b — Source-side docs/ path sweep**

Identify every reference to `docs/` paths embedded in source code (`src/`, `scripts/`, `tests/`, `.github/`). After Task 1.3's `git mv`, paths that begin with `docs/` will 404; they must be updated before or as part of this task. Commit source-side edits as a SEPARATE commit before the `git mv` in Step 1.3 so that blame is clean.

Run:

```bash
rg -n 'docs/' src/ scripts/ tests/ .github/
```

For each hit, apply one of the following resolutions and record it in the execution log:

- **(a) Update to future path** — if the referenced page is planned in Tasks 2–13, update the path to its `docs/current/<page>` equivalent. Verify the target path actually appears in this plan before committing.
- **(b) Point to archive** — if the referenced page will not be rewritten in this plan, update the path to `docs-archive/2026-05-16-pre-reconstitution/<original-path-tail>`.
- **(c) Remove the reference** — if the reference is a dead example, remove it entirely.

Priority by hit type:

- **Runtime strings** (inside `raise`, `ValueError`, `f"..."` error messages, or similar): resolve before committing. These cause live 404s at runtime.
  - Confirmed hits: `src/townlet/environment/vectorized_env.py:562`, `src/townlet/config/brain_config.py:530`, `src/townlet/population/vectorized.py:82,97`
- **Non-runtime** (docstrings, comments, GitHub templates, test docstrings): resolve with the same choices but lower urgency; may be committed in a second pass.
  - Confirmed hits: `.github/PULL_REQUEST_TEMPLATE.md:56`, `scripts/README-no-defaults-lint.md:245`, and approximately seven test-file docstrings referencing `docs/plans/`, `docs/bugs/`, `docs/performance/`

DoD: Paste the full `rg` output into the execution log with per-hit resolution noted. All runtime-string edits committed (as one dedicated commit, titled e.g. `fix: update embedded docs/ paths ahead of tree reconstitution`) before Step 1.3 runs.

- [ ] **Step 1.1: Verify pre-state**

Run: `ls docs | wc -l && ls docs-archive 2>/dev/null || echo "no archive yet"`
Expected: A non-zero count of items in `docs/`, and `no archive yet` (or an empty `docs-archive/`).

- [ ] **Step 1.2: Confirm no in-flight edits in `docs/`**

Run: `git status --porcelain docs/ | head`
Expected: Empty output. If anything is modified or untracked under `docs/`, stop and surface to the user — that is someone else's work and must not be moved silently.

- [ ] **Step 1.3: Move docs/ into the archive with git, preserving history**

```bash
mkdir -p docs-archive
git mv docs docs-archive/2026-05-16-pre-reconstitution
```

- [ ] **Step 1.4: Verify the move**

Run: `ls docs 2>&1; ls docs-archive/2026-05-16-pre-reconstitution | wc -l`
Expected: `ls: cannot access 'docs': No such file or directory`, and a non-zero count under the archive path.

- [ ] **Step 1.5: Create the new docs skeleton (empty directories only)**

```bash
mkdir -p docs/current
```

- [ ] **Step 1.6: Create the shared gate script**

This script is the single source of truth for stale-term and coverage-percentage gating across every subsequent task. Lines that legitimately name a banned term must be preceded (within six lines above) by a `<!-- stale-callout: <term> -->` HTML comment; lines that contain a percentage in pasted command output must be preceded (within six lines above) by a `<!-- pytest-output -->` comment.

Create `scripts/docs_gate.py`:

```python
#!/usr/bin/env python3
"""Gate for docs reconstitution stale-term and coverage-percentage checks.

Usage:
    python3 scripts/docs_gate.py [--stale] [--coverage] PATH [PATH ...]

Exits non-zero on the first uncovered violation, printing the file:line:line-text.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

# STALE update protocol:
# Who updates this list: the PR author who deprecates a term, file, or concept.
# When: in the same PR that retires the old term/file/concept — never after the fact.
# Each addition requires:
#   (a) the term itself added to the regex alternation,
#   (b) a one-line comment above it: # YYYY-MM-DD: <reason for adding this term>,
#   (c) a corresponding test case added to tests/test_scripts/test_docs_gate.py
#       (case group 1 or a new case group if the term needs dedicated coverage).
# Removals require evidence in the PR description that no current doc still uses the term
# (run: python3 scripts/docs_gate.py --stale $(find docs/current -name '*.md') CLAUDE.md
# and confirm zero violations before removing).
STALE = re.compile(
    r"seven-stage|seven stage|drive_as_code\.yaml|"
    r"variables_reference\.yaml|RewardStrategy|reward_strategy field|"
    r"src/hamlet/"
)
# LOOKBACK semantics:
# (a) LOOKBACK = 6 means an allow-list marker must appear within the 6 lines
#     immediately above the offending term's line to suppress the violation.
# (b) 6 was chosen to cover a reasonable paragraph: a well-placed callout sits
#     close to the term it permits. A marker further away is camouflage — it
#     would suppress terms it was not authored alongside, defeating the gate's
#     purpose.
# (c) Changing this constant retroactively invalidates existing allow-list
#     markers: any marker that was exactly at the old boundary may now be out
#     of range. If you change LOOKBACK, run the gate across all gated files
#     and re-verify all existing markers still work.
LOOKBACK = 6
# COVERAGE regex — coverage-adjacent percentages only:
# This regex intentionally does NOT flag all percentages in prose. It only flags
# percentages that appear on the same line as the words cov / coverage / covered
# (case-insensitive), which is the canonical form of a pasted coverage-report
# number that will go stale (e.g., "coverage: 87.3%", "87.3% coverage").
# Prose percentages such as "100% deterministic" or "50% of agents" do not match.
# The pattern uses re.IGNORECASE so "Coverage: 87.3%" and "coverage: 87.3%" both match.
COVERAGE = re.compile(
    r"\b(?:cov(?:erage|ered)?)\b[^\n]*?\b\d+(?:\.\d+)?%"
    r"|\b\d+(?:\.\d+)?%[^\n]*?\b(?:cov(?:erage|ered)?)\b",
    re.IGNORECASE,
)


def violations(path: Path, pattern: re.Pattern[str], marker: str) -> list[tuple[int, str]]:
    if not path.is_file():
        return []
    lines = path.read_text().splitlines()
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not pattern.search(line):
            continue
        window = lines[max(0, i - LOOKBACK) : i]
        if any(marker in w for w in window):
            continue
        out.append((i + 1, line))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale", action="store_true", help="check banned stale terms")
    ap.add_argument("--coverage", action="store_true", help="check coverage percentages")
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()
    if not (args.stale or args.coverage):
        args.stale = True

    rc = 0
    for path in args.paths:
        if args.stale:
            for ln, text in violations(path, STALE, "stale-callout"):
                print(f"{path}:{ln}: STALE: {text}")
                rc = 1
        if args.coverage:
            for ln, text in violations(path, COVERAGE, "pytest-output"):
                print(f"{path}:{ln}: COVERAGE: {text}")
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

Then make it executable:

```bash
chmod +x scripts/docs_gate.py
```

- [ ] **Step 1.7: Smoke-test the gate against a known-good and known-bad fixture**

```bash
# Should pass (empty file)
: > /tmp/gate_ok.md
python3 scripts/docs_gate.py --stale /tmp/gate_ok.md && echo OK

# Should fail (banned term without marker)
echo 'old seven-stage compiler' > /tmp/gate_bad.md
python3 scripts/docs_gate.py --stale /tmp/gate_bad.md || echo "fails as expected"

# Should pass (banned term WITH marker)
printf '<!-- stale-callout: seven-stage -->\nold seven-stage compiler\n' > /tmp/gate_marked.md
python3 scripts/docs_gate.py --stale /tmp/gate_marked.md && echo OK
```

Expected: First and third print `OK`; second prints `fails as expected`.

- [ ] **Step 1.7a: `docs_gate.py` pytest coverage**

Create `tests/test_scripts/test_docs_gate.py`. The executor writes the actual test code; the plan specifies what must be covered. All ten case groups below must have at least one test each, and all must pass.

Required test cases:

1. **Boundary tests for `LOOKBACK=6`**: a marker exactly 6 lines above the violation passes (gate exits 0); a marker 7 lines above the violation fails (gate exits non-zero). Cover both `--stale` and `--coverage` modes for each boundary position. **Regression discipline:** these distances must be hard-coded as the literal integers `6` and `7` in the test source — do NOT compute them as `LOOKBACK` and `LOOKBACK + 1`. If a future contributor bumps `LOOKBACK`, the test must fail loudly so the change is noticed and deliberate.

2. **Multiple violations in one file**: a file containing two or more distinct banned-term violations (each without a marker) must produce a report that names every violation, not just the first.

3. **`--stale` and `--coverage` together in a single invocation**: a file that contains both a bare banned term and a bare percentage must report both categories of violation in one run.

4. **COVERAGE regex specificity — coverage-adjacent percentages only**: verify that the narrowed COVERAGE regex flags percentages only when they appear on the same line as a coverage-related word, and does not flag unrelated prose percentages. Four sub-cases:
   - (i) `100% deterministic` — must NOT be flagged by `--coverage` (passes clean).
   - (ii) `coverage: 87.3%` — must be flagged by `--coverage`.
   - (iii) `87.3% coverage` — must be flagged by `--coverage`.
   - (iv) A line containing `coverage: 87.3%` preceded within 6 lines by `<!-- pytest-output -->` — must NOT be flagged (the existing suppression mechanism still works).

5. **Argument parsing — three invocation modes**:
   - `--stale` alone: only stale-term checking is active.
   - `--coverage` alone: only coverage-percentage checking is active.
   - Neither flag: gate behaves as if `--stale` were passed (the default documented in Step 1.6).

6. **Missing file path**: invoking the gate with a path that does not exist produces a non-zero exit code and a human-readable error message. The gate must not raise an unhandled Python exception.

7. **Empty file**: invoking the gate on an empty file exits 0 with no output.

8. **Exit code semantics**: clean input → exit code 0; any gate violation → non-zero exit code. If the script distinguishes argument/parse errors from gate violations with separate exit codes, test those distinctions explicitly; if it uses a single non-zero code for all failures, document that choice in the test.

9. **Marker form precision**:
   - `<!-- stale-callout: seven-stage -->` (space after colon) within the lookback window suppresses the violation.
   - `<!-- stale-callout:seven-stage -->` (no space after colon) — define in the test whether this form is accepted or rejected and assert that behavior consistently.
   - `<!-- some-other-marker: seven-stage -->` does not suppress the violation.

10. **False-positive resistance for `src/hamlet/` substring**: a markdown file containing the line `https://github.com/example/src/hamlet/external-repo.md` (the banned substring appearing as a URL fragment) MUST be flagged by `--stale`. This is intentional: the gate bans the substring regardless of context; a URL mention is not exempt. The test ASSERTS flagging and documents this as deliberate behavior so future contributors do not accidentally relax it. A separate test case verifies that adding `<!-- stale-callout: src/hamlet/ -->` within 6 lines above that URL line causes the gate to exit 0 (the standard suppression mechanism is the correct way to allow intentional URL mentions).

**Command:**

```bash
uv run pytest tests/test_scripts/test_docs_gate.py -v
```

**Expected:** All enumerated cases have at least one test and all pass. No skips.

DoD: `uv run pytest tests/test_scripts/test_docs_gate.py -v` exits 0 with all ten case groups covered.

- [ ] **Step 1.7b: Wire `docs_gate.py` into CI**

Add a job (or extend an existing job) in `.github/workflows/lint.yml` that runs the gate on every PR that touches the gated surface. The executor decides the exact YAML; the plan specifies the what and when.

**What to run:**

```bash
python3 scripts/docs_gate.py --stale --coverage \
    CLAUDE.md AGENTS.md CONTRIBUTING.md SECURITY.md README.md \
    $(find docs/current -type f -name '*.md')
```

(or equivalent — a `xargs`-based form or a matrix is acceptable provided all five root files and all `docs/current/*.md` files are checked).

**When to run:** Every PR that modifies any of the following paths (use a `paths:` filter in the workflow trigger):

- `CLAUDE.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `README.md`
- `docs/current/**`
- `scripts/docs_gate.py`
- `.github/workflows/lint.yml`

**Python version:** Use the same Python version specifier (`python-version:`) that the rest of `.github/workflows/lint.yml` uses. Do not introduce a second, different version.

**DoD:**

1. The new CI step appears in `.github/workflows/lint.yml` under a `paths:` trigger covering all eight path patterns above.
2. A deliberate test commit that introduces a bare `seven-stage` occurrence in `CLAUDE.md` (without a marker) triggers a workflow failure on the PR.
3. Reverting the test commit makes the workflow pass.
4. The executor performs steps 2 and 3 as part of the DoD and records the result in the execution log.

Note: Step 1.8's commit must include `tests/test_scripts/test_docs_gate.py` (from Step 1.7a) and the updated `.github/workflows/lint.yml` (from this step) in addition to the files already listed in Step 1.8. Do not edit Step 1.8 itself — adjust the `git add` line at execution time.

- [ ] **Step 1.8: Commit the archive move and the gate script together**

Expect a diff of ~500-600 files (full docs/ tree moved + a handful of source-side path edits). Run `git status --short | wc -l` first and confirm the count matches expectations before committing. The `git mv` in Step 1.3 already staged the archive move; this step adds the new `scripts/docs_gate.py`, `tests/test_scripts/test_docs_gate.py`, `.github/workflows/lint.yml` change, and source-side edits.

```bash
git add -A docs-archive docs scripts/docs_gate.py
git commit -m "docs: archive pre-reconstitution docs and add docs_gate.py

Wholesale move of the legacy docs/ tree out of the active docs/ path so
stale claims (seven-stage compiler, drive_as_code.yaml, variables_reference.yaml,
non-existent exploration files, src/hamlet/) stop appearing in docs/ searches.
Adds scripts/docs_gate.py as the single allow-listed gate used by every
subsequent doc task to verify banned-term and coverage-percentage discipline.

Refs: filigree hamlet-7a52a63e0b"
```

---

### Task 2: Write `docs/README.md` (index and source-of-truth policy)

**Audience:** All readers — index and reading paths.

**Files:**
- Create: `docs/README.md`

**Source anchors to cite:**
- `pyproject.toml:1` (package name, version, Python floor)
- `AGENTS.md` (if present at repo root — otherwise omit)
- `CLAUDE.md` (project root) — cite the "pre-release, no backwards compat" rule
- Filigree issue `hamlet-7a52a63e0b` (the canonical reason this rebuild exists)
- `docs-archive/2026-05-16-pre-reconstitution/` (state explicitly that it is reference-only and may contain false claims)

**Required sections:**

1. *What this directory is.* One paragraph: "Source-derived agent docs for Townlet. Each page cites live anchors. If a claim here disagrees with source, source wins; file an issue."
2. *Source-of-truth precedence.* Bulleted: source code → tests → live configs → this docs tree → archived docs (lowest, treat as historical).
3. *Index.* Link to each of the 12 `docs/current/*.md` files with one-line summaries.
4. *Where not to look.* Explicit pointer to `docs-archive/2026-05-16-pre-reconstitution/` with the caveat that it is preserved for history only and is known to contain stale claims listed in the writing contract.
5. *Validation status.* One paragraph naming the two commands that gate "the basic system runs" (see Task 11 verification commands), and the date they last passed in this branch.
6. *Reading paths.* Three suggested traversals for the most common reader types (see skeleton below).

- [ ] **Step 2.1: Draft `docs/README.md` with the six sections above**

Use this skeleton (fill anchors from live source; do not paraphrase from the archive):

```markdown
# Townlet Docs

Source-derived agent documentation for Townlet (package `townlet`, see `pyproject.toml:1`).

## Source-of-truth precedence

1. Source code under `src/townlet/`
2. Tests under `tests/test_townlet/`
3. Live configs under `configs/`
4. This `docs/` tree
5. `docs-archive/2026-05-16-pre-reconstitution/` — historical only, contains known-stale claims (see "Where not to look")

If a claim here disagrees with source, source wins. File a Filigree issue.

## Index

- [Project brief](current/project-brief.md) — what Townlet is today
- [Architecture map](current/architecture-map.md) — subsystem layout
- [Config model v2.1](current/config-model-v21.md) — pack layout
- [Universe compiler](current/universe-compiler.md) — pipeline stages
- [Runtime environment](current/runtime-environment.md) — VectorizedHamletEnv
- [Actions and observations](current/actions-and-observations.md) — ActionCompiler output, observation construction
- [VFS, VTC, and DAC reward composition](current/vfs-vtc-dac.md) — VFS profiles, VTC transition schedule, DAC runtime
- [Training and checkpoints](current/training-checkpoints.md) — DemoRunner, replay buffers, provenance
- [Demo and frontend](current/demo-frontend.md) — CLI flow, current frontend state
- [Testing and quality gates](current/testing-quality-gates.md) — canonical test commands
- [Glossary](current/glossary.md) — one canonical vocabulary
- [Known gaps](current/known-gaps.md) — generated from live Filigree

## Where not to look

<!-- stale-callout: seven-stage -->
<!-- stale-callout: drive_as_code.yaml -->
<!-- stale-callout: variables_reference.yaml -->
<!-- stale-callout: src/hamlet/ -->
`docs-archive/2026-05-16-pre-reconstitution/` is preserved for history only. It is known to contain stale claims including "seven-stage compiler", `drive_as_code.yaml` (current file is per-level `drive.yaml`), `variables_reference.yaml` (replaced by shared `vfs_profiles.yaml`), references to `src/hamlet/`, and hard-coded coverage numbers. Do not cite it as authority for any current claim.

## Validation status

Two commands gate "the basic system runs":

- `uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal`
- `uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q`

Last passing on branch `project-recovery`, 2026-05-16. Re-run before relying on any claim in this tree.

## Reading paths

Suggested traversals for common reader types:

- **New contributor** — [project-brief](current/project-brief.md) → [architecture-map](current/architecture-map.md) → [runtime-environment](current/runtime-environment.md) → [testing-quality-gates](current/testing-quality-gates.md) → [known-gaps](current/known-gaps.md)
- **Researcher reproducing results** — [project-brief](current/project-brief.md) → [config-model-v21](current/config-model-v21.md) → [universe-compiler](current/universe-compiler.md) → [vfs-vtc-dac](current/vfs-vtc-dac.md) → [training-checkpoints](current/training-checkpoints.md) → [testing-quality-gates](current/testing-quality-gates.md)
- **Agent picking up a task** — [project-brief](current/project-brief.md) → [architecture-map](current/architecture-map.md) → [glossary](current/glossary.md) → [known-gaps](current/known-gaps.md) → (whichever specific page the task names)
```

- [ ] **Step 2.2: Verify the file exists and is non-empty**

Run: `wc -l docs/README.md`
Expected: A non-zero line count.

- [ ] **Step 2.2a: Verify the reading-paths section is present**

```bash
rg -c '^## Reading paths' docs/README.md
```
Expected: Returns 1.

- [ ] **Step 2.3: Stale-term gate on this file**

The `<!-- stale-callout: <term> -->` markers in the "Where not to look" section are the only allowed locus of banned terms. Use the shared gate from Step 1.6:

```bash
python3 scripts/docs_gate.py --stale docs/README.md
```
Expected: Exit code 0, no output.

- [ ] **Step 2.4: Commit**

```bash
git add docs/README.md
git commit -m "docs: write README index and source-of-truth policy

Refs: filigree hamlet-7a52a63e0b"
```

---

### Task 3: Write `docs/current/project-brief.md`

**Audience:** New contributor reading on day one.

**Files:**
- Create: `docs/current/project-brief.md`

**Source anchors to cite (each must appear as `path:LN`):**
- `pyproject.toml:1` (name, version `0.1.0`, `requires-python = ">=3.13"`)
- `src/townlet/__init__.py:1` (the package docstring describing v2.1 hierarchical packs and `CompiledUniverse`)
- `configs/default_curriculum/experiment.yaml` (curriculum levels exist as `L0_0_minimal`, `L0_5_dual_resource`, `L1_full_observability`, `L2_partial_observability`, `L3_temporal_mechanics`)

**Required content (no more than one printed page):**

- One sentence on the pedagogical goal (quote CLAUDE.md but do not quote the entire ethos).
- The runtime in one paragraph: Python 3.13, PyTorch, vectorized environment, compiled config packs, CLI demo + WebSocket inference server + Vue frontend (qualified per the frontend gap).
- The five active curriculum levels named once, each with one phrase from its `curriculum.yaml`. Do not invent claims about each level — read `configs/default_curriculum/levels/<level>/curriculum.yaml` and quote the level's own description if present.
- A "what this is not" paragraph: not a production RL framework, not multi-agent yet, not stable API.

- [ ] **Step 3.1: Read source anchors and draft the page**

```bash
sed -n '1,15p' pyproject.toml
sed -n '1,15p' src/townlet/__init__.py
ls configs/default_curriculum/levels/
for L in configs/default_curriculum/levels/*/curriculum.yaml; do echo "=== $L ==="; sed -n '1,20p' "$L"; done
```

Then write `docs/current/project-brief.md` from those outputs.

- [ ] **Step 3.2: Anchor check**

Run: `rg -n 'pyproject\.toml|src/townlet/__init__\.py|configs/default_curriculum/' docs/current/project-brief.md | wc -l`
Expected: At least 3 (each anchor cited at least once).

- [ ] **Step 3.3: Stale-term gate**

Run: `python3 scripts/docs_gate.py --stale docs/current/project-brief.md`
Expected: Empty.

- [ ] **Step 3.4: Commit**

```bash
git add docs/current/project-brief.md
git commit -m "docs: write project brief from pyproject and __init__"
```

---

### Task 4: Write `docs/current/architecture-map.md`

**Audience:** New contributor, agent picking up a task.

**Files:**
- Create: `docs/current/architecture-map.md`

**Source anchors:**
- Top-level subsystem dirs under `src/townlet/`: `agent/`, `config/`, `curriculum/`, `demo/`, `effects/`, `environment/`, `exploration/`, `items/`, `population/`, `recording/`, `substrate/`, `training/`, `universe/`, `vfs/`, `world/`
- For each subsystem, cite the `__init__.py` or the primary module of that subsystem to ground its role in source

**Required content:**

A subsystem-by-subsystem table or section list. Each entry is at most three sentences:

1. What the subsystem does (verb-first, present tense).
2. Primary module(s) — one or two `path:LN` anchors maximum.
3. Who its callers/consumers are inside the runtime (one short clause; if unknown, write "TBD pending dependency audit" — do NOT invent edges).

Order subsystems by runtime data flow: `universe` → `config` → `substrate` → `vfs` → `effects` / `items` → `environment` → `agent` → `population` → `training` → `curriculum` → `recording` → `demo` → (frontend, out of `src/`). Mention `world/` and `exploration/` last with a note on whether each is actively used (verify by `grep`-ing the import graph; do not assume).

- [ ] **Step 4.1: Survey each subsystem**

```bash
for d in src/townlet/*/; do
  echo "=== $d ==="
  head -20 "$d__init__.py" 2>/dev/null || ls "$d" | head -10
done
```

- [ ] **Step 4.2: Verify which subsystems are still imported by the runtime**

```bash
rg -l "from townlet\.(world|exploration)" src/townlet/ tests/test_townlet/ | head
```
If `world` or `exploration` has zero importers under `src/townlet/`, say so explicitly in the page ("imported only by tests" or "currently unused outside its own module"). Do not invent integration claims.

- [ ] **Step 4.3: Draft the page**

Each section is at most three sentences. No diagrams in v1 (a future task can add a Mermaid diagram once edges are audited).

- [ ] **Step 4.4: Anchor check and stale-term gate**

```bash
rg -c 'src/townlet/' docs/current/architecture-map.md
python3 scripts/docs_gate.py --stale docs/current/architecture-map.md
```
Expected: First command returns a count ≥ 13 (one anchor per subsystem listed in `src/townlet/`: `agent`, `config`, `curriculum`, `demo`, `effects`, `environment`, `exploration`, `items`, `population`, `recording`, `substrate`, `training`, `universe`, `vfs`, `world`). The threshold is `>=13` to allow up to two subsystems to be confirmed-unused: if Step 4.2 determines a subsystem is not imported anywhere at runtime, omit it from the page (or explicitly mark it as "present but unused as of 2026-05-16") rather than fabricating an anchor for it. Second returns exit code 0 with no output.

- [ ] **Step 4.5: Commit**

```bash
git add docs/current/architecture-map.md
git commit -m "docs: write architecture map from src/townlet/ subsystem survey"
```

---

### Task 5: Write `docs/current/config-model-v21.md`

**Audience:** Researcher reproducing results, operator.

**Files:**
- Create: `docs/current/config-model-v21.md`

**Source anchors:**
- `src/townlet/universe/raw_configs_v21.py:79` (the `from_experiment_dir` classmethod whose docstring documents the expected directory structure)
- `configs/default_curriculum/` (live example: `actions.yaml`, `brain.yaml`, `effects.yaml`, `environment.yaml`, `experiment.yaml`, `items.yaml`, `stratum.yaml`, `vfs_profiles.yaml`, plus `levels/<level>/{affordances,bars,curriculum,drive,training}.yaml`)

**Required content:**

1. The on-disk shape, as a code block listing the actual filenames from `configs/default_curriculum/` and `configs/default_curriculum/levels/L0_0_minimal/`. Do not paraphrase — list what is there.
2. Per-file one-line summary citing the loader/compiler that consumes it (e.g. `actions.yaml` is consumed by `src/townlet/universe/compilers/actions.py`).
3. **Explicit replacement notes** (one short paragraph each):
<!-- stale-callout: drive_as_code.yaml -->
   - `drive_as_code.yaml` does not exist. The per-level reward configuration is `drive.yaml` under `levels/<level>/`. Cite the live file: `configs/default_curriculum/levels/L0_0_minimal/drive.yaml`.
<!-- stale-callout: variables_reference.yaml -->
   - `variables_reference.yaml` does not exist. VFS configuration is the shared `vfs_profiles.yaml` at the pack root. Cite the live file: `configs/default_curriculum/vfs_profiles.yaml`.
4. The "primary level" rule: `UniverseCompiler.compile` requires an explicit `primary_level`; implicit selection is disallowed. Cite `src/townlet/universe/compiler.py:92` (or the line where the `ValueError` is raised — verify before writing).

- [ ] **Step 5.1: Capture the live layout**

```bash
ls configs/default_curriculum/
ls configs/default_curriculum/levels/L0_0_minimal/
sed -n '60,100p' src/townlet/universe/raw_configs_v21.py
rg -n 'primary_level' src/townlet/universe/compiler.py
```

- [ ] **Step 5.2: Draft the page**

Include the directory tree as a fenced code block reproducing exactly what `ls` printed. Each per-file summary cites a compiler module from `src/townlet/universe/compilers/`.

- [ ] **Step 5.3: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale docs/current/config-model-v21.md
```
Expected: Exit code 0, no output. The banned terms may appear only inside the "explicit replacement notes" paragraphs that name them as gone; the `<!-- stale-callout: <term> -->` markers above those paragraphs tell the gate to allow them.

- [ ] **Step 5.4: Anchor check**

```bash
rg -n 'src/townlet/universe/(raw_configs_v21|compiler|compilers/)' docs/current/config-model-v21.md
```
Expected: At least 3 matches.

- [ ] **Step 5.5: Commit**

```bash
git add docs/current/config-model-v21.md
git commit -m "docs: document v2.1 config-pack layout from live configs/default_curriculum"
```

---

### Task 6: Write `docs/current/universe-compiler.md`

**Audience:** Researcher reproducing results, agent debugging compile failures.

**Files:**
- Create: `docs/current/universe-compiler.md`

**Source anchors:**
- `src/townlet/universe/compiler.py:92` (the `compile` method — read its body to enumerate the actual stages)
- `src/townlet/universe/compilers/` (the per-stage compiler modules: `actions.py`, `effects.py`, `metadata.py`, `observation.py`, `optimization.py`, `vfs.py`)
- The CLI: `python -m townlet.universe validate` (entry point lives under `src/townlet/universe/__main__.py` if present, or whichever module the `-m` invocation resolves to — verify before writing)

**Required content:**

1. The actual stage list, derived by reading `compile()` top-to-bottom. Do NOT use "seven-stage" anywhere. Number the stages as they appear in source — if there are six, say six; if there are nine, say nine. Each stage gets one sentence and a `compiler.py:LN` anchor for its `_log_stage` call (or equivalent).
2. The cache behaviour: where `cache_path` comes from, what triggers the fast path, what invalidates it. Cite the lines.
3. The CLI surface: `compile`, `inspect`, `validate` subcommands as actually defined. Verify by running `python -m townlet.universe --help` and quoting the output.
4. A worked example: the exact command used in this branch's golden path.

- [ ] **Step 6.1: Enumerate the real stages**

```bash
rg -n '_log_stage\(' src/townlet/universe/compiler.py
sed -n '85,200p' src/townlet/universe/compiler.py
```
Count the `_log_stage` invocations (or the equivalent stage markers). That is the stage count.

- [ ] **Step 6.2: Capture the CLI**

```bash
uv run python -m townlet.universe --help 2>&1 | head -40
```

- [ ] **Step 6.3: Draft the page using the captured stage count and CLI text**

- [ ] **Step 6.4: Run the validate command end-to-end and paste the trailing output**

```bash
uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal 2>&1 | tail -20
```
Include the trailing output in a fenced block on the page so the reader sees what success looks like.

- [ ] **Step 6.5: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale docs/current/universe-compiler.md
```
Expected: Exit code 0, no output.

- [ ] **Step 6.6: Commit**

```bash
git add docs/current/universe-compiler.md
git commit -m "docs: describe UniverseCompiler stages from source, with worked validate example"
```

---

### Task 7: Write `docs/current/runtime-environment.md`

**Audience:** Researcher, agent debugging runtime failures.

**Files:**
- Create: `docs/current/runtime-environment.md`

**Source anchors:**
- `src/townlet/environment/vectorized_env.py:190` (verify line in source — the `__init__` phase orchestration block referenced in the file's own comment "hamlet-2559b98232")
- `tests/test_townlet/integration/test_golden_path_smoke.py:1` (the golden-path contract)

**Required content:**

1. `VectorizedHamletEnv` construction: the phased `__init__` (configure POMDP, derive observation dim, build action mask, etc.) — anchor each phase to a real line.
2. The golden tick contract: what `reset()` and `step(WAIT)` produce, how many steps the smoke test asserts. Cite `tests/test_townlet/integration/test_golden_path_smoke.py:1` and reproduce the test's first 30 lines in a code block.
3. The runtime action space surface and how it is wired (`from_universe`).
4. The end-to-end command to verify:

```bash
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q
```

Include the trailing output verbatim (whatever Step 7.2 actually prints — do not pre-fill the number from this plan).

- [ ] **Step 7.1: Read the env file and the smoke test**

```bash
sed -n '180,260p' src/townlet/environment/vectorized_env.py
sed -n '1,80p' tests/test_townlet/integration/test_golden_path_smoke.py
```

- [ ] **Step 7.2: Verify the smoke test passes in this branch**

```bash
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q 2>&1 | tail -5
```
Expected: A pytest pass line of the form `N passed`. Originating brief reports `3 passed` on `project-recovery` as of 2026-05-16.

**If the actual count differs from the brief's `3 passed`**, treat the brief's number as stale, not source: update the page to quote the *observed* count from this command. Do not paste `3 passed` if pytest printed anything else. The page must reproduce the actual trailing output verbatim, with the date the command was run.

- [ ] **Step 7.3: Draft the page**

- [ ] **Step 7.4: Anchor and stale-term gate**

```bash
rg -n 'vectorized_env\.py|test_golden_path_smoke\.py' docs/current/runtime-environment.md
python3 scripts/docs_gate.py --stale docs/current/runtime-environment.md
```
Expected: First non-empty; second empty.

- [ ] **Step 7.5: Commit**

```bash
git add docs/current/runtime-environment.md
git commit -m "docs: describe VectorizedHamletEnv construction and golden-path contract"
```

---

### Task 8a: Write `docs/current/actions-and-observations.md`

**Audience:** Researcher, new contributor adding actions.

**Files:**
- Create: `docs/current/actions-and-observations.md`

**Source anchors:**
- `src/townlet/universe/compilers/actions.py` (`ActionCompiler` — verify the `build_action_space_metadata` method line before citing)
- `src/townlet/environment/action_config.py` (ActionConfig dataclass)
- `src/townlet/environment/vectorized_env.py` (observation construction in `__init__` phases — cite line where observation tensor is assembled)
- `configs/global_actions.yaml` (the global action vocabulary shared across all curriculum levels)
- `src/townlet/vfs/observation_builder.py` (compile-time observation spec generation)
- `src/townlet/vfs/schema.py` (variable scopes `global`, `agent`, `agent_private`)

**Required content (one section per surface):**

1. *Action vocabulary.* What `ActionCompiler` produces (`RuntimeAction`, `RuntimeActionSpace`, `ActionSpaceMetadata`). How the global action vocabulary in `configs/global_actions.yaml` maps to per-substrate action dims (Grid2D: 8, Grid3D: 10, GridND: 16, Aspatial: 4). Where the runtime reads the compiled metadata.
2. *Action configuration.* What `action_config.py` exposes and how `VectorizedHamletEnv` consumes it. Cite the relevant line from `vectorized_env.py`.
3. *Observation spec.* How `observation_builder.py` derives `observation_dim` from VFS profiles. What scopes exist (`global`, `agent`, `agent_private`) — cite `schema.py`, not the archive.
4. *Observation construction.* How the observation tensor is assembled at runtime inside `VectorizedHamletEnv`. Cite the relevant phase from `vectorized_env.py`.

- [ ] **Step 8a.1: Read each anchor**

```bash
grep -n 'def build_action_space_metadata\|class ActionCompiler' src/townlet/universe/compilers/actions.py
sed -n '1,50p' src/townlet/environment/action_config.py
sed -n '1,40p' src/townlet/vfs/observation_builder.py
sed -n '1,40p' src/townlet/vfs/schema.py
rg -n 'observation_builder\|action_config\|ActionConfig' src/townlet/environment/vectorized_env.py | head -20
```

- [ ] **Step 8a.2: Draft the page**

Write from the sources above. Do not paraphrase from the archive.

- [ ] **Step 8a.3: Anchor and stale-term gate**

```bash
rg -n 'src/townlet/(universe/compilers/actions|environment/action_config|environment/vectorized_env|vfs/observation_builder|vfs/schema)|configs/global_actions' docs/current/actions-and-observations.md | wc -l
python3 scripts/docs_gate.py --stale docs/current/actions-and-observations.md
```
Expected: First ≥ 6; second empty.

- [ ] **Step 8a.4: Commit**

```bash
git add docs/current/actions-and-observations.md
git commit -m "docs: document ActionCompiler output and observation construction from source"
```

---

### Task 8b: Write `docs/current/vfs-vtc-dac.md`

**Audience:** Researcher reproducing results, agent designing reward or state.

**Files:**
- Create: `docs/current/vfs-vtc-dac.md`

**Source anchors:**
- `src/townlet/vfs/registry.py` (runtime VFS storage with access control)
- `src/townlet/vfs/schema.py` (VariableDef, ObservationField, NormalizationSpec, WriteSpec — variable scopes and access control)
- `src/townlet/vfs/observation_builder.py` (compile-time spec generation, dimension validation)
- `src/townlet/vfs/transition_schedule.py:36` (`VTCTransitionSchedule` dataclass — **read the dataclass fields directly from source; they are the authoritative list of programs**)
- `src/townlet/environment/dac_engine.py` (DAC runtime reward composition — verify path with `rg -l 'class.*Drive.*Engine|drive_hash' src/townlet/` before citing)
- `configs/default_curriculum/vfs_profiles.yaml` (shared VFS profile definitions; how levels reference profiles by name — do not say `variables_reference.yaml`)
- A per-level `drive.yaml` example (e.g. `configs/default_curriculum/levels/L0_0_minimal/drive.yaml`)

**Required content (one section per surface):**

1. *VFS profiles.* The shared `configs/default_curriculum/vfs_profiles.yaml` and how levels reference profiles by name. What `registry.py` stores at runtime. Access-control readers and writers (`engine`, `actions`, `bac`, `acs`) — cite `schema.py`.
2. *VFS observation spec.* How `observation_builder.py` derives `observation_dim` from VFS profiles. Variable scopes (`global`, `agent`, `agent_private`). Cite the relevant class or function line from `observation_builder.py`.
3. *VTC transition schedule.* Read `src/townlet/vfs/transition_schedule.py:36` and enumerate the `VTCTransitionSchedule` dataclass fields directly. Write one paragraph anchor for each program field declared on the dataclass — the field list in source is the truth; do not use this plan as the source. Each paragraph names the program field, states what it computes, and cites its `VTC*Program` type from the import block.
4. *DAC reward composition.* Reward is composed under DAC (Drive As Code), a composition layer, not a peer subsystem. Find the DAC runtime module with `rg -l 'class.*Drive.*Engine|drive_hash' src/townlet/` — cite whatever path it returns. Describe what the engine does at runtime (compiles `drive.yaml` → GPU computation graph, tracks `drive_hash` for checkpoint provenance). If `drive_hash` is not found in source, omit the claim and note it in Task 13 (known-gaps.md).

- [ ] **Step 8b.1: Read each anchor**

```bash
sed -n '35,55p' src/townlet/vfs/transition_schedule.py
sed -n '1,40p' src/townlet/vfs/registry.py
sed -n '1,40p' src/townlet/vfs/schema.py
sed -n '1,40p' src/townlet/vfs/observation_builder.py
rg -l 'class.*Drive.*Engine|drive_hash' src/townlet/
cat configs/default_curriculum/vfs_profiles.yaml 2>/dev/null || echo "NOT FOUND — verify path"
cat configs/default_curriculum/levels/L0_0_minimal/drive.yaml 2>/dev/null || echo "NOT FOUND — verify path"
```

- [ ] **Step 8b.2: Derive the VTC program list from source**

Read the `VTCTransitionSchedule` dataclass fields (Step 8b.1 output). List only what the dataclass declares — not what this plan says. If the field list differs from any prose in this plan, the dataclass wins.

- [ ] **Step 8b.3: Verify the DAC runtime module — name it from source, not from the archive**

If `rg` returns multiple candidates, read each before naming it.

- [ ] **Step 8b.4: Draft the page**

Write from the sources above. Do not paraphrase from the archive. The VTC section must have one paragraph per program field found in the dataclass — no more, no fewer.

- [ ] **Step 8b.5: Anchor and stale-term gate**

```bash
rg -n 'src/townlet/vfs/|configs/default_curriculum/(vfs_profiles|levels/.*/drive)' docs/current/vfs-vtc-dac.md | wc -l
python3 scripts/docs_gate.py --stale docs/current/vfs-vtc-dac.md
```
Expected: First ≥ 6; second empty.

- [ ] **Step 8b.6: Commit**

```bash
git add docs/current/vfs-vtc-dac.md
git commit -m "docs: document VFS profiles, VTC schedule programs, and DAC reward composition from source"
```

---

### Task 9: Write `docs/current/training-checkpoints.md`

**Audience:** Researcher, operator (security-sensitive: pickle boundary).

**Files:**
- Create: `docs/current/training-checkpoints.md`

**Source anchors:**
- `src/townlet/demo/runner.py:45` (`DemoRunner.__init__` signature)
- `src/townlet/training/checkpoint_utils.py:22` (`attach_universe_metadata` — checkpoint provenance: `config_hash`, `brain_hash`)
- `src/townlet/population/` (the vectorized population module — cite the primary file)
- `src/townlet/training/replay_buffer.py` (if present — verify)
- `src/townlet/training/state.py` (if present — verify)

**Required content:**

1. `DemoRunner` lifecycle: construct (open DB and TensorBoard), `load_checkpoint`, `run`, context-manager cleanup. Mention the CLAUDE.md guidance to use the context manager when not running full training.
2. Population and replay buffer: where batched training lives and how transitions flow.
3. Checkpoint provenance: `config_hash` and `brain_hash` produced by `attach_universe_metadata`; describe what the hashes cover.
4. **Unsafe pickle boundary.** Find and cite the actual loading call (`rg -n 'pickle\.loads\|torch\.load' src/townlet/`). State the trust boundary explicitly — checkpoints must come from a trusted source. Do not editorialize beyond what the code shows.
5. The `drive_hash` claim from CLAUDE.md: verify it exists in source before mentioning it. If `rg -n 'drive_hash' src/townlet/` returns nothing, omit the claim and add a one-liner to `known-gaps.md` (Task 13).

- [ ] **Step 9.1: Read anchors and probe**

```bash
sed -n '40,90p' src/townlet/demo/runner.py
sed -n '20,80p' src/townlet/training/checkpoint_utils.py
ls src/townlet/training/ src/townlet/population/
rg -n 'pickle\.loads|torch\.load\(' src/townlet/
rg -n 'drive_hash' src/townlet/
```

- [ ] **Step 9.2: Draft the page**

- [ ] **Step 9.3: Anchor and stale-term gate**

```bash
rg -n 'src/townlet/(demo/runner|training/|population/)' docs/current/training-checkpoints.md | wc -l
python3 scripts/docs_gate.py --stale docs/current/training-checkpoints.md
```
Expected: First ≥ 3; second empty.

- [ ] **Step 9.4: Commit**

```bash
git add docs/current/training-checkpoints.md
git commit -m "docs: document DemoRunner, population, replay buffer, and checkpoint provenance"
```

---

### Task 10: Write `docs/current/demo-frontend.md`

**Audience:** New contributor, operator running the live inference demo.

**Files:**
- Create: `docs/current/demo-frontend.md`

**Source anchors:**
- `scripts/run_demo.py:31` (CLI argument parser)
- `src/townlet/demo/unified_server.py:32` (`UnifiedServer` class docstring)
- `frontend/` directory listing (verify with `ls frontend/`)

**Required content:**

1. The CLI demo flow: arguments to `scripts/run_demo.py`, what `UnifiedServer` orchestrates (training thread, inference thread).
2. The inference WebSocket surface: which module serves it (cite from source).
3. **Frontend current state.** State explicitly:

   > "`frontend/` currently has `index.html`, `vite.config.js`, and `src/`, but lacks `package.json`. Until Filigree issue hamlet-d892e161c0 lands, `npm run dev` will fail. Do not document the npm flow as working."

   Cite the live `ls frontend/` output.

4. Once package metadata is restored, the documented flow will be: terminal 1 runs `python -m townlet.demo.live_inference …`; terminal 2 runs `npm run dev` under `frontend/`. Mark this block as **conditional on hamlet-d892e161c0**.

- [ ] **Step 10.1: Read anchors**

```bash
sed -n '25,80p' scripts/run_demo.py
sed -n '25,80p' src/townlet/demo/unified_server.py
ls frontend/
```

- [ ] **Step 10.2: Draft the page with the conditional block clearly marked**

- [ ] **Step 10.3: Verify the package.json gap is real and the issue ID is correct**

```bash
test -f frontend/package.json && echo PRESENT || echo MISSING
filigree show hamlet-d892e161c0 2>&1 | head -10
```
Expected: `MISSING`, and the Filigree issue exists with the expected title.

- [ ] **Step 10.4: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale docs/current/demo-frontend.md
```
Expected: Exit code 0, no output.

- [ ] **Step 10.5: Commit**

```bash
git add docs/current/demo-frontend.md
git commit -m "docs: document demo CLI and current frontend gap (hamlet-d892e161c0)"
```

---

### Task 11: Write `docs/current/testing-quality-gates.md`

**Audience:** New contributor, agent picking up a task.

**Files:**
- Create: `docs/current/testing-quality-gates.md`

**Source anchors:**
- `pyproject.toml:119` (the `[tool.pytest.ini_options]` block: testpaths, pythonpath, addopts, filterwarnings, markers)
- `tests/test_townlet/` (top-level test layout: `integration/`, `properties/`, `performance/`, `fixtures/`, `helpers/`, `_fixtures/`, `builders.py`, `conftest.py`)

**Required content:**

1. Where tests live and how they are partitioned (integration vs property vs performance).
2. Canonical commands:
   - `uv run pytest` — full suite, excludes `slow`-marked tests by default (cite the `-m "not slow"` in addopts).
   - `uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q` — smoke
   - `uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal` — config validate gate
3. Coverage: state that coverage is measured per run via `--cov=townlet --cov-branch --cov-report=term-missing` from `pyproject.toml:119`. Do NOT cite a percentage. If a number is wanted, instruct the reader to run the command.
4. Known warnings: list what `filterwarnings` in `pyproject.toml:119` currently suppresses (the `pytest.PytestAssertRewriteWarning` line). Do not paper over other warnings.
5. "Proof before claim" rule: any doc claim that "X works" must paste output from a verification command into the doc and date it.

- [ ] **Step 11.1: Read anchors**

```bash
sed -n '115,160p' pyproject.toml
ls tests/test_townlet/
```

- [ ] **Step 11.2: Run the two gate commands and capture trailing output**

```bash
uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal 2>&1 | tail -5
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q 2>&1 | tail -5
```
Paste both trailing outputs into the page in dated fenced blocks.

- [ ] **Step 11.3: Stale-term gate**

```bash
python3 scripts/docs_gate.py --coverage docs/current/testing-quality-gates.md
```
Expected: Exit code 0, no output. The dated command-output blocks from Step 11.2 are allowed; the gate honours the `<!-- pytest-output -->` marker around pasted pytest output, so percentages within that block do not trip the gate.

- [ ] **Step 11.4: Commit**

```bash
git add docs/current/testing-quality-gates.md
git commit -m "docs: document test layout, canonical commands, and proof-before-claim rule"
```

---

### Task 12: Write `docs/current/glossary.md`

**Audience:** All readers — quick lookup.

**Files:**
- Create: `docs/current/glossary.md`

**Source anchors:**
- Each term must be anchored to at least one source file where it is defined or used.

**Required content:**

A flat alphabetical list of terms with one-sentence definitions and one `path:LN` anchor each. The minimum set:

- **Affordance** — anchor: `configs/default_curriculum/levels/L0_0_minimal/affordances.yaml`
- **Bar / Meter** — anchor: `configs/default_curriculum/levels/L0_0_minimal/bars.yaml`
- **Compiled artifact** — anchor: `src/townlet/universe/compiler.py` (the cache emission)
- **Curriculum level** — anchor: `configs/default_curriculum/experiment.yaml`
- **DAC (Drive As Code)** — anchor: per-level `drive.yaml` and the runtime module found in Task 8b
- **Effects** — anchor: `configs/default_curriculum/effects.yaml`, `src/townlet/effects/`
- **Item** — anchor: `configs/default_curriculum/items.yaml`, `src/townlet/items/`
- **POMDP** — anchor: `src/townlet/environment/vectorized_env.py` (the `_configure_partial_observability` phase)
- **Stratum** — anchor: `configs/default_curriculum/stratum.yaml`
- **Substrate** — anchor: `configs/default_curriculum/environment.yaml`, `src/townlet/substrate/`
- **Universe / CompiledUniverse** — anchor: `src/townlet/universe/compiler.py`
- **VFS (Variable & Feature System)** — anchor: `src/townlet/vfs/`, `configs/default_curriculum/vfs_profiles.yaml`
- **VTC (Variable & Transition Computer)** — anchor: `src/townlet/vfs/transition_schedule.py:36`

Each definition is one sentence. No prose tutorials in this file.

- [ ] **Step 12.1: Draft the glossary**

- [ ] **Step 12.2: Anchor check**

```bash
rg -c '\(src/|configs/' docs/current/glossary.md
```
Expected: ≥ 13 (one anchor per term).

- [ ] **Step 12.3: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale docs/current/glossary.md
```
Expected: Exit code 0, no output.

- [ ] **Step 12.4: Commit**

```bash
git add docs/current/glossary.md
git commit -m "docs: write canonical glossary anchored to source and live configs"
```

---

### Task 13: Write `docs/current/known-gaps.md` from live Filigree

**Audience:** Maintainer, agent picking up unblocked work.

**Files:**
- Create: `docs/current/known-gaps.md`

**Required content:**

Do NOT seed this page from the archived `docs/`. Read live Filigree:

```bash
filigree list --status=open --json 2>&1 | head -500
filigree show hamlet-7a932c4e40 2>&1 | head -40   # parent milestone
filigree show hamlet-c8c316ba03 2>&1 | head -20   # golden tick/phase/hash/checkpoint tests
filigree show hamlet-d892e161c0 2>&1 | head -20   # frontend package metadata
filigree show hamlet-7a52a63e0b 2>&1 | head -20   # this docs task
filigree show hamlet-030f2ce0aa 2>&1 | head -20   # EnvFactory extraction
```

At the very top of known-gaps.md, write the following HTML comment verbatim (this is a regeneration cadence notice for future maintainers):

```html
<!--
Regenerate this page when:
- A listed issue closes (remove the entry).
- A new P0/P1 issue appears that affects users (add an entry).
- The page is older than 14 days (full refresh).

Regeneration command:
    filigree list --status=open --priority=P0,P1 --format=markdown > /tmp/gaps.md

Owner: whoever opens the next plan in plans/ after this date.
-->
```

Compose a flat list of currently open issues that constitute architecture gaps, each with:
- Filigree ID
- One-line description (use the issue's title)
- Status (open / in_progress / ready)
- Blocking relationships (from `blocks` / `blocked_by`)

End the page with a paragraph stating that this list is a snapshot; the live tracker (`filigree ready` and the dashboard at `http://localhost:9105`) is the source of truth.

Immediately after that closing paragraph, add the following footer note as a blockquote:

> Snapshot date: <YYYY-MM-DD>. Consider this page stale if more than 14 days old; consult `filigree session-context` for live state.

(Replace `<YYYY-MM-DD>` with the actual date you write the file.)

If Task 9 found that `drive_hash` is not actually in source, add a one-liner here: "CLAUDE.md mentions `drive_hash` checkpoint provenance; not located in source as of 2026-05-16. Verify or remove from CLAUDE.md."

- [ ] **Step 13.1: Pull the live list**

```bash
filigree list --status=open --label=architecture-gap 2>&1 | head -50
```

- [ ] **Step 13.1a: Definition-of-done gate**

  Before committing, verify the file meets the minimum bar for a useful gaps doc:

  ```bash
  # At least 3 issue entries
  rg -c '^- ' docs/current/known-gaps.md
  ```
  Expected: ≥3.

  ```bash
  # Each entry includes a Filigree ID — check by counting bolded hamlet- IDs
  rg -c 'hamlet-[a-f0-9]+' docs/current/known-gaps.md
  ```
  Expected: ≥3 (one per entry minimum).

  Additionally, manually verify each entry carries: (a) Filigree ID, (b) title, (c) severity (P0/P1/P2 or equivalent label), and (d) a one-line description. Record the per-entry format check result in the execution log. If any entry is missing a field, fill it from the live Filigree record before committing.

- [ ] **Step 13.2: Compose and commit**

```bash
git add docs/current/known-gaps.md
git commit -m "docs: snapshot known gaps from live Filigree (not from the archive)"
```

---

### Task 14: Archive `DEPENDENCY_ANALYSIS_SUMMARY.md` (not refreshed in place)

**Files:**
- Move: `DEPENDENCY_ANALYSIS_SUMMARY.md` → `docs-archive/2026-05-16-pre-reconstitution/DEPENDENCY_ANALYSIS_SUMMARY.md`

**Rationale:** This file is a point-in-time analysis artifact (executive-summary tone, fixed file count "98 Python files"), not a maintained doc. The architecture map (`docs/current/architecture-map.md`, Task 4) is the source-derived successor. Archiving rather than rewriting avoids manufacturing facts the reader might mistake for current.

- [ ] **Step 14.1: Confirm no recent edits**

Run: `git log -1 --format='%h %ci %s' -- DEPENDENCY_ANALYSIS_SUMMARY.md`
Expected: A commit predating this branch. If it shows recent activity from another agent, stop and surface.

- [ ] **Step 14.2: Move it into the archive**

```bash
git mv DEPENDENCY_ANALYSIS_SUMMARY.md docs-archive/2026-05-16-pre-reconstitution/DEPENDENCY_ANALYSIS_SUMMARY.md
```

- [ ] **Step 14.3: Verify**

Run: `test -f DEPENDENCY_ANALYSIS_SUMMARY.md && echo PRESENT || echo MOVED`
Expected: `MOVED`.

- [ ] **Step 14.4: Commit**

```bash
git add -A
git commit -m "docs: archive DEPENDENCY_ANALYSIS_SUMMARY.md as a historical artifact

Successor is the source-derived docs/current/architecture-map.md."
```

---

### Task 15: Refresh `README.md`

**Files:**
- Modify: `README.md` (full rewrite of body; preserve title, badges, license link)

**Source anchors:**
- `pyproject.toml:1` — package name `townlet`, version `0.1.0`, Python `>=3.13`
- `configs/default_curriculum/experiment.yaml` — curriculum levels
- `docs/current/` — link readers to the source-derived set rather than re-stating facts

**Required content (one printed page):**

1. *Title and badges* — keep as-is.
2. *What this is* — one paragraph. Cite `pyproject.toml:1` for runtime baseline.
3. *Quick start* — three exact commands, copy-pasteable:

   ```bash
   uv sync --extra dev
   uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal
   uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q
   ```

4. *Curriculum levels* — short bullet list, one phrase each, sourced from each level's `curriculum.yaml`.
5. *Where to read more* — link to `docs/README.md` and name the 12 `docs/current/` pages by topic.
6. *Status* — pre-release, no API stability, no PyPI package.
7. *License* — link to `LICENSE`.

Do **not** include in the new README: long architecture prose, ASCII diagrams, observation-dim tables, network architecture descriptions, training tips. Those live under `docs/current/`.

- [ ] **Step 15.1: Capture existing title + badges**

Run: `sed -n '1,12p' README.md`
Keep those lines verbatim in the rewrite.

- [ ] **Step 15.2: Draft and write the new README**

- [ ] **Step 15.3: Verify the three quick-start commands work**

```bash
uv sync --extra dev 2>&1 | tail -3
uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal 2>&1 | tail -3
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q 2>&1 | tail -3
```
All three must succeed. If any fail, do not commit a README that claims they work — instead, fix or surface the failure to the user.

- [ ] **Step 15.4: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale README.md
```
Expected: Exit code 0, no output.

- [ ] **Step 15.5: Link integrity**

```bash
rg -no '\(docs/[^)]+\)' README.md | sed 's/[()]//g' | while read p; do test -e "$p" || echo "MISSING: $p"; done
```
Expected: No `MISSING:` lines. Every linked doc/ path must exist after Tasks 1–13.

- [ ] **Step 15.6: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README around source-derived docs/current/ set

Refs: filigree hamlet-7a52a63e0b"
```

---

### Task 16: Refresh `AGENTS.md` (de-duplicate against CLAUDE.md)

**Files:**
- Modify: `AGENTS.md`

**Premise:** `AGENTS.md` currently duplicates the "Pre-Release / Zero Backwards Compatibility" rules verbatim from `CLAUDE.md`. The right shape is the opposite: `AGENTS.md` holds short, agent-facing operational rules (how to claim work, how to use observations, how to commit, where docs live) and links to `CLAUDE.md` for project-specific guidance and to `docs/current/` for runtime facts.

**Required content:**

0. *Header pointer (first block in the file).* To prevent agents that load only AGENTS.md from seeing a summary with no indication it is incomplete, the very first non-title block must be:

   ```markdown
   > **Note:** This file is a quick-start. The authoritative behavior rules for agents live in CLAUDE.md (loaded automatically into every Claude Code session in this repo). Read CLAUDE.md when in doubt.
   ```

   Verify with:
   ```bash
   rg -c 'authoritative.*CLAUDE\.md|CLAUDE\.md.*authoritative' AGENTS.md
   ```
   Expected: ≥1.

1. *Purpose paragraph.* One paragraph: this file is the operational contract for any agent (human or AI) working in this repo.
2. *Working with Filigree.* Short version of the workflow already in `CLAUDE.md`'s "Filigree Issue Tracker" section — link to `CLAUDE.md` for the full reference. Name the atomic verbs (`start_work`, `start_next_work`).
3. *Observations rule.* One paragraph: when to use `observe` (incidental, out-of-scope) vs when to keep work in task scope. Lift the "you fix bugs in your currently defined scope" paragraph from `CLAUDE.md` — single source of truth lives there; this file summarizes and links.
4. *Pre-release / no backwards-compat.* One short paragraph. Do not re-list every antipattern; link to `CLAUDE.md`'s antipattern catalogue.
5. *Where to read.* Link to `README.md`, `CLAUDE.md`, `docs/README.md`, `CONTRIBUTING.md`, `SECURITY.md`.
6. *Source of truth.* One sentence: source code wins over docs; if you find drift, file a Filigree issue.

- [ ] **Step 16.1: Identify duplication between `AGENTS.md` and `CLAUDE.md`**

```bash
diff <(sed -n '1,80p' AGENTS.md) <(rg -A 60 'CRITICAL: Pre-Release' CLAUDE.md | head -70) || true
```
Confirm the antipattern catalogue is the same in both files.

- [ ] **Step 16.2: Rewrite `AGENTS.md` to the six-section shape above (target: 60–100 lines)**

- [ ] **Step 16.2a: Verify section count (DoD gate)**

  The "60–100 lines" length check alone is too weak. Confirm all required sections exist:

  ```bash
  rg -c '^## ' AGENTS.md
  ```

  Expected: ≥5. The six required sections (setup/purpose, Filigree workflow, observations, pre-release, where to read, source of truth) map to at least 5 `## ` headings in the final file. Confirm the exact count matches the sections you wrote and record it in the execution log.

- [ ] **Step 16.3: Confirm both files no longer duplicate**

```bash
rg -c 'NO backwards compatibility arrangements' CLAUDE.md AGENTS.md
```
Expected: `CLAUDE.md:1`, `AGENTS.md:0`. The rule lives in CLAUDE.md only.

- [ ] **Step 16.4: Stale-term and link gates**

```bash
python3 scripts/docs_gate.py --stale AGENTS.md
rg -no '\(docs/[^)]+\)' AGENTS.md | sed 's/[()]//g' | while read p; do test -e "$p" || echo "MISSING: $p"; done
```
Expected: Both empty.

- [ ] **Step 16.5: Commit**

```bash
git add AGENTS.md
git commit -m "docs: shrink AGENTS.md to operational rules; de-duplicate CLAUDE.md content"
```

---

### Task 17: Refresh `CLAUDE.md` (remove stale claims, align with new docs)

**Files:**
- Modify: `CLAUDE.md`

**Known stale claims in current `CLAUDE.md` (to be removed or rewritten):**

1. "All config packs **MUST** include `variables_reference.yaml`." — false; the live shared file is `vfs_profiles.yaml` (see `configs/default_curriculum/vfs_profiles.yaml`).
2. "`drive_as_code.yaml` required for all config packs" — false; the per-level file is `drive.yaml` (see `configs/default_curriculum/levels/L0_0_minimal/drive.yaml`).
3. Compiler described as "seven-stage" — replace with the actual stage count from `src/townlet/universe/compiler.py` (the same value Task 6 establishes).
4. `drive_hash` checkpoint provenance claim — verified in Task 9. If absent from source, remove the claim from `CLAUDE.md`.
5. Any path under `src/hamlet/` described as part of the runtime — that package is obsolete; only `src/townlet/` is live.
6. Hard-coded coverage percentages (`%` numbers in prose) — replace with "run `uv run pytest --cov=townlet`".
7. **Rephrase `(<1%)` parenthetical at CLAUDE.md:370** (the Q-Learning DQN overhead callout). Replace `(<1%)` with `(sub-percent)` or delete the parenthetical entirely. The coverage gate matches `<1%` on the regex `\b\d+(?:\.\d+)?%` (the `\b` fires between `<` and `1`), so this must be cleaned up here in Task 17 so that CLAUDE.md passes Task 21.1's `docs_gate.py --coverage CLAUDE.md` cleanly.

**Approach:** This is a surgical pass, not a rewrite. Preserve the file's structure (Project Overview, Pre-Release Status, Development Commands, etc.). Edit only the stale paragraphs.

**Scope note:** AGENTS.md link/command repair belongs to Task 16; this task only covers CLAUDE.md.

- [ ] **Step 17.1: Identify each stale paragraph**

```bash
rg -n 'variables_reference\.yaml|drive_as_code\.yaml|seven-stage|seven stage|drive_hash|src/hamlet/' CLAUDE.md
```
Print and review each match before editing.

- [ ] **Step 17.2: Verify the replacement facts**

```bash
ls configs/default_curriculum/vfs_profiles.yaml
ls configs/default_curriculum/levels/L0_0_minimal/drive.yaml
rg -n '_log_stage\(' src/townlet/universe/compiler.py | wc -l
rg -n 'drive_hash' src/townlet/ | head
```
Use the outputs to write replacement paragraphs. If `drive_hash` returns zero hits, the claim is removed (not rephrased).

- [ ] **Step 17.3: Edit `CLAUDE.md`**

For each match from Step 17.1, replace the paragraph with one that cites the live source. Do not add new sections; do not move sections.

- [ ] **Step 17.4: Re-run the stale-term grep**

```bash
python3 scripts/docs_gate.py --stale CLAUDE.md
```
Expected: Exit code 0, no output. (The `drive_hash` term may legitimately appear if Step 17.2 confirms it in source; otherwise it must also be empty.)

- [ ] **Step 17.5: Verify the two gate commands still pass**

```bash
uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal 2>&1 | tail -3
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q 2>&1 | tail -3
```
Both must still pass — `CLAUDE.md` edits are documentation only, no runtime code touched.

- [ ] **Step 17.6: Commit**

**Hold this commit until Steps 17.4, 17.5, 17.7, and 17.8 all pass clean.** The commit captures both the stale-claim removals (Steps 17.3) and the dead-link repairs (Step 17.7) in a single atomic diff.

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): strip stale claims and repair dead docs/* links

Stale claims removed/rewritten:
- variables_reference.yaml → vfs_profiles.yaml
- drive_as_code.yaml → drive.yaml (per-level)
- seven-stage compiler count → actual count from compiler.py
- src/hamlet/ runtime references → src/townlet/ only
- hard-coded coverage percentages → dynamic command reference
- <1% parenthetical → sub-percent (coverage gate compat)

Dead docs/* links repaired (see Step 17.7 table):
- docs/UNIVERSE-COMPILER.md, docs/architecture/COMPILER_ARCHITECTURE.md,
  docs/vfs-integration-guide.md, docs/config-schemas/*, docs/plans/*,
  docs/guides/dac-migration.md → rewritten or archived paths

Replacements anchored to:
- configs/default_curriculum/vfs_profiles.yaml
- configs/default_curriculum/levels/L0_0_minimal/drive.yaml
- src/townlet/universe/compiler.py (actual stage count)
- docs/current/ pages created by Tasks 6-13

Refs: filigree hamlet-7a52a63e0b"
```

- [ ] **Step 17.7: Enumerate dead docs/* links in CLAUDE.md**

Run the broad path scan:

```bash
rg -n 'docs/[a-zA-Z0-9_./-]+' /home/john/hamlet/CLAUDE.md
```

Paste the full output into the execution log. For each hit, decide one of:
- (a) Rewrite to `docs/current/<page>` if a planned new page covers the topic (check `docs/current/` after Tasks 2–13 complete).
- (b) Rewrite to `docs-archive/2026-05-16-pre-reconstitution/<original-path>` if the content is preserved only in the archive.
- (c) Delete the link entirely if the surrounding sentence becomes redundant without it.

Suggested per-hit guidance (non-binding; executor confirms by checking the `docs/current/` index after Tasks 2–13):

| Dead path | Suggested action |
|-----------|------------------|
| `docs/UNIVERSE-COMPILER.md` | rewrite to `docs/current/universe-compiler.md` |
| `docs/architecture/COMPILER_ARCHITECTURE.md` | rewrite to `docs/current/universe-compiler.md` |
| `docs/vfs-integration-guide.md` | rewrite to `docs/current/vfs-vtc-dac.md` |
| `docs/config-schemas/variables.md` | rewrite to archive path `docs-archive/2026-05-16-pre-reconstitution/config-schemas/variables.md` |
| `docs/config-schemas/enabled_actions.md` | rewrite to archive path `docs-archive/2026-05-16-pre-reconstitution/config-schemas/enabled_actions.md` |
| `docs/config-schemas/drive_as_code.md` | rewrite to archive path; also rewrite any section pointer to `docs/current/vfs-vtc-dac.md` (DAC reward composition lives in Task 8b) |
| `docs/config-schemas/training.md` | rewrite to archive path; or rewrite to `docs/current/training-checkpoints.md` if the surrounding sentence links to the checkpoint topic |
| `docs/plans/2025-11-06-variables-and-features-system.md` | rewrite to archive path |
| `docs/plans/2025-11-12-drive-as-code-implementation.md` | rewrite to archive path |
| `docs/plans/2025-11-12-dac-runtime-integration.md` | rewrite to archive path |
| `docs/guides/dac-migration.md` | rewrite to archive path |
| `docs/config-schemas/` (bare directory reference) | rewrite to `docs/current/config-model-v21.md` or delete if the sentence is redundant |

- [ ] **Step 17.8: Link-integrity check on CLAUDE.md**

After applying all repairs from Step 17.7, verify that every `docs/` path in CLAUDE.md resolves on disk:

```bash
rg -on 'docs/[a-zA-Z0-9_./-]+' /home/john/hamlet/CLAUDE.md | while read -r line; do
    path="${line#*:}"; path="${path%% *}"
    test -e "/home/john/hamlet/$path" || echo "MISSING: $line"
done
```

Expected: no output (all paths resolve). If any `MISSING:` lines appear, return to Step 17.7 and resolve each before committing.

---

### Task 18: Refresh `CONTRIBUTING.md`

**Files:**
- Modify: `CONTRIBUTING.md`

**Source anchors:**
- `pyproject.toml:119` — pytest configuration (testpaths, addopts, markers)
- `docs/current/testing-quality-gates.md` — canonical commands (created in Task 11)

**Required content:**

This is a surgical pass too. Preserve the file's table of contents; rewrite sections only where they reference old commands, paths, or docs.

1. *Getting started.* Confirm `uv sync --extra dev` is current; cite `pyproject.toml`.
2. *Development workflow.* Replace any "run all tests" example with the canonical command from `docs/current/testing-quality-gates.md` and link there for the full list.
3. *Submitting changes.* Confirm the commit-message and PR conventions still match recent history (`git log --oneline -20`). If the existing prose differs from what recent commits do, update it to match the observed convention, not the inverse.
4. *Where docs live.* Add one short paragraph: "Project documentation is split between root-level files (`README.md`, `CLAUDE.md`, `AGENTS.md`, `SECURITY.md`) and `docs/current/` (source-derived, anchored to code). Archived docs at `docs-archive/2026-05-16-pre-reconstitution/` are historical only."
5. *Where plans go.* Add a section with heading `## Where plans go` reading:

   > New implementation plans live in `plans/<YYYY-MM-DD>-<slug>.md` at the repo root. The legacy `docs/plans/` directory was archived on 2026-05-16; do not write new plans into that directory or into `docs/current/plans/`. The root `plans/` directory is intentional — plans are not docs, they are working artifacts that drive a single piece of work and become history once the work is done.

   Verify with:
   ```bash
   rg -c '^## Where plans go' CONTRIBUTING.md
   ```
   Expected: `1`.

- [ ] **Step 18.1: Identify outdated commands and paths**

```bash
rg -n 'src/hamlet/|docs/[A-Z]|pytest tests/' CONTRIBUTING.md
git log --oneline -20
```

- [ ] **Step 18.2: Apply edits**

- [ ] **Step 18.3: Stale-term and link gates**

```bash
python3 scripts/docs_gate.py --stale CONTRIBUTING.md
rg -no '\(docs/[^)]+\)' CONTRIBUTING.md | sed 's/[()]//g' | while read p; do test -e "$p" || echo "MISSING: $p"; done
```
Expected: Both empty.

- [ ] **Step 18.4: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs(CONTRIBUTING.md): align dev commands with current pyproject.toml and link to docs/current/testing-quality-gates.md"
```

---

### Task 19: Refresh `SECURITY.md`

**Files:**
- Modify: `SECURITY.md`

**Approach:** Verify each policy claim against current state. This is the lightest-touch task in the plan.

- [ ] **Step 19.1: Read the file and inventory claims**

```bash
sed -n '1,200p' SECURITY.md
```
List each factual claim (supported versions, reporting channel, response window, scope).

- [ ] **Step 19.2: Verify each claim**

For each "supported version", check `pyproject.toml:3` for the actual project version. For each "reporting channel" (email, GitHub Security Advisory), confirm it is configured. If the file mentions checkpoint provenance or `pickle` trust boundaries, cross-check with what Task 9 wrote in `docs/current/training-checkpoints.md`.

**Verification audit (W20):** For every factual claim in SECURITY.md, add an HTML comment immediately above the claim (in your working copy only) citing the verification source:

```
<!-- verified: path/to/source.py:LN -->
```
or for a URL source:
```
<!-- verified: https://github.com/<github-org>/<repo>/... -->
```

These `<!-- verified: ... -->` comments are **LOG-ONLY artifacts** — do not commit them to SECURITY.md. Paste the verified-comment-augmented version of the file into the execution log so the verification is auditable. Strip the comments before the Step 19.6 commit.

- [ ] **Step 19.2a: Verify GitHub Security Advisory channel (W11)**

SECURITY.md may claim a GitHub Security Advisory channel is configured. Check the live repository configuration:

```bash
# Option A: browser — visit https://github.com/<github-org>/<repo>/security/advisories
# Option B: CLI (substitute real org/repo for the placeholders)
gh api repos/<github-org>/<repo>/security-advisories 2>&1 | head -5
```

Replace `<github-org>` and `<repo>` with the real values (find them via `git remote get-url origin`).

**Remediation branches:**
- If the advisory channel is **enabled**: no action needed; the claim is verified.
- If the advisory channel is **not enabled**: either (a) enable it (operator decision — requires repo admin rights) and document the action in the execution log, OR (b) remove or reword the claim from SECURITY.md so it no longer asserts the channel is active. Do not leave SECURITY.md claiming an unconfigured channel.

- [ ] **Step 19.3: Edit only the inaccurate sections**

If the file is already accurate, the only required edit is a cross-reference to `docs/current/training-checkpoints.md` for the pickle-boundary section. PyTorch checkpoint loading uses `pickle`, which is a code-execution attack vector. SECURITY.md MUST add a cross-link to `docs/current/training-checkpoints.md` pointing at the pickle-boundary section (use the actual section heading the Task 9 executor established; name it explicitly in the cross-link). This is mandatory, not optional — do not skip it even if the rest of the file is accurate. Do not invent new policy beyond this cross-link.

- [ ] **Step 19.4: Stale-term gate**

```bash
python3 scripts/docs_gate.py --stale SECURITY.md
```
Expected: Exit code 0, no output.

- [ ] **Step 19.5: Link-integrity check on SECURITY.md**

Task 19.3 may add a cross-link to `docs/current/training-checkpoints.md`. Verify every `docs/` path in SECURITY.md resolves on disk:

```bash
rg -on 'docs/[a-zA-Z0-9_./-]+' /home/john/hamlet/SECURITY.md | while read -r line; do
    path="${line#*:}"; path="${path%% *}"
    test -e "/home/john/hamlet/$path" || echo "MISSING: $line"
done
```

Expected: no output (all paths resolve). If any `MISSING:` lines appear, correct the link in Step 19.3 and re-run before proceeding.

- [ ] **Step 19.6: Commit (only if edits were made)**

```bash
git add SECURITY.md
git commit -m "docs(SECURITY.md): align with current state and link to docs/current/training-checkpoints.md"
```
If no edits were needed, skip the commit and note in the task that the file was verified clean.

---

### Task 20: Append a `CHANGELOG.md` entry

**Files:**
- Modify: `CHANGELOG.md` (append-only — do not rewrite historical entries)

**Required content:**

Under the existing `## [Unreleased]` heading, add (or extend if present) a `### Changed` subsection with one entry:

```markdown
### Changed
- **Docs reconstitution.** Archived the legacy `docs/` tree to
  `docs-archive/2026-05-16-pre-reconstitution/` and rebuilt `docs/` as a
  source-derived set under `docs/current/`. Refreshed root docs (`README.md`,
  `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md`) to cite live
  anchors and point at the new pages. Removed stale claims about a
  <!-- stale-callout: seven-stage -->
  <!-- stale-callout: variables_reference.yaml -->
  <!-- stale-callout: drive_as_code.yaml -->
  "seven-stage" compiler, mandatory `variables_reference.yaml`, and
  `drive_as_code.yaml` (the per-level file is `drive.yaml`; the shared VFS
  file is `vfs_profiles.yaml`). Refs: filigree hamlet-7a52a63e0b.
```

- [ ] **Step 20.1: Locate the `## [Unreleased]` line**

```bash
rg -n '^## \[Unreleased\]' CHANGELOG.md
```

- [ ] **Step 20.2: Append the entry under `### Changed` (create the subheading if absent)**

- [ ] **Step 20.3: Verify CHANGELOG passes the stale-term gate**

```bash
python3 scripts/docs_gate.py --stale CHANGELOG.md
```
Expected: Exit code 0, no output. If it exits non-zero, return to Step 20.2 and ensure the three `<!-- stale-callout: … -->` marker lines are present inside the appended block (within 6 lines above each banned term), then re-run until clean.

- [ ] **Step 20.4: Verify nothing else was edited**

```bash
git diff --stat CHANGELOG.md
```
Expected: A small additive diff. If older entries are touched, revert and try again.

- [ ] **Step 20.5: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(CHANGELOG): record docs reconstitution under [Unreleased]"
```

---

### Task 21: Whole-tree stale-term sweep and final commit

**Files:**
- No new file. This is the all-tree gate before declaring docs reconstitution done.

**Scope:** Sweep both the new `docs/` tree **and** the refreshed root docs. Exclude the archive (`docs-archive/`) — it is allowed to contain stale claims; that is the point of archiving it.

- [ ] **Step 21.1: Master stale-term sweep across new docs/ and root docs**

Run the shared gate against every doc-shaped file in the refresh surface. The script honours `<!-- stale-callout: … -->` markers; the archive is excluded by listing paths explicitly.

```bash
mapfile -t TARGETS < <(find docs -type f -name '*.md'; printf '%s\n' README.md AGENTS.md CLAUDE.md CONTRIBUTING.md SECURITY.md CHANGELOG.md)
python3 scripts/docs_gate.py --stale "${TARGETS[@]}"
```
Expected: Exit code 0, no output.

Also run the coverage-percentage gate (only `docs/current/testing-quality-gates.md` is expected to carry pasted pytest output, which it must wrap with `<!-- pytest-output -->`):

```bash
python3 scripts/docs_gate.py --coverage "${TARGETS[@]}"
```
Expected: Exit code 0, no output.

- [ ] **Step 21.2: Verify the two gate commands still pass**

```bash
uv run python -m townlet.universe validate configs/default_curriculum --primary-level L0_0_minimal 2>&1 | tail -3
uv run pytest tests/test_townlet/integration/test_golden_path_smoke.py -q 2>&1 | tail -3
```
Expected: Both pass.

- [ ] **Step 21.3: Cross-link integrity sweep**

Every link from root docs into `docs/` must resolve to a real file:

```bash
for f in README.md AGENTS.md CLAUDE.md CONTRIBUTING.md SECURITY.md; do
  rg -no '\(docs/[^)]+\)' "$f" | sed 's/[()]//g' | while read p; do
    test -e "$p" || echo "MISSING in $f: $p"
  done
done
```
Expected: No `MISSING in …` lines.

- [ ] **Step 21.4: Sanity check that the archive is intact and untouched by the refresh**

```bash
ls docs-archive/2026-05-16-pre-reconstitution | wc -l
git log --oneline -- docs-archive/2026-05-16-pre-reconstitution | head -5
```
Expected: Non-zero count under the archive; commit history shows only the original `git mv` from Task 1 (plus Task 14's `DEPENDENCY_ANALYSIS_SUMMARY.md` move). No subsequent edits.

- [ ] **Step 21.5: Allow-list marker budget check (W5)**

Count every `<!-- stale-callout: ... -->` and `<!-- pytest-output -->` marker across the gated surface:

```bash
rg -c '<!-- (stale-callout|pytest-output)' \
    CLAUDE.md AGENTS.md CONTRIBUTING.md SECURITY.md README.md CHANGELOG.md docs/current/*.md \
    | awk -F: '{sum+=$2} END {print "Total markers:", sum}'
```

DoD: total markers must be **≤ 20**. This is a soft budget — every marker is a small gate bypass. The 20 ceiling derives from the plan's expected legitimate uses: 3 in CHANGELOG, 2–4 in Task 5 replacement notes, 1 in Task 17 stale-claim repair, 1–2 in Task 11 pytest-output paste-ins, and a small buffer. If the total exceeds 20, the executor must either remove unneeded markers or justify each excess marker explicitly in the master-sweep commit message.

- [ ] **Step 21.6: Dead-marker detection (W6)**

Verify that every allow-list marker guards prose that still contains the relevant term (stale-callout) or a percentage/count value (pytest-output). Run the gate script's audit mode:

```bash
python3 scripts/docs_gate.py --audit-markers \
    CLAUDE.md AGENTS.md CONTRIBUTING.md SECURITY.md README.md CHANGELOG.md docs/current/*.md
```

This flag instructs `docs_gate.py` to scan LOOKBACK=6 lines after each marker and confirm:
- For `<!-- stale-callout: <term> -->`: `<term>` appears within the next 6 lines.
- For `<!-- pytest-output -->`: a `\d+%` or `\d+ passed` pattern appears within the next 6 lines.

**Note for Task 1.6 executor**: the `--audit-markers` flag with LOOKBACK=6 logic must be added to `docs_gate.py` when implementing that script (or retrofitted during this task if the flag is absent). If the flag is unavailable at execution time, use this inline fallback:

```bash
python3 - <<'EOF' -- \
    CLAUDE.md AGENTS.md CONTRIBUTING.md SECURITY.md README.md CHANGELOG.md docs/current/*.md
import re, sys
LOOKBACK = 6
errors = []
for path in sys.argv[1:]:
    lines = open(path).readlines()
    for i, line in enumerate(lines):
        m = re.search(r'<!-- stale-callout: (.+?) -->', line)
        if m:
            term = m.group(1).strip()
            window = ''.join(lines[i+1:i+1+LOOKBACK])
            if term not in window:
                errors.append(f"{path}:{i+1}: dead stale-callout marker for '{term}'")
        if '<!-- pytest-output -->' in line:
            window = ''.join(lines[i+1:i+1+LOOKBACK])
            if not re.search(r'\d+%|\d+ passed', window):
                errors.append(f"{path}:{i+1}: dead pytest-output marker (no count in next {LOOKBACK} lines)")
if errors:
    print('\n'.join(errors)); sys.exit(1)
print("All markers live.")
EOF
```

DoD: zero dead markers. Any found must be removed or the surrounding prose restored before the master-sweep commit.

- [ ] **Step 21.7: Pytest paste-in freshness comparison (W7)**

Identify pages carrying pasted pytest output:

```bash
rg -l '<!-- pytest-output -->' docs/current/
```

For each identified page, locate the pytest command cited near the marker (it must appear within 20 lines of the marker in a fenced code block), re-run it, and compare the trailing pass count:

```bash
for page in $(rg -l '<!-- pytest-output -->' docs/current/); do
    cited=$(rg -o '\b[0-9]+ passed' "$page" | head -1 | awk '{print $1}')
    echo "Page: $page  Cited count: $cited"
    # Re-run the command shown in the fenced block above the marker and compare.
    # If live count != cited count, replace the pasted block with fresh output.
done
```

DoD: every cited `N passed` count matches a live re-run executed **within 4 hours** of the master-sweep commit (record the run timestamp alongside the command output). If the cited count differs from the live count, replace the pasted block with fresh output and update the surrounding prose.

- [ ] **Step 21.8: Intra-docs/current/ link integrity (W10 — file links)**

The existing Step 21.3 checks root → docs/ links. This step checks links *within* `docs/current/`:

```bash
for f in docs/current/*.md; do
    rg -no '\([a-z0-9_-]+\.md(#[a-z0-9_-]+)?\)' "$f" | sed 's/[()]//g' | while read target; do
        base=$(echo "$target" | sed 's/#.*//')
        dest="docs/current/$base"
        test -e "$dest" || echo "MISSING in $f: $dest"
    done
done
```

DoD: no `MISSING in …` lines. If a link target is missing, either repair the link to point at the correct file or remove the link.

- [ ] **Step 21.9: Source-anchor file existence (W10 — code path references)**

Verify that every `src/path/to/file.py` or similar source-tree citation inside `docs/current/*.md` (typically found in "Implementation at …" notes or "See:" references) resolves to an existing file on disk. Line-number validity is optional (it is a documentation snapshot) but file existence is required:

```bash
rg -oN 'src/[a-z_/]+\.(py|yaml|json|md)(:[0-9]+)?' docs/current/*.md | \
    sed 's/^[^:]*:[0-9]*://' | sed 's/:[0-9]*$//' | sort -u | \
    while read p; do test -e "$p" || echo "MISSING: $p"; done
```

DoD: zero `MISSING:` lines.

- [ ] **Step 21.10: Anchor file-existence check for backtick paths (W15)**

Verify that every `path/to/file.{py,yaml,md,json}` referenced inside backticks across `docs/current/*.md` exists on disk:

```bash
rg -oN '`[a-z_/][a-z_/.]*\.(py|yaml|md|json)(:[0-9]+)?`' docs/current/*.md | \
    sed 's/^[^`]*`//' | sed 's/`.*$//' | sed 's/:[0-9]*$//' | sort -u | \
    while read p; do test -e "$p" || echo "MISSING: $p"; done
```

DoD: zero `MISSING:` lines.

- [ ] **Step 21.11: Bare code-fence detector (R1)**

Every fenced code block must carry a language tag:

```bash
mapfile -t TARGETS < <(find docs/current -name '*.md'; printf '%s\n' README.md AGENTS.md CLAUDE.md CONTRIBUTING.md SECURITY.md CHANGELOG.md)
rg -n '^\`\`\`$' "${TARGETS[@]}"
```

DoD: no output. Acceptable language tags include `bash`, `python`, `yaml`, `json`, `markdown`, and `text` (for plain output). Any bare ` ``` ` fence must have a language tag added before the master-sweep commit.

- [ ] **Step 21.12: Glossary re-check (R5)**

Extract every bolded `**TERM**` (sentence-case or initialised acronym) from `docs/current/*.md` (excluding `glossary.md` itself) and verify each appears in `docs/current/glossary.md`:

```bash
rg -oN '\*\*([A-Z][A-Za-z0-9 -]+)\*\*' docs/current/*.md | \
    grep -v 'glossary\.md' | \
    sed 's/.*\*\*\([^*]*\)\*\*/\1/' | sort -u > /tmp/bolded.txt

rg -oN '\*\*([A-Z][A-Za-z0-9 -]+)\*\*' docs/current/glossary.md | \
    sed 's/.*\*\*\([^*]*\)\*\*/\1/' | sort -u > /tmp/defined.txt

comm -23 /tmp/bolded.txt /tmp/defined.txt
```

DoD: `comm` output is empty. If there are bolded terms not in the glossary, either add a glossary entry for each or include a one-line justification for each undocumented term in the master-sweep commit message.

- [ ] **Step 21.13: Confirm the Filigree task can be closed**

```bash
filigree show hamlet-7a52a63e0b 2>&1 | head -20
```
The done-definition is satisfied when:
- New `docs/` says source is authority for the reconstruction (Task 2 README).
- New `docs/` uses actual compiler / config / VFS / reward / exploration / frontend facts (Tasks 4–10).
- Coverage is replaced with command output, not a fixed percentage (Task 11).
- Root docs are aligned with the new `docs/current/` set (Tasks 15–20).
- The master grep in Step 21.1 finds nothing.
- Allow-list marker budget is ≤ 20 (Step 21.5).
- All markers are live — no dead stale-callout or pytest-output markers (Step 21.6).
- All pasted pytest counts are fresh (within 4 hours) and match live re-runs (Step 21.7).
- All intra-docs/current/ links resolve and all cited source-file paths exist on disk (Steps 21.8–21.9).
- All backtick-referenced file paths exist on disk (Step 21.10).
- All code fences carry a language tag (Step 21.11).
- Glossary covers every bolded sentence-case term, or every gap is justified in the commit message (Step 21.12).

Close it:

```bash
filigree update hamlet-7a52a63e0b --status=in_progress --actor docs-reconstitution
# … work happens across tasks 1–21 …
filigree close hamlet-7a52a63e0b --reason="Replaced archived docs with source-derived set under docs/current/ and refreshed root docs (README, AGENTS, CLAUDE, CONTRIBUTING, SECURITY, CHANGELOG). Stale-term grep returns empty across docs/ and root docs. Archive preserved at docs-archive/2026-05-16-pre-reconstitution/."
```

- [ ] **Step 21.14: Final commit of any lint/whitespace fixes the sweep surfaced**

```bash
git status
git add docs README.md AGENTS.md CLAUDE.md CONTRIBUTING.md SECURITY.md CHANGELOG.md
git commit -m "docs: final stale-term sweep across new docs/ tree and root docs

Refs: filigree hamlet-7a52a63e0b"
```

---

## Self-Review Notes

- **Spec coverage.** Every doc in the user's 12-file model is a task (Tasks 2–13). The archive move is Task 1. Root-doc refresh is Tasks 14–20. The whole-tree gate is Task 21. The plan's writing contract names the banned stale terms enumerated in the originating Filigree issue (`hamlet-7a52a63e0b`).
- **Placeholder scan.** No "TBD" / "implement later" steps remain. Each task names exact files, exact commands, expected outputs.
- **Frontend conditionality.** Task 10 explicitly verifies `frontend/package.json` is missing before documenting the `npm run dev` flow as conditional on `hamlet-d892e161c0`.
- **Plan-self-preservation.** This plan lives at `plans/2026-05-16-docs-reconstitution.md` (outside `docs/`), so Task 1's archive move does not consume it.
- **No edits to `src/townlet/environment/vectorized_env.py`.** The originating brief calls out that file as someone's in-progress fix. This plan only reads it.
- **Out-of-scope files explicitly named.** `LICENSE` and `CODE_OF_CONDUCT.md` are not edited (no project-specific drift). `DEPENDENCY_ANALYSIS_SUMMARY.md` is moved to the archive (Task 14) rather than refreshed — its successor is `docs/current/architecture-map.md` (Task 4).
- **Root-doc ordering.** Root docs (Tasks 15–20) are refreshed *after* the `docs/current/` set exists (Tasks 1–13), so cross-links from root docs into `docs/current/` always resolve.
- **CHANGELOG discipline.** Task 20 is strictly append-only under `## [Unreleased]`; historical entries are not rewritten. Step 20.4 verifies this with a `git diff --stat`.
- **De-duplication risk.** `AGENTS.md` currently duplicates `CLAUDE.md`'s antipattern catalogue verbatim. Task 16 explicitly checks for and removes this duplication; Step 16.3 asserts the rule lives in `CLAUDE.md` only.

---

## Execution Handoff

Plan complete and saved to `plans/2026-05-16-docs-reconstitution.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks. Best for an audit-heavy task like this where each doc benefits from an independent fact-check.
2. **Inline Execution** — execute tasks in this session with checkpoints. Lower latency, but loads the full archive context into one window.

Which approach?
