# T19 accounting — tests-only authoring handoff

Stationary for root-owned meaningful RED. No project runtime/import, collection,
compiler, pytest, lint, formatter, index mutation, commit, push, branch/worktree
creation, checkout, source copy/deletion, or subdelegation performed. Existing
14-worktree custody preserved: no worktree operation performed. Production edits
remain uncleared and were not made.

## Exact source custody and counts

Whole-source inspection stayed within the four approved files. No imported
implementation/helper/probe source inspected. Read the task brief and supplied
baseline as task metadata. Baseline hashes were independently confirmed before
writing. Only the existing test module was appended; original lines 1–422 hash
back to ecd2db6e72de5fba9453a6fff217d68113f6ff138c3c7a6cc9b5548e9e340c74,
so every original byte/assertion/scenario is retained.

| Source | Full lines now | SHA256 now |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 661 | 3a774dfb042cdbf20b66555c41f75c2d537b6ff49472395877dfcf5595e26e72 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| src/townlet/exploration/adaptive_intrinsic.py | 226 | 80ecb26fb33626cc9efd271422c69cdae495412f5db94a505eb59628b58b6cd9 |
| tests/test_townlet/regressions/bac/test_rnd_service.py | 599 | 85026bb3b203edfaa168c2b0cf8b0bd17e20bcb7e7680ae507b458c8c2e59684 |

Four-file full total: 1780 lines. Appended 177 lines, including local tuple helper
`service_counter_values` at line425. Projected ceiling remains
800+294+300+800=2194<5000. This receipt is ignored, confirmed by git check-ignore;
it is task metadata, not imported source.

## Appended exact test functions and intended expanded nodes

Existing module: tests/test_townlet/regressions/bac/test_rnd_service.py.
Names below use pytest's ordinary parameter ID convention; these are authored
node names, not collection-verified claims.

- test_public_predictor_counters_follow_genuine_legacy_optimizer_work (line435)
- test_public_predictor_counters_bracket_legacy_partial_and_full_direct_updates (line452)
- test_public_predictor_counters_count_real_zero_loss_steps[False] (line479)
- test_public_predictor_counters_count_real_zero_loss_steps[True] (line479)
- test_public_predictor_counters_agree_with_configured_receipts[service_before_admit-paced_fifo] (line509)
- test_public_predictor_counters_agree_with_configured_receipts[service_before_admit-occupancy_fifo] (line509)
- test_public_predictor_counters_agree_with_configured_receipts[drop_oldest-paced_fifo] (line509)
- test_public_predictor_counters_agree_with_configured_receipts[drop_oldest-occupancy_fifo] (line509)
- test_public_predictor_counters_agree_with_configured_receipts[drop_newest-paced_fifo] (line509)
- test_public_predictor_counters_agree_with_configured_receipts[drop_newest-occupancy_fifo] (line509)
- test_public_predictor_counters_are_frozen_owned_primitives_and_observationally_pure[False] (line533)
- test_public_predictor_counters_are_frozen_owned_primitives_and_observationally_pure[True] (line533)

Five appended test functions, twelve authored expanded cases. No new production
symbol is imported at collection. Root should select the first listed test for
first RED: it performs legacy update(rows7), observes an actual Adam post-step
hook, verifies live Adam step1 and changed predictor parameters, then reaches
an in-test missing public method assertion (line447). No RED result is claimed.

## Contract and meaningful assertions

The exact agreed interface is public
`RNDExploration.predictor_service_counters() -> PredictorServiceCounters`, a
frozen dataclass with only admitted_rows, consumed_rows, dropped_rows,
pending_rows, optimizer_updates, each owning a primitive int. Tests require
that DTO name, exact field order, primitive types, and frozen assignment refusal.

Legacy tests cover undersized real update with no Adam history, full direct
one-minibatch work with remaining complete batch, repeated full work, undersized
no-op, delta accounting bracketing caller append plus actual update, and saved
snapshot stability. Unserviced public append changes occupancy while recorded
admissions remain at the last service boundary. This is intentional native
counter timing; the caller interval must start BEFORE the append and end AFTER
update_predictor. Tests do not impose conservation during that unserviced gap.

Zero-loss tests load the existing fixed weights into the predictor and perform
real legacy/configured work. Loss is zero on both successful optimizer steps
and the final undersized no-op. Post-step hooks and live Adam step tensors
independently prove actual work; loss and queue occupancy are never used as
proxies. The positive parameter-change control is a separate genuine-work test.

Configured tests span both service modes and all three overflow policies over
same-tick/new-tick admissions and an empty service call. Cumulative views must
match summed per-call receipts and actual optimizer post-step events, retain
conservation after service, and account for all consumed/dropped/pending rows.

Purity tests start with actual work and a pending tail. Repeated reads prohibit
checkpoint/available-state export, deepcopy, Tensor.clone, torch.stack, network
forward/state export, optimizer step/zero_grad/state export, admission, service,
and configuration. Independent before/after oracle snapshots, queue/tensor and
network/optimizer identities, gradients, normalizer/clocks/options, Torch/NumPy/
Python RNG states must remain unchanged. There is one checkpoint oracle before
and one after the repeated reads, never checkpoint cloning per accounting step.
Subsequent genuine service must advance the live view without changing the
previous frozen primitive snapshot.

## Actual-source gap and prerequisite assessment

RND has no cheap public complete accounting view. Existing full checkpoint
export calls available_state/deepcopy for model and optimizer and stacks/clones
the pending FIFO. Existing configured receipts are per-call only; direct
update_predictor returns a float. OP declares service options, and AI delegates
update/checkpoint to RND without supplying another complete accounting view.

No causal producer prerequisite was found: update_predictor synchronizes native
_admitted_rows with consumed+dropped+current occupancy BEFORE its undersized
return, then increments consumed and optimizer counters only on actual work.
Both partial and full externally appended-buffer cases are therefore already
recorded after a genuine update. A pure getter must expose native recorded
admissions, not repair them or derive optimizer work from loss/occupancy.

Root owns meaningful RED, subsequent separate RND getter/DTO production
clearance, independent review, and actual legacy/configured suite execution.
