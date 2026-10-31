# PDR-0097 — Discovery path is a property of the (executor, pack-design) pair, not of the facet: the novice-facing row is caveated, not dropped

Date: 2026-08-20   Status: **accepted** (owner-ruled at the resume)
Author: Claude (standing product owner)

Related: `PDR-0086` (which opened this row prospectively and set the construct-preamble
precedent for the north-star), `PDR-0095` (the re-run that measured this)
Artifacts: `docs/product/metrics.md` — novice-facing row, new **CONSTRUCT CAVEAT**;
`docs/product/prds/0001-trial-protocol.md` — **B.6**;
`docs/product/trials/0001/O-comparison-20260820.md` §3.3 (SD-7)

## Context

`PDR-0086` opened a prospective *"Zero-Python authoring rate (novice-facing, discovery-path
annotated)"* row — the planned bridge from the north-star's **expert-ceiling** construct to the
vision's actual novice-authorability claim — and A.3 directs the annotation to be derived
retroactively for L/F/M/O from their authoring logs.

The blind re-run measured the construct directly and it did not hold. **SD-7:** the *same*
observability facet reads **docs-reachable, first reach worked** for run 1 and
**source-reading-required** for run 2 — same capability, same engine, same commit. The difference
came from a pack-design choice made three facets earlier (bars vs agent-profile VFS variables),
which decided which pipeline had to carry the observation.

## Options

1. Add a construct caveat to the row and keep collecting.
2. Drop the retroactive L/F/M/O derivation, keep only prospectively-recorded trials.
3. Kill the row — concede the construct cannot be measured this way.

## Call

**Option 1, the owner's ruling.** The caveat is written onto the row itself, ahead of any number,
and mirrored as protocol B.6.

## Rationale

This is the same move `PDR-0086` made for the north-star: when a measurement turns out to measure
something narrower than its label claims, **state what it measures before anyone can quote it**,
rather than deleting the data or publishing the misleading label. The readings remain useful as a
**lower bound on discoverability for the route the executor happened to take** — which is a real
fact about the substrate — provided nobody reads them as a property of the facet.

Killing the row (option 3) would have removed the only planned bridge from expert-ceiling to the
vision's actual claim, at the cost of an instrument problem that is describable. Dropping the
retroactive derivation (option 2) would have bought a cleaner denominator by shrinking an already
tiny one, and SD-7 shows the confound applies to *prospective* readings too — it is not a
retroactive-derivation artefact.

A second, independent confound was already recorded on this row and compounds SD-7: example
-reachability partly measures the **growing trial-pack corpus** rather than the shipped docs. Both
now sit on the row together.

## Reversal trigger

If two trials produce discovery-path readings that **disagree in opposite directions on the same
declarative surface** — not the same facet, the same *surface* — the caveat is insufficient and the
row is killed rather than caveated further, because the reading would then carry no signal about
the substrate at all. Re-examine at the next corpus revision, when the owner sets this row's bar.
