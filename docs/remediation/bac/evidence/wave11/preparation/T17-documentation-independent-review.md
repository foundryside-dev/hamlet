# T17 documentation independent review and scoped cadence recommendation

2026-11-02. Static review only, existing `/workspace/hamlet`. **Accept the proposed source-contract prose: no required correction to the four-hunk documentation patch found.** Application and qualification remain root-owned and pending actual gates. This report does not approve pending runtime measurements.

## Exact reviewed identities and boundary

| Artifact | SHA256 |
| --- | --- |
| `T17-documentation-draft.md` | `ca923f5dbdc5b488e87346e51ef2a59a799a0ebf119617b8a62f9c645b2441e8` |
| `T17-source-docs.patch` | `d85efe0047ff9adbd590d1f98f921d4d931070cd6258218e67fe6edf7d661a57` |
| Supplier prose `T17-consumer-independent-review-r2.md` | `951cc1dafe1cbc5743bf5673bad1b43e72cf1f0cfef50df738058ea9a4dac966` |
| DATA `wave11/r2-main-source-equivalence.json` | `b99801a447a142d25479c8f91ce4e018c41b43826fd61ed7b0b508aa93de5425` |

The first three artifacts are in `wave11-preparation/`. Fresh independent source hashes match the five whole files already reviewed, total2336 lines:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| NET `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| NF `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| BC `src/townlet/config/brain_config.py` | 568 | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| Owned `tests/test_townlet/regressions/bac/test_token_binding.py` | 640 | `bdb25f6e33bae64ede392dfb8ed4fbe4b7521a6dc201184e547decaeabefe544` |

The DATA bridge binds their unchanged R1 tree `5d4685b55ccd85879d0627bb55bbc20277c58af4` identities to R2 tree `f0410f6b8185cf2c87f4f6d5ddbd0a730e886dc9`. Base remains `a0802a442bc7ea529de650b8705629923a0e6c72`. I did not open the extra consumer implementation or follow implementation links. The consumer repair classification below is attributed to its separate independent review, not my own expanded source audit. This review covers supplied patch content, not fresh whole-document preimage/application validation; root must still verify the three preimage hashes before applying.

## Findings and required corrections

No P1/P2 or other actionable source-contract defect found in the patch. It truthfully replaces schema-only claims with actual factory consumption and describes independent encoder/aggregator selection, strict explicit width, the joint prepool MLP, central omission resolution, retained direct constructors and required resolved keyword pair, unchanged linear learned-key geometry, interaction Linear indices0/2, recurrent frame/sequence behavior, and target-owned context. NET:252–335/364–418/449–519/553–655, NF:79–93/153–164, BC:147/172 and OP:23–42 support those claims. The same-mode context claims also have the owned test and my prior12-node R1 runtime evidence, with unchanged source hashes; they do not imply a reviewed external checkpoint loader or a whole R2 runtime pass.

The nested YAML is explicitly a partial architecture block and valid for the strict options DTO. The text preserves both mean/attention and both network families, zero-width flat policies, historical linear alias, and compiler-owned geometry. It makes no new learning/convergence, checkpoint compatibility, full-resume, global review or whole-BAC qualification claim. The unrelated preexisting StructuredQNetwork table issue remains correctly flagged outside this bounded patch.

**Required receipt refresh if the draft is used as current handback:** its second paragraph's “independent12-node reviewer run may still be active” is now stale; that run actually closed12 PASS, as `T17-independent-runtime-r1.md` records. The consumer supplier now reports the completed R1 affected result as2 FAIL/407 PASS and classifies both observation sites, rather than only “at least one” proposed repair. Preserve the historical draft if desired, but carry these precise facts into the final handback and keep R2 actual runtime pending until observed. This is a receipt-freshness correction, not a blocker in the proposed tracked prose. Do not relabel R1's failed consumer run green.

The optional historical-golden limitation remains: current direct/explicit/omitted constructors share `_initialize`, so their comparisons alone are route equivalence; prepatch preservation additionally relies on reviewed unchanged creation/computation order. No new golden programme/probe is required by this review.

## Final scoped cadence recommendation

Apply EXECUTION-ADDENDUM Sections1–3 only with both activation keys recorded for the reviewed addendum (previously read SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370`). This review grants neither key nor a cadence waiver.

The separate R2 consumer review establishes a bounded **observation-only repair**: both test-local observers move from `__init__` to the shared `_initialize`, invoke the real initializer once before installing the original LSTM hooks, and preserve all23 assertions, control flow and scenarios. Production NET/NF and all five main sources are unchanged. It reports no fabricated gradients/memory, altered return values, production fix, shared fixture or runner/import configuration change. Runtime must still establish the measured recurrent gradients, graph connectivity and lane memory.

On that attributed causal classification, **I recommend that this isolated additive encoder branch may defer full repository pytest to G3 after actual direct-consumer passes, required guards and independent repair verification are recorded**, provided cadence is activated and root can bound the affected consumers. No concrete earlier trigger remains established by the two obsolete observation hooks themselves: the changed factory route does not change the retained public constructor signatures or tensor/results, numeric old linear behavior, config meaning, or existing serialization; the repair is confined to test-local observation. An internal observer attached to a constructor is not by itself an accepted production ABI guarantee that all factories call that constructor. Nor is this a shared executable-fixture/collection change.

This is conditional applicability advice, not preapproval of the pending joint38, consumer runtime or guards. Any actual restored-observer failure, unbounded/distant impact, or newly demonstrated consumed-interface change activates the appropriate Section3 earlier full-gate rule and requires causal repair/review before boundary green. Sections1.4–1.5 still require precise receipts and prohibit dismissing a failure because G3 is later. Root owns and records the final gate selection. The documentation-only patch does not itself change that assessment; normal consistency/application checks and all final-SHA refresh requirements remain.

Custody: only this new ignored report was written, after its ignore status was checked. No runtime, source/test/index/tracked-document changes, sixth implementation read, branch/worktree/source copy/deletion or subdelegation. Existing14 checkouts left untouched. Stationary.
