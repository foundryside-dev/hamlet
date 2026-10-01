# Static Epistemic Access Implementation Plan

> **For the implementing agent:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after implementation authorization.

**Goal:** Make authored static permissions control direct state access, runtime writes and policy publication without changing permitted scenario behavior.

**Architecture:** Carry one canonical policy through registry and compiled profiles, enforce it at access boundaries, and authorize batched publication before arena gathers. Track VTC attempted write targets so read-only state is not rewritten incidentally. Preserve the current token ABI while extending semantic identity to item policies.

**Tech Stack:** Python 3.13+, Pydantic 2, PyTorch, MessagePack, pytest, uv; existing compiler/oracle tooling.

**Prerequisites:**
- Owner authorization to implement [PRD-0004](../product/prds/0004-static-epistemic-access.md) is now recorded: execute, commit and merge locally. Publication remains outside scope.
- Clean isolated execution worktree from `bdf64fadc69739c3e204845f9797d08500f46d46` or a reviewed documentation-only descendant. Verify no concurrent product-source changes.
- Own local virtual environment using `uv sync --all-extras --locked`; never repurpose the parent's environment.
- Read PDR-0120, PDR-0147, PDR-0151 and the bounded PRD. Preserve unrelated parent edits and frozen oracle `4222a917`.
- Bank before evidence before the first source/config edit. No calendar promise or implicit GitHub publication authorization.

---

## Source inventory and decisions

Baseline Loomweave status was fresh at `bdf64fad`. Verified source anchors:

| Boundary | Existing implementation | Planned closure |
| --- | --- | --- |
| Authoring | `src/townlet/config/variables_config.py:40` omits permissions | Required closed policy fields, explicit pack conversion |
| Lowering | `src/townlet/universe/compilers/vfs.py:82` hardcodes roles | Copy canonical policy; engine tick stays an explicit engine-owned definition |
| Profiles | `src/townlet/vfs/profiles.py:35` drops roles | Required compiled policy for all scopes including items |
| Access | `src/townlet/vfs/registry.py:611` has checked get/set; convenience/item APIs bypass | Explicit actors through protocol and callers |
| VTC | `src/townlet/vfs/transition_schedule.py:109` returns all state; env at 1284 commits all | Attempted-target provenance, not equality filtering |
| Publishing | `src/townlet/environment/token_publishers.py:879,1023` gathers raw arenas | Authorize bindings against exact canonical definitions first |
| Cache | `src/townlet/universe/compiled.py:967` serializes profiles without roles | Required fields, exact schema bump, coherence/hash validation |
| Hash | `src/townlet/vfs/schema_hashes.py:130` includes registry roles; compiler at 376 excludes items | Qualified item contribution to the same semantic identity |

Readers are engine/agent with engine required. Writers are engine or empty. All
current simulation consumers are engine; observation is agent. Unknown actors refuse.
No actor means a missing argument, not an implicit engine grant. Engine confidentiality,
owner-relative visibility and dynamic propagation remain excluded. These restrictions
must appear in source diagnostics and active documentation, not only this plan.

Implementation steps below are sequential outcome-sized commits. Within every task:
write the specified behavioral regression, run it and record RED for the intended
missing contract, implement, rerun to GREEN, inspect the diff, then commit only that
task's coherent files. No manufactured fixed pass counts. Red/green commands below
are future execution instructions, not tests run during planning.

## Task 1 — Bank the unchanged parent and add an executable evidence comparator

**Files:** create `scripts/check_epistemic_access.py` and
`docs/product/evidence/static-epistemic-access/`; read
`scripts/check_declaration_cut_b.py`, `src/townlet/oracle/{harness,matrix,trace_io}.py`,
`docs/product/evidence/declaration-cut-b/`; add comparator regression under
`tests/test_townlet/unit/oracle/test_epistemic_comparison.py`.

1. Create instrumentation with explicit `capture --output` and
   `compare --before --output --attributions` subcommands; all named arguments are
   required. Reuse trace I/O and harness APIs, not Cut B's baseline-specific labels.
   Capture reads the 31-case inventory, ten replay recipes and eleven reset recipes
   from Cut B evidence and regenerates them from the unchanged current parent.
   Commit instrumentation before product changes.
2. Run `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python scripts/check_epistemic_access.py capture --output runs/static-epistemic-access/before`.
   Bank the resulting inventories, exact input bytes, reset values, trace digests,
   parameters, source SHA and retained raw trace locations under the new evidence
   directory. Capture rejects a dirty execution-bearing tree. Commit before evidence
   before product edits. Resolve all JSON/NPZ references from the supplied before
   manifest and its declared trace base; validate baseline source SHA, config bytes
   and raw trace digests before comparing. Never inherit Cut B's hardcoded ROOT,
   EVIDENCE or BASELINE_SOURCE constants. Record the instrumentation-only descendant actually
   measured rather than falsely stamping its parent. The inherited case set must
   remain complete: no missing case or duplicate manifest entry is skipped. The new
   Task 5 witness is qualified separately and is not evidence of parent equivalence.
3. Write controls for missing attribution, unexpected reward/observation change,
   stale attribution and no-output-change success. Run
   `uv run pytest --no-cov tests/test_townlet/unit/oracle/test_epistemic_comparison.py -q`.
4. Implement exact case/field/before/after/cause attribution. Trace changes cannot be
   excused by a blanket hash allowance. Commit comparator and controls separately
   from the pre-edit baseline bank.

**Done:** before evidence predates product edits; negative controls exit nonzero for
the named reason. Existing Cut B reports are historical input, not this package's result.

## Task 2 — Required canonical permission policy and explicit fixture conversion

**Files:** modify `src/townlet/config/variables_config.py`,
`src/townlet/universe/compilers/vfs.py`, `src/townlet/vfs/{schema,profiles}.py`,
`src/townlet/universe/compiled.py`, live `configs/` and executable fixtures;
tests `tests/test_townlet/unit/config/test_variables_dto.py`,
`tests/test_townlet/unit/universe/test_canonical_variable_compilation.py`,
`tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py`.

1. Add failing required-field/unknown/duplicate/engine-read/exposure-conflict and
   item/global/agent policy-preservation tests. Run
   `uv run pytest --no-cov tests/test_townlet/unit/config/test_variables_dto.py tests/test_townlet/unit/universe/test_canonical_variable_compilation.py tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py -q`.
2. Add the closed fields to the canonical declaration; allow explicit empty writers
   on runtime definitions, retaining closed validation. Lower policy into both
   registry definitions and required compiled-profile tuples. Make a coherent exact
   artifact version bump (currently 1.28); require new fields on load. Do not support
   both artifact versions. Preserve internal tick permissions explicitly.
3. Convert every surviving authored variable and executable fixture to preserve
   its current `readable_by: [engine, agent]`, `writable_by: [engine]`. Negative
   fixtures deliberately omit/alter fields only to test named refusals. Do not
   edit frozen configs, add a translator or broaden the defaults whitelist.
4. Before wider caller conversion, trace one immutable registry declaration and one
   qualified item policy through cold compilation, MessagePack reload and canonical
   policy lookup. This is an early representation/coherence tracer bullet, not a
   claim that all immutable runtime writes already work. Rerun tests and fleet:
   `uv run python scripts/validate_compiler_cli.py`.
   Expected: valid packs pass; invalid fixtures name their actual expected error,
   not an unrelated missing field. Commit this coherent language change.

Proposed policy validation logic (complete executable example to adapt inside
`VariableDeclaration`; this is planned code, not an existing helper):

```python
from typing import Literal

def validate_static_access(
    variable_id: str,
    readable_by: list[Literal["engine", "agent"]],
    writable_by: list[Literal["engine"]],
    exposed_to: list[Literal["agent"]],
) -> None:
    if len(set(readable_by)) != len(readable_by):
        raise ValueError(f"Variable '{variable_id}' has duplicate readers")
    if len(set(writable_by)) != len(writable_by):
        raise ValueError(f"Variable '{variable_id}' has duplicate writers")
    if "engine" not in readable_by:
        raise ValueError(f"Variable '{variable_id}' requires engine read access")
    if not set(exposed_to).issubset(readable_by):
        raise ValueError(f"Variable '{variable_id}' exposure requires read access")
```

Pydantic's required typed fields reject missing/unknown role values before this
validator. Runtime access validates actor strings too; annotations alone do not.

**Done:** one policy survives DTO → registry/profile → artifact; old payloads fail
loudly; all valid existing worlds retain their current permissions and behavior.

## Task 3 — Checked ordinary/item APIs and production callers

**Files:** `src/townlet/vfs/{registry,evaluator}.py`,
`src/townlet/effects/{context,executor}.py`, `src/townlet/items/manager.py`,
`src/townlet/environment/vectorized_env.py`; protocol stubs and tests:
`tests/test_townlet/unit/vfs/{test_registry,test_scoped_registry,test_item_scoped_variables}.py`,
`tests/test_townlet/integration/test_item_self_modification.py`,
`tests/test_townlet/performance/test_component_benchmarks.py` and
`src/townlet/vfs/__init__.py` exports if present.

1. Write allowed/denied accessor tests, explicit missing/unknown actors, clone
   isolation, profile-qualified item policies, same-value denial and unchanged
   storage. Run
   `uv run pytest --no-cov tests/test_townlet/unit/vfs/test_registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py tests/test_townlet/unit/vfs/test_item_scoped_variables.py tests/test_townlet/integration/test_item_self_modification.py -q`.
2. Require keyword actors on `get_global`, `get_agent`, `read_item`, `write_item`;
   route convenience APIs through common authorization. Keep `set_engine_value`
   as an explicitly named fixed-engine checked API (not a default-actor overload).
   Unknown actors raise `PermissionError` before access; omitted required actors
   produce a signature `TypeError`, separately tested. Preserve scope/type/shape
   refusal. Add profile-qualified policy lookup independent of shared column offset.
   Snapshot validated role sets as immutable tuples in a single registry-owned policy
   authority at construction. All checked access and publisher plans use that same
   authority; changing a mutable source DTO/list cannot revoke a getter while leaving
   an old publisher authorized. Policy edits require a new runtime instance. Existing
   gated variable addition validates and snapshots each newly admitted policy; it
   cannot mutate policy for an existing variable.
   Update the observation-facing protocol and all stubs; no optional old signature.
   Delete the unused duplicate `ScopedVariableRegistry` implementation and exports.
   Port its meaningful scope/copy and performance/observation fixtures to canonical
   `VariableRegistry`; remove tests that merely pin the deleted unchecked API.
   Verify complete caller closure with fresh Loomweave before deletion.
3. Update actual evaluator/effects/item/spawn callers explicitly as engine. Replace
   spawn-predicate raw `_storage` reads with checked engine access. Default allocation
   and reset use private lifecycle operations; authored override/hook writes use
   checked APIs. Keep lifecycle helpers inaccessible as public permission bypasses.
4. Search caller closure using fresh Loomweave and source diff; run the focused
   tests and `uv run mypy src`. Commit only after no retired signature survives.

**Done:** every supported read/write route enforces policy before access; profile A
does not grant profile B; no new role promises or agent-owner inference.

## Task 4 — Real write intent and compile-time target authorization

**Files:** `src/townlet/vfs/{vtc,transition_schedule}.py`,
`src/townlet/environment/vectorized_env.py`,
`src/townlet/universe/{compiler,validation/references}.py`,
`src/townlet/universe/compilers/{vfs,effects}.py`,
`src/townlet/environment/affordance_engine.py`,
`src/townlet/effects/{compiler,context,executor}.py`, `src/townlet/items/manager.py`;
tests `tests/test_townlet/unit/vfs/test_vtc_action_writes.py`,
`tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py`,
new `tests/test_townlet/integration/test_static_epistemic_access.py`.

1. Write an immutable literal lifecycle matrix: global/agent tick, episode and
   persistent values at their existing reset boundaries, and immutable item defaults
   through allocation/reset. Add WAIT with unrelated state and denied same-value
   action writes. Separate known-declaration compiler refusal from deliberately
   constructed runtime denial; an old-signature TypeError cannot prove PermissionError.
   Add separate social-rule, expression, effect, affordance and item override
   negative controls, including nested/conditional commands. Run
   `uv run pytest --no-cov tests/test_townlet/unit/vfs/test_vtc_action_writes.py tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py tests/test_townlet/integration/test_static_epistemic_access.py -q`.
2. Extend `VTCTransitionState` with required attempted-target data propagated from
   action and social-residue execution using one common write-result/intent contract.
   Capture selected writes before equality or
   composition; respect active/action/condition selection. Preauthorize the complete
   selected VFS target set before publishing any bars, VFS values or dones from that
   transition result. Commit only reported VFS targets after authorization.
   Do not simply skip denied entries or infer writes
   with `torch.equal`. Keep bar/done choreography and declared phase ordering intact.
3. Add source-aware engine-write validation for every known variable target:
   profile expression output, custom action, social transition, lifecycle/effect
   nested command, declared/dynamic item override. Traverse typed AST/command nodes
   rather than regex. Dynamic targets must retain runtime resolution+authorization.
4. Prove no-op denied writes cannot pass, unused immutable state does not fail, and
   allowed writes still land once in order. Capture partial-mutation concerns:
   reject statically known invalid programs before stepping; preflight each dynamic
   command's complete target set before its own mutation. Preflight every item
   initial_state override before allocating a free slot, initializing defaults,
   incrementing instance counters or registering an item.
   Do not promise transaction rollback for
   earlier independent commands. Construct a runtime operation with an allowed
   target followed by a denied target; assert bars/dones/VFS remain unchanged for
   the transition commit. For denied spawn overrides, assert free-slot set, instance
   counter, registry, active/held items and arena state are unchanged. Rerun focused
   tests and commit.

**Done:** immutable state is usable, not a schema-only promise; all relevant known
author errors refuse before constructing a runtime; a dynamic denied operation
preserves its target storage. If target resolution cannot support a declared form,
refuse that form explicitly instead of accepting an unchecked write.

## Task 5 — Authorized batched publication and config-in witness

**Files:** `src/townlet/universe/{compilers/observation,dto/token_spec}.py`,
`src/townlet/environment/{observation_encoder,token_publishers}.py`;
create `configs/static_epistemic_access/` using a complete copied simple pack;
tests `tests/test_townlet/unit/environment/test_token_publishers.py`,
`tests/test_townlet/integration/test_static_epistemic_access.py`,
`tests/test_townlet/integration/test_item_vfs_observations.py`.

1. Test exposure contradiction at compile and malformed publisher construction,
   permitted public registry/item values, hidden absence, row-local agent values
   and wrong-profile/dead-item absence. Run
   `uv run pytest --no-cov tests/test_townlet/unit/environment/test_token_publishers.py tests/test_townlet/integration/test_item_vfs_observations.py tests/test_townlet/integration/test_static_epistemic_access.py -q`.
2. Validate each binding against its exact registry or qualified compiled item
   immutable registry-owned policy before building batched gather indices. Test
   attempted post-construction role-list mutation against both checked getters and
   publisher output: their authorization must remain consistent. Preserve one gather per scope;
   authorized internal arenas need not copy through per-element Python getters.
   Existing static hidden variables emit no slots. A denied constructed binding
   refuses; future conditional masks would need presence AND payload zeroing, but
   are not introduced by this package.
3. Commit a witness pack with public state, hidden agent-scoped score updated by
   an action and used by a named reward, and an immutable literal. Exercise two
   rows, two resets and cold/MessagePack-loaded artifacts. Item tests allocate
   controlled instances through current supported APIs and declare that they do
   not qualify the known initial-appearance serialization defect.
4. Run the tests and fleet validation, inspect actual bindings and normalized
   readings, then commit. No reward-loss or learned-convergence assertion.

Complete accessor witness to place in the new integration test after extending
the existing canonical test helpers to author required policies:

```python
from pathlib import Path
import pytest
import torch
from townlet.universe.compiled import CompiledUniverse
from tests.test_townlet.integration.test_canonical_variable_runtime import (
    _compile, _pack, _variable,
)

@pytest.mark.parametrize("cached", [False, True])
def test_hidden_immutable_state_denies_agent_access(tmp_path: Path, cached: bool) -> None:
    declaration = _variable("hidden", scope="agent", initial=2.0)
    declaration.update(readable_by=["engine"], writable_by=[])
    universe = _compile(_pack(tmp_path, [declaration]))
    if cached:
        artifact = tmp_path / "world.msgpack"
        universe.save_to_cache(artifact)
        universe = CompiledUniverse.load_from_cache(artifact)
    env = universe.create_environment(num_agents=2, level_name="L0_simple", device="cpu")
    env.reset()
    with pytest.raises(PermissionError):
        env.vfs_registry.get_agent("hidden", reader="agent")
    expected = torch.full((2,), 2.0)
    with pytest.raises(PermissionError):
        env.vfs_registry.set("hidden", expected, writer="engine")
    wait = universe.get_level("L0_simple").runtime_action_space.action_ids["WAIT"]
    env.step(torch.full((2,), wait, dtype=torch.long))
    assert torch.equal(env.vfs_registry.get("hidden", reader="engine"), expected)
```

This tests immutable access/WAIT only. Separate named-reward and token-binding
assertions are mandatory; this helper test alone cannot satisfy criterion 5.

**Done:** authorized publishing preserves numeric behavior; hidden state executes
without direct policy input; role checks make no item-owner/spatial privacy claim.

## Task 6 — Semantic identity, artifact coherence and exact checkpoint refusal

**Files:** `src/townlet/vfs/schema_hashes.py`,
`src/townlet/universe/{compiler,compiled}.py`,
`src/townlet/training/checkpoint_utils.py` only if gate coverage requires it;
tests `tests/test_townlet/unit/vfs/test_schema_hashes.py`,
`tests/test_townlet/unit/universe/test_compiled_token_coherence.py`,
`tests/test_townlet/integration/test_live_inference_checkpoint_identity.py`,
new `tests/test_townlet/integration/test_static_epistemic_checkpoint_identity.py`.

1. Test hidden/exposed registry/item policy-only mutation, ordering equivalence,
   omitted/tampered item profile policy, incoherent registry/profile definitions,
   and exact resume/serving rejection before applying any weights. Mutate authored
   policy, registry definition and compiled item policy independently; compare both
   directions of their coherence. Equivalent role order may change transport/config
   fingerprint but must not change semantic identity. Run
   `uv run pytest --no-cov tests/test_townlet/unit/vfs/test_schema_hashes.py tests/test_townlet/unit/universe/test_compiled_token_coherence.py tests/test_townlet/integration/test_static_epistemic_checkpoint_identity.py tests/test_townlet/integration/test_live_inference_checkpoint_identity.py -q`.
2. Extend canonical variable identity with sorted profile-qualified item policy
   entries, including hidden definitions. Use tagged registry/item identity tuples,
   not dotted string concatenation that could collide with legal registry IDs.
   Preserve existing VFS hash composition;
   do not use a blanket config-hash compatibility gate. Recompute policy identity
   on load and verify registry/profile/token coherence. Require all new fields.
3. Retain fixed token widths/type schema for permission-only edits. Exposure
   changes retain their existing layout/observation identity effects. Exact resume
   checks VFS identity for both flat and token brains; deliberate transfer stays
   separate. Run tests then commit.

**Done:** cache loading cannot restore a stale permission identity, and hidden item
policies are as checkpoint-significant as ordinary registry permissions.

## Task 7 — Attribution, local gates and independent acceptance

**Files:** comparator/evidence from Task 1, new entry in the live oracle divergence
register (locate current file from `townlet/oracle/harness.py`), active
`docs/config-schemas/variables.md` and VFS references, PRD criterion evidence and
a new accepting PDR only after measured success.

1. Run the new comparator against the committed parent bank:
   `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python scripts/check_epistemic_access.py compare --before docs/product/evidence/static-epistemic-access/before --output runs/static-epistemic-access/after --attributions docs/product/evidence/static-epistemic-access/attributions.json`.
   This planned new CLI must reject stale/unexplained movements and changed permitted
   streams. Register measured identity changes under the next unused DIV number;
   do not reserve a guessed ID or broaden old allowances. Run the frozen CPU matrix
   using the read-only existing-worktree invocation in
   `docs/product/evidence/declaration-cut-b/qualification-commands.md`, changing only
   the run ID/directory to this package and retaining clean-tree/SHA checks. The
   verified public entry point is `uv run python -m townlet.oracle.harness --help`;
   there is no `townlet.oracle.__main__`. Use the existing-worktree invocation to
   avoid the CLI's worktree-construction path touching the frozen oracle.
2. Run `uv run ruff check`, `uv run black --check .`, `uv run mypy src`,
   `uv run python scripts/no_defaults_lint.py src --whitelist .defaults-whitelist.txt`,
   `uv run python scripts/validate_compiler_cli.py`, and `uv run pytest`.
   All must exit zero; preserve the defaults whitelist. Record test/skip counts and
   coverage from the actual output, device and exact source SHA. A skip is not a pass.
3. Have independent reality/architecture/quality/systems reviewers read all eight
   PRD criteria, including source call-site closure. Correct stale current references
   narrowly; preserve historical PDR facts. No doc-only invented unit tests.
4. Commit and integrate locally only once qualified, preserving parent dirt. If
   GitHub publication is separately authorized, publish the feature branch/draft PR
   and wait for exact-head terminal-success CI. Bank local and hosted evidence as
   distinct checkpoints. Close implementation/acceptance tasks only at their gates.

**Done:** precise static-access acceptance with causal evidence; no convergence,
browser, CUDA, main merge or dynamic-propagation completion claim.

## Stop/revise conditions

If immutable VTC support needs a broader world-transition redesign, review the
write-intent interface before editing more consumers. If item policy cannot enter
semantic identity without losing profile qualification, fix that before publication.
If a declared command target cannot be resolved safely, reject the unsupported form
with source provenance rather than bypass authorization. Any observed unrelated
numeric change needs a causal explanation and independent review, not an expanded
oracle allowance. Owner/spatial privacy requests require a new scope decision.

## Execution record

Task 1 is complete: instrumentation `0fdb16ea` passed 46 comparator controls and
focused Ruff/Black. The unchanged parent bank was captured on CPU and committed
at `dd8ec028`, with 31 cases, 884 identity readings, ten trajectories, eleven reset
recipes and 408 exact YAML inputs. All raw trace digests and relocated manifest
references passed validation before product edits. See the [execution evidence](../product/evidence/static-epistemic-access/README.md).

Tasks 2–7 are complete at qualified source `b70fda104e5061ed2735e8b31b7f8f9caaf99f19`:

| Task | Execution and closure |
| --- | --- |
| 2 | `30b6adaa`: required finite policy authoring, explicit live packs and compiled profiles; schema 1.29. |
| 3 | `cb91522c`: single registry, explicit checked actors, cloned public reads and frozen qualified policies. |
| 4 | `7becd007`, `b6a75042`, `91374849`, `9211346c`, `45ba42bb`: attempted-write provenance, complete preauthorization, static target refusal, checked spawn overrides and metadata-only loop preflight. |
| 5 | `09872f8a`, `b70fda10`: authorized publishers, public/hidden/immutable witness and retained explicit refusal controls. |
| 6 | `3db56521`: tagged ordinary/item semantic identity, artifact coherence, real resume/serving refusal. |
| 7 | `6a0951ed`, `d22e7940`, final qualification/evidence: exact causal attribution, historical-limit/input controls, full local gates and criterion-by-criterion cross-review. |

Full local suite: **4,250 passed, 18 skipped, 15 warnings**, 1561.29 seconds, **85% coverage**, terminal exit 0 at the qualified source. Skipped tests are not passes.
The five static/compiler gates, parent and frozen CPU comparisons returned zero at
the same clean execution head. Evidence includes corrected counterexamples and
superseded failures; no partial run is counted as a pass. See the
[acceptance report](../product/evidence/static-epistemic-access/acceptance.md) and
[PDR-0153](../product/decisions/0153-static-epistemic-access-accepted-against-prd-0004.md).

This documentation records implementation acceptance. Authorized local merge and
postmerge verification are recorded separately after they occur. Publication,
hosted CI, learning/convergence and broader privacy remain outside this completion.
