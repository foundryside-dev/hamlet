# T17 independent R1 runtime receipt

2026-11-02; existing `/workspace/hamlet`. Root explicitly cleared the previously independently selected12 owned test nodes against candidate tree `5d4685b55ccd85879d0627bb55bbc20277c58af4`, base `a0802a442bc7ea529de650b8705629923a0e6c72`.

**Actual outcome:12 passed, no failed/skipped tests, pytest14.95s; job wall22.76939368247986s, job exit0.** The outer wrapper also closed normally with exit0 (session41827). I read the actual `independent-result.json`, complete pytest log, and all three identity JSON records; the verdict is not inferred solely from outer exit status. The log records two workers/12 items and twelve passing dots. Its only warnings state that pytest-benchmark disables benchmarks under xdist; no selected benchmark or test is skipped.

Only the sanctioned runtime command was executed, from `/workspace/hamlet`:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave11-r1-independent-spec.json
```

The supplied DATA spec and returned result list exactly the12 nodes proposed in `T17-independent-review-r1.md`, with `/workspace/hamlet/.venv/bin/python -m pytest`, `--no-cov -p no:cacheprovider -p bac_source_identity -q -n 2 --dist worksteal`, and unique `--basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave11-r1-independent`. The spec's outer `workers:1` schedules one job; pytest itself used two xdist workers as authorized. No wrapper/plugin implementation was opened; its control semantics are supplied by root's source-verified tool contract.

## Evidence and identity

All evidence paths below are under `/workspace/bac-review-2026-11-01/qualification/wave11-r1-independent/`:

| Artifact | Independently computed SHA256 |
| --- | --- |
| `independent-result.json` | `d7e5f238bd6ab94a9ef4a2943e17cb594969fef340eb950393bd498e68ac3acd` |
| `independent.log` | `f1c20324f760aeb40473b6965b2b78bf715e7f5f15ce4ee848fdabafbbba1077` |
| `independent/identity-controller.json` | `6488eaa70f1268b4c8d47c7c6008b71a4f7273a6ba9511bcf0880a7f056cf109` |
| `independent/identity-gw0.json` | `f17f5e1d65f3b411c2bfafb775755802a1c9e82384eb889b10984079725ea89a` |
| `independent/identity-gw1.json` | `19e6cf05c1cc4ca7b0776a2dc8db28edb15b06156bb309c6a07e60459e9ff449` |

Controller/gw0/gw1 each report base `a0802a442bc7ea529de650b8705629923a0e6c72`, candidate tree `5d4685b55ccd85879d0627bb55bbc20277c58af4`, module `/workspace/hamlet/src/townlet/__init__.py`, Torch `2.11.0+cu130`, and `threads:1`; their worker labels are controller, gw0, gw1 respectively. The result metadata reports manifest SHA256 `f73646500ff6c97978847948b10738863fc3f1a959599bedd4499c51f88f0101` and harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. These last two are tool-reported identities, not a claim that their implementations were inspected.

Fresh independent post-run hashes for the same five sources match the frozen R1 inventory:

| Source | SHA256 |
| --- | --- |
| NET `src/townlet/agent/networks.py` | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| NF `src/townlet/agent/network_factory.py` | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| BC `src/townlet/config/brain_config.py` | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP `src/townlet/config/bac_options.py` | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| owned `tests/test_townlet/regressions/bac/test_token_binding.py` | `bdb25f6e33bae64ede392dfb8ed4fbe4b7521a6dc201184e547decaeabefe544` |

## Interpretation and custody

The selected invalid-selection, exact mean binding, authored selected-Q, nonuniform attention, route equivalence, semantic context permutation, poisoned absence/all-empty gradients and recurrent history controls now have my own actual passing execution evidence. The static report's historical-baseline limitation remains. The separate root-reported constructor-hook consumer failure is not tested or resolved by this selection; its bounded owner audit and cadence decision remain separate. This receipt claims neither package release nor repository/BaC qualification.

Only the new ignored receipt was manually written; its ignore status was checked before writing. Runtime artifacts were produced by the authorized existing harness. No sixth implementation/helper/probe/test, new test node, source/index/tracked-document change, branch/worktree, project source copy/deletion or subdelegation was introduced. No additional runtime was run. Root independently owns broader custody verification. Stationary after normal wrapper closure.
