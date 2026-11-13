# Packet A I5 finite prefix matrix / fix3 preparation

Read-only preparation against R98 tree `abb7f417b8098b139db3d5156f4c320b21ab8f6d`,
manifest `02adec84e69868cdcf6e065d9d02f9736cb17c0c13d1450f2fed0ac43b622fe1`.
Review read verbatim: FIX2 IMPLEMENTATION REVIEW,
SHA256 `c7b71870e33e3656f8ac531ed9deee65d55c597307b9e77073a0818fb2b7d84f`.
Owned source/test and report `b0061fb8` remain frozen. No application execution,
Git action, delegation, source copy or additional implementation body read.

## Structural choice

Replace inventory's duplicate examples with family-owned ordered metadata
prefix routines also called by the real validators. Share their predicates,
parsed scalar metadata and deferred original diagnostics; do not reproduce
validators as a second set of planner conditions. Separate successor-mask
metadata guards from its existing value reduction in the owned shared file,
and use the same guards in public recorded entry and planning. Keep the public
recorded rank guard before the shared mask guard. Known-vocabulary plain push
has an allocation before transition validation and cannot borrow recorded's
pre-allocation refusal rules.

A prefix result distinguishes ordinary refusal, protected diagnostic/comparison
boundary, and possible value/copy continuation. Planning never renders a
deferred diagnostic, compares/truth-tests a Tensor, or runs a value check.
The real body raises the original exception at its original point, including
original message, repr and type/shape access behavior. Moving a metadata block
to a shared helper must preserve its call position relative to preceding
effects. A planner may inspect a later metadata block on the possible-success
continuation of an earlier effect: retain that earlier effect's sources, and
omit later sources/target if that block guarantees refusal. This is not a
prediction that the preceding value check succeeds. No body work moves ahead
of its present validation order.

Ordinary here has the existing supplier profile: plain scalar/container data,
ordinary tensor metadata and numeric NumPy array metadata. Preserve accepted
Mapping views, DTOs, archive formats and subclass inputs. For nonplain scalar
protocols or Tensor-valued fields, stop that safe predicate path and inventory
its comparison/conversion/diagnostic sources before protected real evaluation;
do not narrow acceptance to make the metadata path simpler. Existing conservative
issuer-held-candidate inventory remains additive and separate.

## Raw validation/preparation matrix (ordered within each family)

`D` means the original selected diagnostic/comparison operands, not all values
in the transport. Ordinary scalar refusal below has no CUDA source/target.
Tensor-valued D requires its devices even if the payload is refused. Pure
validation never selects the replay destination. Preparation selects it only
on a possible current, nonempty materialization path; archive merges can need
installed-archive devices even with an empty/legacy destination.

| Stage | Flat actual order and guard | PER actual order and guard | Inventory/refusal boundary |
| --- | --- | --- | --- |
| R0 | Mapping check; exact-int version in {4,5} | Mapping check; exact-int version in {4,5,6} | Nonmapping refuses without tensor work. Unsupported version uses version!r: D=version. |
| R1 | Exact version-specific key set, then kind equality | Kind equality/repr, then exact version-specific key set | Flat kind error has constant text, but malformed kind comparison may itself work. PER D=kind for comparison and repr. Key mismatch formats sorted missing/unknown keys: D=keys, never unrelated values. Preserve this family order. |
| R2 | Exact-int capacity range then configured-capacity equality | isinstance-int/non-bool capacity range then configured-capacity equality | Preserve differing accepted int classes. Invalid integer D=value; PER out-of-range formatting uses value conversion. Wrong plain kind/bool capacity exclude unused CUDA rows/live/archive/target. |
| R3 | Exact-int size range, position range, position == size % capacity | alpha and beta_initial finite-number/unit interval/configured equality; exact-bool beta_annealing/configured equality; beta range and no-annealing consistency; size_current/position integer ranges and partial-ring relation | D=the reached scalar operand for repr/conversion/comparison. No earlier scalar rejection may enroll row/archive values. PER int/float subclasses retain current acceptance; planning must not execute their hooks. |
| R4 | Current only: mode type/value; recorded action_dim integer/configured width or unconstrained None; historical_archives list type | priorities ndarray type, float32 dtype, capacity shape; then NumPy finite/range checks; max_priority finite/range/positive/float32 insertion conversion and active-priority consistency; then current mode/action_dim/archive-list guards | NumPy metadata is safe for ordinary arrays; value reductions/conversion checks are real data-dependent CPU work, not predicted by inspecting values. Subsequent metadata blocks can prove a later refusal on the possible-success continuation without running these reductions. D includes a later malformed scalar only if real execution can reach its rendering. |
| R5 | Current nonempty archive list reconstructs/owns entries before empty/row checks; empty list has no archive work | Same position after PER R4 | Each direct record first needs Mapping then exact six keys. Ordinary record type/key refusal touches no values; malformed Tensor keys need protected diagnostics. Exact-key record clones source_formats then original_state before semantic/count/digest checks. Retain earlier records' copy sources if a later record refuses. Installed archives are not touched merely because incoming validation reached this stage. |
| R6 | Empty: all relevant row fields None by identity; current empty vocabulary guard; legacy history._clone at return | Empty: same null/current-vocabulary guards; later current6 identity/sampler checks; legacy clone occurs at final DTO construction | A non-null unused row is a metadata refusal, not tensor work. Current empty validation with no archives has no tensor copy. Legacy final clone must inventory everything actually cloned; do not reuse a raw-input refusal rule for DTO clone-before-refusal. |
| R7 | Nonempty observations Tensor/rank/positive width; expected_obs_dim/current-storage width; observations dtype/full shape in first _require_tensor | Same, preserving separate rank/positive-width messages; first _require_tensor dtype then shape | Metadata refusal excludes untouched row tensors and destination, while retaining earlier archive/diagnostic sources. D includes malformed expected_obs_dim comparison/format operands. Ordinary retained width access is metadata only. |
| R8 | First floating observations isfinite/all, then detach/clone; later row-by-row validation/copies, action/presence/mask reductions | Same first observations value/copy boundary; PER legacy/current differences remain in real body | Stop predicting row values. Inventory all genuinely possible continuation sources, not tensors behind a guaranteed earlier metadata refusal. No finite/nonnegative/mask result is inferred. |
| R9 | After validation: materialize clones DTO/reconstruction before revalidation; current nonempty allocates/moves rows; legacy archives/fresh-start; merge installed and incoming archives | Same, plus existing CPU identity/priorities/sampler behavior | Keep full DTO fields/legacy mapping inventory before initial clone, including malformed metadata. Raw validation refusal cannot borrow this clone-first rule. Retained/installed sources enter only on a path that can reach their copy/merge. |

PER R4's CPU reductions do not authorize reordering alpha/configuration errors,
moving mode ahead of priority checks in the real body, or declaring sampler
validation before row copies. PER6 identity and sampler checks actually occur
after row validation; their failure can follow GPU clones and must retain those
sources. All supported 4/5/6 behavior and existing error precedence stay intact.

## Push matrix

| Stage | Actual order | Metadata decision and required prefix |
| --- | --- | --- |
| P0 plain, no vocabulary | No mask entry work | Start with no source and no replay target. |
| P0 plain, known vocabulary | torch.ones((*dones.shape, action_dim), device=dones.device) before _validate_push | Allocation is already a real effect on dones.device, even if observations later fail or batch is empty. Retain this source; a later guaranteed transition-metadata refusal still excludes replay destination/live rows. |
| P0 recorded | Public masks Tensor/rank2 guard; shared exact positive-int width; mask bool dtype; dones Tensor/bool dtype; masks shape == (*dones.shape,width) and same device; then (~dones) & ~masks.any(...), reduction/truth | Each preceding refusal has no mask/done tensor effect. Width0, wrong dtype, bad dones, shape or device refusal must not arm unused CUDA mask/done values. Only after all metadata guards is mask/done value work possible. Preserve duplicate later validation in _push and its actual ordering. |
| P1 flat | observations rank/dtype/positive width; batch <= capacity; next_observations full shape/dtype; actions, rewards.total, dones each full row shape/dtype | Shared real metadata helper, in this order. Malformed plain no-vocab transitions refuse without all later inputs/live/target. Exact field access failures remain original failures, not converted to a new schema policy. |
| P1 PER | observations rank/dtype/positive width; next_observations rank/dtype; actions rank/dtype; rewards.total rank/dtype; dones rank/dtype; batch <= capacity; common leading dimensions; full next-observation shape; retained observation width | Separate family helper preserves these messages/order. Do not substitute flat's early capacity check or full-shape checks. Retained width comparison is before first action reduction only in PER. |
| P2 first transition value effect | Both actions<0 / any / bool | The action tensor must be covered even if empty. Flat retained-width refusal follows this action effect; it cannot be moved ahead in the body or labeled no-work. Planning can exclude destination on known width refusal while retaining preceding mask/action sources. |
| P3 remaining validation | Optional reward metadata interleaved with observations/next/total/component finite reductions; then _push mask checks, action-width reductions and retained actions | Do not predict data validity. Preserve all possibly reached independently deviced components and retained-action effects. A known optional-component metadata failure retains earlier reductions, not later copies/target. Batch0 returns only after these checks; no replay destination allocation, but prefix/value sources still exist. |
| P4 nonempty commit continuation | PER ID exhaustion/insertion-priority CPU checks; placeholder allocations on rewards.total/dones devices; moves/clones to destination; retained storage work | Arm genuine input/component/retained sources plus possible concrete selected destination before work. No target merely for entry-mask allocation or a guaranteed preceding metadata refusal. |

## Finite controls and stopping rule

Preserve existing129 nodes/ten child mappings. Add table-driven paired-family
cases in the same test body, using existing real CPU fixtures, CUDA-metadata
seams, pure-plan checks and real public refusal/state/revision assertions.
Representatives cover R0 invalid plain/Tensor version (existing), R1 wrong kind
and keys (including family error precedence), R2 bool/range capacity, R3 bad
count/position and PER configured scalar/type mismatch, R4 mode/action/archive
container and priorities dtype/shape, R6 empty non-null row, R7 observation
dtype/shape/expected width. For each distinct prefix class use an unused CUDA
later value/selector and a paired valid-boundary plan that retains source2;
reuse existing capacity/malformed-version/Mapping/DTO/archive controls.

Push representatives cover all P1 metadata classes, plus recorded rank/width/
dtype/dones/shape/device pre-reduction refusal and paired valid-mask boundary.
Keep known-vocabulary allocation and recorded valid-mask positives with later
bad observations/next observations. Include batch0 and flat-vs-PER retained
width ordering. Pure planning must emit no Tensor work. Public positive GPU
work, admitted preparation and installed GPU archives stay honestly B-blocked.

No value-outcome oracle is added for finite values, nonnegative actions, mask
legality, NumPy priority support/maximum, unit identity or sampler content.
The plan computes possible touched devices; real protected algorithms decide
these outcomes. Positive boundary controls must show source/completion coverage,
not merely a lack of metadata events. Existing poison/outer-failure/hardware
obligations are unchanged; ten children remain UNRUN pending authentic A/B.

## Budget and resolved supplier seam

Current four bodies:689/807/1260/1668=4424. Refactor by moving existing predicate
blocks and deleting their inventory duplicates; do not retain two validators
or compress code. Target net production growth <=104 and table-driven test
growth <=132, total <=4660. A prospective same-total reslice is shared740,
flat830, PER1290, test1800 (=4660); this needs root's explicit reslice before
crossing an existing per-file ceiling. It leaves the previously planned B150
and D150 at4960/hard5000. Measure formatted growth before freeze; if this
estimate fails, report exact overage before crossing, not hide helpers/tests.

Consumed root's narrow `T18e-R0-CUDA-ARCHIVE-PREFIX-FACTS.md`, SHA256
`98fc3b06f2e13f2e42452a3d5bb409f27be0d581fc1cc8fb66e65590f172f68a`;
helper675/hash74709ebe unchanged. This resolves the identified helper seam:
Mapping check, six-key set check with missing/unknown-set diagnostic, then
constructor; no field-value validation precedes constructor clones. The six
keys are source_formats/original_state/source_digest/archived_row_count/
reward_semantics/approval_reference. Exact-key malformed reward/count/digest
must still cover source_formats/original_state clones. A malformed later
record does not erase earlier records' work. The replay callers directly
iterate their list; do not import _embedded_archives' all-items-Mapping precheck
ahead of their first constructor. Add malformed-record-type/ordinary-key and
exact-key-invalid-semantics paired controls using these existing seams.
No helper body was requested/read, and no further supplier fact is currently
needed. No implementation approval or runtime PASS is claimed by this matrix;
source/report remain at R98 seals during publication.
