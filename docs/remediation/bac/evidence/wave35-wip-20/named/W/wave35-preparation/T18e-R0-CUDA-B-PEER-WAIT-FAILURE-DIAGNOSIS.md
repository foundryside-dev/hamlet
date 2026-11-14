# R113 replay peer-wait failure diagnosis

Status: read-only diagnosis and proposed fixture repair; **WIP, not acceptance**.
No source/test edit, runtime execution, retry, branch, worktree, checkout,
execution copy, or further delegation was performed by this investigator.
The two R113 failures remain authoritative and must remain in WIP20.

## Bound input and scope

Root supplied candidate tree `b5298dec04379db31bf9107a26ead7764f53d73c`
and manifest SHA256
`0f05c4f3faab3e6f5ea15b7ba8fc8c466f0e3dda9bbc87abbde47af7bd2f3daa`.
The existing qualification result independently repeats both values, base
commit `0597715b8d59ab3bdda41ef5521b9772aaa9c436`, exit code 1 and the
exact 53-node command. Its existing log reports **51 passed / 2 failed**.
This diagnosis did not reproduce or change those execution facts.

Only these three implementation bodies were read (3174 lines total):

| Body | Lines | SHA256 of inspected current bytes |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_replay_rng_custody.py` | 1098 | `5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7` |
| `src/townlet/training/replay_contract.py` | 881 | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| `src/townlet/exploration/rng_custody.py` | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |

The following exact evidence lives below
`/workspace/bac-review-2026-11-01/qualification/wave35-r113-replay-healthy/`:

| Evidence | SHA256 |
| --- | --- |
| `replay-healthy.log` | `7f063a16bde9344934c8f346afd713dd7c2678634b457ef80e6727fa823d7f77` |
| `replay-healthy-failure-index.json` | `bbfbb76b16b30cec5587e36e927aba396a3f185147a5fbee196a78e9e4b06030` |
| `replay-healthy/failure-controller-49fe7366fe4cec2f.json` | `62b3f49c573899185c89d237c24c7e7af15d1d6529f2ad90587d4f0792e55e46` |
| `replay-healthy/failure-controller-e61d076cf28e86ee.json` | `43019c8b3e3af0dce1572b0bc41c9d3a2d97a1de10207224fc06c860938d86be` |

The initially supplied shorthand `failure-index.json` does not exist there;
the actual index is the prefixed filename above. No evidence was rewritten.

Root supplied these source-qualified facts without expanding the body slice:
`ReplayBuffer.sample` at 386 has `@replay_device_sample` at 385;
`PrioritizedReplayBuffer.sample` at 651 has that decorator at 650;
`SequentialReplayBuffer.sample_sequences` at 418 has `@replay_sample` at
417, as does `sample_batch` at 1365/1364. All require explicit lineage.
No flat/PER/sequential implementation body was read by this investigator.

## Cause and proof

The failure is an obsolete observation boundary in the test. Both failing
cases stop at test line 341, `assert reached.wait(3)`. `reached` is set only
inside the monkeypatched `AmbientRNGDomain.operation`, selected by the exact
worker thread object and replay participant identity. Neither failure trace
shows an early draw, an acquired lease, changed ambient state, or a worker
exception. The timeout assertion occurs before those checks.

The migrated flat/PER source path is:

1. `replay_device_sample` (contract 612-620) enters the original
   `_device_operation("sample", required_lineage, route, ...)`.
2. `_device_operation` (479-524) first enters
   `domain.admission(lineage=lineage)` at 486, before owner planning,
   enrollment or invocation issuance.
3. `admission` (core 703-725) takes `self._lock` at 706 and retains it across
   the yielded gate. The registered peer's original `operation` holds that
   same lock through `_operation` at 1042. A worker thread therefore waits
   at admission while the main thread holds the peer operation.
4. After peer release, the original helper plans under owner guards and
   calls `domain.device_invocation(...)` at contract 503-505. It enters the
   returned original invocation at 510 and only then yields its lease at
   519, retaining both the actual admission scope and owner exclusion.
5. `RNGDeviceInvocation.__enter__` (core 64-65) calls `_enter_invocation`
   (956-979), which directly enters `_operation` at 964-973. This route
   never calls the patched public `operation` method, even after release.

Consequently the existing hook cannot set `reached` for either migrated
case. Increasing its timeout cannot repair that structural mismatch.
Hooking only `device_invocation`, `device_operation`, or `_operation` is also
insufficient: the first and third are downstream of the blocked admission;
the second is not used by this route.

The recurrent case uses `replay_sample` (contract 656-665), then
`_domain_operation` (245-247), then public `domain.operation`. Its hook runs
before acquisition, so its pass in the same 53-node run matches the exact
dispatch distinction. The differing outcomes are not evidence that migrated
flat/PER no longer use the common lock.

This explains the observed assertion without changing any runtime behavior.
It does not establish that every concurrency property is correct: the
failing run has no worker-stack capture or reached/acquired timeline, and
the failing cases never reached their remaining exclusion assertions.
The repaired fixture must execute those assertions before any acceptance
claim. No runtime fix is supported by this failure evidence.

## Smallest proposed repair and required controls

Restrict the repair to
`test_direct_ambient_sample_waits_for_registered_peer` in the already-owned
test body. Keep the recurrent operation observer and the real registered
peer. For the migrated cases add two delegating observations:

- Wrap the exact original bound `owner._device_operation` for the selected
  worker. Set `reached` immediately before entering that original context,
  which is before its real admission lock. Set `acquired` only after that
  original context yields its authentic `RNGOperation`; retain that exact
  token identity for the assertion record. Delegate its full exit. Do not
  fabricate a lease, replace the owner guard, or set acquired merely when
  admission succeeds.
- Observe the selected worker's actual `domain.device_invocation` factory
  arguments and delegate to the original factory, returning its exact issued
  invocation unchanged. Record the actual passed participant/kind/lineage
  and device tuple. On these CPU fixtures require exactly
  `(replay_participant, "sample", None, ())`. Do not infer the actual factory
  arguments from the closed-over owner or replace invocation entry/exit.

These observations distinguish attempted entry before admission from actual
issued operation authority after admission. The helper observer alone
would lose the existing actual dispatch-argument proof; the factory observer
alone would never be reached while the peer holds admission. No compatibility
adapter or restoration of the old runtime API is needed.

Required causal checks in all three existing parameter cases:

1. Start the selected real sampler while the registered peer holds the
   genuine domain operation. Require the relevant pre-acquisition `reached`
   event within the existing bound; do not weaken or remove the wait.
2. While still held, require `acquired` unset, worker completion absent for
   the existing wait interval, live rows unchanged and the selected ambient
   stream unchanged. For migrated cases no selected invocation may yet have
   been issued. A worker exception must remain a failure, never a wait pass.
3. Release the peer and join with existing bounded cleanup. Require actual
   original context acquisition, exactly one authentic returned operation
   token observation, exact actual invocation identity/kind/lineage/inventory
   for flat/PER (existing operation argument record for recurrent), and one
   successful real sampler result with no captured exception.
4. Retain complete serialized replay equality and the selected stream's
   actual advancement after release. Do not stub RNG primitives or sampler
   results. Preserve exact `peer` lifetime ownership throughout.
5. Under a later runtime grant, run the existing three peer-wait nodes first,
   then the exact affected 53-node selection with source/process provenance.
   Publish a new immutable attempt; retain R113's 51/2 outcome. Do not broad
   retry the unrepaired failing selection.

The proposed predicates fail on absent route entry, bypassed real admission,
early draw/completion, missing invocation issuance, wrong participant/kind/
lineage/inventory, fabricated acquisition, failed real sampling, storage
mutation, or absent selected RNG advancement. An acquisition observation at
admission alone is explicitly insufficient for the operation-token control.

## Needed next facts and limits

No additional implementation body is needed for this fixture repair proposal.
The root decorator facts close the direct-dispatch question; the three
inspected bodies establish the lock and token paths. A later authorized
test-only patch needs fresh exact bytes/hash, independent review of the
delegating observers, and the focused qualified runtime observations above.
No repaired PASS, CUDA hardware result, B activation, B6, package acceptance,
or programme closure is claimed here. WIP20 publication must preserve both
current failures before any later repair work.
