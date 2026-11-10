# RNG binding bridge — tests authored, awaiting root freeze

ABI review: RNG-BINDING-ABI-REVIEW.md, requested Astra MEDIUM configuration confirmed by root. Blocking active-context snapshot conflict and nonnegative none-provider observation geometry correction recorded. Public binding bridge remains minimal and additive; existing quiescence and construction semantics unchanged.

TDD state: tests authored before production. No pytest, collection, imports, compilation, lint, typecheck or other runtime qualification executed. Production source untouched. Root must seal custody/spec, run collection and fixture prerequisite, then observe genuine missing-public-method RED before authorizing implementation. No claim of passing tests or completed bridge.

Fixture prerequisite node:
`tests/test_townlet/regressions/bac/test_pw_rng_binding.py::test_binding_fixture_prerequisite`
It resolves actual YAML through actual config models/resolver, roundtrips descriptor, constructs actual EpsilonGreedyExploration through actual OwnedWorldBackend.construct callback, verifies snapshot/from_snapshot active-context rejection and unchanged owner/ambient state. It does not invoke the missing method.

Primary RED node:
`tests/test_townlet/regressions/bac/test_pw_rng_binding.py::test_binding_inside_actual_owned_constructor`
With fixture prerequisite independently green, this enters actual construct's candidate callback then asserts the missing callable activation-safe binding guarantee. Real none backend returned after validation. No failure by absent import.

Authored test families: fixture prerequisite; actual constructor callback; all four component no-draw reads; actual candidate per-domain advancement and original-owner restoration; reordered/replaced/removed spectators; same-ID different-owner nested refusal; 18 malformed/mismatched binding probes in both quiescent/active contexts; broken owner from real capture failure; CPU avoids CUDA queries; collectable CUDA hardware-conditional binding/callback; malformed actual owned descriptor; real restoration-failure coordinator quarantine. Test-only coordinator monkeypatch is cleanup custody, not production validation. CUDA test initializes explicitly at quiescence; CPU profile should exclude CUDA execution if root has not authorized it.

The no-draw/state assertions compare public snapshots and complete ambient Torch/Python/NumPy states, with CUDA for the conditional case. Deliberate constructor draws compare envelope RNG against retained actual callback candidate and unchanged input owner. This bridge does not prove bank learning, five-provider factory behavior, runner integration, or broad qualification; those gates remain required.

Inventory (exactly three whole source/test files):
- WS MODIFY reservation, unchanged: src/townlet/exploration/world_curiosity_state.py; 847 lines / cap1000; SHA256 ec3cf8ded83f952ca4c1993b084b2ee0c7f1e611bf172ab31830ecfdc27f352d.
- RP READONLY: src/townlet/config/exploration_policy.py; 768 lines / cap1100; SHA256 af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c.
- NEW test: tests/test_townlet/regressions/bac/test_pw_rng_binding.py; 374 lines / cap1400; SHA256 b55c9102d5893e47e71fb6f09cdf1c493c80ff1a80a764b2e593b25681c89d57.
Actual sum1989<=3500<=5000. No fourth source read, branch/worktree/copy/subagent/index/commit/install actions. Prose references AGENTS.md, RNG-BINDING-brief.md, PW03-ABI-PROPOSAL.md, PW03-brief.md, PW03-source-verified-api.md only. Shell/Python used solely for text editing and metadata, not runtime tests.

Known limits: authored tests await collection; syntax/style/API assumptions are unexecuted. Root owns any fixture repair authorization after sealed prerequisite failure, RED observation, and production-write authorization. This writer is stationary until that handoff.

## Authorized production bridge, ready for R1 freeze

Root supplied sealed R0 evidence: tree98498b71cb0c29d1a7fd6e7809e465bfe965a352; collection52 PASS; actual YAML/resolver/backend/lifecycle fixture prerequisite1 PASS; RED50FAIL/1PASS/1CUDA-skip in9.7827s, all50 call-phase failures at missing activation-safe public validate_binding and no setup errors. Root negative custody197source/573config/13artifacts/3process/thread1/import/index/registry PASS; all sessions CLOSED. Evidence references supplied by root: wave22/r0-negative-custody.json and Q/wave22-r0-*. Production implementation was written only after that explicit root authorization.

Added WorldRNGState.validate_binding with required descriptor/world_id/cuda_devices keyword arguments. Uses existing lock, coordinator usable check, broken-owner refusal and exact active owner guard; validates requested and actual descriptor/domain inventories with existing validators, compares existing canonical _identity and exact world/device values via existing _same. No RNG clone, stream capture/install/draw, counter changes or private API exposure. Existing snapshot/from_snapshot, activation, OwnedWorldBackend construction, prepare/install/revision logic unchanged.

Selfreview: read-only preflight works under same-owner active callbacks because it does not call _quiescent or snapshot. Different owner remains fail-fast even with the same descriptor/ID. Full descriptor reconstruction validates seed/clock/guarantee fields outside stable identity, while stable identity deliberately excludes spectators/order. Requested world membership and actual owner membership both checked. CPU empty-device validation does not query CUDA. Nonnegative observation_dim retains existing descriptor contract. Restoration quarantine and broken owner checked before binding acceptance. Generic backend construction behavior and current capabilities unchanged. Component continuation semantic validation remains the responsibility of create/from_snapshot, as before; this bridge checks binding and owner lifecycle usability, not transported continuation payloads.

No tests/runtime/static tools run by this writer after implementation; root owns frozen R1 execution and independent review. No formatter needed for the24-line additive method by inspection. Test artifact remains byte-identical to sealed R0. Green status is not yet established.

Updated exact inventory:
- WS871/cap1000 SHA256 a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c.
- RP768/cap1100 SHA256 af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c (unchanged).
- test374/cap1400 SHA256 b55c9102d5893e47e71fb6f09cdf1c493c80ff1a80a764b2e593b25681c89d57 (unchanged).
Actual sum2013<=3500<=5000. Sole source edit WS+24lines. Writer stationary for R1 freeze.

## Round1/5 formatting-only handoff

Root R1 results:51PASS/1CUDA-skip9.001s; independent Sol51PASS/1skip with custody/spec/quality PASS and no material defect. Additional360-case covering run:26FAIL/332PASS/2skip31.31s; root attributes all26 failures solely to old test_pw_rng_domains.py missing required rng/unit constructor inputs. That fourth source was neither opened nor modified by this writer. Current scope/clock/local suites passed. Global mypy9 known errors unchanged; defaults601/doc checks passed. These results are root-provided, not newly executed by this writer.

Authorized correction: Ruff --fix followed by Black on ONLY test_pw_rng_binding.py. Ruff fixed import layout; initial pass retained4 long-line findings, all resolved by Black wrapping. No assertions, test matrix, fixtures, or production behavior intentionally changed. Subsequent scoped Ruff check PASS and Black --check PASS on the exact3 owned files. No tests, imports, runtime qualification or index mutation executed by this writer. Root will reverify exact final testbytes.

Public source-verified handoff written: RNG-BINDING-CURRENT-CONTRACT.md. It specifies actual candidate active-boundary usage, required keyword inputs, spectator-independent canonical identity, exact ID/device binding, errors/no mutation and limits. Production hash remains unchanged.

Final formatting custody:
- WS871/cap1000 SHA256 a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c.
- RP768/cap1100 SHA256 af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c.
- test419/cap1400 SHA256 07503ca5c5e9e92ea94a4403d688f6b0528f96012a2aa0ad025c9e2df6aeea06.
Actual sum2058<=3500<=5000. No other source/test changed by this writer. Stationary for root final freeze. Full global guard remains pending stationary draft factory formatting,9 known mypy errors and26 old-consumer migrations; no integrated release/count increment claimed.


## Final R2 receipt and contract wording correction

Root supplied final post-format R2:51PASS/1CUDA-skip10.0588s; custody PASS197source/573config/13artifacts/3process; scoped static PASS. Sol style re-review ADDR/no new breakage. Sol correctly notes structurally forged typed records may fail during serialization with AttributeError/TypeError before validated from_dict reconstruction. Narrowed CURRENT-CONTRACT.md exception wording to distinguish ordinary structured descriptor/domain/binding ValueErrors from these forged-record serialization/type errors. All still refuse before RNG mutation; no new exception normalization promised. This is prose only; production/tests/hashes unchanged and no runtime run. Amended factory ABI review awaits root's ready exact hash.

Final revised factory ABI proposal reviewed at exact SHA256 d55ec8f46c1c772e4bf55002fdd3caeebc8eac10ce646380da4bfdcd5a6b3bcd. Astra MEDIUM spec/quality APPROVED at proposal level; receipt PW03-ABI-FINAL-REVIEW.md. Prior active snapshot conflict and nonrandom zero-width geometry restriction corrected; actual-candidate ownership, spectator identity and active provider parameter negatives preserved. Prose review only; code/test hashes unchanged, no runtime or factory source/test read.
