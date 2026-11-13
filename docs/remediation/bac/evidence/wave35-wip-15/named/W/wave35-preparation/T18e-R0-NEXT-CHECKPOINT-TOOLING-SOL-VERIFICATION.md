# Explicit other-model verification of frozen checkpoint selector FIX1

2026-11-13. **Scoped source verification: PASS at the frozen FIX1 hashes below.** The two repaired contradictions are rejected, and no material defect was found in the bounded contract, catalog, or assembly paths inspected. This is synthetic integrity verification, not an actual checkpoint selection, qualification, assembly, or publication approval.

## Identity and scope

The root orchestrator explicitly selected `gpt-6-sol` at medium reasoning effort for this verifier, separately from the `gpt-6-astra` medium producer. This records the orchestration selection; no more precise runtime model version is exposed or asserted. This verifier read the repository `AGENTS.md`, the tooling BRIEF and amended REPORT, the original and FIX1 independent reviews, and the FIX1 scoped diff. The only complete source bodies read were `E/bac_checkpoint_contract.py` and `E/test_checkpoint_contract.py`; no application or historical selector source body was read. `E` is `W/evidence-management`, `P` is `W/wave35-preparation`, and `W` is `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`.

| Frozen source | Lines | SHA-256 before and after execution |
| --- | ---: | --- |
| `E/bac_checkpoint_contract.py` | 573 | `6fc6845ccb73e9bc8a0e24837bf005b0d2cd156107cb8a8341ded9012b7c54b3` |
| `E/test_checkpoint_contract.py` | 616 | `b0dd9f8a3f7420771f237cc35be453040b134924a59225d1ba7c5fdb88a0d07d` |

The amended `P/T18e-R0-NEXT-CHECKPOINT-TOOLING-REPORT.md` was verified at SHA-256 `13b9190ae664255af62dfeb92804dfdc1eb79b50e71a1546db44db9cec2e7aa0`; the scoped diff at `f1173ed4e0ca88447e15b92475141b77a4ba9337aa800642403d1785f8e737ce`. The diff contains the two repaired guards and two corresponding synthetic test methods. The earlier independent review found S1/S2; the FIX1 review marked both addressed but did not claim a verified exact other-model identity.

## Actual execution and findings

From `E`, I executed `python -B -m unittest test_checkpoint_contract.py`. Exit code was 0: `Ran 30 tests in 0.846s`, `OK`. These are 30 synthetic test methods, including the two successive contract/catalog case; they are not application runs or independent real qualification.

I also ran three direct probes through the existing temporary synthetic fixture without modifying source. A JSON child witness with the correct candidate tree but `attempt_id=older-attempt` was rejected with `child witness attempt mismatch`. An `UNRUN` attempt carrying a non-null end time, passed counts, and duration was rejected with `unrun cannot claim execution`. The existing witness schema with no literal `attempt_id` returned `READY FOR ROOT PUBLICATION CHECKS`, preserving the supported historical shape. All probe files were temporary DATA and cleaned by the fixture.

Source inspection confirms the qualifying child's receipt `attempt_id` must equal the check's terminal attempt; a JSON witness's explicitly present `attempt_id` must equal that child identity. A witness without that literal field does **not** gain same-attempt proof from this guard. Root must retain the limitation or establish genuine spec/result/PID and source linkage from recorded evidence before relying on it. The UNRUN guard requires a reason and null/absent `exit_code`, `started_at`, `ended_at`, `counts`, and `duration_seconds`; the separate qualifying runtime branch still requires positive finite elapsed time and real passed count.

The neutral catalog reader checks an inventory anchored predecessor, ordered chain suffix and current pointer, contiguous explicit intervals, format-tagged WIP13/WIP14/neutral layouts, manifest/plan links and object agreement, and provenance of reused paths. The test suite exercises two successive synthetic future checkpoints without code changes, including reused objects and byte-exact assembly. `assemble` demands a READY plan, recomputes it against current inputs, checks exclusive destinations and hashes selected sources/reuse, then verifies copied bytes. No material defect was identified in those inspected paths. These checks do not replace root's substantive review of receipt truth or protect against every concurrent filesystem race.

No actual archive input was selected or assembled. No application import/runtime, Git/index/remote write, branch/worktree/checkout/source execution copy, deletion, or delegation occurred. The application remains frozen at R81. The only persistent write from this verifier is this note. Root still owns sealed actual terminal inputs, absent-literal child linkage, qualification and independence judgments, final publication, and remote/CI gates.
