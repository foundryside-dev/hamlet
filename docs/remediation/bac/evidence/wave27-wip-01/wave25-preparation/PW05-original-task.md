#### PW05: Scoped private-instance registry

**Interfaces/acceptance:** Run RND/adaptive/count/ICM/none in two scoped banks. World1 parameters/moments/RMS/queues/history/weights/RNG/counters match across different world0 activity, with at least two real world1 predictor/ICM updates and nonzero parameter change. Assert optimizer/parameter/container identity separation, not just matching logged counters. Shared scope retains a positive coupled-reward/count-collision control.

**Exact tests:** `test_private_models_moments_and_queues_do_not_alias`, `test_world1_updates_match_when_world0_activity_changes`, `test_shared_mode_retains_coupled_control`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_bank.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): add per-world provider state banks` and record immutable source/evidence SHA, inventory and limits externally.