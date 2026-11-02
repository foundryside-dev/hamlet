# T17 implementation candidate — awaiting root GREEN and review

2026-11-02 UTC; existing `/workspace/hamlet`; root is the sole integration owner. Root cleared production authoring after its actual R0 tree `55e3c6c4`: collection34 PASS, Ruff PASS, Black check requested formatting, and owned four-worker RED **28 failed / 6 passed / no errors** in 20.8507s wall. Root attributes failures to the missing callable `from_resolved_encoder` and factory-ignored `interaction_mlp`; the real authored fixture completed. Root reports 164 source hashes, 573 configs, 13 protected artifacts, 14 worktrees and five source/import/thread identities checked, with both runtime sessions closed. Evidence attribution: `Q/wave11-r0-owned/owned-negative-custody.json`; this worker did not reopen that artifact or run those commands.

This candidate follows the already adopted P4 API choice. Authorized production edits are only NET/NF, with formatting-only changes to the owned test; BC/OP remain read only. No new design/plan/review loop, capability reduction, source expansion, helper or optional programme was introduced.

## Exact implementation changes

- NET adds `from_resolved_encoder` on `TokenSetEncoder`, `TokenSetQNetwork` and `RecurrentTokenQNetwork`. All arguments are keyword-only and required, including `token_encoder_mode: Literal['linear','interaction_mlp']` and `token_encoder_hidden_width: int|None`. Existing direct constructor signatures and positional calling behavior are unchanged; they explicitly retain their established linear meaning.
- Each class has one `_initialize` shared by its retained constructor and new classmethod. The classmethod allocates via `cls.__new__(cls)` and calls shared setup once, including one `nn.Module` initialization. It does not first construct a linear network or replace modules afterward. The retained constructor passes the fixed pair `'linear', None`; explicit new selections have no local policy/width defaults.
- The encoder validates the explicit pair using the existing immutable `TokenEncoderOptions` schema. Linear remains the same direct per-type `nn.Linear` ModuleDict in the same live type order. Interaction adds per-type `nn.Sequential(Linear(payload_width, hidden_width), ReLU(), Linear(hidden_width, token_embed_dim))`; Linear indices are exactly0/2. The assembled descriptor and live payload jointly enter that module before pooling.
- `token_encoder_mode` and `token_encoder_hidden_width` are ordinary Python attributes on the encoder and both wrappers. They add no state tensors/buffers. Retained linear parameter names remain `encoder.encoders.<type>.weight/bias`; interaction uses `.0.weight/bias` and `.2.weight/bias` with explicit hidden-width geometry.
- NF calls existing `resolve_token_encoder(config.token_encoder)` in both `build_token_set` and `build_recurrent`, then forwards the selected mode/width through the new wrapper classmethod. Existing factory signatures, dimensions, aggregators/heads and LSTM arguments remain unchanged. OP owns versioned omission resolution; NF invents no fallback policy or width.

Static readback confirms the old linear parameter creation order remains: target assembler, row Linear modules, zero type vectors, optional attention projections, then the wrapper head or LSTM/head. Explicit pair validation and scalar attributes consume no torch RNG. No forward, presence predicate, output-side mask/count clamp, attention backend/key guard, token roster layout, zero hidden initialization or sequence reshape/LSTM/head computation was changed. The assembler is still constructed from each caller's target TokenSpec, and its separately supplied nonpersistent context/scatter ownership is untouched. These are source-preservation observations; root's pending runtime gates must independently establish actual linear byte/forward equality and new-mode behavior.

## Formatting and preserved test assertions

The only executable formatter command this worker ran was:

```text
/workspace/hamlet/.venv/bin/black src/townlet/agent/networks.py src/townlet/agent/network_factory.py tests/test_townlet/regressions/bac/test_token_binding.py
```

Exit0: one file reformatted (`test_token_binding.py`), NET/NF unchanged by Black. The test grew from633 to640 physical lines through formatting. This phase made **no test semantic edit**; no assertion, tolerance, parameter combination, fixture DATA, callable assertion, failure condition or control was weakened/removed. Its preformat R0 hash was `6ca7838f97021cfd88151b7b0b9c2ef225d9e8f9affcd8d5f8cadb866bac91f3`; its postformat hash is in the inventory below.

Full formatted-test readback retains all six named functions and34 declared cases: required explicit resolved construction; exact two-row `.375/.125` descriptor/value witness; nonuniform attention; real compiled authored reset/WAIT pooled/selected-Q witness; retained direct/explicit/omitted linear initialization/state/forward/alias controls; semantic row-plus-context permutation, target context, poisoned absence/all-empty exact-zero gradients, and deterministic zero-start/threaded recurrent memory controls. No skip, xfail or mock was added.

## Complete five-source inventory

Counts are independent `wc -l` physical newline counts; hashes are independent `sha256sum` values after edits/Black. NET/NF and the formatted owned test were read whole after authoring. Previously whole-read BC/OP retain their exact original hashes.

| Alias | Exact complete source | Access | Actual lines | Adopted projection | SHA256 |
| --- | --- | --- | ---: | ---: | --- |
| NET | `src/townlet/agent/networks.py` | modified | 655 | 750 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| NF | `src/townlet/agent/network_factory.py` | modified | 179 | 250 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| BC | `src/townlet/config/brain_config.py` | read only; unchanged | 568 | 568 | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP | `src/townlet/config/bac_options.py` | read only; unchanged | 294 | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| test | `tests/test_townlet/regressions/bac/test_token_binding.py` | Black formatting only this phase | 640 | 800 | `bdb25f6e33bae64ede392dfb8ed4fbe4b7521a6dc201184e547decaeabefe544` |
| Total | Same five complete sources | bounded | **2336** | **2662** | — |

Every file stays within its adopted projection; total2336 is below2662 and the5000 ceiling. No sixth implementation/helper/probe/test/source was opened or created.

## Custody, limitations and handback

Only NET, NF, Black formatting of the owned test, and this ignored receipt were written in this phase. No BC/OP, other source/test, tracked documentation, fixture DATA, protected artifact, index, commit, push, branch, worktree, checkout, project source copy/deletion, `.oracle`, tracker or delegation action occurred. All14 existing worktrees remain in place. Readback/count/hash/ignore checks are static custody evidence.

Apart from the explicitly authorized Black formatter, this worker ran no project runtime/import, compiler, pytest, collection, probe, linter or format-check command. No GREEN/pass, full qualification or review verdict is claimed. No unresolved issue was observed in the bounded source readback; actual numerical behavior, full-suite preservation and fresh Astra-medium review remain root-owned gates. Worker returns stationary for root GREEN and review.
