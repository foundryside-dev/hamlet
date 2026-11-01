# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-astra-core-execution-r1.md`, SHA256 `ebef961ffb57703c844a22830529a8cfa94786f4f5f924e3d44e18fb601a50ba`, retained unchanged. Portable rendering normalizes execution paths.

# T14 independent core execution R1

**Verdict: scoped core review GREEN — no concrete P1/P2/P3 finding from the complete five-source static review and this independent exact-candidate execution.** All69 existing core cases passed, job exit0. This closes the runtime-pending portion of the separate R1 core review, without changing that historical static report. Whole-BAC/full gates and native/final acceptance are not established by this run.

## Exact command and observed result

Root explicitly allocated one CPU, with all writers stationary, for candidate `324438ad58d9d5a85bba54e18be1ee225ada5969`, base HEAD `01f2f64f42c2932177729607b337419355cb2720`. The external spec and output paths were checked absent before creation; no previous output was reused.

Driver invoked from `/workspace/hamlet`:

```text
.venv/bin/python qualification/run_bac_packet_checks_locked.py qualification/wave08-astra-core-r1-spec.json
```

The spec selected workers1 and one job, producing this actual child command:

```text
.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_recurrent_per.py -q --no-cov -p no:cacheprovider -p bac_source_identity
```

Observed log: collected69; **69 passed in2.44s**, no failures/skips. Per-job result explicitly records `exit_code:0`, wall duration `6.805499076843262` seconds; outer driver also exited0. Log completed `2026-11-01T20:52:56.503807526Z`; results were inspected at `2026-11-01T20:53:00Z`. Success was assessed from the actual per-job result and full log, not merely the outer driver exit.

## Source and execution identity

The supplied root-owned locked harness was used through its declared API without reading its implementation or the plugin implementation. Its SHA was independently checked before execution: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. The root-supplied plugin identity is `0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d` (attributed, not a new source read). Harness contract verifies112 manifest hashes/tree/HEAD before and after and uses the existing metadata lock; no manual write-tree/index operation was performed here.

Per-job result records the exact candidate/base above and manifest SHA `2c60cc34fe84cccefb7041aa9ad67928c8a7184a69bb01935b59b4fba6ccb6e5`. The actual identity-controller record confirms `src/townlet/__init__.py`, worker `controller`, Torch `2.11.0+cu130`, `threads:1` and the same candidate/base. No xdist workers or extra review jobs were requested. Harness supplies one-thread numerical settings and empty CUDA visibility as declared by root.

| Evidence file under `qualification/wave08-astra-core-r1/` | SHA256 |
|---|---|
| core.log |f349222d5b6084532c4f4e5d913062aa18bc97289b722137f0b6ef5e3bc03303|
| core-result.json |194a4bfc49ccc5336c8ca23a511f693683a417f3678224517635e175d68a010f|
| core/identity-controller.json |4385079c379b3f7bd975f54c2d54eae571db405e7a7c9dd81b6fe1bf36487175|

All five reviewed source identities were independently rehashed after execution, unchanged:

| Complete source | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/sequential_replay_buffer.py |1815|f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c|
| src/townlet/training/per_sampling.py |163|0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| tests/test_townlet/regressions/bac/test_recurrent_per.py |677|941747bb722eaa2c7a33dc7fa879dc591481f29cc73cfb4d837334854c8533bb|

Inventory remains **5/3171**. Read-only cached-tree comparison and unstaged-diff checks passed after execution. R0 static review SHA remains `3d2ff1b56bd8c928db6c8581352cb3806113f4d28c0768281c762a3c29c47b7b`; R1 static review remains `828a48d75d209834daa2e498a513aa59c4efdd10af834c18eea9668e52eee579`. Neither report was edited.

## Coverage and limitations

The executed counted suite covers the actual SB→PS estimator with finite ordered/replacement expectations, both recurrent objectives/reducers and a nonconstant LSTM; multiple-L context/eviction/clear identities; duplicate and mixed-domain atomic updates; five-family RNG ownership/continuation; late sample/materialization failure atomicity; full-N, beta0, fractional and extreme support/weight behavior; readiness and absolute clocks; strict malformed restore; genuine captured6 DATA adaptation; historical/inspection/uniform preservation; factory and early configured-target refusals. No new defect or material counterexample emerged. This is independent execution of the existing reviewed regression, not a newly authored adversarial probe suite.

No HC/POP/native test/helper implementation was inspected. Root's separately reported native65, sequence-owner136, consumer118 and six-guard passes are attributed context only and are not recast as this reviewer's execution. Raw POP6/inner7 transport still differs from HC demo10/pop7 classification. Automatic authored recurrent-PER integration, T15 producer/weighted learner/vector tick wiring and X04 finite unweighted mean-TD telemetry remain required before release/G2. Whole-BAC/full gate, nativeC07, T24/T25, evolved optimizer continuation, inference/resource/RNG isolation and final acceptance remain OPEN. Any subsequently observed existing-consumer failure still requires bounded repair and review.

The cloud runtime reported current/running; no network/Docker/credential work was needed. Environment-runtime and verification-before-completion skills were applied. Writes were limited to the external JSON spec, supplied harness output and this ignored execution prose. No source/test/index mutation by reviewer, manual staging/commit, branch/worktree/source copy/deletion, new executable helper/probe or subdelegation occurred. Existing14 worktrees remain untouched. Returned stationary; runtime process is closed.
