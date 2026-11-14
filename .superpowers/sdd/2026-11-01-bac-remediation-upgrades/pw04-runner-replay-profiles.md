# PW04 original real-runner replay profile extension

The existing `test_shared_runner_checkpoint_still_roundtrips` now has explicit
`flat-uniform`, `flat-per`, `recurrent-uniform`, and `recurrent-per` parameter IDs.
It copies the authored feedforward or recurrent pack into pytest temporary
storage, preserves the corresponding architecture (including the recurrent
block), and configures PER in `brain.yaml` with `prioritized: true`,
`priority_alpha: 0.6`, `priority_beta: 0.4`, and
`priority_beta_annealing: true`. Uniform profiles retain `prioritized: false`.

Every profile uses the original two-world, three-episode, three-step witness:
capacity 64, batch/minimum size 5, training frequency 1, checkpoint interval 1.
The shared curiosity service is held at the original paced FIFO settings,
one update per tick, six pending rows, and service-before-admit overflow,
with training-sourced provider parameters. This preserves the original exact
episode-2 curiosity assertions: 12 admissions, 10 consumed rows, two updates,
and two pending observations. Authored replay policies remain profile-specific.

The test still verifies artifact SHA-256 sidecars, trains through episode 3,
copies the genuine episode-2 artifact and roster to a fresh runner, and
compares its continued-learning episode-3 artifact with the uninterrupted
result. The unchanged recursive whole-population comparison covers the full
native replay payload, including priority, RNG, mask, and identity fields
where present. Actual Q-network and curiosity parameter changes, positive
training-counter advancement, optimizer state, and 18 completed live-agent
steps remain required. No replay owner is replaced.

This worker has run no tests, repository imports, or Git commands. Runtime
qualification belongs to the root worker; this prose is an implementation
handoff, not a passing evidence record.

With root authorization, a pure observation wrapper records fresh population,
Q-network, optimizer, replay, and Q-network parameter object identities around
the unchanged production `DemoRunner.load_checkpoint` call. It forwards all
arguments, returns the actual result, and asserts the wrapper ran exactly once.
The same identities must survive continued learning, and the population's bound
replay must still be its actual replay buffer. The observer supplies no state,
restore authority, success result, or replacement owner.
