# Replay prefix other-model adversarial verification — frozen R104

**Disposition: CHANGES REQUIRED for bounded source acceptance. One material P2 finding: the FIX5 count proof can under-inventory reachable digest/live-row/destination work across a supported preceding clone hook. F1's ordinary-key repair is supported. Ordinary clone-stable F2 mismatches are repaired; F2's general clone-stability boundary is not established. The finite root probe below is UNRUN by this reviewer.**

This is an independent Codex adversarial review of Astra-authored FIX4/FIX5, separate from final whole-BAC review. It does not reject the prior review's conservative opaque-semantic composition merely for retaining extra possible work. The new finding is the opposite direction: a preceding opaque clone can restore successful continuation, but the new ordinary-count predicate declares that continuation impossible.

## Frozen subject and custody

Reviewed root R104 tree `e206288d4f6eee330e3fcb8114a47af3002eecb1`, manifest `90534e49a82821c82df027828e1ed85037ed7d5cb98d723250584e75a9e5672a`, using the existing `/workspace/hamlet` checkout. Branch identity is supplied by the dispatch and frozen evidence; no Git command was used. Read repository AGENTS.md, the FIX5 brief, I5 prefix matrix and binding interpretation review, FIX3/FIX4 findings, FIX5 scoped review, relevant author-report sections, actual FIX4/FIX5 diffs and root R104 check record.

Only the following three implementation bodies were admitted; personally checked line counts and SHA-256:

| Body | Lines | SHA-256 |
| --- | ---: | --- |
| `src/townlet/training/replay_contract.py` |842|`3fd73601d1ec9110a7ca03157d452827e0fc1d8249f0c3a86a18cad364c8b23c`|
| `src/townlet/training/historical_checkpoint.py` |675|`74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`|
| `tests/test_townlet/regressions/bac/test_replay_cuda_producer.py` |2204|`d178bb0a40340292e3b06328438ec2d825378d9464df8bf600873d3c7e2fce9b`|

Total3721 lines/3 bodies, below5000. The actual FIX4 diff includes its narrow family call-site hunks; neither excluded family implementation body was opened. No core/tool/other implementation body, application import/runtime, test execution, source edit, index/branch/worktree/checkout action, source copy or delegation occurred. This report is the only write.

Personally rehashed evidence:

| Artifact under preparation unless stated | SHA-256 |
| --- | --- |
| `T18e-R0-CUDA-FLAT-PER-A-FIX4-R102.diff` |`28098d47ae3d7b0d805d7968a6d7bf16f2b5687d3ee0681f8ec74d2818250eec`|
| `T18e-R0-CUDA-FLAT-PER-A-FIX5-R104.diff` |`269d2c9aba57214aa9c0121c9496e34b2b918eca26b43a4a4517830abbc80ab7`|
| `T18e-R0-CUDA-FLAT-PER-A-FIX5-IMPLEMENTATION-REVIEW.md` |`0a8dd26f5e704097dbbdfe9002b25fba193b362df951143ff85f4b341634ab17`|
| `T18e-R0-CUDA-FLAT-PER-PRODUCER-A-REPORT.md` |`ac27c6965cf7f5c4e3d5be0196db01f9a6ea3eb40d39f6941812789032c67aad`|
| `../wave35/r104-root-checks.json` |`f2f93e2193ecd2e837b67a5bec4438c692196cf7d31f3fd6f3d6585824f53717`|

## P2: count refusal assumes stability across preceding clone inputs

Location: `ReplayPrefix.archive`, shared119–136, particularly the proof at131–136. The helper executes `_own(self, ("source_formats", "original_state"))` at295–296, then obtains cloned state/formats at297. `_Owned.__getattribute__`268–270 and `_own`273–275 make these genuine recursive clones. `_clone`51–62 calls supported Tensor detach/clone, Mapping items/key/value traversal, container traversal and scalar `copy.deepcopy` before archive semantics/state/count/digest validation at298–304.

FIX5 checks that raw state keys are exact strings and that raw selected kind/count are exact primitives. That protects against the selected key/kind/count individually changing representation during cloning. It does not establish that *earlier* cloning cannot change a later raw metadata value. `source_formats` is cloned first and is not screened for such a boundary by the planner. Its accepted scalar subclass can implement `__deepcopy__`, update the still-uncloned source state's ordinary count, and return a valid exact scalar. This needs no monkeypatch, concurrent mutation, unsupported extra field, fabricated archive, new type policy or change to production.

Concrete finite witness, based on the existing genuine four-row `_family_archive` fixture:

1. Obtain its six-key record, archived count4 and valid original state with all archive row Tensors on2. Keep its exact ordinary state kind and exact-string keys. Change only raw `size` (flat) or `size_current` (PER) to exact integer3.
2. Replace `source_formats["replay"]` with an int subclass retaining the existing numeric value4. Its `__deepcopy__` sets that same raw original state's count back to exact4 and returns `int(self)`. The hook therefore normalizes to accepted ordinary source-format metadata, using the helper's actual supported cloning protocol.
3. Set `source_digest` to existing `_ArchiveComparison(torch.tensor(0), 1)`, whose supported real inequality performs observable sum work on1 and returns false. This is the existing accepted digest-success fixture behavior, not a new permissive comparison.
4. Embed the record in the existing valid nonempty current family transport with live rows3 and preparation selector4.

Planning never invokes the clone hook. It reads exact raw3, compares it with archived4 at shared135, stops with `unknown=False`, and retains only the source-format/state clone inventory2. The digest operand1 is not in that inventory. `_transport_inventory`309–317 consequently also excludes live3, installed merge continuation and target4.

Actual construction first clones source formats, whose hook restores raw count4 before original-state cloning. All owned state/count metadata is then the original valid ordinary4; the initial malformed raw3 is never validated. The helper proceeds to digest comparison on1 and accepts. Valid live-row processing and preparation destination are consequently possible. Thus the discrepancy is missing reachable work, not conservative excess enrollment. The missing digest1 alone supplies a direct helper-level causal observation without B/public producer execution. The live3/target4 conclusions additionally rely on the unchanged family continuation interface supplied by the binding matrix; they are not claimed as executed outcomes here.

The prior FIX5 review correctly declines to infer a later definite refusal after arbitrary opaque semantic comparison: such a hook may mutate later state. The same reasoning must apply to an earlier clone hook. Here the implementation advances a definite-refusal proof across that hook instead of preserving unknown continuation.

## Finite root falsification packet — execute only under root custody

No additional source write is requested by this report. Root can adapt this inert recipe to its authorized probe mechanism with the existing admitted fixture namespace. Limit it to flat and PER: four pure-plan captures (validate/prepare for each) plus two direct helper positives. Do not rerun the436 checks to answer this question.

For each `family`, construct exactly the existing nonempty setup used by `test_archive_declared_count_boundaries`: CPU owner, `_push(owner, _rows(), recorded=True)`, `before=owner.serialize()`, and `incoming` replacing every direct Tensor value with `_CUDAData(value,3)`. Use a fresh genuine record and this closure:

```python
record = history._record(_family_archive(family, 2))
state = record["original_state"]
field = "size" if family == "flat" else "size_current"
assert type(state[field]) is int and state[field] == 4
assert record["archived_row_count"] == 4
state[field] = 3
clone_calls = []

class RepairCountDuringFormatsClone(int):
    def __deepcopy__(self, memo):
        clone_calls.append("source_formats.replay")
        state[field] = 4
        return int(self)

record["source_formats"]["replay"] = RepairCountDuringFormatsClone(
    record["source_formats"]["replay"]
)
record["source_digest"] = _ArchiveComparison(torch.tensor(0), 1)
incoming["historical_archives"] = [record]
owner.device = torch.device("cuda:4")
validate_plan = _metadata_plan(owner, "validate_serialized", (incoming,), False, simulated_cuda)
prepare_plan = _metadata_plan(owner, "prepare_serialized", (incoming,), True, simulated_cuda)
assert state[field] == 3 and clone_calls == []
assert simulated_cuda.events == []

# Establish accepted real continuation before attributing any plan failure.
simulated_cuda.events.clear()
restored = history._archive_from_state(record)
assert restored.archived_row_count == 4
assert clone_calls and state[field] == 4
assert any(event[:3] == ("finished", "clone", (2,)) for event in simulated_cuda.events)
assert any(event[:3] == ("work", "sum", (1,)) for event in simulated_cuda.events)

# First predicted wrong assertion on frozen FIX5:
assert validate_plan == (None, (1, 2, 3))
assert prepare_plan == (torch.device("cuda:4"), (1, 2, 3))
```

Source-predicted frozen observations for both captured plans are `(None, (2,))`; the first plan assertion above should fail after the positive helper assertions establish causality. The archive is mutated only by its actual supported clone hook after both plans are captured, so the test does not infer a problem from manually changing the input between planning and execution. Preserve any setup/fixture failure as such; do not call it reproduction. Exact root execution and result custody remain owed.

## Finite structural ruling and limits

The necessary contract is stability of the metadata proof across *all preceding accepted operations capable of changing that metadata*. Exact raw kind/count/key types alone do not provide it. The finite repair decision is whether the planner can certify an ordinary clone-stable input envelope, retaining opaque possible continuation when it cannot, or whether an explicitly owner-approved supported-input contract can provide that stability. Silently rejecting currently accepted subclasses/Mapping inputs would violate the binding requirements. This report grants no next repair round, broad hardening programme or acceptance waiver; root must adjudicate this material remainder at the existing5/5 cap.

Relevant concrete boundaries:

- Scalar `__deepcopy__` in either cloned mapping can normalize itself and affect a later input, as above. The existing count-subclass control proves normalization only for the selected count, not other fields.
- Mapping `.items()` is invoked by the planner at124 and separately by actual `_clone`; accepted Mapping does not promise a stable/repeatable item stream or side-effect-free traversal. MappingProxyType of an ordinary stable dict is a valid control, but it does not establish that promise for arbitrary supported Mapping. This is a proof limit, not an additional executed finding.
- Tensor subclasses dispatch detach/clone before the count check. Production accepts them and does not enforce side-effect-free clone behavior. The existing `_CUDAData` test seam behaves stably for these cases, so ordinary count-mismatch tests legitimately check that fixture's intended prefix. Their oracle implicitly relies on that fixture-specific clone stability; it is not a stability guarantee furnished by the production Tensor/Mapping accepted-type checks. Do not whitelist the fixture class in production or claim its behavior proves all subclasses stable.

For clone-stable ordinary inputs, shared119–136 correctly uses the successful helper return relationship rather than predicting reductions: helper157–166 and199–262 return the declared exact count for all standard/prioritized/sequential kinds. All earlier clone/internal-validation sources remain retained, and unequal counts exclude digest/later work. Reward→approval short-circuit, fixed-diagnostic count refusal and reached opaque semantic/digest operands are otherwise preserved. No new error rendering or acceptance restriction was found in the actual FIX4/FIX5 real path; `archive(planning=False)` immediately delegates to unchanged restoration at99–100.

F1's ordinary unexpected-key proof at shared72–81 correctly prevents an unrelated opaque key from enabling continuation for the supplied stable key sets. All reached keys and earlier record effects remain retained; true opaque equality controls remain possible. No new F1 finding is established. Arbitrary mutating Mapping/key protocols are not independently qualified by this bounded review.

Root's hash-verified R104 record attributes757 collected,436 unique reachable PASS and321 UNRUN, with zero errors/skips/warnings, static/default600 PASS and the retained one missing B `device_invocation` type error. Those existing checks were not rerun; their totals are unchanged and do not include the new probes. The reviewed tests separately exercise selected count-clone normalization and opaque comparisons, but do not exercise the preceding-source-format-clone composition above.

Authentic core invocation/outcome and B producer integration, public producer completion, ten isolated children, parent/recurrent/native behavior, one-/two-device CUDA and whole-BAC gates remain absent or unqualified as recorded. No hardware/B/whole-A qualification is claimed. Package accounting remains28 qualified/38 remaining/66 total. Root must resolve the finite P2 and retain the actual probe outcome before treating this other-model gate as passed.
