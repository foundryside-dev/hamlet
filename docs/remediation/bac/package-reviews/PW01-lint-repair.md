# PW01 repair Phase A ready

Status: source stationary for root's shared RED/GREEN/review refresh. This repair
only replaces the seven root-identified default expressions with explicit
equivalent branches. It adds no behavior and leaves authored choices,
derivations, shared identities, private ownership guarantees, tests, YAML DATA,
native DATA, whitelist and ratchet unchanged.

Root supplied the causal guard evidence at
`/workspace/bac-review-2026-11-01/qualification/wave03-green-r0/no-defaults.log`:
OP119/176/178, EF188 and RP508 ternary assignments; RP62 `.get(..., {})`; and
WS110's whitelisted ternary (the separately isolated 615-versus-614 count).
The worker read this report and the corresponding owned source expressions;
the linter implementation and every sixth source remain unopened.

Scope of repair: each original condition and both original values remain the
same, with the conditional expression now an `if`/`else`. The RP training read
uses an explicit key-presence branch with the same absent-key empty mapping.
No whitelist/ratchet edit masks a violation or increases the accepted ceiling.

| Source path | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| `src/townlet/config/effective_run.py` | 365 | `9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c` |
| `src/townlet/config/exploration_policy.py` | 768 | `af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c` |
| `src/townlet/exploration/world_curiosity_state.py` | 223 | `295314b7f891cdbf33646a73df6a57c39d9fd407d61675ee6fee80bd9053d9ae` |
| `tests/test_townlet/regressions/bac/test_pw_scope_contract.py` | 261 | `d467ede1f0d2a841f62d51c70812f10b2dc6cb2ada28fa288ca32f14bcd8e150` |

Complete source inventory remains exactly five files / 1911 lines, within all
per-file and total bounds. No inline executable probe was run.

Actual worker verification: scoped Black reported all five owned files unchanged;
scoped Ruff reported all checks passed. Both used writable UV cache
`/tmp/hamlet-bac-pw01-uv-cache` and `uv run --no-sync`. The worker reviewed the
seven-expression diff, source counts, final hashes and unchanged test/DATA status.

Root-attributed earlier evidence, before these branch-only edits: the two owned
nodes passed in 23.82s; independent Astra's 171 corruption/immutability and the
five-provider/drive/native/seed controls passed on candidate `ca22c9f`.
These are prior-source results, not current-candidate qualification.

Unrun in this repair: project runtime imports, pytest, probes, no-defaults or
other broad guards, owner suites, full pytest and fresh review. Root must run
the shared frozen-image checks and observe the ratchet count; the worker makes
no current-candidate guard, runtime, package, BAC or final acceptance claim.
No index operations, commits, source copies, branches, worktrees or delegation
were performed.
