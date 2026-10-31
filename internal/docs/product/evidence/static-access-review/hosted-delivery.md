# PR #44 — Hosted delivery reading

Read: 2026-10-02 Australia/Canberra (2026-10-01 16:22 UTC).

[PR #44](https://github.com/foundryside-dev/hamlet/pull/44) merged at
2026-10-01 15:08:34 UTC. Published head was
`171318c8fe0d834408e563e612577589d9c5184d`; actual main is
`95b2f828dae4f52d6e30e79600fc3491364a1eb5`.
All three PR checks completed successfully. The actual-main push checks also
completed successfully, with exact `headSha` matching that merge commit:

| Workflow | Actual-main run | Verdict |
| --- | --- | --- |
| Lint | [36881920856](https://github.com/foundryside-dev/hamlet/actions/runs/36881920856) | completed / success |
| Config Validation | [36881915779](https://github.com/foundryside-dev/hamlet/actions/runs/36881915779) | completed / success |
| Tests | [36881921637](https://github.com/foundryside-dev/hamlet/actions/runs/36881921637) | completed / success |

The actual-main log collects **4,295 tests** and reports **4,276 passed / 19 skipped /
15 warnings / 85% coverage**, 1504.18s. This is a hosted reading, distinct from the
retained local **4,277 / 18** result. The additional hosted skip is the MP4 export
test; the log alone does not establish its skip reason. No marker deselection is
reported. No new local full suite ran during this resume.

The merge and published head have identical complete trees:
`a672e98a4f5032700e56d3717cfc0c4cec545ecf`. Execution source, tests, configs,
scripts, CI configuration and dependency files have no diff from qualified repair
`7eb7ded3`; later changes were the requested skill-reference commit and product
documentation. Local main, origin/main and the newly created
`fix/episode-lane-accounting` started this resume at `95b2f828` with a clean tree.

Commands: `gh pr view 44 --json state,mergedAt,mergeCommit,headRefOid,statusCheckRollup,url`;
`gh run list --commit 95b2f828dae4f52d6e30e79600fc3491364a1eb5 --json databaseId,name,event,status,conclusion,headSha,url`;
`gh run view 36881921637 --log`; `git rev-parse HEAD^{tree} 171318c8^{tree}`;
`git diff 7eb7ded3 95b2f828 -- src tests configs scripts .github pyproject.toml uv.lock`.

Retrieved raw log: `runs/episode-lanes/2026-10-02/pr44-main-tests.log`, SHA256
`9b66b175630f2b760bb358b9cb69a0a2242a66ff14a00959e45f7a3fd21b00b2`.
The workflow run is the durable remote source; the local raw log remains ignored.

This closes the pre-publication delivery uncertainty in the resume brief. It does
not qualify allocator performance, CUDA rollback, frozen trajectories, episode
integrity or convergence. No release, tag or deployment is part of this reading.
