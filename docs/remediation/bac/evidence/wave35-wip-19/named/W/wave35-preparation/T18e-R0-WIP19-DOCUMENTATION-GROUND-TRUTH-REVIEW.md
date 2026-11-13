# WIP19 applied documentation — ground-truth review

**SPEC: PASS. QUALITY: PASS for the four applied documentation deltas at the exact hashes below. No concrete source/API, scope or accounting inaccuracy established.** This is documentation approval for the frozen checkpoint proposal, not terminal evidence approval, a claim that planned archive destinations already exist, or application/programme qualification.

Reviewed `git diff -- README.md docs/remediation/bac/STATUS.md docs/remediation/bac/EVIDENCE-INDEX.md docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md`, the applied bytes, V3 proposal and root application record. The changes match the proposed blocks and final identities; historical R89/R98 prose remains explicitly dated/source-bound. Only this report was written. No application imports, execution/tests, source/document edits, branch/worktree/copies, excluded-body inspection or delegation occurred.

## Exact reviewed document and proposal identities

| Applied document | Lines | Personally checked SHA-256 |
| --- | ---: | --- |
| `README.md` |551|`efed71def427225be84e0d6f9e67d6f87df4401df392907de2195d195d3e36a3`|
| `docs/remediation/bac/STATUS.md` |300|`52d5261a3b7eb5f8f36286ab2c7e5aa5b13abcaf8764147dcfeb21fe32c4affe`|
| `docs/remediation/bac/EVIDENCE-INDEX.md` |45|`9646ff5b9672b505943d2a3c335b01d8662253f8b92358aee16ad0b050ef6fad`|
| `docs/remediation/bac/CURRENT-RNG-CUSTODY-CORE-CONTRACT.md` |232|`553a840a6b54c28763cec8a1e2e84f8161f9aa67832b2d3e1b07bf90c0eb7aab`|

Proposal `P/T18e-R0-WIP19-DOCUMENTATION-PROPOSAL-V3.md` personally checked at `6c93f909dbfbf3ddcdcf07f74f584c03f2f378d6270cb85d51a5b5839e1bc048`. Application record `E/wip19-preparation/wip19-document-application-v1.json` personally checked at `7ba70ee256d74f04895f6bca51d958cb41bf3a29f2520245f3dc8e695afa35b3`; here `E` is `W/evidence-management`, `P` is `W/wave35-preparation`, and `W` is `.superpowers/sdd/2026-11-01-bac-remediation-upgrades`. All four live after-hashes equal both records' expected final identities.

## Source-grounded API checks

The sole added implementation body is `src/townlet/exploration/rng_custody.py`,948 lines, personally rehashed `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`. Retained prior scope is shared881 `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4`, helper675 `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`, producer test2468 `d639ebaac4a0e24d313ef5d8d46202f17a32077e111f99905fa110fab4cbdac0`; all rehashed unchanged. Total4972 lines/four bodies. The core test and all other implementation bodies were not read. Its documented initial packet count/hash are attributed to the independently source-bound initial review, not a new personal test-body inspection.

The API table and new contract prose agree with the actual source:

- Core59–79/675–699 expose the required keyword-only factory and opaque `RNGDeviceInvocation`, authentic operation entry, required exit arguments using `TracebackType`, `Literal[False]` exit and bool getter. Issuance checks PID/membership/lineage/device tuple without taking domain exclusion, doing CUDA work or pinning the participant owner. Actual entry delegates to the shared operation implementation.
- Core691–753 checks PID before the public enter/exit/getter registry/thread path, authenticates exact issued identity and issuing Thread object, implements issued→entering→active→exited or entry_failed, and refuses historical reads until completed exit. Release clears participant/kind/lineage/devices/context; the retained outcome record does not itself retain an operation/error/traceback/generator. Historical getter uses no active-operation, membership, owner/domain-lock or CUDA check and grants no renewed authority.
- Core350–361 certifies False only when that invocation's actual `_complete` returns. Failure leaves initial True; body/report/poison/error identity does not determine certification. Nested `_finish` uses its admitted subset at840; outermost `_finish` uses the accumulated union at869. Each invocation has its own record, so later outer failure cannot rewrite a completed child's result. Exit seals state in `finally` before outward delivery, with no second completion pass.
- `_complete`345–348 touches no CUDA attribute for an empty tuple and currently stops on a synchronization exception. The docs avoid turning that generic tail behavior into a permanent new outcome guarantee and distinguish local completion's separate rule. Required owner exclusion, parent outcome consumption and justified owner transitions are stated as producer obligations, not properties proved by the boolean.
- The production local-contract manifest remains empty at139–141. Neither the source nor these docs assert authentic leaf activation, producer completion or hardware readiness. The reviewed clone gate retains its previously approved ordinary-native-runtime boundary rather than claiming universal custom-protocol precision.

This source reading checked documentation claims, not a new broad audit or new runtime qualification of the core.

## Exact evidence and scope checks

Personally rehashed/read the initial core review `841eb6bc15a15161a970fb306d427f36c6a3b167d9c73fc73e16ab22b0a8789f`, R106 root record `803d831ae57fbc8fd46963be58ee095301895beb6c4fcc88fb572aa6a4b05570`, R108 root record `500a588b4c6af705cf7f824b0bbc1d1953b67efe2cb0beb99a8d38672c959dec`, and clone other-model review `eaf6b4b20eb37d4bbc7056d91d04c0c0d4d34fedbf61c060a32d7fc1f7345213`.

R106's76 are66 nonisolated plus ten *existing* isolated cases on tree `ab46784efc86bab95b031494529e06871a12f1ff`, manifest `12e5609bf4f300e608ebd6f94297fd0f2496bf95169e757864cb6ad50fbd0970`. Initial source approval is accurately described as bounded; new own-phase/nonempty/nested failure, invocation fork, direct state and numeric-ID alias qualification remain open. Old children are not promoted to new outcome coverage.

R108's507 are distinct final-candidate reachable cases on tree `fa1c6804fcff475f5652e5f5f357468e2d931c0d`, manifest `27b28f930659b690c55db0a0e4a2edc97155210ce0c9bf1f0e38738e4f85bdce`:436+8+34+21+8. Its836 collection and329 UNRUN, including ten producer children, remain distinct from execution. The docs do not add R10676 to507 or relabel it as an R108 run. Clone source SPEC/QUALITY PASS is confined to the concrete P2 under its adopted runtime premise; full A/B acceptance remains open.

R108 owned/public typing, style and unchanged defaults600 PASS are reported accurately as bounded root evidence. Global mypy16 remains historical; the docs neither invent a fresh global result nor subtract the repaired owned error to claim a new15 result. Remote WIP18 Config PASS/Lint FAIL16/fast-suite Tests FAIL with logs unavailable is explicitly reported root provenance from this task; this review did not independently retrieve remote CI or infer detailed test causes. No current successful CI claim appears.

The delta retains28 qualified/38 remaining/66 original packages and the open B activation, own-invocation second phase, producer children, actual parent handoff/recurrent integration, hardware, runner/repository/coverage/slow/learning/final review/CI gates. Historical R89 qualification is clearly bound to core821/test1409 rather than silently rebound to core948. WIP18/R98 is relabeled historical while its failed/unrun evidence and dated limitations remain intact.

The WIP19 manifest and selection-plan links are reviewed as **planned final publication destinations**, consistent with V3/application-record conditions. Their existence, exact assembled contents, terminal receipt/review/attempt inventory, execution-versus-publication equivalence and remote identity/CI are not certified here. Root must verify those destinations and remaining publication conditions after assembly before commit/publication; the present tense intended for the final checkpoint page does not establish prior existence during this preparation review.

No concrete correction is requested. This review may bind only the four exact document hashes above; changed document/source/evidence bytes require renewed relevant verification. It grants no application acceptance or publication action by itself.
