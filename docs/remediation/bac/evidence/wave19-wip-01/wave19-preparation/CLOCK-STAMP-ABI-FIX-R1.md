# CLOCK-STAMP ABI design fix receipt R1

Addressed the two required defects and future consumer handoff from CLOCK-STAMP-ABI-REVIEW-R1.md. Only ignored prose artifacts changed; no source/test/runtime/import/formatter/Git/index/branch/worktree or subagent operation occurred. The sole preserved copy is the explicitly requested original ignored proposal, not a repository/source copy.

- R1-1: stamp explicitly declares __hash__ = None; prose specifies identity equality with hashing disabled; finite ownership control requires hash(stamp) to raise TypeError. ServiceClock/EventId value equality/hash retained.
- R1-2: publishes accepted explicit current-format conversion/evaluation-clone source epoch+1, cleared active caches, local eligible and service origin0, actual restored episode identity, inherited learned/history template semantics and source artifact preservation. Ordinary reset still retains cumulative service. No new APIs/decoder/runtime implementation.
- Consumer handoff: records existing WS→RP dependency and future cycle-safe RP stamp validation requirement, without new source inspection.

Preserved original: CLOCK-STAMP-ABI-PROPOSAL-R1.md SHA256 dd37a9aa538780fa96c7fb6e67df4de84c5f749e644baa9faefe4ec4981050c2.
Updated proposal: CLOCK-STAMP-ABI-PROPOSAL.md SHA256 5251388f5ad7c0328b6be4825be595e4b3f8fafd2271f1babd6618ded8bac0f0.

Ready for the same Astra scoped rereview. Tests/source implementation remain unauthorized and untouched. No runtime qualification or full acceptance is claimed.
