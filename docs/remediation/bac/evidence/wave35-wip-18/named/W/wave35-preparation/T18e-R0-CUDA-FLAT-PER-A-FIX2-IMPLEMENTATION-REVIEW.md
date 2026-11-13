# Packet A FIX2 implementation review — R98

**SPEC / QUALITY verdict: CHANGES REQUIRED.** FIX2 correctly repairs the two selected I5 witnesses and both assignment-type errors. It does not yet satisfy I5's branch-planning requirement: the same metadata-determinable refusal class remains in the two existing planner families. This is not approval of packet A or of downstream CUDA execution.

## Immutable scope

Root candidate tree `abb7f417b8098b139db3d5156f4c320b21ab8f6d`; supplied manifest `02adec84e69868cdcf6e065d9d02f9736cb17c0c13d1450f2fed0ac43b622fe1`. Exact combined R96→R98 diff `T18e-R0-CUDA-FLAT-PER-A-FIX2-R98.diff`, personally hash-checked as `553068961fb793f42c53c5158eb4ed65f15d18d7b2592a142167a181dac43dfd`. Author report's FIX2 freeze section was read; supplied report seal `b0061fb833b43e1c5c29559f7b2a03c6eb2c63b353c1d7438874ad4342593a4f` may receive root evidence appendices.

Four retained bodies, 4424 lines within the 4660 grant and hard 5/5000 ceiling; personally checked SHA-256 values:

| File | Lines | SHA-256 |
|---|---:|---|
| replay_contract.py |689|`6bf839271ed030ba7787dca24cd9305dfef4d8ae382b67b300906b66ca495265`|
| replay_buffer.py |807|`752f9690da797edd4acbdda04e2a85e60aa6c19875cb8eb6956de3805e657270`|
| prioritized_replay_buffer.py |1260|`225bb6582a6d53bac3ce6ab5bed3e481a26fe3e904e272af14b9657d2746ca4c`|
| test_replay_cuda_producer.py |1668|`e005667a8ad82db97aacc4882812e44b09947fa26fdf97b45d4cf6057abbd8b7`|

Review used only the authorized bodies/delta and prose. No runtime, imports, Git, additional bodies, delegation, or source/test edits. Prior FIX1 review is preserved.

## Correct repairs and test quality

Raw transport planning now excludes ordinary input/live/archive sources on the exact supported-version, exact-schema, expected-plain-kind, unequal-plain-integer-capacity branch. The actual validator still emits the original error. The plain push/no-vocabulary malformed-observations branch now has an empty prefix; recorded push retains dones/masks, and known-vocabulary plain push retains dones. These changes preserve the genuine pre-observation mask work in the latter branches.

The new tests observe real metadata planning and retain actual public calls, unchanged-state checks and no-CUDA sentinels. The plain-push control also checks mutation revision. Necessary-prefix controls distinguish pure-plan observations from B-dependent public completion assertions. The installed-archive control uses genuine installation and remains B-blocked; it does not fabricate installed ownership. Changing the public device selector on a CPU-constructed owner is intentional in these controls and tests target laziness as well as source exclusion.

Explicit `effective: torch.device | None` annotations in both operation methods correctly accommodate both branches without ignores, API shims, or behavior changes. Root's owned-three mypy evidence confirms the two A errors are gone; only the absent B invocation API remains.

## I5 remains open: one finite causal class, two planner families

The normative requirement is to exclude targets and sources known to be unused from ordinary metadata and the real validation order. It is not merely to recognize the literal examples in the previous review. It does not require predicting data-dependent validation outcomes by running Tensor operations during planning. No such speculative requirement is introduced here.

### Raw validation/preparation

At flat inventory lines 180–188 and PER 240–248, FIX2 adds one exact capacity predicate, then otherwise falls back to the whole input (and preparation's retained/archive inventory). Actual validators have additional ordinary metadata refusals before any row or archive work.

Concrete examples, valid version/key set and otherwise ordinary scalar metadata, with an unused CUDA observations value:

* Wrong plain-string `replay_kind`: flat rejects kind before capacity; PER rejects kind before key-set checking. Neither touches observations. The new predicate requires the correct kind, so it falls through to full inventory. Preparation may also select a CUDA target for otherwise valid capacity/count.
* Correct kind but boolean capacity: both `_require_int` implementations reject bool before row/archive work. Their repr of an ordinary bool is CPU-only. The new exact-int predicate is false, so unused CUDA observations is still inventoried. Target suppression alone does not fix that source enrollment.

These witnesses use no prepared handles and no installed GPU state. They remain within the same raw-input early-refusal route as I5. Both source inventory and target selection must follow the validator prefix; supported scalar types, error order, and existing diagnostics must be preserved. In particular Tensor-valued diagnostic fields may need protected comparison/representation and cannot be treated like the ordinary bool/string examples. The accepted conservative issuer-held-candidate rule remains separate.

### Push metadata prefix

Shared `_push_inventory` checks only observations metadata/capacity before selecting the destination and all input/retained values. Both actual `_validate_push` bodies have further metadata-only checks before their first Tensor reduction.

Concrete paired-family witness: plain push, `action_dim is None`, valid nonempty float32 observations, CPU `next_observations` with invalid rank/dtype, otherwise valid CPU arguments except unused CUDA dones, and an unused CUDA destination selector. Flat rejects next-observation shape/dtype; PER rejects next-observation rank/dtype. Both do so before reading dones or executing action/nonfinite reductions. The planner instead takes the nonempty-observations branch, selecting the destination and inventorying dones. Thus FIX2's observation-only shortcut is insufficient.

Recorded/known-vocabulary paths require their real mask prefix even if later metadata fails. A malformed recorded mask can itself be rejected by the public rank/type guard before successor validation, so route identity alone is not proof that the entire mask/dones prefix executes. The repair should model these actual prefix boundaries, not indiscriminately empty or retain all route arguments.

This is existing I5 incompleteness, not an unrelated scan or a newly imposed API policy. No separate new production defect is established in the small FIX2 edits themselves.

## Bounded corrective and verification obligations

Replace the two planners' enumerated example shortcuts with a finite account of each producer's ordinary metadata validation prefix up to its first genuine Tensor/copy/allocation effect. Account for raw version/kind/schema/scalar configuration checks in their actual family-specific order, and push entry-mask plus transition shape/dtype/capacity checks in their actual order. Return only the prefix's real sources and select a destination only on a branch that can reach destination work. Do not run comparisons/repr/reductions on malformed Tensor fields during metadata planning. Keep diagnostic-source inventory, clone-before-refusal coverage, and issuer-held material coverage intact.

Supply a bounded branch matrix for those two planner families, with representative controls for each distinct metadata-refusal class and paired positive first-effect boundaries. The matrix should explain where metadata prediction stops and protected data-dependent validation begins; avoid adding one equality exception per reported example. The concrete wrong-kind, bool-capacity, and next-observation witnesses above can be tested on real CPU owners with unused simulated CUDA sources and sentinels, without B authority fabrication. Preserve original public errors/state and mutation behavior. Actual public admitted preparation, installed archive processing, and genuine GPU prefix completion remain B-dependent.

## Attributed evidence and remaining gates

Root reports R97 six intended metadata RED and four necessary-prefix plan controls PASS before repair. On frozen R98: 129 collected; owned-four Ruff/Black and unchanged defaults600 PASS; reachable24 PASS, zero skips/warnings (prior16, public capacity-validation2, public plain-push2, necessary-prefix plan4). Root reports all custody verified. Runtime log SHA-256 `4a5bd6b601995ed326e1c8a66d2cb934a1038898b7e2072febc8cf9e1ba90d29`. Owned-three mypy now fails only on known missing B `device_invocation`, shared line313. These are root results, not independently executed here.

The passing controls establish the selected repairs, not the untested metadata-prefix classes above. Prior source dispositions for I1–I4/I6 remain staged; I7's two A type regressions are repaired. I5 is not closed.

The existing ten-producer-child verifier extension is already independently qualified according to root (58 synthetic and seven mutation controls); this review does not reopen that completed tool gate. Actual child execution/verification, B constants/policy/invocation outcomes, future core-outcome protocol extension, parent outer-failure ownership, and hardware qualification remain owed. No production or whole-program acceptance is implied.
