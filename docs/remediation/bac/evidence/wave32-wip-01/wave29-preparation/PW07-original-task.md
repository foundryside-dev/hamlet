#### PW07: Explicit shared-to-private initialization

**Interfaces/acceptance:** fresh_private has declared fresh origin; clone_learned_archive_pending retains compatible learned tensors/moments/RMS/counts/history as independent copies, inherited counters labeled, future local counters0, mixed pending unchanged archivally. Both preserve source/shared resume and captured replay; old maskless data still follows approvedA. No initial private history is fabricated.

**Exact tests:** `test_fresh_private_and_clone_learned_origins`, `test_shared_pending_is_archived_not_falsely_attributed`, `test_current_captured_replay_is_preserved`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_conversion.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): add explicit private initialization policies` and record immutable source/evidence SHA, inventory and limits externally.

