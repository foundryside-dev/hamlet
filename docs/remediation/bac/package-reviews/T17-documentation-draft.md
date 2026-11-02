# T17 documentation draft — unapplied; qualification/closure still required

2026-11-02 UTC; existing `/workspace/hamlet`. Root requested only this ignored draft and `T17-source-docs.patch`. No tracked document or source/test was edited. The patch is prepared for root to apply **only after package qualification and all runtime/reviewer sessions close**; this receipt does not assert that those gates have completed.

Root reports R1 owned34 PASS and six guardsPASS, with fresh Astra-medium static review finding no confirmed blocking main defect. Root also reports an affected22-module run closed with at least one constructor-observer failure: its separate three-file owner diagnosed interception of `__init__` being bypassed by real `from_resolved_encoder` construction and proposed a repair preserving assertions. That consumer repair is outside this worker's source boundary and has not been inspected here. An independent12-node reviewer run may still be active. This draft does not turn those facts into package/full-suite qualification.

## Unapplied patch and exact prose targets

Patch: `wave11-preparation/T17-source-docs.patch`, SHA256 **`d85efe0047ff9adbd590d1f98f921d4d931070cd6258218e67fe6edf7d661a57`**. It is an ordinary unified diff with four hunks across exactly three prose targets. It was constructed from the exact read preimages in memory; no tracked-file edit, source copy, `git apply`, dry-run, index action or patch application occurred.

| Target | Read preimage lines | Proposed lines | Preimage SHA256 | Exact update |
| --- | ---: | ---: | --- | --- |
| `README.md` | 515 | 524 | `798cdb9a1a1a0cb222208120f8325d53705804372811c0226b1fc8297baa6faa` | Add one bounded T17 encoder paragraph beside the existing T15/T16 notes, retaining their text and broad dated review boundary. Link the encoder options and architecture contract. |
| `docs/architecture/BAC.md` | 308 | 331 | `f63a931a130dec5559ba782dabfaf64f857e8bfb3a31298fad44c346c6c4244d` | Update §2.2's shared row-encoder/factory description, add a bounded T17 correction describing explicit construction/state/context, and update §4's bridge wording from projection-only to selected row encoding. |
| `docs/remediation/bac/options.md` | 142 | 174 | `06020a8a006f21265b1ba4ded600c6cf64b8f91a344aad5082c9414a962784f0` | Replace only the encoder-declaration section: actual consumption, a valid width1 nested YAML example, both aggregators/families, central omission resolution, fixed linear direct constructors, required explicit classmethod keywords, learned-key geometry and target context. |

Existing prose outside these exact encoder updates is retained. No global status stamp, old acceptance record, historical learning witness, feature family, option or capability is removed or downgraded. Root should reject/rebase the patch if any target preimage hash has changed rather than treat its context as permission to replace unrelated prose.

## Source verification for proposed claims

Claims are confined to the existing five complete source files and their unchanged, previously read contents. No implementation links in the three prose documents were followed and no sixth implementation/helper/test source was opened.

| Claim | Existing-scope source evidence |
| --- | --- |
| Portable modes; explicit positive interaction width; linear takes no width | OP `TokenEncoderOptions` at23–35; BC's optional encoder declarations at147/172. |
| Central omission semantics and origin; actual routing in both factories | OP `resolve_token_encoder` at38–42 returns recorded linear resolution or authored selection; NF at80/150 uses it and forwards both required selection values. |
| Joint descriptor/live encoding before pooling | NET `_embed_tokens` at364 feeds all assembled payload fields to the type encoder; `_initialize` at274 builds direct Linear or Linear/ReLU/Linear at317–333. Existing pooling at387 remains downstream. Owned test's exact `.375/.125` construction and full authored witness exercise this contract. |
| Both aggregation and network families retained | NET attention/mean branches and existing pooling remain; token and recurrent wrappers each use the shared encoder. Recurrent `initial_hidden` at637 and `forward` at641 preserve explicit zero-start/threaded sequence behavior. The owned test retains nonuniform attention and both-family controls. |
| Old direct constructors remain fixed linear; explicit classmethods require mode/width | NET retained constructors dispatch to shared setup with `'linear', None`; new classmethods at252/449/553 require both keyword names and no defaults. NF selects those classmethods rather than consumer-local policy defaults. |
| Learned-key geometry | NET direct Linear ModuleDict retains `.weight/.bias`; selected Sequential uses Linear indices0/2 and explicit hidden width, with wrapper `encoder.` prefix. Ordinary mode/width attributes add no state tensor. |
| Target-owned context outside learned state | NET at312 constructs assembly from the supplied target TokenSpec. The owned test checks no context/scatter keys, builds immutable permuted target context, loads same-mode learned state and compares pooled/Q/hidden semantics. Root reports those owned tests passed at R1. No assembler/loader implementation was newly inspected. |

The five-source snapshot was freshly hashed before drafting and remains:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| NET `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| NF `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| BC `src/townlet/config/brain_config.py` | 568 | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| Owned `tests/test_townlet/regressions/bac/test_token_binding.py` | 640 | `bdb25f6e33bae64ede392dfb8ed4fbe4b7521a6dc201184e547decaeabefe544` |
| Total | **2336** | Same five complete sources |

The patch describes current source contracts. It does not claim that an older source version was executed as an optional historical golden comparison: the retained direct/new initialization tests compare current construction paths, while source readback checks the preserved Linear creation sequence. No checkpoint transfer, full resume, native continuation, new learning/convergence or whole-BAC qualification claim is added. Learned-key documentation describes module state shape, without asserting an excluded loader's acceptance/refusal policy.

## Stale prose and boundaries

- **Corrected in the proposed patch:** options' sentence “The new field is schema-only until T17 consumes it” contradicts the current NF resolver/classmethod calls. BAC's unqualified “per-type projections” wording omits the now-selectable interaction branch; the bridge is updated accordingly.
- **Flagged, preserved outside this update:** BAC §2.3 lists `StructuredQNetwork` among classes the network module exposes. The whole-read NET snapshot has no such class; its closed four-family BC authoring surface also has no structured architecture literal. The existing prose already labels that path unreachable. This patch preserves the unrelated table/history rather than removing a capability or expanding this work into architecture cleanup.
- **Dated/unrefreshed context:** BAC's document-wide August review stamp, old source-line references, broader provenance/consumer/transport statements and README's historical source/CI/oracle/learning records remain unchanged. This bounded encoder correction does not reverify them or supply a new global review result.

## Custody and disposition

Only the two ignored artifacts were written. Both ignore paths were checked. All three tracked prose preimages and all five source hashes are to remain unchanged; final readback/hash checks cover custody only. No project runtime/import, compiler, pytest, collection, lint, formatter, probe, tracked edit, index/commit/push, branch/worktree/source copy/deletion, `.oracle` action or subdelegation occurred. All14 existing worktrees were preserved. Worker returns stationary; root owns consumer repair integration, final qualification/runtime closure, applying the patch and any subsequent publication.
