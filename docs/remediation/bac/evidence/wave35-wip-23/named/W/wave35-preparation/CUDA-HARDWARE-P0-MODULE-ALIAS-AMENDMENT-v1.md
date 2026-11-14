# P0 named-reference module-alias amendment v1

Status: finite proposal only; no implementation or runtime authorization implied.

## Evidence and bounded inspection

Read `/workspace/hamlet/AGENTS.md` and only these two source bodies in
`/workspace/bac-review-2026-11-01/qualification` (Q):

| Body | Whole lines | SHA-256 |
| --- | ---: | --- |
| `bac_hardware_protocol_v1.py` | 520 | `adc8efeba368998e2e875a60c54ed3338a5ad2aa7daa710b7609e9ed2119de3c` |
| `test_bac_hardware_protocol_v1.py` | 611 | `f602359decd4a73626a737f186501f2f2e6e2a8d81f3cfdd354b4749f98f0899` |

Hashes match `evidence-management/hardware-protocol-p0/freeze-v4.json`.
Total inspected source: 2 files, 1,131 whole lines, within 5 files/5,000 lines.
No P3 source snapshots, application source, or unrelated source bodies were read.

P3 failure is recorded in
`evidence-management/hardware-identity-p3/owner-amendment/green09/execution.json`
and `output.log` beneath the same work root as this proposal. That attempt used
R's real `.venv/bin/python`, exited 1, and recorded 1 failed/50 deselected.
`test_preloaded_fork_recorder_zero_imports` failed while writing the process
start record: `process.imports[].name` reaches P0's `id` check and raises
`ValueError: unsafe ID`. The log does not identify the first offending alias.
The P3 owner reports observed `_pytest`, `_pytest.config`, and
`_pytest._code.code`; `__main__` and `__mp_main__` must also remain literal
when observed. These are test cases, not a claim that green09 printed each one.

## Existing contract and chosen correction

`TYPES["named-reference"]` currently binds `name` to `id`. Its three schema
uses are `admission-request.tools`, `spec.tools`, and `process.imports`.
Tool names are generic labels, including `children-verifier`, and both tool
containers independently require the exact six-name `TOOLS` set. Process
imports independently reject duplicate names. Thus this shared field is not
exclusively a Python import identifier, nor is it a path-forming attempt/job ID.

Propose changing only `named-reference.name` to a new scalar `reference-name`.
Its value must be an exact string, NUL-free, and 1–128 ASCII characters, and
must satisfy either of the two present-day semantic forms:

1. A generic named-reference label matching
   `[A-Za-z0-9][A-Za-z0-9_.-]{0,127}`.
2. A dotted Python module identifier matching
   `[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*`, with the same
   explicit total length bound of 128.

The addition admits leading underscores in legitimate module aliases while
retaining the generic label contract used by tool references. This is a single
shared-field semantic rule, not a legacy mode, fallback, or normalization path.
The second form admits no slash, backslash, whitespace, empty dotted segment,
leading dot, hyphen, or digit-leading segment. Existing generic label semantics
are preserved rather than silently narrowed. For example `a..b` already
passes the generic label form; this amendment does not claim to make every
generic label a valid Python identifier. The newly admitted underscore-leading
forms must satisfy the strict module grammar.

No case folding, stripping, underscore removal, alias substitution, import,
module lookup, reference-path rewrite, or pytest-specific allowlist is allowed.
The exact name and reference remain in the caller's input unchanged. Source
closure and actual observed alias correspondence remain mandatory P3 duties;
passing P0 is structural/reference validation only.

Alternatives considered: changing `id` globally would broaden path-forming
identifiers and is rejected. Changing `named-reference.name` to free text would
lose bounded name safety and is rejected. Splitting tool and module reference
types would narrow presently accepted process labels and expand the amendment
into a schema redesign; that is unnecessary for this additive correction and
would require separately scoped consideration under the owner's capability
removal/degradation/consolidation rule.

## Exact acceptance work after an implementation grant

Use the existing P0 fixture and inert regular-file reference, adding tests to
the existing test file only. Do not load pytest modules to generate the names.

1. `test_named_reference_module_aliases_preserve_exact_name`: parameterize
   `_pytest`, `_pytest.config`, `_pytest._code.code`, `__main__`, `__mp_main__`,
   `_`, and `_` followed by 127 `a` characters. Validate both a named-reference
   and a process containing it; compare the complete input to a deep copy after
   validation. Each must pass without mutation.
2. `test_named_reference_generic_labels_preserved`: parameterize `protocol`,
   `children-verifier`, `9label`, `a..b`, and `a` repeated 128 times. Validate
   named-reference records; the complete existing synthetic spec and request
   must continue to pass.
3. `test_named_reference_unsafe_names_refuse`: parameterize empty string,
   `.`, `..`, `_pytest/runner`, `_pytest\\runner`, `_pytest..config`,
   `_pytest.`, `._pytest`, `_pytest.9config`, `_pytest.-config`, `_pytest-config`,
   `_pytest config`, a newline-bearing name, a NUL-bearing name, non-ASCII
   `_pýtést`, `_` followed by 128 `a` characters, `None`, `True`, and integer 1.
   Each must raise public `ValueError` through named-reference and process
   validation.
4. `test_module_aliases_do_not_broaden_ids`: for the literal `_pytest`,
   independently replace `process.attempt_id`, `job_id`, `process_id`, and
   `role_id`, plus standalone `job.id`, `role.id`, and `obligation.id`; all must
   still fail. Also assert an underscore-leading spec/request attempt ID
   rejects even when matching output/scratch destinations are supplied.
5. `test_module_alias_duplicates_refuse`: two `_pytest` names with identical
   references must fail process validation; `_pytest` and `pytest` with the
   same reference must pass as distinct literal aliases. No deduplication.
6. `test_module_alias_reference_checks_remain_required`: for `_pytest`,
   independently change the reference digest and byte length, use an escaping
   raw path, and use a symlink leaf/parent; all must still fail.
7. `test_module_alias_cannot_replace_pinned_tool`: in both spec and request,
   replace one tool name with `_pytest`; exact tool-set checking must fail.

Run the full existing P0 test file plus these cases in the inert P0 harness
after authorization; retain existing path, duplicate, refusal, source-freeze,
layout, hardware, and reference tamper coverage without deletion or skips.
First retain the expected regression failures against frozen P0; then retain
the amended full run with exact source hashes, argv, exit and log. Keep source
changes to these two bodies and their combined size below freeze-v4's existing
1,400-line budget. Do not claim P3 closure from this synthetic P0 suite.

## Impact, gates, and handoff

Implementation scope is the two Q files above: one schema scalar selection,
one bounded scalar validation branch, and additive acceptance tests. `id`,
`path`, `_path`, `file_reference`, `_unique`, exact tool sets, layout checking,
all refusal logic and all source-freeze obligations remain unchanged. There is
no removed, degraded, or consolidated capability and no compatibility layer.
Unicode and longer module names remain outside this existing bounded contract;
expanding those domains is not proposed or claimed here.

P0 source remains immutable until root grants implementation and P3 observes
the freeze boundary. After testing, publish a successor immutable schema and
interface inventory and a new freeze referencing its predecessor; never rewrite
freeze-v4 or green09. P3 must observe the new hashes before its own authorized
real pytest/Git fixture retry and independently establish exact alias/source
closure. Other consumers must observe the amended freeze as directed by root.
No runtime, Git/index operations, branch/worktree/checkout, source copies,
Git initialization, deletion, application changes, or R124 changes were made
for this proposal. No hardware acceptance is asserted.
