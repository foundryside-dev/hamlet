# Replay evidence handoff — R73 onward, DRAFT / NOT PUBLISHABLE

2026-11-13. Durable predecessor is WIP14 at
`678513c7540a61114d59a17d1b1e0eb8a06ce0a2`. The next interval starts R73;
**terminal round is unknown**. R77 tests are being authored, not asserted executed.
This finite metadata/prose reconciliation preserves every existing receipt and
review. No application/helper edit, source import/execution, Git/index action,
new source body or delegation occurred. Selected receipt/log/spec/identity data
were read and named receipt/manifest hashes measured; this is not a complete
artifact-inventory rehash or independent rerun of source/process verification.

Paths: W=`/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`,
P=`W/wave35-preparation`, Q=`/workspace/bac-review-2026-11-01/qualification`.
All following candidates have the WIP14 base commit above. Authoritative round
receipts live under W/wave35; each keeps its own actual execution tree.

| Round / authoritative receipt | Actual candidate tree | Measured candidate-manifest SHA256 (`rN-candidate.json`) |
| --- | --- | --- |
| R73 `r73-replay-stagea-receipt.json` | 93e04eee6a305ede45ad2b3acc5181942f8e98cc | fc65aba14dfecbd91458ca533047498786605bc3ed26d8da1bee4110f60a555a |
| R74 `r74-replay-stagea-fix1-receipt.json` | 6fe4a41e45e35af808e98164b6015a34503cf97b | 426a7de7f7c6505cd5ff502606e062f8958bfbc24def55748fed550edd48029a |
| R75 `r75-replay-stagea-fix2-receipt.json` | c46acb9860c50cfe4162c65d696a8662947179fc | 8a65e8b33d08442c6f37c98907945196a22b7e60d82be5b337a7b5d05b5d2b55 |
| R76 `r76-replay-stageb-initial-receipt.json` plus additive `r76-replay-poison-receipt.json` | ea50156c62b594cb1343f4d2561120b77164707b | 7403ba79434c65940524f844c8e1e9703eb2aed2fcfa5217f7166e331a15749d |

## Check map and accounting

For each row below, raw directory is `Q/wave35-rN-<check>/`, spec is adjacent
`Q/wave35-rN-<check>-spec.json`, and ordinary named result/log are
`<check>-result.json` / `<check>.log` inside that directory. Custody receipts,
negative custody and failure indexes are referenced by the authoritative receipt.
Static/types directories contain multiple explicitly named commands as shown.
These are concrete producing paths, not a directive to recursively copy them.

| Round | Check(s), observed status/counts | Review / accounting boundary |
| --- | --- | --- |
| R73 | `collection`: 18 collected; `replay-healthy`: 9 PASS; `replay-admission-red`: 3 FAIL; `replay-owner-red`: 1 FAIL; `replay-prepared-red`: 4 FAIL | 17 distinct executed = 9 pass + 8 intended behavioral failures; one explicit-lineage node unrun. Real held-domain/owner bypass and successful-invalid-publication RED preserved. Collection adds no execution. Stage A SPEC accepted as RED; QUALITY required four test corrections. |
| R74 | `collection`: 19; `replay-healthy`: 10 PASS; `replay-prepared-red`: 4 FAIL; `replay-custody-api-red`: 5 FAIL | 19 distinct executed. API failures are three missing participants, one missing lineage keyword, one unreached owner guard; they are not new actual waiting-bypass observations. Fix1 corrected original four issues but introduced PER active-prefix comparison P2; QUALITY changes required. |
| R75 | `collection`: 20; `replay-per-fixture`: 1 PASS; `replay-healthy`: 11 PASS | Fixture1 is included in healthy11: **11 distinct, not12**. No broad RED repeat. Fix2 review accepts bounded Stage A SPEC/QUALITY; does not approve production behavior. |
| R76 | `collection`: 21; `replay-healthy`: 11 PASS; `replay-causal`: 9 PASS; later `replay-poison`: 1 PASS | Actual healthy and causal specs are complementary `-k` sets with poison excluded from causal; named poison runs its single exact node. **21 distinct executed**, not42 including collection. Prior-round cases remain separate executions of different candidate bytes, not additive unique coverage. |
| R76 | `static`: `expression-doc` PASS; `ruff-global` FAIL test import sort; `black-global` FAIL five owned files; `no-defaults` FAIL601>600 | Static evidence has no pytest count or controller-runtime claim. Do not waive failures because runtime selections pass. |
| R76 | `types`: `owned-mypy` PASS four files; `mypy` FAIL9 (oracle6 + visible POP3) | Decorator signature erasure undercounts caller migrations; owned PASS is not integration/type acceptance. |

Review pointers: P/T18e-R0-REPLAY-STAGEA-{REVIEW,FIX1-REVIEW,FIX2-REVIEW}.md;
P/T18e-R0-REPLAY-STAGEB-REVIEW.md and STAGEB-ADDENDUM.md. Stage B SPEC and
QUALITY remain CHANGES REQUIRED despite the21 bounded passes. Findings remain
B1 stale destination validation, B2 caller-held prepared payload, B4 missing
finite nesting/staging/publication/quarantine controls, B5 erased typed
signatures, B6 CUDA constructor capability reconciliation. B3 permits the finite
ambient-free, persistent-stream-preserving scratch-generator category, with
accurate producer prose still owed; it is not literally RNG-free. External
callers, CUDA completion/owner lifetime, parent integration and final gates stay
open. Programme accounting remains28 qualified /38 remaining /66 total.

## Source/process and actual new child custody

Round receipts report815 source guards,573 config digests,13 protected artifacts,
14 registered worktrees/1 available, and source/index guards. Named pytest runs
include controller/import/thread custody; static commands do not. No xdist worker
population is established by spec `workers:1`: this is harness job concurrency.
Elapsed job seconds are actual harness durations; absolute UTC start/end are
absent and must remain null with reason. Pytest's shorter internal timing is not
a discrepancy: for example poison log4.26s versus parent wall8.439117670059204s.

R76 poison authoritative raw directory is Q/wave35-r76-replay-poison; spec hash
`6447a42aeeb70159e94766a66d97fafb3398c796ecbb911f0a16ac845a479acb`.
`replay-poison-result.json` hash
`76773d434d85eaa7eda092982f895d3397cdadd254d30e76eb2ca80908f5e173`
records exit0; generic `replay-poison-custody.json` records1 pass, zero
warnings/skips and one controller identity. That count is not the child census.
Under its `replay-poison/` subdirectory, child-owned
`spawn-identity-replay_poison.json` and parent-owned
`spawn-observation-replay_poison.json` pair actual child PID37026 with observed
Process.pid37026 and queued PID37026; actual child PPID37001 equals recorded
parent PID37001. Exit0, qualified True and exact `replay poison fail closed`
message are present. Child retains imports3 plus fully qualified replay_imports4,
Torch2.11.0+cu130, intra1/interop5, debugTrue and the R76 manifest hash. This is
CPU evidence; the Torch build string does not establish CUDA execution.

`replay-spawn-custody-replay_poison.json` hash
`71d5c3044a06c95b8a95b34f790f438b3ae60fdcbdce4a62c0935ab26a00a6fa`
binds those exact inputs to verifier fix1 SHA
`aef826f304f66798c1845bdf1436b8fb27336708776a514f50d2f353942402a8`
and harness SHA
`180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.
The original old-role verifier remains unchanged and does not admit replay;
“generic and replay child verifiers PASS” means generic job custody plus the
separately named replay verifier, not old-role admission. Old child receipts did
not have PPID; their actual Process/queue PID custody is not rewritten.

Tooling lineage is P/T18e-R0-REPLAY-CHILD-VERIFIER-REPORT.md, initial independent
review (`98717b6f...`, D1 duration finding), then
T18e-R0-REPLAY-CHILD-VERIFIER-FIX1-INDEPENDENT-REVIEW.md
(SHA `92bc216a6cb635c8b213a4880098f45d9da59bb87f13a3351a3eeaac6b1ba11a`).
D1 is closed; narrow SPEC/QUALITY pass follows finite-positive duration checking.
Independent fix1 log/exit are named in that review:13 synthetic tests PASS.
Root/independent runs overlap; initial12 plus fix1 13 are not25 distinct tests,
and none counts as application execution. Author report's UNRUN statements remain
true for the author, superseded for execution status by root/independent records.
The child is a public-poison **consumer refusal** witness, not a genuine
restoration/setter-failure witness or resolution of Stage B findings.

## Predecessor CI and reconciliation findings

W/evidence-management/wip14-final-ci-observation.json has measured SHA
`aabfb31db6716aeed07d48dc38b650fd96824d031a4c1e80ce07fc6d7ddf9411`.
At WIP14 base: Config Validation43380483349 SUCCESS; Lint43380483338 FAILURE
(known six oracle errors per prior log); Tests43380483451 FAILURE at fast-suite
step, job131736848095. Test cause/counts remain unknown: no raw log was acquired;
the empty redirected wip14-tests-ci.log is not evidence. Recorded CI timestamps
are real remote metadata and do not supply missing local attempt timestamps.
These are predecessor failures, not executions of the R73–R76 working candidates.

No contradictory counts or child PID/hash bindings were found in the selected
metadata. Apparent stale status is historical scope: R74/R75 “review pending”
precedes later immutable review decisions; initial R76 “poison not run” precedes
the additive poison receipt. Preserve those bytes and link later records rather
than repairing history. The actual acceptance blockers are the retained source,
static/type and remote-CI failures above. The packet is not a terminal checkpoint:
it lacks a known terminal round, complete finite attempt/member inventory,
terminal qualification subject/review and publication seal. R73's compact receipt
has fewer explicit artifact references than later receipts; root must include its
actual named specs/custody/failure/log records in that future inventory, rather
than treating its prose custody label as a complete artifact table.

## Finite next-checkpoint handoff

Keep WIP14 as predecessor; start the next explicit interval atR73 and append
future attempts, including real R77 results only after they exist. Retain every
failed, unrun and superseded attempt with source identity; never substitute the
terminal tree for the tree that actually executed. A terminal child claim must
belong to the qualifying check's terminal attempt; R76 child success cannot
qualify later changed replay/test source by reuse. Next terminal review must
bind the frozen qualification subject and independent review before publication.

EVIDENCE-PROCESS.md supplies immutable evidence/publication rules, but its finite
selector section is explicitly WIP14/R59–terminal. It is not an authorized ready
selector contract for the next R73 interval. Root must seal the next finite
contract and reconcile actual interval membership before any final plan, avoiding
recursive historic-wave copies or repeated full baseline scans. Preserve null
UTC timestamps, actual elapsed seconds, exact commands/log hashes, check kinds,
overlap accounting and pending hardware/caller/CI gates. Rehash selected bytes
and existing reuse targets immediately before publication. This handoff grants
no final-mode selection, assembly, publication or application acceptance.

Measured authoritative receipt hashes, in table order above:

- R73: `55af950829bb32176ab976b757a461aa2514fda99d11e998b947fea304c13700`
- R74: `98ee3a1114ac0556be89af709675cc357b9e8a887578df213f79125576d744e2`
- R75: `e91f096991d134ffb268f632703967082b925594b31a8024169a9d71fe8c76b6`
- R76 initial: `37122e2432de18be98f7b07d0e3757cb9a90460cde181abf32963f7ca06d9667`
- R76 poison: `f0304d5140e8b6c5f3b477bd1d87485949d61cb1d3dc6c4b3892cba589e47ae8`
