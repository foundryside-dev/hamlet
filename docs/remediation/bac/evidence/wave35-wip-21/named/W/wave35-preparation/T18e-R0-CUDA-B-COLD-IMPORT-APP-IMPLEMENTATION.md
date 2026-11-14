# B cold-import APP implementation — frozen handoff

2026-11-14. TEST BYTES AUTHORED; APPLICATION/COLLECTION/CHILD RUNTIME UNRUN.
Root remains integration, capture, execution and evidence-publication owner.
The sole APP writer is stopping for independent source review and TOOL
qualification. No production behavior or existing control was changed.

Authority: root grant `wave35/r115-cold-import-app-tests-grant.json` SHA256
`97b95b84130baaaf7f8360d9ffa8d6519bb08580fd344eb1e49d02ccbdb3f83a`;
accepted v2 plan SHA256
`a3afe3ff38c1de66176c751a16ec8b43edc0e65c4c23dc190e3de903f3837a31`;
Astra v2 review SHA256
`123c6745dfd85b96480bb25b51486cc5b849502a624eee1cf5ab3655075398ee`.
Root supplies WIP20 publication fe9cc615 and R115 peer-wait54 qualified with
closed runtime; this author ran no Git or application verification of them.

## Final source seals and budget

| Body | Whole lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/rng_custody.py`, unchanged | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`, owned | 2883 | `b1f05946a4f2c0e145c44226323dc7b599f36a1364c854d26f090fa45b1a4409` |
| Q existing spawn verifier, unchanged read-only | 752 | `6006c7247d79a99226a74756a2266a2966fce800f9f84af802f2990db4606173` |

Q=`/workspace/bac-review-2026-11-01/qualification`.
Test growth523,127 lines below the3010 ceiling. APP total4078/two, below4205.
Cumulative already-read body reservation4830/three, below4957 and hard5000/five.
No producer/helper/new TOOL body was read, including via diff, snippets,
imports or introspection. Only interface/schema metadata was exchanged with
the separate TOOL owner; no recursive agents were created.

A stdlib in-memory static comparison removed only the appended cold block and
the one new `import subprocess` from final test bytes. The reconstructed
original bytes hash to original2360 SHA256
`6ec962f9c0b3d467375528b26de39bac154b46e4d5c6435ffcc289960f063085`.
Thus every previous test/helper byte is preserved; no required control was
dropped, relocated, weakened or compressed. No source execution copy was made.

## Exact probe and node metadata

Constant: `_COLD_IMPORT_PROBE`, one module-level ASCII raw ast.Constant string,
one STRING token, one assignment and no rebinding/delete. Its exact evaluated
UTF-8 bytes:20489; lines360; SHA256
`449a01b27740c7744f9e44e4f86beaf7acf56f0fa646609e43e0588d30093705`.
Parent Popen consumes that exact variable directly, with exact argv9:

`[root/.venv/bin/python, "-I", "-c", _COLD_IMPORT_PROBE, mode, entry, root, J, nonce]`.

Venv invocation spelling is preserved; actual binary is independently observed
through resolved `/proc/self/exe`. Both actual sys.orig_argv and proc cmdline
are captured. Script hash uses actual argv[3] UTF-8; command hash uses compact
ensure_ascii JSON as v2. The script itself imports no test/bootstrap/plugin.

All new IDs have prefix
`tests/test_townlet/regressions/bac/test_rng_cuda_admission.py::`:

| Exact suffix | role | mode | entry |
| --- | --- | --- | --- |
| `test_cold_import_probe_faults[preloaded]` | `cuda_core_cold_preflight_preloaded` | `preflight_preloaded` | core |
| `test_cold_import_probe_faults[cuda_touch]` | `cuda_core_cold_preflight_cuda_touch` | `preflight_cuda_touch` | core |
| `test_fresh_process_canonical_import_order[core]` | `cuda_core_cold_import_core` | qualify | core |
| `test_fresh_process_canonical_import_order[flat]` | `cuda_core_cold_import_flat` | qualify | flat |
| `test_fresh_process_canonical_import_order[per]` | `cuda_core_cold_import_per` | qualify | per |

Original89 plus5 gives94 SOURCE-EXPECTED nodes only. Root must actually collect
and compare the complete ID set. No collection result is claimed here.

Fault metadata, line numbers within the actual -c script, not enclosing test:

- `_cold_boundary` assertion192; unique preload branch caller `<module>`200.
- NoCUDA `__getattribute__` RuntimeError raise158; direct CUDA-touch caller
  `<module>`202.

Negative witnesses are actual child-origin records immediately before the
designated assertion or sentinel raise. Their modules/CUDA counts distinguish
real preload from untouched application state and exactly one sentinel access.
They never emit a positive identity. Parent preserves full stderr; the strict
TOOL validator owns independent source-derived traceback-site validation.

## Implemented boundaries and source-issued observations

The probe checks actual empty Townlet module inventories before Torch, after
Torch/NumPy and before selected entry. It installs NoCUDA before application
imports and keeps it through real owner cleanup. A stdlib-only profile hook
matches custody filename/function names without importing it; the forwarding
import observer resolves absolute/relative/fromlist producer requests and
rejects custody-initiated eager producer imports during the selected import.
Prior hooks are restored in finally. Core-first asserts producers absent after
selected entry; allowed module origins derive from sealed manifest source files.

Actual CPU threading is configured before application import and observed as
one Python thread/OS task plus actual Torch intra/inter-op1/1. CPU RNG baselines
are taken after owner construction and compared after genuine gate work.
No CUDA query supplies provenance, readiness or a claimed hardware result.

The exact18 source-issued descriptor inventory is checked/recorded without
resetting cache or patching manifest. Real CPU flat/PER constructors, genuine
participants and actual owner context/lock use root-supplied producer facts.
Both real canonical class exports are removed/restored one at a time before
any success. Genuine gates must fail ImportError without body/cache insertion.
Then real flat/PER serialize gates resolve canonical policy once each; repeats
retain exact tuple/policy identity without resolution. Four gate records,
resolver counts2->3->4->4->4, two policies, unresolved16, exact live owner/
participant/descriptor/policy binding and empty completion are recorded.
State snapshots surround whole gate/owner-context lifetimes as Astra requires.
Actual unregister happens in finally; no disposal assumption or domain reset.

Every child/parent artifact uses the accepted v2 finite schema/profile. Qualified
parent uses the source-issued worker FileRef and actual PID/start_ticks, including
a live post-Popen proc read; strict root-log/plugin authentication remains TOOL
responsibility. Parent rejects partial qualification env rather than silently
downgrading. Process logs/files are exclusive; timeout termination/escalation,
bounded wait/reaping and separate failure records preserve unsuccessful attempts.

## Environment and strict-tool handoff

Required qualified env: existing BAC_QUAL_ROOT/OUTPUT/MANIFEST/SHA/TREE plus
root-approved `BAC_COLD_SPEC=<exact sealed cold spec absolute path>` on each
of the five separately launched one-job harness runs. It is inherited unchanged
by the child. Child independently reads its spec, validates root/manifest_ref
and byte-authenticated tool_seal_ref/runtime. `sys.version` uses the full exact
string; runtime paths/versions are compared exactly, never by prefix.

The accepted closed child/worker schemas do not gain a spec_ref field.
Actual spec path/hash authority belongs to the strict custody receipt's existing
spec_ref. Child typed manifest_ref/test_ref/worker_ref plus independently read
spec/tool-seal references form the accepted chain; root explicitly confirmed
this interpretation. TOOL owner was sent exact schema/role/site/script metadata.

Unqualified ordinary pytest uses temporary local source/worker context for
the same semantic child probe. It supplies no qualified root-run/plugin marker
chain and cannot pass the strict validator. Root-qualified runs never use that
local branch. Local execution was not performed here.

## Static checks and outstanding execution

Permitted checks only, exit0:

- Black formatted the owned test and final `black --check` reports unchanged.
- Stdlib ast.parse/compile of both enclosing module and extracted -c code
  passed without executing either; literal/token/single-binding assertions pass.
- In-memory original-byte seal comparison and final whole-body hashes/counts
  match the table above. Existing core and existing spawn verifier remain sealed.

No Ruff, application import, test, collection, child, GPU, new verifier, Git/index,
branch/worktree/checkout or source-copy execution occurred. Tool owner supplied
interim synthetic progress only; no TOOL qualification is inferred here.

Root next obtains independent final-byte APP and TOOL review, exact tool/runtime/
candidate captures, actual collection94, then qualifies both fault jobs before
the three positives. Existing89 and required activation/producer/profile checks
remain owed on final bytes with unique-union accounting. These CPU import/gate
controls establish no producer leaf, actual GPU, post-poison permission, B6/R0,
package completion or whole-programme acceptance by themselves.
