# PW04 capacity documentation: source ground truth

Disposition: the published sentence overstates the implementation when read as an all-provider guard against already over-capacity live queues. RND/adaptive implement that explicit pre-service refusal for the supported public obs_buffer. ICM implements a capacity invariant established by construction/native validation and maintained by its supported admission paths; it does not independently reject an already over-capacity internal _pending queue before service. Correct the prose precisely. This bounded review establishes no additional capacity violation reachable through ICM's supported provider inputs from a valid quiescent state, and does not waive any existing required guarantee.

Only this ignored report was written. No tracked documentation, source, tests, index, runtime/project imports, formatting, Git/branch/worktree operations, repository copies, deletion or subagents were changed or run. No additional implementation source or regression file was inspected. Root retains integration of corrected prose and any required repair if further caller evidence changes the reachable-state conclusion.

## Evidence and scope

Read the current public docs/remediation/bac/CURRENT-BACKEND-LOCAL-SERVICE-CONTRACT.md, including its W21 appended owner-fixture and focused-execution receipts. Observed public prose SHA25618f0e19f2c5c5450f7f7278176359577cabbe74d5d5336011463b1428efa6165 (110 lines). Its W21 additions do not change the capacity sentence or backend source hashes. Root/reviewer historical executions remain attributed evidence; no new execution occurred here.

Measured the three already-owned providers before targeted source inspection:

| Source | Whole lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 834 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d |
| src/townlet/exploration/icm.py | 481 | eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 |

These match the qualified producer source receipt. Existing four-file inventory/caps are unchanged; this task did not read the test or allocate another implementation/helper file.

The disputed sentence is: “Existing buffer occupancy above configured capacity refuses before bounded admission, counters/clocks or callbacks.” Its immediately preceding “All modes” wording can reasonably imply that every provider performs the same live-buffer preflight. That implication is false for ICM.

## Exact source behavior

RND:

- rnd.py:393–402 validates incoming observations and every existing buffered row, requires resolved options, and explicitly raises when len(obs_buffer)>max_pending_rows. The check precedes clock handling and _admit_service_rows.
- rnd.py:388–391 routes shared admit_and_service through that boundary. Configured shared update routes there at314–325 and assigns step_counter only after success. Thus both supported public shared entrypoints reject the over-capacity external buffer before service/counter/clock changes. The same explicit guard also exists on the typed private entrypoint.
- rnd.py:489–500 preserves public shared update_predictor's substantive one-minibatch behavior. It has row validation but no new capacity check; direct external buffering can legitimately leave an oversized tail, which a subsequent bounded admission rejects. Unconfigured direct update at327–329 is likewise retained. No claim that every direct operation enforces the bounded-service capacity is appropriate.
- Native pending validation at797–800 rejects oversized pending observations when bounded options are selected. This is distinct from preserving lawful unconfigured shared direct tails.

Adaptive:

- adaptive_intrinsic.py:153–157 delegates typed/shared service to the actual RND; its update delegates to RND. It inherits the explicit public-buffer bounded-admission refusal.
- Native preparation validates outer state then loads only an off-side RND at275–304, thereby inheriting RND's selected-capacity native check before live installation. No separate adaptive queue is introduced.

ICM:

- icm.py:89–95 validates positive geometry/batch/capacity and capacity>=batch, consistent with the selected policy. _pending is initialized as an empty private deque at118.
- icm.py:225–246 validates context and clock and dispatches admission. It does not check len(_pending)>max_pending_transitions before dispatch. At254–258 the service position/budget can change and the overflow condition is equality, not greater-than: len(_pending)==max_pending_transitions.
- On full capacity, service_before_admit consumes a complete batch, drop_oldest removes one row, and drop_newest counts the admission/drop and skips appending (258–267). Otherwise one owned row is appended (268–271). Ordinary service only removes full batches (272–275 and190–208).
- Native preparation explicitly rejects len(pending)>max_pending_transitions at410–412, before model/optimizer preparation and before live installation. Current selected configuration equality is checked at394–400. Owned pending rows are materialized off-side at463 and installed only through the prepared candidate at466–481.
- Public checkpoint_state recursively owns its pending list/tensors through _owned (38–47,291–315); mutating a returned pending list does not append to the live deque. Observation-only update refuses at187–188. There is no supported public direct-buffer append path equivalent to RND's obs_buffer in this owned provider source.

## Reachability and required-guarantee assessment

For ICM, starting with k<=C and B>=1, C>=B, each admitted row preserves occupancy<=C. If k<C, appending one row yields at most C. If k=C, mandatory service first removes B rows before appending one, drop_oldest removes one before append, or drop_newest leaves occupancy at C. Subsequent ordinary service decreases occupancy. This induction holds for shared grouped input and private per-row input, and for each selected overflow policy. Constructor state supplies k=0. Complete native import supplies k<=C. Copied valid backends preserve the same occupancy. Empty/inactive calls do not append rows. These are source arguments, not new runtime tests.

Consequently the required normal admission capacity bound, bounded overflow/drop behavior, and malformed oversized native-state refusal are not shown to have a new gap by this equality check. The RND/adaptive public-buffer defect had a supported external mutation route and a genuine missing preflight; the repaired explicit check remains required and present. This correction does not reopen or weaken that guarantee, remove direct training, alter pacing, change any option, or replace real overflow evidence.

There is nonetheless a real limit that the prose must state accurately: if ICM's internal _pending is directly overwritten beyond C, or its selected capacity is altered outside its supported configuration/restore protocol, the current equality-only loop does not provide the advertised universal greater-than refusal. It may update the service clock, append and train instead. No such synthetic internal-corruption operation was executed here. It is not valid to describe ICM as having the RND-style live-queue preflight merely because native validation and normal admission maintain the invariant.

Finding classification: confirmed documentation overstatement; no additional material supported-input capacity defect established within the authorized provider scope. This is a boundary finding, not a declaration that an accepted guarantee became optional. The accepted full-input preflight, complete native validation, immutable snapshot ownership, capacity conservation and actual integration tests remain mandatory. No external caller source was read: this report does not assert that every current consumer obeys private-state/configuration custody. If a required real consumer is shown to bypass that custody or if root identifies an accepted explicit arbitrary-live-ICM-corruption refusal requirement, the missing ICM guard remains an unresolved required source/integration repair; corrected prose cannot substitute for it. The presently supported provider API proof alone does not close POP/bank/runner qualification.

## Precise replacement paragraph for root integration

Replace the paragraph beginning “All modes conserve” with:

> All service modes preserve admitted = consumed + dropped + pending and consumed = successful service optimizer updates × training_batch_size when operating from valid provider state. RND/adaptive bounded admission explicitly refuses an existing public obs_buffer above the selected capacity before service, counter or clock mutation; public direct update_predictor and lawful unconfigured tails retain their separate direct-training behavior. ICM's empty initial queue and complete native pending-state validation establish occupancy<=max_pending_transitions, and its per-row handling at full capacity preserves that bound during supported shared/private admission. Oversized ICM native pending payloads refuse before live installation; ICM does not separately preflight an already over-capacity internal _pending queue for arbitrary direct internal mutation. The B2/capacity4/cap1 private RND/adaptive geometry has zero overflow by its per-admission drain order; real shared same-tick overflow and imported-full-tail private ICM overflow are separately qualified, not conflated.

This wording preserves the actual provider algorithms, all supported direct/shared/private capabilities and the qualified test distinctions. It makes no new source claim or runtime result. Existing required real runner/native-parent, bank/lifecycle, external caller and final BAC gates—including the unchanged required runner case called out in the W21 append—remain open exactly as recorded. Root alone integrates the corrected tracked prose while respecting its active freeze.
