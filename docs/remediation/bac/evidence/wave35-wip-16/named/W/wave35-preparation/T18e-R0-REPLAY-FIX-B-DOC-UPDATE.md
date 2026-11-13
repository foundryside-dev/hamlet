# Replay B documentation proposal — R84 component checkpoint

2026-11-13. Prose-only proposal for root's reviewed checkpoint application. No tracked document/source edits, application imports/runtime, tooling code, Git/index actions or delegation. No new implementation body was read; retained five-body source packet remains4413 lines. Read only the affected README/status/current-contract prose and independent B review. Source basis is the approved B CURRENT-API SHA256 `5a2292099017c7fa32180ee0384f4e2221096496535e28c31b5a49b234cb3bf5`; independent source/specification/quality/API and CPU component review SHA256 `e7f29a3a4ed3dd046f8ed8b6d3fc6a21c8ea5420892a6afd4ce3c3d659cc9dca`.

Exact approved candidate R84: tree `aa583c282043c445c2286b0b93df244cad9149c5`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, manifest SHA256 `17663fe0963563037d072a000f0aee466d0a3dc812b0c94c720aa94aee72c089`. Runtime/static outcomes below are attributed to the reviewed root and independent evidence, not author reruns. The owner-test writer is currently separate; this proposal does not assert the eventual outcome of that repair.

## 1. README.md — replace only the BAC progress paragraph at current line382

Exact replacement:

```markdown
BAC remediation remains in progress: 28 qualified, 38 remaining, 66 total. R84 qualifies the bounded CPU replay repairs: recurrent DTO content is owned and revalidated against the current destination before authority is issued, and real scratch sampling preserves ambient and persistent streams. Root passed 109 replay cases; independent execution repeated the 55 recurrent cases. This is component qualification; owner/caller migration, CUDA and programme gates remain open. See the [shared and flat/PER replay contract](docs/remediation/bac/CURRENT-REPLAY-CUSTODY-CONTRACT.md), [recurrent replay contract](docs/remediation/bac/CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md) and [BAC status](docs/remediation/bac/STATUS.md).
```

Do not refresh the broader dated source/CI review elsewhere in README. This paragraph supersedes its current R81 statement that recurrent B is still pending; it does not replace retained CI history with an inferred current pass.

## 2. STATUS.md — prepend current R84 status and explicitly mark R81 historical

Keep `# BAC implementation status`. Replace only the current first R81 heading with the following block, then retain every existing R81 body paragraph and all older entries verbatim. This preserves the actual WIP15 text and evidence link while preventing its superseded B work list from reading as current status.

```markdown
## 2026-11-13 — bounded CPU replay repair B qualified at R84

Recurrent materialization now owns the selected validation DTO content and reruns the complete validator against the current destination before issuing authority. Captured6/7, active inspection, archival5 and captured6-to-prioritized adaptation remain supported. Support checks still perform real disposable-generator draws; ambient and persistent RNG streams remain unchanged. Existing width refusal is preserved behavior, not a new repair.

At candidate `aa583c282043c445c2286b0b93df244cad9149c5`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, root passed 109 replay cases: 54 retained and 55 recurrent, including their isolated CPU children. Independent execution passed the same 55 recurrent cases; these overlap root's selection. Source/process and actual-child custody were verified. Global Ruff, Black and defaults checks, owned-four types and public prepared-result type checks passed. Independent specification/quality/API and bounded CPU review approves this component (review SHA256 `e7f29a3a4ed3dd046f8ed8b6d3fc6a21c8ea5420892a6afd4ce3c3d659cc9dca`).

The separate owner49 gate stopped after 1 PASS and 1 missing-lineage FAIL; 47 cases were UNRUN. Its required test-only caller repair is in progress, so neither owner49 nor the package is qualified by the replay result. CUDA capability/lifecycle/completion and hardware evidence, remaining callers and native integration, broader suites and final programme gates remain open. Accounting stays 28 qualified, 38 remaining, 66 total.

See the [recurrent contract](CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md), [shared and flat/PER contract](CURRENT-REPLAY-CUSTODY-CONTRACT.md) and [evidence index](EVIDENCE-INDEX.md). R84 supersedes the R81 pending recurrent-B and recurrent defaults/formatting statements below. Earlier candidate/CI records remain historical; R84 supplies no new remote/CI or CUDA pass.

## Historical checkpoint — 2026-11-13 replay repair A at R81

The following R81/WIP15 entry is preserved as its source-specific record. Its pending recurrent-B and recurrent style/defaults statements are superseded by the R84 entry above; its original evidence and remaining programme boundaries are retained.
```

At publication root should bind new immutable evidence through EVIDENCE-INDEX, using the actual allocated checkpoint filename. This proposal deliberately invents no WIP16 artifact URL or publication/CI receipt. Do not edit `evidence/wave35-wip-15.json` or archived WIP15 review/contract records.

## 3. CURRENT-REPLAY-CUSTODY-CONTRACT.md — scope header and historical handoff

Replace only its first heading with this exact block; retain its existing dated R81 source provenance and flat/PER/shared contract body:

```markdown
# Shared and flat/PER replay custody — R81 source contract, R84 status

Current recurrent behavior and R84 CPU component evidence are documented in the [recurrent replay custody contract](CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md). The shared and flat/PER interfaces below retain their R81 source basis. R84 supersedes this document's historical pending recurrent-B/defaults/style work; CUDA, owner/caller integration and programme gates remain open. See [BAC status](STATUS.md) for current gate outcomes.
```

Replace only heading `## Recurrent supplier boundary and remaining handoff` with:

```markdown
## Historical R81 recurrent supplier boundary and handoff

This section records what remained at R81/WIP15. Its “next slice B” work list is historical and is superseded by the [R84 recurrent contract](CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md). Keep the original R81 source/review/results below as evidence for that checkpoint; they are not current pending-B claims.
```

Leave the original R81 handoff paragraphs and their hashes/counts unchanged beneath that notice. The new standalone document supplies current recurrent facts; do not relabel the five-body A inspection as a recurrent source inspection or rewrite archived WIP15 artifacts.

## 4. Proposed standalone docs/remediation/bac/CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md

Exact proposed file contents:

```markdown
# Recurrent replay custody — R84 CPU component contract

2026-11-13. This contract records the bounded recurrent B implementation at tree `aa583c282043c445c2286b0b93df244cad9149c5`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, manifest SHA256 `17663fe0963563037d072a000f0aee466d0a3dc812b0c94c720aa94aee72c089`. Sequential source is 1,930 lines, SHA256 `e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317`. Source/specification/quality/API and finite CPU review is approved at SHA256 `e7f29a3a4ed3dd046f8ed8b6d3fc6a21c8ea5420892a6afd4ce3c3d659cc9dca`. This supersedes the pending recurrent-B handoff in the [R81 shared and flat/PER contract](CURRENT-REPLAY-CUSTODY-CONTRACT.md), whose history remains preserved.

## Data validation and prepared authority

`validate_serialized(state, *, expected_obs_dim)` returns a data DTO under owner exclusion. Frozen DTO fields do not make their episode dictionaries/tensors and nested priority data immutable. The DTO is not publication authority.

`materialize_validated(state, *, lineage)` now reconstructs owned selected transport, runs the full current serialized validator against the current destination, then materializes and issues an identity-only `PreparedReplay`. Domain-before-owner exclusion covers this entire preparation. Caller-mutated values, masks, IDs, fragment metadata, unexpected keys, inspection rows and priority provenance must pass full validation before receiving fresh authority. Existing width-change refusal remains intact; it was already implemented before B.

`prepare_serialized(state, *, expected_obs_dim, lineage)`, mode/archive preparation and `load_prepared(candidate, *, lineage)` retain their existing explicit admission. The `lineage: RNGOperation | None` keyword is required for domain-entering methods: None requests standalone admission; nesting requires the exact authentic active issuing-thread lease. Shared typed guards preserve parameters and publish the `PreparedReplay` result type. No omitted-lineage default, implicit ambient lookup, payload-bearing public handle or second domain is introduced.

Installation retains issuer identity, one-use, owner revision and current-domain checks. Fallible archive/episode/policy/generator work is staged before publication. Clean staging failure preserves live data; uncertain partial publication quarantines the owner. Clear and serialization cannot heal quarantine. Installed material is independent of caller input and retained candidate material. Managed owner mutation and ordinary nested sibling sampling invalidate prepared authority through their distinct revision/currency checks.

## Preserved transport and sampling behavior

- Captured6 retains its selected rows, metadata, resolved policy, stable identities and archives as format6 during reconstruction. A configured prioritized destination still uses the existing captured6 active adapter, preserving destination priority configuration/clock/stream and recording adapter provenance.
- Captured7 retains the complete priority/domain/RNG/provenance representation and re-enters its existing validator. Captured legality, configured/unconstrained rules and real row identity remain enforced.
- Inspection retains its actual active rows plus archives in the existing inspection envelope. Absent optional legacy reward components use their established explicit None transport encoding; missing required fields, unexpected keys and malformed selected data are not discarded.
- Archival5 continues using its selected original transport, owned and revalidated before existing archive materialization. Historical rows do not acquire invented legality or become captured learning rows.

Recurrent support validation performs a real `sample_units` draw with a disposable complete-state generator clone. Priority-update and store-refresh therefore perform scratch sampling, not literally RNG-free work. For the accepted ordinary-data and exact-engine profile, their ambient and persistent generator states remain unchanged under owner exclusion. Real selected support draws are retained; no domain lock or status query is acquired beneath an owner lock. Healthy-owner local scratch work can continue after common poison but cannot heal poison/quarantine or authorize learning samples, preparation or installation. Qualified learning samples still enter the process domain and publish the advanced persistent generator only after complete batch construction.

## Evidence and remaining gates

Twelve genuine malformed-DTO failures at R82 preceded this repair. At fixed R84 source root passed 109 replay cases: 54 retained plus 55 recurrent, including their isolated CPU children. Independent execution passed the same 55 recurrent cases, overlapping root's selection. Source/process and strong actual-child custody were verified. Global Ruff, Black and defaults checks, owned-four types and public prepared-result type checks passed. These controls cover malformed DTO rejection, archive/inspection and captured6 adaptation, nested currentness, staging/partial-publication/alias behavior, and real scratch-state preservation/continuation.

The separate owner49 gate currently records 1 PASS, 1 missing-lineage FAIL and 47 UNRUN, with its test-only caller repair in progress. R84 therefore qualifies the bounded CPU component, not the owner suite, package or whole BAC programme. CUDA constructor/lifecycle/completion, applicable hardware, remaining callers/BANK/ENV/native integration, broader suites and final programme reviews remain required. The child proves CPU post-public-poison consumer behavior, not a restoration-failure witness or CUDA correctness. No current remote/CI pass is inferred. Accounting remains 28 qualified, 38 remaining, 66 total. [BAC status](STATUS.md) and the [evidence index](EVIDENCE-INDEX.md) carry subsequent gate and checkpoint updates.
```

## Application boundary

Root should apply these proposed texts only at the coordinated checkpoint after their prose review. If the owner gate changes before publication, replace the explicit1/1/47 in the new current paragraphs with its exact new source-bound result while preserving the R84 failure as history; do not silently turn this proposal into evidence of that future repair. The current tracked docs, source and archive bytes have not been changed by this task.
