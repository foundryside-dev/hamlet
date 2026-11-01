# Review provenance

Historical finding/review; see the final implementation receipt for repair and qualification.

Original artifact: `T06-preservation-interface-review.md`; SHA256 `9baf1736c2b93bbac2005f115d1684633e7fcc6bc26295fe029b030a11e7229f`. The original is retained unchanged. This portable rendering normalizes execution paths; it does not alter the review verdict or source binding. This artifact describes its recorded earlier source. The repaired implementation and final review are linked from the package receipt; final qualified release `eb73173496a7955b30a6fea4b65ccae8cc615b87` has sum tree `1a1ca88cab7cc5bfe97e0922534d23e733d17e2d`. Historical findings below are not current unresolved findings.

# T06 training-only constructor preservation review

Verdict: **P2, in-scope preservation regression; T06 release blocked pending additive repair and owner verification.** This supersedes the earlier static PASS's claim of complete old-valid-input preservation. No user scope decision is needed to retain this behavior. No source/test/index edits or runtime were performed.

## Evidence and bounds

Exactly five current whole sources, 1,933 lines (actual counts differ from dispatch estimates):

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/demo/unified_server.py |542|7789de97326fadd9f828df5c41f6c5641ceda709e7b44f57235e4485c381f1ad|
| tests/test_townlet/unit/demo/test_unified_server_unit.py |122|0e4e90f087d69772ba25438871f4b4c19618a1076d73546246f6ae4a63eaaa28|
| src/townlet/config/resolved_launch.py |102|b55b4b816b02b167ee963a9a443045bff9b26d2ec5e3a0307026253767fe939d|
| src/townlet/universe/declarations.py |724|983336171a2e49d4e91f86dbbc03f10d9e7bde58a86ab5e8a49cb51dc18f5a6c|
| src/townlet/config/training_v2_config.py |443|d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68|

Also read the baseline SERVER at HEAD23755537926c2808c8b312f4f5b52ad76ab594ab (same source path, no checkout/copy), current T06 brief, and root's launch-owners.log. No sixth source was opened. Root log records 112 passed then setup error, not failure of a launched training run.

Baseline constructor checks only existence of levels/<selected>/training.yaml and leaves _training_config unset. Baseline _load_training_config calls the publicly exported load_training_v2_config lazily. That public loader explicitly accepts a level directory containing training.yaml and validates the training DTO independently of an experiment. Existing helper tests intentionally construct such an input with valid required training fields and assert sanitized output metadata, idempotent snapshot copying and logging cleanup. They neither mock the constructor nor claim a runnable universe.

Current SERVER line65 calls resolve_launch immediately. LR calls DeclarationStore.discover, whose unconditional _require_families requires six pack families and five per-level families. The root log shows exactly those missing-family failures during fixture construction. Thus formerly operational metadata/snapshot/logging work is now unreachable for this valid training-only input.

The baseline constructor doc describes a full v2.1 experiment root. That supports requiring a complete pack for start/training/inference; it does not erase the deliberate, tested pre-start behavior and standalone loader contract under the explicit no-removal/degradation instruction. Classifying the fixture as synthetic therefore cannot justify changing it into a full pack or deleting the test. Conversely there is no evidence that training-only input must successfully run a server, and this review does not demand that.

## Smallest additive repair route

Keep complete resolve_launch as the mandatory runtime admission authority, before start creates directories/snapshots/log handlers/threads. Preserve the historical conventional constructor/helper surface as a separate pre-start state, without claiming it is a ResolvedLaunch or a runnable pack. A bounded SERVER-local adapter can do this without changing LR or the public training loader:

1. Normalize pack/direct-level selection and refuse conflicting explicit/direct selections. For the historical conventional training path, retain its existence-only constructor admission and initialize component handles/request receipt normally; represent unresolved launch explicitly. For nonconventional transports, retain actual content resolution, never introduce a filename requirement for them.
2. A training-helper accessor should prefer actual resolved compiled training when available. For a deferred conventional input it may attempt complete resolution; only a structured all-missing-required-family failure may select the existing standalone training loader. Never catch arbitrary compiler/parse/collision/scope/sidecar validation errors as permission to fall back. This preserves selected compiled metadata for complete packs and known standalone helper behavior for incomplete packs. Keep real standalone path/origin separate from compiled provenance; do not invent effective/execution identity. Snapshot/logging helpers need no fabricated compiled result.
3. start must acquire/verify a complete ResolvedLaunch even when a standalone training DTO was previously cached, install normalized root/level/compiled training/origin together, and only then perform side effects. A helper DTO cache must never mark launch admission complete. Keep constructor request provenance immutable and distinct from CLI-origin evidence.

This is a compatibility adapter, not a new broad section-discovery implementation or a catch-and-ignore compilation mode. The implementation owner must check exact exception issue attributes within its counted inventory before choosing the structured missing-only discriminator; this lens did not open the error-definition source. If that cannot fit the implementation inventory, use an explicitly re-sliced owner, not a sixth helper. Alternatively the forthcoming T07 standalone declaration producer can supply content-based section discovery, but T06 may not release with this failure while waiting for it.

A clean bounded repair owner can own SERVER and the counted launch regression, with LR, training_v2_config and existing server unit test as its three read-only sources (five total, currently1,534 lines before edits); CLI/RR must remain frozen for that repair lens. The earlier five-file T06 owner cannot silently add these sources. Root can authorize this additive finite re-slice; no capability-reduction approval is involved.

## Required causal controls and handoffs

Retain and rerun all three existing helper tests unchanged. Add/retain controls that training-only construction and metadata succeed, but actual start refuses missing pack content before filesystem/logging/thread side effects; complete conventional and renamed/multidocument inputs still use selected compiled training; duplicate/conflicting declarations and malformed sidecars do not enter standalone fallback; direct-level/explicit selection conflicts remain located refusals; a cached helper DTO cannot bypass runtime admission. Check existing public constructor arguments/defaults and immutable request receipt unchanged. Execute only after root unfreezes and authorizes runtime. Current long transport matrix alone cannot discharge this regression.

T07 owns the later canonical standalone producer handoff. T32 actual live/evaluator transport/readiness and T36 serialized provenance remain required; no end-to-end, full-BAC or final closure claim is made. The existing R3 identity binding remains historical evidence of the reviewed source, not a release PASS after this finding.
