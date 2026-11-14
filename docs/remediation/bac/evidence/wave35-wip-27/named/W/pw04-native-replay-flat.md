# PW04 native flat replay implementation handoff

Status: authored RED tests, production replay unchanged; root execution pending.

Owned cumulative whole-body inventory: training/replay_contract.py881,
training/replay_buffer.py816, existing regression test_parent_intrinsic_handoff.py900,
and new test_native_replay_data.py (under100). Four bodies, under2800 lines.
No other implementation bodies opened; no imports, execution, Git, source copies,
branches or worktrees. Root supplies RNG core facts; actual C and POP owners supply
their source contracts.

The five authored tests cover fabricated native handle and unissued parent refusal,
ordinary prepared replay exclusion, genuine native parent staging without live
publication/current-token authority, and malformed transport refusal. Positive
fixture is genuine make_parent(compiled), target.bind(), source POP checkpoint,
new target POP prepare_native_checkpoint_data(mode='initial'), then owned replay
transport. This is component staging evidence only, not successful native restore.

Agreed producer interfaces are stage_native_restore(state, expected_obs_dim,
parent_plan, lineage) and install_native_restore(data, parent_plan, attempt,
restored, lineage). The parent producer supplies source function
validate_native_population_data(plan=..., owner=...) in population/vectorized.py.
It checks genuine issued identity, PID/thread, healthy fresh POP revision and exact
receiving owner/parameter associations, permitting FINALIZING after world install.
The C producer supplies pure validate_restore_finalizer(attempt=..., owner=...,
restored=...) inside its one fixed callback. Repeated child validations are lawful;
the callback runs under an idle outer domain gate without an active invocation.

Planned implementation retains all source-owned replay custody. Staging materializes
and validates complete destination storage and merged archives under genuine device
prepare, before the BANK cut. Opaque private staged data holds no currentness token
or install permission. The registry pins receiving revision/configuration/PID/thread
and weakly references the genuine parent plan to avoid plan/data retention cycles.
Actual finalization independently checks that record, parent identity and C callback,
then takes a new genuine replay install invocation and assignment-publishes the
preallocated payload on the same replay owner. Failure consumes the staged record
and quarantines uncertain publication; actual completion failure retains existing
custody quarantine. Admitted device inventory includes all retained staged payloads.
Ordinary PreparedReplay currentness/revision guards remain unchanged.

Still owed: root RED observation, implementation, positive actual finalizer/continued
sampling witness, adversarial stale/foreign/consumed/thread/device controls, source
review and owner regression. No CUDA/native package qualification claimed.

## Implementation after root RED

Root reported R161 candidate7452243522ed237f42bb25c64c18c9b198cdf2de:
all five authored tests reached the intended missing data/stage/install APIs;
collection and failed-run custody passed. The genuine POP fixtures reached stage,
so the red result was not hidden behind a fixture prerequisite.

Production now written and frozen for root checks: contract949, flat860,
newtests152, prior inspected fixture900 =2,861 lines/four bodies. Nine tests total;
four added controls exercise real data with missing genuine finalizer, foreign
receiver, lawful receiver revision change, and foreign thread. No runtime claim.

Shared StagedReplayData is constructor/copy/serialization-refusing opaque data.
Private weak registry owns payload and binds exact parent weakref, receiver revision,
capacity/device, PID/thread. Device planning includes all retained native payloads.
Flat staging uses complete existing validated materialization and archive merge,
then issues DATA without a current token; actual prepare completion precedes return.
Installation checks actual POP plan and C fixed finalizer, then takes a new genuine
install invocation. Its payload has all destination storage ready; publication
assigns the same receiver's storage/counters/archives and consumes DATA first.
Publication failure quarantines; genuine invocation completion failure uses the
existing quarantine path. Ordinary PreparedReplay checks and installers unchanged.

No successful native finalizer installation or nonempty continued sampling has
been executed here. These remain explicit joint integration evidence obligations,
as do independent source review, device qualification and full owner regressions.
