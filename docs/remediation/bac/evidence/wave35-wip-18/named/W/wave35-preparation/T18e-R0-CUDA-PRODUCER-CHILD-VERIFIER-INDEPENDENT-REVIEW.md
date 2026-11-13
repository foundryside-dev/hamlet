# Independent SPEC/QUALITY review: producer child verifier

2026-11-13. **Verdict: PASS for the frozen synthetic tooling scope.** No blocking false acceptance found in the two permitted implementation bodies. This does not qualify application behavior, CUDA hardware, or any of the ten actual children; all ten remain UNRUN pending the A/B source dependencies and this tooling qualification.

## Scope and provenance

I read `AGENTS.md` and the producer CHILD-API first. Before reading implementation, I measured its exact bytes: verifier 581 lines / SHA256 `8639eae953abe0961a4d4af941c15fbf4d3c85b9bd342d4409158a629e0eae7e`; synthetic tests 989 lines / SHA256 `36ed3c3ae1d4b0a7c5835ff95ed705a30a8ca4b548826b406eb9957d8cf4c14c`. These are the only implementation bodies inspected (1570 lines total). The requirements, author report, review diff, and supplier prose matched their supplied hashes: respectively `e5072eb3ab320566faa705831de4927e4d358b2ecc01786014601a13d8898e9e`, `4d9f76076db90af06458c7eaa7cc7e312fe33589b46d5d8a20f05417a3df4014`, `3d2ead4468bd49914dae3f3080522e057600f88208773c2841db15d938e3ac56`, and `dd31a7d4d24b06e59182e872eb4a21a14bc399728ed2c8774f3de095db3a4e80`. I inspected no imported helper, application, or other test body. No Git, application/runtime, or branch action occurred.

## Findings

- The allowlist has exactly ten producer case strings and preserves the original two replay and ten CUDA-core mappings. Each producer mapping seals one exact job, node, message, role, argument array, worker count 1, and single-job spec. The diff only changes common dispatch to add producer-specific branches; it does not weaken the pre-existing replay/core requirements.
- The producer path requires exact child, preflight, after, parent-before, and parent-observation schemas. It ties case, PID/PPID, Process/queue, source import map and hashes, controller/Torch profile, manifest, and successful result. Missing records, a preflight/fault after phase, false or integer success, error records with extra/missing fields, wrong error identities/order, outcome read errors, and unhealthy baselines refuse. Numeric values use exact `int` where boolean coercion would matter.
- The accepted baseline permits generation/revision drift while requiring healthy before/after domain states and equality of Python, NumPy, Torch, and CUDA RNG snapshots. The NumPy flag and position use exact integers; cached Gaussian is a finite float. This agrees with the encoding supplement.
- The admitted completion trace accepts any nonempty list beginning with 0 and containing only exact integers 0/1. That matches the frozen API's explicit lack of a fixed visited suffix. Local trace is exactly `[0,1]`.

No change is requested. The verifier checks the sealed evidence format and manifest-bound source; it cannot independently establish that the as-yet-unrun application child actually performed the behavior represented by a success record. Fresh actual children and root custody verification remain necessary.

## Independent finite mutations

I ran the following command. It imports only the reviewed synthetic test body and verifier, builds inert synthetic fixtures, and mocks repository subprocess calls through that fixture. No application module is imported or executed.

```bash
/workspace/hamlet/.venv/bin/python - <<'PY'
import importlib.util,json
from pathlib import Path
p=Path('/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/evidence-management/test_replay_spawn_verifier.py')
s=importlib.util.spec_from_file_location('synthetic_verifier_review',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
mutations=[('bool_child_pid','child',lambda d:d.update(pid=True)),('bool_preflight_pid','preflight',lambda d:d.update(pid=True)),('integer_parent_success','observed',lambda d:d.update(success=1)),('integer_child_success','after',lambda d:d.update(success=1)),('integer_outcome_flag','after',lambda d:d['observations'].update(completion_failed=[1])),('preflight_failed_final_success','after',lambda d:d.update(phase='preflight',success=True,failure=None)),('preflight_failure_field_final_success','preflight',lambda d:d.update(failure={'type':'AttributeError','message':'missing API','id':1,'children':[]}))]
for label,record,mutate in mutations:
 t=m.ProducerVerifierTests();f=t.fixture();d=json.loads(f.paths[record].read_text());mutate(d);f.write(record,d)
 try:
  f.invoke();print(label,'ACCEPTED')
 except Exception as e: print(label,'REFUSED',type(e).__name__,str(e))
 finally:t.doCleanups()
PY
```

Result (exit 0; **7/7 refused**):

```text
bool_child_pid REFUSED ValueError PID must be a positive exact integer
bool_preflight_pid REFUSED ValueError producer record process mismatch
integer_parent_success REFUSED ValueError producer parent success/case mismatch
integer_child_success REFUSED ValueError producer not completed successfully
integer_outcome_flag REFUSED ValueError producer completion outcome mismatch
preflight_failed_final_success REFUSED ValueError producer not completed successfully
preflight_failure_field_final_success REFUSED ValueError preflight schema mismatch
```

The author reports 58 synthetic methods passing and Ruff/Black passing. Root is separately repeating that suite; I did not duplicate it. This review authorizes no merge, publication, or whole-BAC claim.
