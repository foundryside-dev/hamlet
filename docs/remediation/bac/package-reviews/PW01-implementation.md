# PW01 implementation ready for coherent-image qualification

Status: source stationary; implementation and owned assertion additions await
root's coherent freeze/GREEN. No worker runtime source imports, pytest, probes,
broad checks, index changes, commits, branches or source-tree copies occurred.

Root authorized Phase 2 after shared RED observed both intended missing-contract
failures following genuine old-cache load/hash controls. Root-attributed RED:
`/workspace/bac-review-2026-11-01/qualification/wave03-red/PW01.log`; guarded index
`406dd9044cfd8052c456d6db6988979d4519a508`. Base HEAD
`1f9d831a8fe76ab00e06774ef6888985f6c2aec2` adds receipt files only over qualified
production `1c99510967c132fce04548564f4cb317e2ecddaf`.

Implemented within the complete five-file inventory:

- OP: immutable typed `CuriosityScopeOptions`, compatible shared omission and
  versioned seed-policy resolution. The nested portable serializer omits only
  the new absent scope field, preserving old nonempty authored-option bytes for
  historical training hash computation. Private omitted capacities use local
  cardinality1; shared capacities retain global N.
- RP: ownership/seed/clock/origin/guarantee fields, roles and units; scope-aware
  capacity derivation; unchanged shared identity recipe and explicit private
  ownership identity. Known old decoding admits only the exact pre-scope field
  set without new scope markers. Partial current payloads and mismatched scope
  declarations/units refuse.
- EF: materializes selected scope/queues and preserves the shared execution
  projection. The old-view validator uses an explicit pre-scope outer/nested
  field set and strips only the known additive ownership metadata from the
  re-resolved shared view before exact canonical comparison.
- WS: immutable `WorldCuriosityDescriptor` and `derive_world_seed`. Seed inputs
  are only version, training seed, exact WorldId, provider and named component.
  Canonical ID-keyed seeds remain separate from ordered runtime binding hash;
  duplicate/empty strict IDs and corrupted persisted seeds/binding refuse.
  Descriptor dictionaries are fresh copies, with nested runtime maps immutable.
- Regression: preserved the authored two-node control set and added 13 lines
  of strict/current missing-tag corruption checks; no assertions were removed
  or weakened.

Public APIs consumed without inspecting their implementations:
`UniverseCompiler.compile`, `CompiledUniverse.to_dict/from_dict`,
`save_to_cache/load_from_cache`, `effective_run`, `get_level` and typed
brain/training/drive DTOs. No sixth source/helper was opened. Genuine native DATA
and its qualified-producer manifest remain unchanged. Real compiler/native-cache
preservation is pending root's execution; any required serializer-owner change
outside these files needs a bounded reslice before inspection.

Final counts/hashes:

| Source path | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/config/bac_options.py` | 285 | `d4de5950c63398f8d7ebf977733e0204dad2038be05e7685f097ac369f253931` |
| `src/townlet/config/effective_run.py` | 362 | `0cc2c58fa70f5416b03721119103acdfdcb83a2bed97db6a4a66db610446be99` |
| `src/townlet/config/exploration_policy.py` | 762 | `c5e7a767b4eea2069e9854f145434d2acde7b3eb1be8bcf4be06d9c3df9c7970` |
| `src/townlet/exploration/world_curiosity_state.py` | 220 | `4310308ca8d02ed2460997da728df3ea5513b8b51439a421505d4b3d0c51af5d` |
| `tests/test_townlet/regressions/bac/test_pw_scope_contract.py` | 261 | `d467ede1f0d2a841f62d51c70812f10b2dc6cb2ada28fa288ca32f14bcd8e150` |

Complete source charge: 5 files / 1890 lines, within every per-file ceiling and
the total 5/5000 bound. No inline executable probes were run.

Owned YAML DATA profiles remain:
`configs/test/bac_remediation/options/curiosity-shared.yaml` SHA256
`cf70624bec851452cf33aa3615c6345ed30a9cdd575a49ed0862b087c15cc073`, and
`configs/test/bac_remediation/options/curiosity-per-world.yaml` SHA256
`1cc5bf6e27be79963aba24bf13e89ec29a60dfcfaa5460f052d0e4b02a90a02f`.

Actual worker verification: scoped Black and Ruff on these five files passed
after the final edit. Commands used `UV_CACHE_DIR=/tmp/hamlet-bac-pw01-uv-cache
uv run --no-sync black --check` and the corresponding `ruff check`, each followed
by the exact five paths above. Source counts, hashes and owned status were read.

Unrun by worker: all post-implementation source import/collection checks,
focused GREEN, owner suites, six full guards, full pytest and fresh independent
review. Root owns the common candidate/index and will run those checks only
after all production writers are stationary. Serialization/identity change
requires the approved early-full gate before dependent release; no full-suite,
package, BAC or final acceptance is claimed here.

The scope guarantee is a portable declaration. This packet does not implement or
certify state-bank isolation, actual optimizer independence, private RNG domains,
event/stamp cursor receipts, service wiring or training/serving integration.
Downstream fresh/reset/resume/conversion epoch/cursor requirements remain exactly
as published in the Phase 1 receipt and reviewed B-section contract.
