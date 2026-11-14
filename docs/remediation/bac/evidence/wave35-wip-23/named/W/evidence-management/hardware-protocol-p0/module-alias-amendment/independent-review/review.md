# Independent bounded P0 module-alias review

Disposition: APPROVE exact frozen amendment for root adoption within P0 structural/reference scope. No material P1/P2 finding identified.

Freeze-v5 SHA-256: 42e94b4f7f912bb94b2a5a9851fe89adb63c718a679458eb4232ded9c974a052. Actual protocol SHA-256: e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860. Actual test SHA-256: d954011ea35a78e200747aef12a28c287e9da375b13797a6cca8861ad7c283c5. All freeze reference byte lengths and hashes independently match, including author RED/GREEN logs and snapshots, schema/interface inventories, and predecessor freeze.

Reviewed actual complete 526-line protocol and 686-line tests. In-memory removal of only reference-name branch and reversal of named-reference.name scalar selection reproduces exact predecessor protocol hash adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c; first 611 test lines reproduce predecessor f602359decd4a73626a737f186501f2f2e6e2a8d81f3cfdd354b4749f98f0899. Production delta is precisely new scalar branch and one schema selection; old tests remain an unchanged prefix. No snapshot executed.

The scalar enforces exact str, inherited NUL rejection, 1–128 characters and explicit ASCII regex union. Newly accepted underscore-leading forms require dotted identifier grammar. Generic labels retain their current domain. Input is never rewritten. Ordinary IDs, paths, digest/length/no-follow checks, duplicate process names and both pinned six-tool sets remain unchanged. Source closure remains downstream P3 responsibility.

Independent attempt02: 197 passed, zero skipped, exit 0 (179 existing cases plus 18 independent cases), PID 211603, one CPU affinity [0], no xdist, plugin autoload disabled and no conftest. Requested and /proc-observed argv match. attempt02/execution.json preserves UTC interval, PID, cwd, environment overrides, before/after source hashes, freeze rehashes and log hash. Independent probes include a separately expressed character/segment oracle over 7,381 short strings, public process boundary/type/character rejection, exact preservation, case-distinct aliases and duplicate rejection. Author RED log retains 10 failures/169 passes; rehashed GREEN reports 179 passes.

Preserved first attempt: 197 passed, but immediate /proc cmdline sampling returned empty during exec transition. It is not accepted as complete process provenance. Fresh attempt02 repeats the same selection with bounded nonempty argv sampling. Counts are not summed across overlapping runs.

Source budget: actual two reviewed bodies 1,212 lines; independent probe 53, first capture runner 45, second capture runner 51: five unique source files / 1,361 total lines, below five files / 5,000 lines. Amendment itself is below 1,400 lines. No other application/P3 source body inspected. Evidence/metadata are not source bodies.

Limits: inert synthetic P0 only. No APP/Torch/GPU, real P3 fixture, Git/index/branch/worktree/checkout, deletion or tool-source mutation. Only new independent-review artifacts and inert pytest fixtures written. This approval does not qualify P3, full-chain custody, observed alias/source closure, or hardware acceptance. Root must adopt exact freeze before separately authorized consumer retry.
