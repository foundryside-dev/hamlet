#### PW03: Reusable backend and policy-selector factory

**Interfaces/acceptance:** Construct all five existing classes, same shared configuration effect, real per-world fresh mutable instances, and matching model geometry. Factory/selector APIs are complete before facade consumption; no absent ICM/count source helper or duplicate model implementation.

**Exact tests:** `test_factory_reuses_all_five_backends`, `test_private_factory_returns_disjoint_mutable_instances`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_backend_factory.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `refactor(curiosity): separate backend construction from scope routing` and record immutable source/evidence SHA, inventory and limits externally.