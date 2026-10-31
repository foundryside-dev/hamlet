# Historical replay decision for Emmy / John

## Approved decision

**John approved Option A** via explicit question reply in this chat on 2026-11-01: “A — preserve artifacts, start fresh qualified replay (Recommended)”. Approval reference: `BAC-HISTORY-A-2026-11-01`; async question `call_e5fbd34979324b9f9574e38b6e61fbef`. Option B is NOT selected.

This authorizes only archival preservation plus fresh qualified replay for the supported pre-capture histories described below. It does not authorize data deletion, unrelated scope reduction or removal of current captured-mask resume.

## Why a decision was needed

Astra medium round02 has one blocker: the plan preserves currently supported old replay with its known D01 unmasked targets, then excludes those rows from the strong closure claim. That exception needs explicit delegated approval. The user requires both preservation approval for capability reductions and zero unresolved in-scope P1/P2; the coordinator cannot silently choose either side.

Current callable formats are demo9 / population6 / uniform4 / PER4 / sequence5. They contain no successor legality masks or sufficient hidden-world state to reconstruct exact state-dependent masks. The current D01 proof gives target51 instead of legal3. The existing no-backwards-compat/no-trained-checkpoints owner ruling does not itself authorize quietly changing a currently callable access capability under the newer user instruction.

The exact plan under review is SHA25671a0a08b0659ab3877a7a984844a9d5e158b2fb51940cee9f9c6a4f59e07b671; see plan-reviews/round-02.md. No code implementing an exception or restriction has been written.

## Option A — approve archival preservation plus fresh qualified replay (recommended)

Preserve old artifacts and all replay tensors for read/query/export and identity inspection, without deleting or rewriting them. Restore available weights/target, optimizer/scheduler, exploration/curriculum/persistent world state and clocks at a fresh episode, but use a fresh qualified training buffer. Historical replay is archived and never sampled for the corrected constrained learner. New rows carry exact successor masks; declared warmup applies to the new retained-row count. Runtime records the import mode and archived-row count.

Approval grants the precise reduction: old maskless rows no longer continue to drive optimizer updates through ordinary legacy resume. It does not authorize data deletion, removing public inspection/export, reducing current captured-mask replay, or any other capability change.

## Option B — approve a bounded pre-capture historical semantics exception

Preserve actual ordinary legacy training access for these exact formats. Only historical unrecorded rows retain the original unmasked target semantics; their recorded reward/components remain as historical evidence. Newly captured rows always use actual masks and corrected current provider/scale semantics. Mode, source formats, per-row legality status, guarantee limits and the approval reference are persisted and reported. Strong legal-target closure is claimed only for recorded rows; legacy behavior is visibly outside that guarantee.

Approval grants the precise scope exception to C05/D01 (and the interpretation of recorded pre-fix reward history), not a claim that the known wrong target is fixed for historical rows. It does not permit missing masks for new compiled-world admission, a silent all-legal reconstruction, silent history deletion, or current X01 wrong reward emission.

## Work that continues meanwhile

T01 finite/constructible parameter validation (D06-D08/G06) and other independently approved additive work do not depend on this decision. No pending choice is treated as approved by elapsed time. Emmy may approve either option or provide another concrete policy under John's delegated authority.
