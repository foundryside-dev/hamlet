# R0 replay child verifier fix1 — independent D1 closure review

2026-11-13. This review is additive to `T18e-R0-REPLAY-CHILD-VERIFIER-INDEPENDENT-REVIEW.md` (SHA-256 `98717b6fe88354f41a927999fbefe25185a7bc60ccb5741bc556090445eda75f`). The initial report remains unchanged. Scope was the same three bounded source bodies and only defect D1; actual child execution and application qualification remain unrun by this reviewer.

| Body | Lines | SHA-256 |
| --- | ---: | --- |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_publication_spawn_identity.py` (read-only) | 102 | `8fd7638fca79d2479286821f55573445f1acb4fc28a5efd801cec8a40cb53209` |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_replay_spawn_identity.py` | 157 | `aef826f304f66798c1845bdf1436b8fb27336708776a514f50d2f353942402a8` |
| `W/evidence-management/test_replay_spawn_verifier.py` | 241 | `bf2a20c8f2fa7120219717b62a8db4186e3914b66e78b0efe3955c2293658b4f` |

Total 500 lines across three bodies. The new verifier now requires `result["seconds"]` to have exact Python type `int` or `float`, be finite, and be greater than zero. This accepts positive integral and fractional elapsed values while rejecting booleans, null, strings, zero, negatives, NaN and either infinity. The new test exercises the invalid values; the prior positive fractional fixture and twelve other tests still pass. The receipt remains hash-bound to the result bytes, although it does not duplicate the elapsed value.

**SPEC verdict: D1 closed for verifier logic; the earlier bounded pass remains subject to actual producer and root evidence review. QUALITY verdict: pass for this narrow fix.** No regression was found in the previously reviewed role/message, parent exit, PID/PPID, import, source/index, or exclusive-output guards in the 157-line verifier. The synthetic tests do not prove real child execution, actual JSON producer custody, actual harness bytes, or publication readiness.

## Independent synthetic test receipt

Command from `/workspace/hamlet`:

`/workspace/hamlet/.venv/bin/python -B /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py`

Observed exit `0`; captured combined output:

```
.............
----------------------------------------------------------------------
Ran 13 tests in 0.048s

OK
```

Captured log `W/wave35-preparation/T18e-R0-REPLAY-CHILD-VERIFIER-FIX1-INDEPENDENT-TEST.log`, SHA-256 `73343775a7dd0d9d74536331d0e5bfbb1ef2ba28af51e61d16db81c5574587a7`; exit file `W/wave35-preparation/T18e-R0-REPLAY-CHILD-VERIFIER-FIX1-INDEPENDENT-TEST.exit`, SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`, containing `0`. UTC start/end times were not captured. Synthetic fixtures used temporary DATA and mocked external metadata, with no real Git/index or application invocation.
