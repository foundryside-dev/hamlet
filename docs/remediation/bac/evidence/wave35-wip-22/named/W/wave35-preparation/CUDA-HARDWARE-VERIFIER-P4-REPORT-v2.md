# P4 verifier repair v2 — bounded author report

Status: FROZEN FOR FRESH INDEPENDENT REVIEW; NOT SELF-ADOPTED.

The prior independent review's two custody findings are repaired: same-host/boot process monotonic lifetimes are enclosed by parent pre-Popen/post-cleanup wait bounds, and worker lifetimes by controller observations; worker inventories require one run UID/mainargv and unique initial gateways. Same-gateway replacements require the exact previous gateway process as predecessor plus the existing accepted failed-down/configure chain. All replacements additionally require nonoverlapping predecessor END/replacement START monotonic times. The post-Popen launch sample is deliberately not a lower bound on child observations.

Root authorized the supplier-confirmed transport repair as well. P2's factual capsule establishes exact copying of five completion arrays, including source_witnesses, and mandatory raw-provenance membership in producer inventory. P4 now independently enforces both. The existing nonempty result source rule plus exact copying requires nonempty completion sources. Producer inventory remains distinct from the independently complete final inventory; no universal equality/subset or transitive source-array closure was invented.

The inert fixture's worker monotonic values previously exceeded controller and sometimes parent bounds; they now stay within both, preserving positive worker/replacement/PID-reuse controls. Tests coherently rehash all references, so regressions fail on semantic checks rather than stale digests.

Retained attempts:

- repair-v2-red-v1: 13 failed / 73 passed. New coherent mutation helper supplied str where P0 requires Path. This is a retained test-helper failure, not causal defect evidence.
- repair-v2-red-v2: 11 failed / 75 passed. All 11 new negative cases failed with DID NOT RAISE, demonstrating accepted inconsistent observations. Existing 73 and two new valid-edge controls passed.
- repair-v2-green-v1: 86 passed after implementation.
- repair-v2-format-v1: Black reformatted both writable bodies; before bytes retained.
- repair-v2-green-final: 86 passed on frozen formatted bytes; PID194976, actual argv/PID/PPID/UTC/exit and source hashes recorded in pytest.json.
- repair-v2-static-final: Ruff and Black check exit0.

Each mutation and each RED/GREEN attempt has an exclusive before snapshot of all four packet bodies. Failed attempts, fixture directories and all stdout remain present. Only one synthetic pytest process ran at a time; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, no conftest, no bytecode, and OMP/MKL/OpenBLAS threads1. Tests import no APP/Torch/CUDA or real producer toolchain. The existing receipt race test uses threads within that one pytest process.

Read/review scope conservatively counts four packet bodies plus the retained independent reviewer probe (five bodies, 3,121 lines), below five/5,000. Wrapper and P0 bytes remain identical to v1. No P1/P2/P3 bodies read or imported; P2 supplier and adopted interface were read as metadata. Source edits were limited to Q/verify_bac_hardware_v1.py and Q/test_verify_bac_hardware_v1.py. No Git, branches/worktrees/copies, APP source, publication or root inventory creation.

P3 Python-debug/owner-launch/no-import fork amendments, P5 semantics, six CUDA groups, actual source-qualified owners, full producer integration and actual hardware remain pending/unrun. A common-only synthetic pass supplies no device evidence. Root must obtain independent review, adopt exact bytes, then author its concrete job inventory. General producer inventory/source closure remains an explicit supplier-policy limit.
