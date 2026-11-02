# T19 entropy API handoff — finite static supplier receipt

This closes the bounded controller DATA/API inspection for upcoming `LaneOutcome.policy_entropy`. It authorizes no implementation, T20 design, or new planning/review loop. Root remains sole integration owner; T17 source authoring remains active as supplied by root.

Whole-file source reads were limited to the three paths declared in `T19-entropy-source-baseline.json`. Imported implementation/helper/test sources were not opened. `T19-task-brief.md` and `T19-interface-readiness.md` were read as prose suppliers only; their linked sources were not followed. Source identity was checked with SHA-256 and line counts, matching the baseline:

| Path relative to `/workspace/hamlet` | Lines | SHA-256 |
| --- | ---: | --- |
| `src/townlet/curriculum/base.py` | 86 | `04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26` |
| `src/townlet/curriculum/adversarial.py` | 565 | `8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b` |
| `src/townlet/curriculum/static.py` | 143 | `4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be` |

Total source inspection: 794 lines. All source citations below refer to these pinned files unless explicitly attributed to readiness prose.

## Existing exact entropy calculation

`AdversarialCurriculum._calculate_action_entropy(self, q_values: torch.Tensor) -> torch.Tensor` exists at adversarial.py:428–451. Its documented input is `[batch_size, num_actions]` and result is one value per batch row. Exact operations at 440–451 are:

```text
p = torch.softmax(q_values, dim=-1)                         # temperature 1
h = -torch.sum(p * torch.log(p + 1e-10), dim=-1)
a = torch.tensor(q_values.shape[-1], dtype=torch.float32,
                 device=q_values.device)
result = h / torch.log(a)
```

The numerator uses natural logarithms with epsilon inside the log, without probability renormalization after epsilon. Normalization uses the actual last-dimension width, not a hardcoded action count, number of legal actions, or batch mean. Comments mention six actions; the code uses the supplied width. There is no temperature parameter, epsilon-greedy mixing, sampled-action entropy, cross-lane reduction, final clamp, detach, CPU conversion, or `.item()` inside this helper. Device follows the input; the normalizer is explicitly float32 and the output dtype follows the shown tensor operations, with no promised output-dtype conversion.

There is **no legality/action mask input or extraction**, no eligible/completed-lane mask, and no mask inferred from `agent_states` in this calculation or its caller (294–384). Every supplied action column participates as presented. Caller-preprocessed Q-values may affect the result, but this inventory cannot certify any upstream masking. There is no explicit shape/rank, row-count, finite-value or width validation. Width 1 divides by `log(1)=0`; no finite-result guarantee or one-action fallback exists. The epsilon and absence of a clamp mean the implementation does not enforce a strict mathematical [0,1] interval despite its normalization comment. These are static limits, not executed numerical witnesses.

## Actual usable interfaces and exposure limits

```python
# CurriculumManager, base.py:22–35
initialize_population(self, num_agents: int) -> None
get_batch_decisions(self, agent_states: BatchedAgentState,
                    agent_ids: list[str]) -> list[CurriculumDecision]

# AdversarialCurriculum, adversarial.py:222–225,294–299,412–428
initialize_population(self, num_agents: int)  # no return annotation
get_batch_decisions_with_qvalues(self, agent_states: BatchedAgentState,
    agent_ids: list[str], q_values: torch.Tensor) -> list[CurriculumDecision]
get_batch_decisions(self, agent_states: BatchedAgentState,
    agent_ids: list[str]) -> list[CurriculumDecision]
_calculate_action_entropy(self, q_values: torch.Tensor) -> torch.Tensor

# StaticCurriculum, static.py:53–63
initialize_population(self, num_agents: int) -> None
get_batch_decisions(self, agent_states: BatchedAgentState,
                    agent_ids: list[str]) -> list[CurriculumDecision]

# Existing tracker mutation hooks
# PerformanceTracker, adversarial.py:85
update_step(self, rewards: torch.Tensor, dones: torch.Tensor)  # no return annotation
# _StaticTracker, static.py:141
update_step(self, rewards: torch.Tensor, dones: torch.Tensor) -> None
```

The Q-taking method is a public adversarial-specific extension, absent from the base and static implementations. It requires initialized tracking and raises otherwise (304–306). It calculates entropy for the supplied tensor once (308–309), then reads `entropies[i].item()` in `enumerate(agent_ids)` order (315–318). It supplies that lane's entropy to advancement checks (331); retreat has priority (321–338). It returns only decisions (371–384), whose construction passes difficulty, active meters, depletion multiplier, reward mode and reason, with **no entropy field argument**. The imported DTO implementation was not inspected, so no wider DTO schema is claimed.

The existing private helper can compute the identical row signal from Q-values, but it is not a public entropy accessor contract. The public Q-taking method does not return entropies. Calling it solely to retrieve entropy is not read-only: it may change stages, dwell counters, episode counters and reward baselines and append transition events (321–354). `_record_transition_event` stores the lane entropy only when a stage transition occurs (344–354,386–410); `transition_events` is mutable history cleared by initialization (155–156,222–225), not a per-lane completion record. `get_stage_info(self, agent_idx: int = 0) -> dict` (523–565) returns stage, episodes, last survival and likely-transition flag, with no entropy. Tracker fields and checkpoint fields contain no entropy (74–83,455–477).

The no-Q adversarial fallback does **not** calculate exactly zero despite its docstring: it fabricates five Q columns with action 0 set to 10 and others 0, then delegates to the same calculation (412–426). That is a small positive entropy for the fabricated distribution, not measured policy entropy. Static curriculum ignores state and returns one shared decision object repeated in a list (static.py:59–83); it computes, retains and exposes no entropy. Base.py:1–86 declares no entropy method or completion hook.

## Timing: current-Q lane signal versus completed envelope

Inside adversarial.py the signal belongs to each invocation's supplied Q-values; `agent_states` is not used in the Q-taking method. There is no observation evaluation, post-transition recomputation, episode accumulation, last-eligible cache, final-entropy snapshot, external-cut rule, reset retention rule, or completed-envelope publication anywhere in these three whole files. No `LaneOutcome`, `completed_outcomes`, `begin_batch_episode`, or `commit_episode_outcomes` implementation exists in this inspected inventory.

The readiness prose's final finite POP clarification attributes the production call timing to POP: current predecessor Q-values at POP:1230; Q-taking curriculum call at 1245–1251 before action selection and ENV physics; current decisions retained afterward. This is **attributed prose evidence**, not a new POP read. Combining it with the inspected formula establishes the current per-lane pre-physics controller signal. It does not establish a completed-episode aggregate or final-successor entropy.

The task brief's P5 `LaneOutcome(..., policy_entropy: float)` and P6 retained completion entropy are requested interfaces, not existing controller APIs. Thus the formula/normalization/mask absence is now supplied exactly; the choice of which owned eligible invocation is frozen into a completion, and behavior at an external cut, remain unspecified by existing code. No mean, zero/static fallback, successor-Q recomputation or final-versus-aggregate convention is invented here. No T20 behavior is designed by this receipt.

## Completion and adaptive callback ownership

Direct inspection: `PerformanceTracker.update_step` updates all supplied lanes' episode sums, episode steps and stage dwell, then uses `dones` for baseline capture, last-survival capture, episode counts and reset (adversarial.py:85–108). Its comment states that the argument named rewards actually receives survival step counts. Last-survival capture divides that input by 100 (100–101); `get_survival_rate(max_steps)` instead uses current `episode_steps / max_steps` (110–112). These are current tracker semantics; this receipt does not reinterpret them as completed P6 survival fractions or add a callback. Static tracker update is a no-op (static.py:134–143). No adaptive intrinsic call, death callback, completion DTO consumer, event identity or completion deduplication is implemented in any of these three files.

Attributed readiness prose reports the existing owner: POP `_finalize_episode(self, agent_idx: int, reason: CompletionReason) -> EpisodeCompletion | None` at POP:1114 is the guarded, nonempty/not-already-completed route; it snapshots completion data and calls adaptive completion once. Public `flush_episode(..., reason: RunnerCompletionReason)` at POP:1139 delegates to it, and terminal/retirement completion uses the same route. Later calls return None until reset. Its implementation and the adaptive callee/signature were outside this inventory and were not independently inspected. The brief explicitly requires preserving current adaptive once-only completion calls and says the outcome-commit API adds no second death route. Publishing entropy/envelopes therefore supplies data to that existing owner; this handoff authorizes no second adaptive callback or controller-completion route.

Only this ignored handoff was written. No project runtime/import/compiler/test/collection/lint, source edit, index/staging/commit/push, branch/worktree/checkout action, source copy, deletion or subdelegation occurred. Existing fourteen worktrees were left untouched. Static receipt only; no test pass or repository-green claim. Stationary.
