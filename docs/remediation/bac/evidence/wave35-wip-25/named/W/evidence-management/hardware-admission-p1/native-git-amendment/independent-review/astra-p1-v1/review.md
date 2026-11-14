# Independent finite P1 native Git review

Disposition: REQUEST CHANGES for one bounded diagnostic-custody defect. No false admission demonstrated. Root is sole publisher; this is not root adoption or full-chain/hardware qualification.

Subject freeze SHA256 86b5921ab660ad861e8a9933f14ee90b15dd306c1c3d163aedb1bcb3cad95740 and interface SHA256 459470cddf05d5f2098bb12a5d00168d4abd16b71ba6ca5421787772087db7ff were verified. Capture/test/protocol exact hashes and sizes are retained in attempt.json, unchanged before/after. Authorized source packet was measured before reads: 974+890+526=2390 lines, three bodies. Independent probe adds 94 lines: total 2484/four bodies. Historical source was not opened. No implementation edits, new source copies, actual Git, APP import, CUDA runtime, worktree, branch, index mutation, or extra agent was used.

## Finding: cleanup failure discards native command evidence

At capture_bac_hardware_v1.py:702-705, the timeout/cancellation handler kills and calls communicate(timeout=30) without containing failures of that second operation. A second TimeoutExpired exits run_git before post-reference observation and commands.append at lines708-716. Partial stdout/stderr available on TimeoutExpired are also lost. This can occur when pipe EOF remains unavailable after the direct child is killed; proving that the direct child was killed does not establish pipe closure. No escaped-descendant supervision guarantee is requested.

The independent timeout probe supplies a child whose two bounded communicate calls time out and whose kill sets returncode=-9. records remains empty. On the source-query path, sample's finally consequently persists an empty command list; capture's exception tuple does not include TimeoutExpired, so it propagates after the terminal finally rather than retaining its reason. This latter consequence is static call-path analysis, not a separately executed integration test. Discovery's observe catches Exception but likewise loses the native command record. No accepted result is claimed for either path.

Contain cleanup exceptions and finalize one refused command observation even when cleanup does not finish; retain available partial byte streams, error status and post-reference outcome. Keep bounded cleanup and existing resource rules. Add an expected-refusal regression for the second timeout. The second independent RED injects a kill ProcessLookupError and demonstrates the same uncovered exception-handler edge, but typical CPython Popen suppresses that race; it is a robustness observation, not a second independently established production defect.

## Results and scope

Single inert run: existing119 PASS, independent5 PASS, independent2 assertion FAIL (the timeout and injected kill failure above), overall124 PASS/2 FAIL. These are separate selections, not broader hardware results. Independent positives check exact version lines with and without terminal LF, reversible non-UTF8 stderr, spawn failure, post-wait executable mutation, and wrong PPID. Existing tests cover ordinary timeout/cancellation, current P0 versus old pin, missing/duplicate Git dependency, fixed argv/cwd/environment, actual executable/PID, CRLF/multiline/version mismatch, source pin and failed-source diagnostic retention, CPU no-Torch/NVIDIA, and prior allocation/lease/terminal regressions.

Static construction review finds source commands use the same declared environment Git reference; no PATH-selected fallback remains. Native command field shape is closed, fixed caller argv and environment are recorded, before/after references match on success, and raw stdout/stderr use reversible decoding. validate_discovery is not a complete consumer proof: the output interface correctly requires P2/P4 to join exact version argv, PPID/host/boot, interval, cwd, executable, and inventory. Those consumers were outside this source packet and remain pending. Interpreter and cgroup rules were not relaxed. Current platform full ancestry remains unsupported and actual hardware unrun.

The previous P1 independent-review metadata was read for terminal gating and custody context; earlier historical results were not counted as this run. Existing no-writer/source/namespace authority remains an external requirement.

## Retained provenance

Execution argv exactly: `/workspace/hamlet/.venv/bin/python -B /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/hardware-admission-p1/native-git-amendment/independent-review/astra-p1-v1/probe.py`. The Python sys.argv reconstruction in attempt.json omits the interpreter flag; this paragraph records the exact shell launch. cwd was Q; PID237515; UTC2026-11-14T12:14:15.701056+00:00 through12:14:17.066718+00:00. Affinity CPU0, RLIMIT_AS4294967296. Pytest plugin autoload and bytecode/cache output disabled. Unique basetemp fixtures-v1 remains retained, with all failure traces in attempt.log.

- attempt.json SHA256 fc9777e6bc86ea07b32dec1e22c13076c5087c4a95e5f5570d8b0e5f429896fe
- attempt.log SHA256 5bb994c9f9e1f0db8d4c4ff4464d864219c9487f8e94538325138eb66cde44ff
- probe.py SHA256 d77b8902e61d4f596e8999d2ff5cfaafc5e8f844234f77dc430958721f7d34e5

Exact implementation bodies remain at their original pinned Q paths; no executable-source-copy was made. The run manifest binds those bytes before and after. No further extension or real capture is recommended by this finite review.
