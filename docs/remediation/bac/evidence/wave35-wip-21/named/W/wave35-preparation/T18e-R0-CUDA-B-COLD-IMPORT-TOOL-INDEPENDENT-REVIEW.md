# Independent cold-import TOOL implementation review

2026-11-14. **SPEC: PASS. QUALITY: PASS for the bounded TOOL implementation.**
No material P1/P2 defect found in the admitted implementation. This is independent
tooling review, not APP source approval, actual cold-run qualification or BAC acceptance.
Reviewer: `/root/bac_astra_cold_tool_review`, separate from the tool writer; root
dispatched the fixed-source review with the accepted V2 contract and immutable hashes.
No application source/test body or existing strict-suite body was read or introspected.

The accepted proposal hash is
`a3afe3ff38c1de66176c751a16ec8b43edc0e65c4c23dc190e3de903f3837a31`;
plan-review hash `123c6745dfd85b96480bb25b51486cc5b849502a624eee1cf5ab3655075398ee`.
Reviewed implementation report hash
`59a7686541b653201b259b27e5beb8672da9e0a91ad58975e976128b4a3f1f32`,
freeze `7ffc1c74e91bd031cb7353978a27794bfe472c3c11059038c39dd0a89f6ea98c`,
and proposed seal `dc0694e146e2c74c984efb51c86ce19d3047e33e0f6533e50eaacaa2b958b3a1`
were independently rehashed and match the dispatch anchors.

## Source and contract assessment

Read validator605, worker105 and new synthetic suite702: 1412 lines/three bodies.
Authored one independent110-line synthetic probe; actual read/authored total1522/four.
Even charging the optional old752 body (hash-only here) gives2274/five, within3364/five.
All frozen tool bytes remained identical before and after independent execution:

| Tool | SHA256 |
| --- | --- |
| `verify_bac_cold_import_identity.py` | `5263c63dd4881a9d2b4af951819e89876b76b8c63cd724ba36d953fa515fb9cb` |
| `bac_cold_worker_identity.py` | `eadc46dd32ec17e74f59d53293d4e5a774eefa3af489146335bd5c2be3a4379a` |
| `test_verify_bac_cold_import_identity.py` | `1e3c9272c28af735f6f64e8ad9f53ebbdce02c27741a73749893c72fbfd8e1c0` |
| unchanged `verify_bac_replay_spawn_identity.py` | `6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173` |

- Recursive duplicate/nonfinite rejection, exact object membership, type-sensitive
  equality and explicit integer/duration checks implement the accepted typed grammar.
- Source extraction parses data only: a unique module assignment, ASCII constant,
  one string token and AST binding checks. Fault locations are derived from the
  literal's assertion/raise and closed-mode caller branches. No application import
  occurs in the validator or plugin. Exact Popen variable use remains APP review.
- All five closed jobs and five distinct one-job specs are authenticated. Selected
  root result/log, exactly one worker hash marker, source/plugin references,
  parent/child IDs and start ticks bind the worker chain. The plugin obtains actual
  process/thread facts, with no controller-PID inference or qualified-env downgrade.
- Nine argv elements, original/proc agreement, script/command hashes, nonce/output,
  venv launch spelling and separate resolved executable hash are checked. Origin
  names derive from candidate source inventory; child inventories cannot expand it.
  Canonical path/symlink checks and final rehashes cover evidence/source drift.
- Positive schema enforces cold checkpoints, ordered18 descriptors, empty failed
  lookup caches, four ordered gates, resolver counts, repeated and distinct binding
  identities, cache order/unresolved16, state pairs, RNG equality and cleanup.
- Negative schema cannot substitute for a success identity. Exact fault count,
  phase, inventory and AST caller/site pairs are checked against one terminal
  traceback, expected exception, exit1, no timeout and completed reaping.
- Receipts are exclusive and scoped. Existing spawn verifier is only hash-bound;
  no old-profile branch is relaxed or called. Repository guard subprocess calls
  remain the established root-owned guard; synthetic runs stub those calls.

## Fresh independent evidence

Evidence directory:
`E/cold-import-tool-qualification/independent-review/`, with E=`W/evidence-management`.
`record-v2.json` records the exact argv, cwd, UTC boundaries, duration, environment,
PID, one-CPU affinity, sampled OS task count1 and all before/after source hashes.
`pytest-v2.log` and `pytest.xml` retain the complete terminal result:
**222 passed, exit0, pytest11.77s, wall12.101692s**.
This is188 existing new-suite nodes plus34 independent nodes, not222 new controls.
The writer's earlier269=188+81 evidence remains separate and is not added to222.
The existing strict suite was not rerun or read in this packet.

The independent110-line probe, hash
`6b78ca2738646c171a1220fca0de259e763b2a35051ac66b263b7edda895c945`,
uses admitted inert fixture construction but authors independent mutations:
five role baselines;24 coherently resealed record mutations; five additional AST
binding cases. Rejections cover bool state/resolver/IDs/exit/line, descriptor order,
missing final producer, invented origin, cross-class owner/policy aliasing,
repeat-participant substitution, cache/unresolved order/membership, extra RNG field,
worker native/PID collisions, extra proc terminator argument, coherent resolved-
binary argv substitution, integer duration, nested infinity, terminated negative,
appended exception and reversed terminal frames. Mutated evidence is rehashed
through its parent links; rejection is therefore not merely stale-file detection.
Every rejected case confirms no custody receipt was created. Baselines additionally
check no Townlet, Torch or NumPy module is imported into the synthetic test process.

The first independent invocation exited4 before collection because plugin autoload
was disabled while `--no-cov` lacked its plugin. `record.json` and `pytest.log`
retain that setup failure. The terminal invocation explicitly loads `pytest_cov`;
the frozen tools and authored probe were unchanged. This is an execution-command
repair, not a product fix or hidden failed test. `review-artifacts.json` binds
the command records, logs, XML, probe and reviewed document anchors by size/hash.

## Remaining bounded gates

No new blocker or schema extension is requested. Torch/NumPy path+version is the
accepted runtime grammar; external byte hashes remain root runtime adoption
provenance. The parsed assertions cannot themselves prove observed zeros, real
owner/gate identity, descriptor rationale semantics, observer ordering, live proc
custody or causal fault emission. Those require independent APP literal/source
review and the sealed actual executions already required by V2.

Root must adopt exact tool/runtime/source/spec seals, qualify both negative jobs
before launching positives, and retain failed/partial attempts and final selection
accounting. This review changes none of the outstanding GPU/producer/post-poison,
B6/R0, original-package, coverage or final-CI obligations. No Git/index/remote,
branch/worktree/checkout, source execution copy, application/CUDA execution or
delegation was performed. Writes are confined to this report and the independent
synthetic evidence directory; frozen tools are unchanged.
