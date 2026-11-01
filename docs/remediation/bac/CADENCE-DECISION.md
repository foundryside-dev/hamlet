# BAC repository test cadence approval

Decision: **approved**, reference `BAC-CADENCE-A-2026-11-01`.

John explicitly answered “Approve the bounded cadence exception (Recommended)” to question `call_5dc18c01d6bd4780aca18c819555a704`, which identified [the reviewed addendum](EXECUTION-ADDENDUM.md), exact SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370`. The [same Astra MEDIUM technical review](plan-reviews/execution-addendum-approved.md) supplies the technical key. Both activation conditions are met.

This is the precise exception to the per-commit full-pytest cadence in `docs/remediation/STATUS.md` §4.3. Every package retains meaningful regression/owner tests, all standing non-pytest checks and fresh other-model adversarial review before dependency release. Full suites run at G1–G7 and the addendum's earlier impact triggers. Each receipt records selected checks, unrun checks, trigger disposition and next full gate. Final repository/coverage/slow/applicable-hardware gates, fresh common-source spec/design reviews, joint evidence, finite learning and remote CI are unchanged.

PF-06's complete T08a context is also technically approved. This decision authorizes no capability removal, unrelated scope reduction, new spending/access/deployment or broader publication authority. The byte-frozen implementation plan and reviewed addendum remain unchanged.

T02 triggers an early full suite because serialized configuration/identity inputs change; it is not a deferred full-gate package.
