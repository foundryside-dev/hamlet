## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_effects.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| E1 | P1 | Effects survive `env.reset()`; no `EffectManager.reset()` | hamlet-d76684f549 |
| E2 | P1 | Scalar `modify: bar.X` rebinds to a broadcast view; next per-agent write hits every agent | F1 |
| E3 | P1 | `if`/`switch` commands reduce the condition with `.any()` | F2 |
| E4 | P1 | `mean` crashes on ints; four functions and `elapsed_ticks` disagree with the type checker on dtype | F3 |
| E5 | P1 | Effects cannot read time (refuses) or position (crashes) | hamlet-a737e444c0 |
| E6 | P2 | `for_each … as:` never bound | F4 |
| E7 | P2 | `nearby_agents`, `spawn_item quantity/initial_state` on the AST, not the DTO; resolver Euclidean | F5 |
| E8 | P2 | `active_effects` iterates self N times | F6 |
| E9 | P2 | `self`/`target` same entity; `self.vfs.X` unspellable; affordance and global effects address an agent row | F7, hamlet-b3a30b82ef residual |
| E10 | P2 | Distance functions refuse vectors and collapse the batch | F8 |
| E11 | P2 | Temporal operators compile in effects and always crash | F9 |
| E12 | P2 | `time_in_window` hardcodes 24 | F10 |
| E13 | P2 | Registry variables shadow effect lifecycle scalars | F11 |
| E14 | P2 | `switch` cases untyped; typo'd keys compile | F13 |
| E15 | P2 | Observable effect in zero-budget scope silently unobserved; non-observable never budgeted | F14 |
| E16 | P2 | Parameter-identical affordances and effects compile | F15 |
| E17 | P2 | `effects.md` and `expressions.md` contradict the DTO and the engine | F12, hamlet-7eadeb214c, hamlet-8f2e13c5a9 |
| E18 | P3 | Same-tick write order; `lag(x,0)`; shared random draws; `simplex_noise` is Perlin | F16-F18, F20 |
| E19 | P3 | Dead surface, swallowed import, 87 hidden defaults under blanket whitelist | F19 |
