# Shared review brief — Townlet review/bug-finding pass (2026-10-23)

Repo: /home/john/hamlet (branch fix/episode-lane-accounting, clean apart from a startup-hook edit
to CLAUDE.md/AGENTS.md/.claude/skills that you must not touch). Python env is synced:
`cd /home/john/hamlet && uv run python ...` / `uv run pytest ...`. CUDA exists but use CPU.
Read /home/john/hamlet/CLAUDE.md first (project rules; especially "Zero backwards compatibility",
"No-Defaults Principle", "Never branch on a variable's name", and the observation-is-tokens section).

## Context

The owner just finished a major refactor pass over VFS, the universe compiler, the strata
(substrates) and Universe-as-Code (effects/items/affordances/rewards/expressions). This is a
REVIEW AND BUG-FINDING pass over that work. You are NOT fixing anything. You are NOT writing
product docs, PDRs or evidence records. Deliverable: a findings file.

Two layers of work, both required:

### Layer 1 — adjudicate the existing bug backlog in your seam

/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/triage_bugs.md
holds 45 triage bugs with their original reproductions. Your seam's subset is listed in your
prompt. Most were filed BEFORE the refactor ("Cut A", "Cut B", "static epistemic access", see
README.md "Author a universe"). Several name authoring surfaces that no longer exist
(environment.yaml variables, vfs_profiles.yaml, static overlays). For EACH bug in your subset
give exactly one disposition, with evidence:

- STILL LIVE — you ran a reproduction against current source and it fails as described.
  Cite file:line of the defect and paste the command + actual output.
- FIXED — you ran a reproduction and it now behaves correctly. Name the test or commit if you
  can find it (git log -S is fine), else just the passing output.
- OBSOLETE — the authoring surface or code path the bug is about was deleted. Say what replaced
  it and whether the UNDERLYING concern (not the surface) is addressed on the replacement. If the
  concern survives on the new surface, that is a NEW finding, not an obsolete one.
- UNVERIFIED — only if a reproduction is genuinely impossible (say why). Avoid.

Treat the bug descriptions as CLAIMS TO TEST. A reviewer who reads the description and writes
"plausible" has added nothing. Many reproduce in a ten-line Python script against the packs in
configs/test/, configs/simple, configs/trial_k_cold, configs/trial002_money_log_gdp,
configs/static_epistemic_access, configs/aspatial_test, configs/default_curriculum. Compile with:

    from pathlib import Path
    from townlet.universe.compiler import UniverseCompiler
    u = UniverseCompiler().compile(Path("configs/<pack>"), primary_level="<level>")
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    env = VectorizedHamletEnv.from_universe(u, level_name="<level>", num_agents=2, device="cpu")

Put scripts in /tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/<seam>/
never in the repo. Do not create files under /home/john/hamlet. Compiling may rewrite
configs/<pack>/.compiled caches; that is ignored by git and fine.

### Layer 2 — fresh hunt, by method not vibes

The Trial probes that filed the backlog found one repeatable defect pattern: declared vocabulary
with no runtime consumer, or runtime capability with no authoring reach, or two vocabularies that
disagree. Hunt for more of the same, systematically, in your seam:

1. Every DTO field / enum member / config key in your seam → who consumes it in src/townlet/?
   A required field consumed by nobody is a bug (no-defaults forces authors to write dead config).
2. Every runtime branch / capability in your seam → which YAML surface reaches it? None = dead.
3. Residual references to surfaces CLAUDE.md says were deleted — the grep is pre-run in
   scratchpad/residuals.txt (94 hits: ObservationField, VFSObservationSpec, observation_builder,
   curriculum_active, ObservationActivity, vfs_profiles, static_overlay, observation_mode,
   observation_encoding, reward_strategy). Some are legitimate refusal messages; some are stranded
   paths. Adjudicate the ones in your files.
4. Literal default-curriculum meter names in engine code — pre-run in scratchpad/meter_literals.txt.
   Docstrings are fine; executable branches on "energy"/"money" etc. are the CLAUDE.md
   "engine knows the game" defect. Adjudicate the ones in your files.
5. vulture output in scratchpad/vulture.txt (450 lines at 60% confidence; pydantic validators and
   `forward` are false positives). Check the entries in your files.
6. .defaults-whitelist.txt entries covering your files: is each still justified, or hiding a
   hasattr-guarded / dict.get default that CLAUDE.md calls an antipattern?
7. Genuine correctness bugs: wrong tensor shapes under num_agents != batch assumptions, device
   mismatches, off-by-one in bounds/wrap, reset not restoring declared initial state, order
   dependence between phases, silent clamps, exceptions swallowed. Reproduce before reporting.
8. Think about the ABI contracts: every hash the compiler emits — is it compared by anyone?
   Every "refuse" the docs promise — does it actually refuse?

Do NOT report style, naming, or "could be simpler". Do NOT report missing docs unless the doc
actively lies about behaviour. Do NOT propose fixes beyond one sentence.

## Output — REQUIRED shape

Write /tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/findings_<seam>.md:

    # Findings — <seam>
    ## Backlog adjudication
    | id | disposition | evidence (file:line, command, 1-line output) |
    ## New findings (ranked, most severe first)
    ### F1. <one-line claim>
    - severity: P1 (wrong behaviour / crash / silent data corruption) | P2 (dead or unreachable
      declared surface, misleading refusal) | P3 (latent)
    - where: file:line
    - failure scenario: concrete inputs → wrong output
    - reproduction: command + actual output (pasted)
    - note: one sentence on likely fix, optional
    ## Refuted
    Claims (backlog or your own hypotheses) you tested that did NOT reproduce, with the command.
    ## Coverage
    What you read fully, what you skimmed, what you did not reach. Be honest.

A findings file with no Refuted section means you tested nothing and will be discarded.
Return a 10-line summary in your final message; the file is the deliverable.
Budget: be thorough but finish. Prefer running code over reading it.
