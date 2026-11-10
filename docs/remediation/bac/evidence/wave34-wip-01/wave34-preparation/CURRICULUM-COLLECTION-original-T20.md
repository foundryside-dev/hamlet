### T20: Completion-driven curriculum and meaningful adaptation — D12/D13/D14/G05

**Interfaces:** CB defines `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None`; CA/CS implement it with P6's event deduplication, completed metrics, dwell and named commitment/difficulty modes. Retain public legacy step methods as their documented step interface, without using them for completion snapshots.

- [ ] Add `test_full_survival_survives_reset`, `test_dwell_counts_ten_transitions`, `test_singleton_band`, `test_rate_has_declared_effect`: survival10/horizon10 gives1.0 after reset; dwell adds10; .6 singleton always.6; rates.01/.1 over10 eligible steps move toward target by.1/at most1.0, clamped to band, while stage-band output preserves its old mapping.
- [ ] Run `test_curriculum_events.py` red; same event twice causes no metric/dwell/stage change, distinct-lane completions remain independent, cap ending is retained.
- [ ] Implement completed fraction baseline/progress in equal units, commit once after thresholds/dwell/entropy, rate-limited mode and truthful inactive adaptation in stage-band mode.
- [ ] Run green plus B06 curriculum/stage-info/signal-purity controls; no second death/completion call is added.
- [ ] Review and commit `fix(curriculum): use owned completion metrics and clocks`.

