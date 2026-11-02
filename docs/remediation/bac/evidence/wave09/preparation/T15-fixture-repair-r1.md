# T15 fixture prerequisite repair R1

Root's exact prior test SHA `5724687f98e668c7dc6ab56139b57eeb6367db14d02b1b38175827ef1d1e9d90` collected127 cases. Its six selected runtime cases all stopped before intended assertions: training `exploration.epsilon_decay` must be less than1. The retained external `qualification/wave09-red-r0-narrow/narrow.log` confirms that same schema error; this is failed prerequisite evidence, not causal RED.

Changed exactly one owned-test line: authored training epsilon_decay `1.0` → explicit `0.99`. Authored start/end epsilon remain0; low-level provider constructor epsilon_decay1 remains unchanged. No assertion, parameterization, production validator, fixture helper or accepted control was changed.

Owned test remains1059 lines, new SHA256 `5076b30e1b020fbd14b9e37ade1d652dde4ae7e2547c1a5363d8634462f4dfda`. Actual complete context remains5/3509; current projection POP3000/RC250/QT100/OP300/test1300 remains5/4950. All four implementation hashes match the authoring receipt. HEAD/tree remain75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7/7924a5c5b47f680bf011ddff3174719d85ac1d18.

Target-only `.venv/bin/black --check tests/test_townlet/regressions/bac/test_learner_legality.py` and `.venv/bin/ruff check tests/test_townlet/regressions/bac/test_learner_legality.py` both pass. The working diff against root's staged original is exactly1 insertion/1 deletion. No index operation, production change, extra implementation/helper read, import/runtime/pytest/collection, branch/worktree/copy/subagent or commit occurred. Only the owned test and this ignored receipt were written.

No new runtime result or collection count is claimed. Return stationary for root to restage/update identity and rerun the exact six narrow cases with workspace TMPDIR/basetemp before any broad RED.
