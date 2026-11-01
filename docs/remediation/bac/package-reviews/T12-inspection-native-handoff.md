# Source provenance

Original `INSPECTION-TRANSPORT-HANDOFF.md`, SHA256 `294ada233e371029e9a4f6da9a9b5a5c44df5be962a5c6134eefa4679e40bf94`; portable rendering, original retained.

# Required inspection-transport interface handoff

The exact T12 proposal SHA256 `fbe4c27a940a002b3d94ece5a8d7f4ef758bf1be3243bbaa3efb57835137c145` is technically approved by Astra MEDIUM and adopted by root after two real second-save relocation failures. See `T12-archive-transport-proposal.md` and `T12-archive-transport-review-r0.md`. Implementation and consumer qualification remain pending; this is not native acceptance.

Archive-bearing unconfigured sequential transport serializes an exact four-key envelope: `inspection_kind='sequential_replay_inspection'`, exact integer `inspection_version=1`, exact old5 `legacy_transport`, and existing complete six-field `historical_archives`. It has no outer replay kind/version/count or captured geometry. History-free legacy serialization stays exact5; configured captured serialization stays closed6. No masks, A, options or reward provenance may be fabricated.

T14 and T24/T25 must discriminate the explicit envelope before assuming every serialized object has replay_kind/format_version/capacity/count. Designated newly authored legacy rows stay separate unqualified transport; original imported rows remain archive-only and cannot be sampled. Neither set seeds qualified occupancy/warmup or learning clocks, and new legacy rows are not relabeled historical_recorded_pre_fix. Configured6 cannot be silently downgraded to inspection.

Native owners must preserve the complete separately owned inspection transport off-side, alongside actual compatible learned state/clocks and a fresh qualified replay where appropriate. Canonical outer historical registry is the validated domain-aware union of actual HC records only; preserve nested-subset consistency, extra outer-only different-kind history, contradictions/refusal and once-only accounting. Do not discard inspection data because a configured buffer refuses the unqualified type. Complete current native validation, all fallible resource/RNG/learned-state preparation and atomic installation remain required.

Run actual affected current consumers immediately. A new KeyError, silent omission, guessed5/6 tag, loss of formerly supported save/load, or archived-row activation is a blocking regression requiring bounded repair before the affected boundary releases. Future task names do not waive a caused failure. T12 standalone success does not close C07 or actual native/inference/full-resume acceptance.
