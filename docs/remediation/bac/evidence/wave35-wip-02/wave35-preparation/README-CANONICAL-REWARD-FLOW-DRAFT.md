Replace the current T19 paragraph only, retaining the README's broader dated review stamp:

T19 exposes caller-bound `LaneOutcome` snapshots and an immutable global `ClockLedger`.
Current programmatic population rollout uses an actual world reservation, owned reset record
and owner activation. On an accepted rollout, the environment invokes the population's bound
claim before physics. The population captures the environment's canonical rewards in replay,
services the retained curiosity context, and then advances its authoritative vector clock.
The environment binds its runtime and claim callback once before world custody; reward
composition receives provider raw values and per-row runtime scales separately. See the
[current reward-flow API](docs/remediation/bac/CURRENT-CANONICAL-REWARD-FLOW-CONTRACT.md).

This integration remains unreleased. Multi-batch failure retry, restore role custody, mixed
participation, native transfer/reset, native clock/history correlation, and the ordinary runner
still require repairs and joint qualification recorded in [BAC status](docs/remediation/bac/STATUS.md).
The [owned-outcome reference](docs/architecture/BAC.md#owned-lane-outcomes-and-global-clocks)
and [API units reference](docs/remediation/bac/options.md#owned-lane-outcomes-and-global-clocks)
describe the broader completion and clock contracts.
