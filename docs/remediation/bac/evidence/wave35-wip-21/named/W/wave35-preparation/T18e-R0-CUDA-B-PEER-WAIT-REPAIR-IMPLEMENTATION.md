# R114 peer-wait observer repair implementation

Status: concrete test-only patch ready for independent exact review and root
qualification. **No repaired PASS or acceptance claim.** Writer is
`/root/bac_peer_wait_diagnosis`; all writes stop with this handoff for freeze.

## Authorization and exact identity

Root released the source freeze after WIP20 commit/push/verification at
`fe9cc615b1a0e3e94fb5dcf7e7e3fdea0be306eb` and granted only the existing
peer-wait test, its explanatory text and necessary imports/annotations.

- Approved plan: `wave35-preparation/T18e-R0-CUDA-B-PEER-WAIT-REPAIR-PLAN-REVIEW.md`,
  verified SHA256 `ad226cbd95ddb0e36a19631e79fef25512f633989da4cff92714b50d2bc94d42`.
- Grant: `wave35/r114-peer-wait-tests-only-grant.json`, verified SHA256
  `83d19c85d20a132b53b1795801cb7bb41f2178916ef2285c500a5f25a4b81d87`.
- Existing published causal RED remains R113 healthy53 = 51 PASS / 2 FAIL,
  and affected54 = 52 PASS / 2 FAIL including the isolated poison child.
  No known-bad fixture rerun was performed. Those historical failures remain.

Paths above are relative to
`.superpowers/sdd/2026-11-01-bac-remediation-upgrades/`.

| Inspected body | Before lines | After lines | Before SHA256 | After SHA256 |
| --- | ---: | ---: | --- | --- |
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` | 1098 | 1158 | `5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7` | `0bf62bb8d0a411b12f55ad05459e7d5d7bbbbf1a0f879b3b592b405f9acab80d` |
| `src/townlet/training/replay_contract.py` | 881 | 881 | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| `src/townlet/exploration/rng_custody.py` | 1195 | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |

Actual three-body budget is **3234 lines**, growth60 from3174. The test is
1158/1250, leaving92 lines; aggregate is3234/3326, leaving92. No fourth body
was read or changed. No source was split, moved or copied to fit the budget.

## Concrete change and assertion mapping

Only `test_direct_ambient_sample_waits_for_registered_peer` changed, plus the
`RNGDeviceInvocation` import needed to annotate retained authentic issuance
objects and check their concrete type. The existing sampler helpers, fixture,
all production and other test functions are unchanged by this writer.

| Approved obligation | Concrete revised test lines |
| --- | --- |
| Capture original bound public operation, owner helper and factory before monkeypatching | 298-300 |
| Recurrent keeps original public operation path and exact dispatch tuple; records its exact original yielded token | 308-318, 354-355, 406-408 |
| Migrated owner observer selects the exact worker Thread, signals attempted entry before original admission, forwards kind/lineage/route/args/kwargs/mutation unchanged, records token and sets acquired only after original helper yields, yields the identical lease and delegates full exit | 320-337, 357 |
| Factory observer selects every actual invocation in the worker, including a wrong participant; forwards all actual arguments unchanged, records actual arguments plus original returned invocation and returns exactly that object | 339-352, 358 |
| Preserve real direct samplers, explicit None lineage and worker exception outcome | 360-371 |
| Preserve real registered peer hold and worker start within it | 294-296, 382-383, 426 |
| Preserve reached3s and negative done0.5s; check acquired both before and after negative wait; require no token, and no migrated issuance, while held | 384-390 |
| Preserve lock-free live row check and exact selected Torch/NumPy/Python ambient state while held | 391-397 |
| Preserve finally-based join5s and surviving-worker failure; monkeypatches remain installed through cleanup | 398-402; pytest monkeypatch lifetime |
| Require acquired, completion and exactly one original yielded RNGOperation after release | 403-405 |
| Require exactly one actual migrated issuance, participant identity, sample kind, None lineage, empty CPU inventory and retained source-issued invocation type | 409-417 |
| Preserve single successful real result, full serialized replay equality, selected ambient stream advancement and strong peer lifetime | 418-426 |

The concrete type assertions supplement identity-preserving delegation; they
are not the authenticity proof by themselves. Authenticity comes from
recording the exact original context yield and original factory output while
leaving their entry/exit behavior untouched. No invocation method is called
from the main thread, and no new token or authority is constructed by a test.
The pre-entry observation establishes attempted source-route entry; it does
not claim an OS-level worker stack capture or exhaustive scheduler proof.

The production changes this control is meant to catch include bypassing
genuine peer exclusion, early invocation/token acquisition or draw, incorrect
actual participant/kind/lineage/device dispatch, failure to obtain authentic
authority after peer release, worker/context failure, replay mutation and a
missing real ambient RNG draw. Expectations use the known CPU fixture and
literal sample/None/empty-device contract rather than recomputing expected
arguments from the implementation under test.

## Validation boundary and freeze

Performed only text inspection, exact SHA256 checks and line counts, plus
the scoped patch and this report. The two production hashes remained exact.
No test, application source import, lint, formatter, static type tool or
runtime was executed. No Git/index, branch, worktree, checkout, execution
copy, subagent, tracked-document edit or compatibility/production change was
performed. No context, exception, timeout or existing assertion was weakened.

Root owns the next steps: independent exact patch review, freeze of revised
source/manifest/tree/node inventory, changed-test style checks, qualified
focused3, and the exact affected54 selection (healthy53 plus isolated poison1
with its actual child custody and verifier). Focused3 overlap affected54;
their counts must not be added. Any unexpected failure remains an immutable
failure to diagnose. Broader B/BAC gates and all original programme limits
remain open. The writer is ready for source freeze and will make no further
writes without a renewed grant.
