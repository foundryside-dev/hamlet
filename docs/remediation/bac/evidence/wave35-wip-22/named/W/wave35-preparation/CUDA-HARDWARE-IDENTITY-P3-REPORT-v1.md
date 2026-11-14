# P3 actual-process identity — frozen author packet v1

Status: author implementation and bounded synthetic qualification complete;
independent review and root adoption required. No APP/Torch/CUDA/server execution.
P0 and historical identity bytes remain unchanged. Four counted bodies total
1,711 lines: historical 60, adopted P0 520, new identity 610, new tests 521.

Final retained run: E/hardware-identity-p3/final-suite-v1/execution.json and
stdout.log; 44 passed, 3 discovery-only tests deselected, exit 0. Final collection
separately confirmed 44/47 selected without executing fixtures. Exact commands,
actual PID/UTC/exit and contemporaneous source snapshots are recorded per attempt.
The final synthetic fixture tree is retained at final-fixtures-v1. Counts are not
application or hardware acceptance: three inert case helpers and the hook surface
check occur in the selected count, while the substantive assertions below name
observable behavior. No overlapping test counts are summed.

Implemented actual PID/PPID/Linux start token/host/boot, interpreter, /proc argv,
cwd, exact environment and source/import hashes; source-grant root authority,
source/index no-writer checks, start/end pairing and monotonic duration. Roles
observe existing runtime configuration without setters or RNG draws. Uninitialized
loaded Torch uses module dictionaries only; fork guards make no Torch/CUDA calls.
The public record_process API takes explicit owner authority; pytest uses the
root-approved acyclic static-policy/P2 runtime descriptor handoff. Exact actual
workerinput and controller configure/down lifecycle associate replacements with
real predecessor identities. Crashed workers retain their start and no invented
end. Pytest emits causal per-phase reports and exclusive closed completion.json;
runner-owned exit/end/log facts are absent.

Tests include actual spawned child, guard-only fork process, crashed spawned child,
serial pytest controller, controller plus two xdist workers, and a worker crash
followed by its admitted replacement. Stub Torch APIs raise on forbidden observer
calls; work observations check exact 1/5/True configuration. Source/import/index,
interpreter/environment and root grant mutations refuse. Later adversarial REDs
proved and fixed an import-root omission, an unreported loaded source import,
malformed grant time, and grant expiry during source observation.

Retained attempts include intentional REDs and fixture failures. Initial GREEN
attempts green-core-v1/v2/v3 failed because inert fixtures violated exact P0 argv/
import-root or pytest phase environment semantics; those provisional negative
passes were not acceptance evidence. green-core-v4 first passed valid core
fixtures. red-hooks-v1/v2 exposed subprocess fixture COLUMNS/LINES additions;
red-hooks-v3 demonstrated absent pytest transport options. green-hooks-v1's
xdist failure came from a test double affecting unrelated uname subprocess use;
scoping the double to the recorder gave green-hooks-v2. replacement-v1 verified
actual dynamic replacement. red-adversarial-v1 (3 failures) → green-adversarial-v1;
red-interval-v1 (1 failure) → green-interval-v1. All snapshots/logs are retained.

Rulings and boundaries:
- Root's explicit existing-checkout/no-Git-write/no-APP scope overrides generic
  skill worktree/commit/full-project-suite recommendations. No Git mutation,
  checkout, execution copy, installation, remote operation or deletion performed.
- P0 structural validation is not authority or qualification. The delegated
  descriptor is trusted only through root-authorized P2 execution, known paths,
  exact references and actual live parent custody. No hash-authorship claim.
- CPU-bound/source-grant/spec/static-policy construction follows v3's acyclic DAG.
  v1/v2 proposals are retained as history; v3 supersedes their cyclic transport.
- Tests use inert source bytes and a read-only Git metadata double. They prove
  observation/validation mechanics; they do not prove current APP source identity.
- Loaded Torch CUDA initialization marker is not proof about every native context.
  Admitted device mapping is recorded provenance, never evidence of device work.
- Source hashes cannot exclude a transient edit restored between samples; root's
  no-writer interval remains mandatory. Source observation checks the interval at
  both beginning and completion of its read-only metadata work.
- P4 owns full cardinality, replacement-limit/causal-lifecycle and missing-end
  acceptance. P3 retains incomplete process evidence without fabricating a pass.
- Actual owner child/producer/fork-three-trial/RNG/phase instrumentation is outside
  this packet. Guard test establishes no-Torch observer behavior in a synthetic
  process; it does not replace inherited owner-module/strict three-trial evidence.
- completion.json does not fabricate obligation evidence. Required-case/source/
  custody/child obligation validators and P2→P3→P4 complete attempts remain owed.
- P1/P2 private source-grant reference ordering reconciliation was requested via
  metadata. Current P3 compares exact flattened input list order; owner confirmation
  is outstanding at freeze. A mismatch must be resolved explicitly before integration.

Fresh independent review should inspect authority DAG, all exact runtime bindings,
actual-versus-declared argv and imports, role observation restrictions, partial
writes/reparenting, worker lifecycle ambiguity/replacements, source-freeze time
coverage, and proof limits of the stubbed metadata/real process tests. This report
is not self-approval and does not advance hardware qualification.
