# Episode-lane planning probes — 2026-10-02

Source: `fix/episode-lane-accounting@ec463fdaaa632e4e1f778b938ace94f53a73a745`.
All runtime/test/config source equals merged main `95b2f828`. These are executed
parent defects and prerequisite feasibility, **not corrected-candidate acceptance**.
No runtime code was changed. Scripts are archived byte-for-byte beside this receipt
as `.py.txt`; raw outputs/artifacts remain in ignored
`runs/episode-lanes/2026-10-02/planning/`. Earlier discovery receipts remain unchanged.

| Witness | Executed result | Limit |
| --- | --- | --- |
| Authored lifecycle | Real compiler, shipped compiled feedforward brain `[256,128]`, END_LANE action at ticks 2/5; reset energy `[1,1]`, deaths `[2,5]`, seven eligible rows/five ticks, reported `[5,5]` | Scripted action selector; no meter injection; gradients suppressed |
| Pinned oracle | Actual import from oracle `4222a9176e68e232a0e46c7004183440e27f22c3`; deaths `[2,5]`, survival `[5,5]`; lifespan-5 tick-5 rewards `[1,1]` | Controlled initial energy injection; second case overrides runtime lifespan, not config bytes; no new standing full matrix |
| Real gradients | Standard/PER each five Q updates/one predictor update; recurrent 23 Q/11 predictor updates; both parameter sets change | Existing defective parent, no actual target-value assertions; brain DTO unit fixtures rather than authored compiled-brain qualification |
| Identifiable samples | Seq1 recurrent Q consumes 15 phantom rows/46; predictor 23/77. Standard/PER predictor consumes two phantom rows/seven | Original sampler and real predictor hooks, no ambiguous row identities; seq2 hides one-step ghosts from Q sampling |
| Two episodes, runner/sinks | Correct live budget14; DB slot0 survival5 both; TB `[5,5]` both; curriculum once/batch `[5,5]`; slot0 recording five rows `[F,T,T,T,T]`; baseline curves claim20 | Learning suppressed; actual DB/events/LZ4 files queried |
| Budget6, runner/sinks | Four vector ticks/six live transitions; true `[2,4]`; DB/TB/curriculum publish4; recording four slot0 rows; baseline curves claim8 | Checkpoint-backed regression transition counter remains truthful6 |
| Final outcome alias | Early terminal health `.9900000095`, later published `.9750000238` | Executed CPU `detach().cpu()` alias; snapshot needs clone |
| Existing prerequisite tests | 20 passed, one skipped, 58.42s, exit0 | Existing skip: stochastic affordance interaction test; no fresh full suite/convergence |

## Commands and fixture custody

Executed from the primary worktree using its own `.venv`; actual imports were
verified. Authored probe copies shipped `configs/default_curriculum` to a temporary
pack, appends all required END_LANE write fields and enables it at L0_0_minimal.
The oracle probe uses the untouched frozen pack and its actual source in a
separate interpreter; all 33 frozen input files remained byte-identical and both
Git roots stayed clean. Initial energies `.015/.045` are a controlled runtime
fixture. In its second case only `env.agent_lifespan` changes 1000→5. This placement
differs from the original main probe's temporary YAML override; effective lifespan
is identical, and the difference is disclosed rather than called byte parity.

```bash
.venv/bin/python runs/episode-lanes/2026-10-02/planning/authored-lanes-probe.py
PYTHONPATH=/home/john/hamlet/.oracle/oracle-2026-08-17/src \
  .venv/bin/python -P runs/episode-lanes/2026-10-02/planning/oracle-lanes-probe.py
.venv/bin/python /tmp/episode-lane-gradient-setup.py 1
.venv/bin/python /tmp/episode-lane-gradient-setup.py 2
.venv/bin/python runs/episode-lanes/2026-10-02/planning/runner-sinks/probe.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/pytest --no-cov -q \
  tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py \
  tests/test_townlet/integration/test_recurrent_bptt_runtime.py \
  tests/test_townlet/integration/test_runner_integration.py
```

Gradient script was run under `/tmp`, then copied to `planning/gradient-setup.py`;
its two original logs were copied as `gradient-seq1.log`/`gradient-seq2.log`.
The runner script/results retain temporary execution paths; `runner-sinks/receipt.json`
maps them to retained copies, including databases, events, recordings, checkpoints
and temporary authored packs. This is a nine-MB ignored evidence bank, not shipped
data. Do not delete or reinterpret it.

The runner probe explicitly waited for the real recording writer to persist its
queued final marker before ordinary cleanup, isolating the known shutdown/drain
seam. It did not replace the writer. Its results qualify accounting of persisted
rows, **not ordinary shutdown durability**. Candidate acceptance must prove the
ordinary persisted artifact exists; a sleep in a test cannot repair the product.
If the seam blocks acceptance, record the failure and amend package scope first.

## SHA256 custody

| Archived source / raw output | SHA256 |
| --- | --- |
| authored-lanes-probe.py.txt | `85af8397c9ff3937ebc6df15df612a686092cea99597e1323e805f993fcbe74e` |
| authored-lanes-probe.log | `d4fa0b7060a53619a3ea73a584fb2856dc5a329530531030bc58bc1d9b49cb3a` |
| oracle-lanes-probe.py.txt | `dd09937a41690cb0710f02f6031ead389c3a291aabac1a511461acf88bc4addd` |
| oracle-lanes-probe.log | `ba9ab2526e4bef2a9ebc8c5f2a09d9e217a72b1bf9b0fcebc18165308a1c9fba` |
| gradient-setup.py.txt | `0197aa041305ac2a2ccfe3797ca98157a0cbfefed570d1024fcf51cede0f1b93` |
| gradient-seq1.log | `f532658a3868d86146b4e5d41bb58f74a870d9ee7eb211bc942cf4b58657a586` |
| gradient-seq2.log | `34fdd8d6e5bb19e71b80abdc74dcfdfbfd626bb741dec769d35f2cc8985ab055` |
| runner-sinks-probe.py.txt | `c2aebf28b534ed171ae2164950aa2e6bb29200a1ede5607bff4f5e1e7a8912a2` |
| runner-sinks/result.json | `f61649546e2c6bee151f86214f35928adc566e50e0189b2525ba24dc1db424f1` |
| prerequisites.log | `7e0d57ce3d73380667992b1e78edd5db1793944dcb549c8aff599a78a7b870dd` |

## Planning decisions supported by probes

Normal runner cap equals the environment retirement lifespan; it cannot alone
qualify a pure cap truncation. Budget6 genuinely cuts the surviving lane. An
explicit lower caller cap must be tested separately. Actual recurrent updates
on the corrected candidate need nine 2/5 episodes: the eighth reaches sixteen
genuine stored sequences only after its final update check. Parent eight-episode
updates benefited from ghosts and cannot set the corrected warmup claim.

The oracle's format4 observes only observations/rewards/dones/actions and identity
hashes. It cannot observe survival/replay/RND/completion/sinks, and its 100-tick
standing cells miss the configured 1000-tick retirement boundary. Controlled
lifecycle comparisons and independently counted samples/sinks supplement it.
No new divergence was registered or accepted during planning; PDR-0058's exit
review remains separately open.
