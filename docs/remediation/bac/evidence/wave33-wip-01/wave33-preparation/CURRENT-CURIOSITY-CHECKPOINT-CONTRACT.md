# Current curiosity checkpoint producer contract

Source-verified T18d none-scale prerequisite successor at current coherent candidate `b848b95aec04d580b9d188f10061f1e5c9173ddb`, base `c1de41509ae108848fd5bf295487510254daab6b`. Current CP1138/BANK1284/RP768/conversion-test1456 occupy exactly4646 whole source lines within existing named ceilings5000. The narrow BANK selected-zero/CP strict-cache-zero repair is qualified; whole T18d and integrated BAC remain open. No runtime accompanied this document; execution below is attributed to root and independent Astra. Root owns publication after scoped source-truth prose review.

## Sources and scope

Exactly four whole semantic sources were inspected; dependency implementations were not opened. Relative source links below are for publication under `docs/remediation/bac`.

| Source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| [curiosity_checkpoint.py](../../../src/townlet/exploration/curiosity_checkpoint.py) | 1138/1350 | 4de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a |
| [scoped_curiosity.py](../../../src/townlet/exploration/scoped_curiosity.py) | 1284/1350 | 294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f |
| [exploration_policy.py](../../../src/townlet/config/exploration_policy.py) | 768/800 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| [test_pw_scope_conversion.py](../../../tests/test_townlet/regressions/bac/test_pw_scope_conversion.py) | 1456/1500 | 672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 |

Total 4646 lines; named ceilings total 5000. Accepted PW07 ABI and wave28/29 public provider/RNG/HC capsules supply dependency facts. The superseding wave31 `OWNED-NATIVE-METADATA-QUALIFIED-API.md` qualifies actual owner WS883 SHA `cb8a7fd9f27c73537ec3f18f37b6cd5a3d88ca23c281b76376cece8be5f9dfb1`; it supersedes the historical WS871 metadata-loss limitation without an extra implementation read. [BANK contract](CURRENT-CURIOSITY-BANK-CONTRACT.md) covers runtime/completion operations.

## Public API and current format

On `townlet.exploration.scoped_curiosity.CuriosityBank`:

- `checkpoint_state()` returns a complete owned mapping.
- `prepare_restore(*, state, mode, accepted, parent_restore, validate_parent_restore)` prepares ordinary same-scope restoration.
- `prepare_private_initialization(*, state, initialization, parent_restore, validate_parent_restore)` prepares explicit shared-to-private initialization.
- `install_restore(*, prepared)` publishes once and returns None.

Every listed keyword is required. Both preparation methods actually return the identity-only `townlet.exploration.curiosity_checkpoint.PreparedCuriosityRestore` handle, although the BANK annotations are `Any`. Publication data stays in the receiving BANK. Ordinary restore never guesses initialization or converts scope.

The exact `curiosity-bank-state-v2` top-level fields are `schema, policy, policy_identity, descriptor, source_device, curiosity_epoch, bank_phase, dispatch_identity, worlds, shared_backend, step, completion, initialization_origin`. Missing/extra fields and BANK v1 refuse. Complete current policy must reconstruct and roundtrip exactly; ordinary receiving policy must match completely, not merely by execution hash. Descriptor reconstruction checks exact membership, geometry, seed and policy-derived identity; source device string must match. Float32 and CPU or explicitly indexed CUDA are required; CPU is the executed profile here.

RP still contains pre-scope policy compatibility functions, but CP's complete roundtrip equality rejects an old policy field set at this boundary. These documents neither authorize those older paths nor introduce a legacy training loader. Historical A artifact inspection/export and current captured replay capabilities remain preserved; obsolete BANK training formats have no fallback.

| Record | Exact fields / meaning |
| --- | --- |
| World | `world_id, backend, gradients, cursor, phase_cache`; exact unique world IDs |
| Cursor | `accepted_episode_seq, eligible_seq, cumulative_service_position, participated, disposition` |
| Shared backend | `native, gradients`; private BANK uses None |
| Private backend | healthy `owned-world-backend-v1`: `schema, healthy, backend, rng`; shared world backend/gradients are None |
| Reward cache | `event_id, content, update_stats, raw, scale` |
| Service cache | `event_id, content, receipt` |
| Completion cache | `episode, disposition, content` |
| Transition content | `predecessor, successor, actions, active, vector_tick` |
| Event | `curiosity_epoch, world_id, world_episode_seq, eligible_seq` |
| Step | `original_binding, stamp, tick, active, context, update_stats, reward, receipts, serviced` |
| Stamp | `event_ids, world_ids, world_episode_seqs, eligible_seqs, eligible` |
| Step reward | `raw, scales, eligible, event_ids, scope` |
| Completion | `status, original_accepted_identity, boundary_key, completion_content, participated_world_ids, dispositions, outcomes`; status must be `committed` |

A service receipt contains `scope, world_id, event_ids, eligible, clock, admitted_rows, consumed_rows, dropped_rows, pending_rows, optimizer_updates, mandatory_service_updates, last_loss`; clock is None or `unit, position`. Accepted value identity is `batch_episode, world_ids, world_episode_seqs`. Batch/boundary0 is legal; accepted event episode sequences are positive. Metadata integers reject bool/float aliases. Dense finite tensor shape/dtype/device, action bounds, cache/cursor/phase/event/receipt correlations and complete outcome canonical `(payload.hex(), fingerprint)` tuples validate. A fingerprint alone does not carry completion evidence. Reserved, rewarded-before-service and settled live steps are represented explicitly.

## Explicit initialization and preserved source

`initialization` is exactly `fresh_private` or `clone_learned_archive_pending`. Receiving BANK must be healthy, untouched INITIAL and private, with no prior origin, activation, active reservation, cache or nonzero cursor. Source is a complete ordinary shared v2 checkpoint with origin None at `initial` or committed `completed_boundary`; live or prepared completion is not a conversion boundary. Source and target scopes must both be explicitly authored: shared/vector_tick to per_world/world_eligible_admission.

Require the same exact world membership, training seed, observation/action geometry and device profile. Selected behavior compares strategy, all epsilon fields, provider parameters, reward/predictor phases and input kind; non-none scale/base/modifiers; RND/adaptive parameter source; and trainable service mode, update budget, pending capacity and overflow policy. Adaptive active values reside in validated provider parameters. Inactive presets retain provenance without becoming execution identity. The caller supplies a genuinely resolved target policy with compatible selected capacity; conversion does not silently derive smaller capacity or forge scope tags. Receiving order may differ at a settled boundary.

Both choices retain one complete independently owned source checkpoint archive per BANK, including original native learning, ordered pending tail, optional gradients, policy/descriptor, clocks/counters, cursors/caches/step/completion. It remains inactive; no archived row enters private service, becomes a fabricated drop, or acquires an invented world attribution. Source live objects are neither mutated nor re-exported during preparation.

Fresh uses actual same-ID factory-created models, targets, initial gradients, RMS/Count/history and private RNG; it inherits no learned state. Clone independently retains learned models/fixed targets, Adam moments/steps, optional residual gradients, RMS, Count/LRU/evictions, adaptive history/weight and diagnostic epsilon. Count/ICM native policy fields become the validated target policy. Only the specified native ledger/clock/budget/queue fields change. Both choices use fresh world-derived RNG continuation after actual factory initialization, not copied shared/global streams or a claim of historical private randomness. The separate global selector is unaffected.

For trainable clone, source counters A,C,D,U and optional M yield inherited baseline `A0=C+D, C0=C, D0=D, U0=U, M0=M`. Live pending starts empty, native service position A0, unit world_eligible_admission and ordinary updates at position0; RND/adaptive step_counter0. RND/adaptive preserve their signed optimizer_step_offset and actual zero-row tensor shape/dtype/device; ICM uses its native empty list and retains last_loss. Source archive preserves original A, tail, budget and clock unchanged. Fresh baseline numeric values are zero. RND/adaptive mandatory cumulative baseline is None because no such native cumulative counter exists; none/Count baseline is None.

Native counters mean inherited settled work plus future local work. Subtract baseline to obtain nonnegative exact future counters a,c,d,u,m, requiring `a=c+d+len(active_tail)`, `c=u*B`, and ICM `m<=u`. Native Adam pairing remains strict: ICM step=U, RND step=U+signed offset. BANK cumulative position equals a and starts0. Next private provider clock is A0+a+1, while public receipt position is a+1. Inherited work grants no new service opportunity. None/Count have no predictor ledger; their genuine eligible BANK positions still advance.

Origin exact fields are `schema, initialization, source_checkpoint, target_policy, target_policy_identity, target_descriptor, native_counter_basis, inherited_baseline, episode_baseline`; schema `curiosity-private-initialization-v1`, basis `inherited_settled_plus_future_local`. Target fields preserve actual initial receiving identity; later permutation does not rewrite that provenance. Episode baseline is source exact-ID accepted-sequence mapping. Epoch is source+1 (currently1 for ordinary shared source), and ordinary resume preserves it. Origin None requires epoch0. All runtime event/cache/stamp/receipt decoders validate retained epoch; old epoch events cannot replay as new private work.

## Phases and real authority

| Mode | Required receiving authority and state |
| --- | --- |
| `initial` | `accepted=None`; explicit None/None parent pair or actual INITIAL preparation/callback. Zero cursors, no dispatch/step/completion/cache/disposition. Converted INITIAL remains initial, with origin and epoch1. |
| `private_initialized` | Completed-source initialization retains real source episode sequences, but eligible/cumulative0, participation false, disposition None, empty cache, no dispatch/step/completion or accepted capability. Restore requires real completed parent preparation/callback correlated against the archived shared source. |
| `live_episode` | Actual ENV-authenticated receiving `WorldAcceptedEpisode`; both parent arguments None. Match saved batch and every ID/sequence, receiving order, and authenticate before/after candidate work and again at install. |
| `completed_boundary` | `accepted=None`, retained real ENV `prepared_restore` and genuine parent callback. Current completion/history remains data, never close authority. |

`begin_episode` after private_initialized requires actual next ENV token with each sequence baseline+1; it clears the boundary marker and creates ordinary live private work. No private completion, participation or disposition is fabricated from source history. Later live/completed origin-bearing restore validates current runtime against its current token/parent, and validates archived origin separately. It never compares a later parent cursor to the old source cursor.

Ordinary origin-bearing INITIAL/private_initialized restore additionally checks complete native state and gradients against the actual fresh factory template or validated transformed clone template. Later genuine learning need not remain equal to that initial template. Every origin restore validates archived shared native data through actual producer validation/loading under separately disposable RNG custody.

Parent correlation checks public world/roster/binding/VFS data: seed/membership/cursors, receiving VFS projection, snapshot producer binding, original closure binding/order, canonical completion/participants/boundary and retained accepted binding. The callback is required to authenticate real retained preparation and parent transaction custody. It receives independently owned views before and after candidate work; synchronous mutation refuses and later retained-view mutations cannot alter prepared data. BANK does not install ENV or issue a restored parent release. Actual parent `WorldBoundaryAuthority.restored(*, restore, boundary)` and ENV install remain external, with final all-child freshness/publication obligations.

Private live row permutation projects current step tensors/receipts by exact ID while retaining local provenance. Shared live grouping order is strict. Completed historical original order/agent indices and canonical payload survive receiving permutation. Imported history has no accepted/activation/prepared/committed capability. Next genuine begin clears episode-local history/cache while retaining learning, gradients, tails, RNG, origin and cumulative positions.

## Native custody, refusal and publication

CP independently owns current dense tensors, NumPy arrays and finite NumPy floating RMS scalars without changing scalar type/precision. Actual OrderedDict kind/order and recursive optional `_metadata` are preserved; CP exact equality checks them. The qualified owner codec now preserves those structures across callback/snapshot/preparation too. This is actual current producer support, not an arbitrary custom model format guarantee.

Provider schemas remain rnd-state-v2, adaptive-intrinsic-state-v2, icm-state-v2, count-state-v1 and the exact EPS three-scalar payload. Actual native validators/loaders remain mandatory. EPS is separately checked for finite policy-bound epsilon/decay/minimum; Count's actual loader is used on a disposable provider with additional BANK observation-width checks.

BANK explicitly transports None/zero/nonzero gradients: RND `predictor_network`, adaptive `rnd.predictor_network`, ICM `encoder/inverse_model/forward_model`; none/Count mappings are empty. Fixed targets must have no gradients. Module/name/shape/dtype/device/finiteness and actual Adam group/state Parameter pairing validate. Attach gradients to actual candidate Parameters after final native load; owner/native serialization alone does not preserve `.grad`. Private candidates are independent actual owners created in canonical ID order. Shared restore prepares one coupled provider and does not serialize process-global RNG or Q/selector/replay/controller owners.

Allocation inventory/report admission precedes owned input, disposable RNG/factory/native work, outcome codecs and callback clones. Reports reserve resident/candidate/model/gradient/Adam/tail, numeric input/runtime/archive and both possible retained callback views. Python Count/container/integer overhead, allocator/library workspace and external/prior retained copies remain unknown: estimates are not total memory bounds. Refusal never changes scope/capacity or skips updates.

Actual late cache/receipt/outcome allocations feed the prepared runtime after native preparation. Final callback and revision checks finish before retaining a token. Install verifies exact destination-owned handle, unchanged revision, no pending completion and live acceptance, then replaces one preallocated BANK dictionary. No provider load or allocation follows publication. Foreign/copied/stale/consumed handles refuse. Successful export/snapshot advances revision and invalidates pending handles. Expected off-side refusals preserve live state and permit healthy retry; unexpected observed runtime/publication failures quarantine. Healthy saved state can explicitly restore a quarantined destination; quarantined export refuses. Parent quiescence, global RNG coordination and whole-parent failure handling remain external.

## Evidence and remaining gates

Historical PW06 at e52234ed had root147PASS65.5674s and Astra147PASS80.4319s, with covering635PASS/3 conditional CUDA skips101.5953s; that evidence concerned v1 and remains historical. PW07 repaired coherent Count boundary-origin negatives, typed RND pending tensors and the separate owner OrderedDict metadata producer seam without weakening equality. Historical PW07 main root153PASS84.7200s and independent Sol153PASS137.7268s bind candidate3c0052b8; whole bounded actual source/design/runtime SPEC and QUALITY approved (review SHA prefix499bf106). Separate historical codec root16PASS14.3636s and independent Astra16PASS13.9113s have source/design approval SHA4e1e894321fc4048ba0aaad150a1479d8157312715cff45da406955e78fc3b2c. Selections overlap and are not summed.

Historical coherent4f755ce9 completed951PASS/3 conditional CUDA skips121.8010s at354source/573config/13artifact/4pytest custody. Historical pure reference-fixture correction had root31PASS/1skip18.1072s and independent Astra31PASS/1skip18.9909s, final test-reference prefix9457bc3f942 and reviewer prefixbfd9324f APPROVED. Those results remain historical component evidence, not current-source reruns.

Current narrow T18d prerequisite evidence at b848b95a: root22PASS36.4422s and independent Astra22PASS279.6575s, with final bounded actual fixed-source/design SPEC and QUALITY APPROVED. The independent review used its own four-source4111-line envelope, including the new none test; this documentation context did not inspect that test. Root's final combined976 selection completed973PASS/3 conditional CUDA skips, wall345.2238s (pytest159.50s), actual child and verifier exit0. Custody355source/573config/13protected artifacts/4pytest identities/current index/import/thread/14registry MAIN1 PASS. Sources are frozen and all runtime is closed. These overlapping selections are not summed. The evidence qualifies the narrow none-scale prerequisite and current component regression selection, not whole T18d, full-parent runtime or a BAC release.

Current four global guards PASS/default601; global mypy retains the same nine old oracle/POP caller errors across197 sources. Previous public c1de CI is Config PASS and Lint FAIL, with the actual Lint log verified to contain those same nine errors; Tests is still running at this evidence boundary. No final remote Tests verdict or exact-current-tip CI success is inferred. Earlier public a7c Tests FAIL remains historical and untriaged; its cause is not inferred from the mypy failures.

Synthetic3D/2action CPU tests exercise actual learning/gradients/Adam/RNG, genuine ENV authority and cooperative local other-role interfaces. Minimal actual HC/ReplayBuffer/RewardTensor cases preserve captured rows/masks/components/clocks and active current replay; they do not qualify DQN sampling or full parent artifacts. Full parent/population/runner/native save-load, fresh completed full-parent replay/private counters/next update, final-child refusal, T26, full/default/coverage≥70/slow/hardware/CLI/learning/CI and final54requirements/22lenses remain owed. Original28/66 release counts stay unchanged. K01's qualified/deferred exact stochastic or mid-episode simulator scope remains unchanged; ordinary live BANK restoration is a supported component, not a new simulator continuation promise.

The narrow T18d none-scale prerequisite is complete: eligible `none` now emits raw0, selected scale0 and contribution0; inactive raw/scale remain0. BANK selects zero inside its actual provider callback, so returned rewards, pending reward and local caches carry the same value in both scopes and on retry. CP requires exact selected-device float32 cached zero and separately requires raw zero; coherent nonzero cached scale, missing fields and obsolete schemas refuse without normalization or fallback, including archived source records validated through origins. Other families, initialization/archive/phase/authority custody retain their existing semantics. Next work remains whole T18d current runtime/facade/global selector and actual parent/native/learning integration with the final gates above.
