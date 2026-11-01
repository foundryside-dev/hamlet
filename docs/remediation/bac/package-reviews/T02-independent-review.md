# T02 repaired candidate — fresh independent bounded review

Verdict: **specification PASS; implementation quality APPROVE with one nonblocking P3 coverage gap**. No P1/P2 defect found. Approval is scoped to T02 declarations/resolution/transport and its repaired schema expectation; the coordinator-owned full gate remains mandatory before commit/release. This is not whole-BAC readiness or runtime-mode qualification.

## Immutable identity and bounded inspection

Reviewed snapshot `/tmp/bac-verify-T02-r1-94de8d44e8`, base HEAD `5c91dfb9d09b8ba2d422c6fef5c3e468eadfebaf`, staged tree `94de8d44e8c1f3c7da48f4ffe986440946058c06`. Before tests and again after the test run, checked HEAD, `git diff --cached --exit-code <candidate-tree>`, clean tracked working tree, all five candidate source SHA256 values and 1545 total lines. Frozen plan SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1` and execution addendum SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370` matched before/after. Exact hashes are in `task-T02-r1-candidate.json`.

Complete source assessment: brain_config.py568, training_v2_config.py443, bac_options.py243, test_options.py219, test_recurrent_token_qnetwork.py72. Exactly five implementation/test files; no sixth implementation/test/helper/probe source read or authored. Reviewed extracted task-T02.md requirements, repaired receipt, review package, options.md and relevant positive fixture YAML. Did not read the whole plan or rely on the previous review's verdict. No edits to candidate, git mutation, delegation, installs or network access. The only authored artifact is this ignored review report; additional contrasts were inline CLI commands operating on temporary YAML copies.

## Specification assessment

The new option models are strict, finite-only, immutable and additive. None denotes omission; unknown keys, bad literals, wrong strict types and invalid ranges reject. Nested declarations remain immutable; provenance is an immutable tuple of immutable entries and serializes. The central v1 resolution table matches the extracted old-document policy, including legacy uniform sequence sampling, paced bounded-service upgrade, completion/stage-band, greedy evaluation and initial/final save policy. Explicit values change their leaf; documented ICM dependencies follow resolved feature/batch overrides.

TokenEncoderOptions is declared in OP with exactly mode/hidden_width and reexported by BC. Linear rejects a width, interaction requires a positive explicit width, both token families have nullable additive fields, and encoder selection is independent of mean/attention. Existing required training fields, presets, optimizer/loss/family alternatives, zero widths and five overrides remain intact; production diffs do not change replacement/override logic. Four complete YAML packs exercise real compile/cache/rename paths. Documentation truthfully distinguishes authored transport from T03 effective receipts, T18a provider precedence, T17 encoders and T27 serving.

The fifth-file repair is exactly the addition of token_encoder to the existing exact-field set at test_recurrent_token_qnetwork.py24. It preserves strict exclusion of any additional field; forward, single-layer-dropout and rank checks are unchanged. The obsolete four-field expectation contradicted the approved additive interface; updating it does not conceal a production regression.

## Independent execution

Used `/workspace/hamlet/.venv/bin/python`, snapshot PYTHONPATH, empty CUDA_VISIBLE_DEVICES, OMP_NUM_THREADS=1, MKL_NUM_THREADS=1 and torch.set_num_threads(1); asserted actual townlet import resolves to snapshot. One test process, no xdist.

`pytest --no-cov -p no:cacheprovider` selected repaired recurrent module, test_options.py, test_numerics.py, test_brain_config.py, test_loss_factory.py, test_network_factory.py, test_optimizer_factory.py and test_training_v2_config_dto.py: **144 passed, 2 expected zero-width tensor warnings in127.12s** (5 +35 +104).

Fresh independent inline CLI contrast copied token_set and recurrent packs, changed only copied YAML, and compiled token_set attention+linear and recurrent mean+interaction_mlp(hidden_width17). Both asserted exact encoder AND aggregator preservation through compile, to_dict/from_dict, msgpack save/load, and brain/training transport-only rename/recompile. Both passed. These complement the permanent test's original family combinations. No existing external probe source was opened or executed.

## Nonblocking finding

**P3 — Permanently assert compiled encoder transport**, `tests/test_townlet/regressions/bac/test_options.py:90`. Trigger: the family round-trip test verifies authored training options and selected family, but its restored/cache/renamed assertions do not check the compiled token_encoder. A future compiler encoder-dropping regression could pass that test while failing the intended transport contract. Add explicit token-family encoder equality after initial compile, dict restore, cache restore and renamed compile when test maintenance is scheduled. This is a regression-coverage gap, not a present transport defect: this review's fresh compiler contrast passed both token families through those boundaries. It does not block T02 scoped approval.

## Declined judgments and limits

No blocker inferred from later runtime wiring being absent: T02 is explicitly schema/transport, and options.md qualifies its scope. Did not treat old DTO-hash changes as an unreported semantic redefinition; they are disclosed, trigger the full gate and have T03a adaptation ownership. Did not classify preservation of inactive/unqualified fields as operational support or as forbidden content. No capability reduction found in this bounded package.

Did not rerun the full suite, coverage, hardware checks or standing repository guards; these remain coordinator-owned. The earlier interrupted full campaign is not green evidence. No claim about unseen compiler/runtime implementation internals, provider dispatch, learned competence, historical migration, integrated BAC acceptance or release readiness.
