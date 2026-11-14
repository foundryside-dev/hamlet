# R127 independent diagnostic admission probe authoring v1

Linked source verdict: r127-adversarial-source-review-v1.md (unchanged). Independent author /root/bac_diagnostic_adversarial_review. Exactly one new probe body, 149 lines; cumulative charged budget 4353 lines/five bodies. No extra producer/test body opened, APP edits, runtime execution, Git/index mutation, or executable source copy. This is new independent auxiliary test code, not copied application code.

Frozen probe: test_r127_diagnostic_independent.py SHA256 `461213cb70ce1249015b4c2dc79f11777381f4607899b36b6b34f37be78272df`.

Nodes (each parametrized owner runtime/bank and scope shared/per_world; 12 total):
- test_diagnostic_stolen_thread_binding_refuses
- test_diagnostic_thread_contender_preserves_lock_order
- test_diagnostic_actual_fork_refuses_before_owner_lock

All start with genuine begin, actual reward/service, and public runtime_failure quarantine. No private health fabrication or latch clearing. Read-only latch assertions qualify continued truthful failure and absence of new completion uncertainty. The active parent and binding are genuine registered Controller invocations. Wrong-thread stolen binding must fail before native work, with same-owner actual diagnostic successes during and after retained custody. Public standalone cross-thread new-method contender must WAIT before owner-lock acquisition until parent custody ends, then succeed without worsening state. This distinction preserves existing test_runtime_contender_does_not_take_lock_before_domain contract; no invented cross-thread public-entry refusal.

Actual os.fork child invokes the public diagnostic while inheriting an active parent scope. A child-local trap owner mutex must never run; public PID guard must raise RuntimeError and report via pipe within five seconds. Child uses os._exit and parent reaps it. Parent valid diagnostic still succeeds during and after scope. Actual fork skip is explicit only when os.fork unavailable; skip cannot count as witnessed PID coverage.

UNEXECUTED. Root must grant/capture exact auxiliary probe bytes with before/after SHA256, matching R127 manifest/tree, source identity guard, exact node ids and fresh actual result. This file does not claim acceptance or execution. Existing broader gates remain open.
