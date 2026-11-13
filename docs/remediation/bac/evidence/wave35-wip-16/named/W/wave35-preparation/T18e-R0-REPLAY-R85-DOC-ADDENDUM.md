# R85 documentation evidence addendum

Apply only with approved R84 DOC-UPDATE (863e5797) and DOC-REVIEW (4a133586). This supplies subsequent actual evidence, not a replacement for archived R84 failure. Source: wave35/r85-owner-caller-component-receipt.json SHA256141a28a97d95c318d4cffde51a5877966768fe83e0cb547c920c7599b2af8683; independent owner review02651be5184464c84335549971a4e4752d4de5f582fcd43e1a073618d8883998. All sessions closed; root verified custody.

## README replacement (supersedes proposed R84 paragraph)

```markdown
BAC remediation remains in progress: 28 qualified, 38 remaining, 66 total. The bounded CPU replay repair now rejects malformed mutable payloads before issuing installation authority. At R85, all 109 replay regression cases and 49 sequential owner cases passed; independent execution repeated the same 49 owner cases. CUDA, remaining caller integration and programme gates remain open. See the [shared and flat/PER replay contract](docs/remediation/bac/CURRENT-REPLAY-CUSTODY-CONTRACT.md), [recurrent replay contract](docs/remediation/bac/CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md) and [BAC status](docs/remediation/bac/STATUS.md).
```

## STATUS current entry (prepend ahead of proposed R84 entry)

```markdown
## 2026-11-13 — sequential owner caller repair qualified at R85

The older sequential owner tests now declare standalone lineage explicitly at 21 call sites. The masking test patches the sampler actually used and checks a concrete terminal followed by masked rows; its existing assertions remain intact. Production replay and both replay regression modules are unchanged from R84.

At candidate `e1d5bf0e123cc04eca943a34125bdfbd1e6fc42a`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, all 49 owner cases and 109 replay regression cases passed: 158 distinct cases. The first repaired node was also run separately and overlaps the owner suite. Astra independently passed the same 49 owner cases, with no source/specification/quality findings (review SHA256 `02651be5184464c84335549971a4e4752d4de5f582fcd43e1a073618d8883998`). Source/process and both actual replay child identities were verified. The changed test passes Ruff and Black; the global static results below remain evidence from R84, not new R85 commands.

This closes the R84 owner49 caller prerequisite. Its original failure remains recorded below; the repair is no longer pending. CUDA capability/lifecycle/completion and real hardware, remaining BANK/ENV/POP/native caller integration, broader gates and final fresh programme reviews remain required. Accounting stays 28 qualified, 38 remaining, 66 total. See the [evidence index](EVIDENCE-INDEX.md) for the actual durable checkpoint and CI status.
```

Retitle the proposed R84 heading as `## Historical source checkpoint — 2026-11-13 bounded CPU replay repair B at R84` and prepend one sentence before its owner49 paragraph: `The following owner-gate failure is the historical R84 outcome, superseded by the R85 repair above.` Keep the R84 result/counts intact.

## Standalone recurrent contract final evidence paragraph

Replace only the final proposed paragraph beginning `The separate owner49 gate currently records` with:

```markdown
The R84 owner49 gate initially recorded 1 PASS, 1 missing-lineage FAIL and 47 UNRUN. The subsequent test-only R85 candidate `e1d5bf0e123cc04eca943a34125bdfbd1e6fc42a` repaired those standalone callers and the terminal-mask fixture. All 49 owner cases and all 109 replay cases passed at R85; independent Astra execution repeated the same 49 owner cases, with verified source/process custody and no scoped review findings (review SHA256 `02651be5184464c84335549971a4e4752d4de5f582fcd43e1a073618d8883998`). The recurrent production and both regression modules retain their exact R84 bytes. These are bounded CPU results; CUDA constructor/lifecycle/completion, applicable hardware, remaining callers/BANK/ENV/POP/native integration, broader suites and final programme reviews remain required. The child proves CPU post-public-poison consumer behavior, not a restoration-failure witness or CUDA correctness. No current remote/CI pass is inferred. Accounting remains 28 qualified, 38 remaining, 66 total. [BAC status](STATUS.md) and the [evidence index](EVIDENCE-INDEX.md) carry subsequent gate and checkpoint updates.
```

No tracked docs changed by this addendum. Shared/flat/PER header remains source-qualified R81 with R84 recurrent link; current STATUS resolves the later owner result without misattributing an A inspection.
