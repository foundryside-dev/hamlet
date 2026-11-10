#### PW06: Strict scope checkpoint preparation

**Interfaces/acceptance:** Same-scope private state roundtrips all IDs, models/moments/RMS/LRU/tails/RNG/dedup. Missing/extra/duplicate/mismatched IDs, wrong scope/provider/config/geometry, malformed last-world tensor/RNG/queue or allocation failure leave all active state unchanged. Current full resume preserves active captured replay and private counters.

**Exact tests:** `test_private_restore_matches_by_world_id`, `test_invalid_last_world_leaves_all_runtime_state_unchanged`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_restore.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): prepare strict world-owned checkpoint state` and record immutable source/evidence SHA, inventory and limits externally.

