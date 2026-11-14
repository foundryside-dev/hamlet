# Independent P4 frozen-v2 review

Disposition: **changes requested before root adoption**. The two original blockers and the supplier-confirmed completion correspondence repair pass fresh tests. One additional replacement-ancestry substitution still satisfies common custody.

Exact target: freeze-v2 SHA256 `5e395cfa90cc4620a53358628d69c2e731cb0f70a3cd84be6513e6ddf359cdce`; verifier `708f4f39b41639a56dbe90a62083f434e3ea1fe909de75342a38a2b11c92d5f4`; tests `dc4cc904d81e31a22a7d0e616b8c6ecafc36958356fcc84134737895f895a79b`. Both execution attempts verify freeze/source/snapshot bytes and every interface metadata dependency, including supplier capsule `0d2da3b50402cd7bcc281e39b10a08ffd932070aac635ff5747fc75af8f6c925`. No supplier body beyond the existing packet was inspected/imported.

## Remaining blocker

**Medium: an external failed-down record can substitute for the actual inventoried predecessor down.** In `_lifecycles`, verifier lines 598–619 load replacement configure.prior_lifecycle and check selected fields but never require that reference to be the exact unique inventoried down already associated with predecessor_start. The earlier down selection checks the actual predecessor record independently. The `consumed` set also keys the supplied prior reference rather than the actual predecessor/down identity.

Retained probe `replacement-external-down` starts with a valid one-worker replacement. It saves a copy of predecessor's failed-down JSON outside job output, changes the actual inventoried predecessor down to normal shutdown (`error=""`), and points replacement configure.prior_lifecycle to the external failed copy. All observation/reference DAGs and sealed inventories are coherently refreshed. The actual predecessor lifecycle is normal, but the external copy grants replacement ancestry. Result: **custody=satisfied, test_outcome=successful, hardware=unrun**, with all common obligations satisfied.

Bind each replacement prior_lifecycle to the exact unique inventoried down for its predecessor, and consume that predecessor/down identity once. Reuse the already validated lifecycle records instead of accepting another structurally plausible record. This is the specifically promised accepted failed-down ancestry rule, not a new demand for general producer inventory closure. Add a coherent regression for normal inventoried down plus external failed-down substitution; also consider two differently referenced copies claiming the same predecessor. Existing valid fresh-gateway and same-gateway replacements must remain accepted.

## Verified repairs and controls

The author suite ran once: **86 passed in 17.26s**, PID195493, CPU affinity `[3]`, exit0. Twenty-one independent probes then completed in the same process:

- Controller after-wait and worker before-controller monotonic observations refuse; post-Popen late parent sampling remains valid.
- Foreign worker run UID, inconsistent mainargv, duplicate initial workerid, unrelated gateway reuse and overlapping replacement refuse.
- Valid replacement with a fresh gateway and valid reuse of its own predecessor gateway both satisfy common custody.
- Completion source omission and ordering changes refuse. Empty source arrays refuse. Missing raw provenance in completion.inventory refuses.
- A minimal completion.inventory containing process raw provenance plus an external inert reference is accepted while final result inventory remains complete. This is correct under the supplier's explicit distinction; universal inventory equality/subset was not imposed.
- Unknown validator ID/source substitutions refuse. Missing inventory remains unsatisfied; missing end remains completed-unverified/unsatisfied. Required P5 keeps the conservative aggregate unsatisfied, with hardware unrun.

Static review of the bounded existing code confirms finite direct p4-common-v1 dispatch, exact source/protocol pins, schema parsing, report membership and phase checks, source/grant bindings, and conservative P0 aggregation remain intact. Synthetic exact-spec inventories remain test data, never root authority.

## Retention and scope

This directory retains `execution.json`, `suite.json`, `suite.log`, `probes.json`, `probe.py.txt`, all 86-case fixtures and all 21 probe fixtures. After the new ancestry concern arose, an **ancestry-only** process PID195936 ran on CPU3; the suite was not repeated. Its exact source, argv/PID/PPID/UTC/exit0, single probe and resulting satisfied receipt are retained in sibling `independent-astra-v2-ancestry/`. Its suite.json has null exit because pytest was deliberately not invoked; the actual execution.json carries exit0.

The existing independent-astra-v1/probe.py body was updated in place, as authorized, rather than adding a sixth source body. Every executed version was retained before its next update: original 88-line bytes in independent-astra-v1/probe.py.txt, v2 suite/probe bytes in this directory's probe.py.txt, latest 114-line ancestry bytes in the sibling directory. The frozen-v2 review_scope reference to the old live probe path therefore describes prior bytes; its exact old version remains available at the original .txt snapshot. Conservative current scope is **five bodies / 3,147 lines**. Both processes ran sequentially, at most one review process/CPU active. No APP/Torch/CUDA, actual producer toolchain, P0/P2/P3 edits, Git/index writes, branches, worktrees, or adoption occurred.

P3 Python-debug/owner-launch/no-import fork amendments, P5 strict-child/RNG/fork/phase semantics, six CUDA groups and full producer integration remain pending/unrun. General producer inventory/source closure limits remain explicit supplier policy. Root must resolve this remaining blocker before adoption, then create any concrete inventory only after exact frozen-byte independent review and bind it to the authorized job prerequisites. This review does not publish or adopt the packet.
