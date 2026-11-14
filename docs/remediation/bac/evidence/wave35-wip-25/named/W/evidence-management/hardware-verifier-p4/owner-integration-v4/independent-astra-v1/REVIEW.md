# Independent actual-source review: changes required

Reviewed frozen P4 `bcba4418dea2de31b8be600922f0dfd22cf601de2063fa721fc67fa44bf701fe` against complete current P0 and P1 bodies and the supplied P5 closure/P3 sampler metadata. This is an independent bounded current-capture/consumer review, not whole-chain or hardware qualification. The 266 author cases are retained evidence, not the basis for approval. Two unresolved P2 findings prevent bounded approval.

## P2 — Capture retained scratch footprint is never charged to overhead

P4 `capture_authority` checks allocation overhead CPU >=1 (line433), and `capture_resources` subtracts the declared overhead while reconstructing admitted budget (lines604–616). No later P4 check compares the actual mandatory capture output to that overhead. P1 explicitly refuses when allocated capture bytes plus projected final files exceed overhead scratch bytes, or existing entries plus four exceed overhead inodes (P1 lines916–922). Thus declaration arithmetic can pass while the actual retained capture graph is unbudgeted.

Executable witness: the unmodified author CPU-common fixture declares capture overhead scratch_bytes=0 and scratch_inodes=0. Its capture directory contains ten mandatory JSON files totaling47,788 logical bytes,77,824 allocated bytes including the directory, and11 inodes including the directory. Public P4 verify nevertheless returns custody=satisfied and test_outcome=successful. This is a current resource-consumer defect, independent of the future P2 wire protocol. All files are synthetic evidence; no claim is made that actual capture produced this invalid graph. The point is that the independent consumer accepts a graph the frozen producer's resource check would refuse.

Required repair: independently account for the complete retained mandatory capture output, including directory/final admission/spec/result and native-query siblings, against the authorized overhead bytes/inodes; retain/recheck the consumed closure. Avoid substituting input-file bytes, declared free space, or only seven sibling reference lengths for actual retained allocation accounting. Add a meaningful rejected zero/undersized overhead control and a valid sufficient-overhead positive.

## P2 — Native subprocess birth-token checks accept impossible kernel tokens

P4 capture/discovery parent identities use ASCII `[0-9]+`, but native Git child identities at line884 and driver child identities at line658 use `str.isdigit()`. Unicode superscript `²` passes that predicate although Linux `/proc/PID/stat` field22 cannot emit it. P0 identity accepts nonempty text and does not close this gap. This breaks the stated strict kernel birth-token contract in the newly repaired native consumers.

Executable witnesses: changing only source-before-git.json command0 identity.start_identity to `²` still yields public verify custody=satisfied/test_outcome=successful. Changing mandatory CUDA driver version-command identity.start_identity to `²` passes public initialization/capture custody. The CUDA witness calls initial(), not full verify, and runs no hardware command. Both use the frozen source and fixture's documented coherent resealing API. The analogous ordinary process check at line1251 also uses isdigit; that extension is static evidence only and is not an additional executed witness.

Required repair: use one explicitly ASCII decimal kernel-token predicate consistently at these consumers, with rejected superscript/non-ASCII controls and accepted actual ASCII tokens. This is evidence-shape rejection, not a claim that string declarations cryptographically prove process execution.

## Scope and verification

Read three whole implementation bodies: P4 2734 lines, P0 526, P1 992 =4252. Own independent probe61 lines:4313 total, four bodies. No P4 test/P2/P3/P5 implementation source or traceback bodies inspected. Test module imported only for documented inert fixture data/helpers; P5 may be imported by that module, but no P5 private interface was invoked. No implementation edits, source execution copies, branches/worktrees/checkouts, Git/APP imports, capture/native commands, or hardware execution.

Root granted CPU0/4GiB before runtime. Probe PID243872 ran2026-11-14T13:12:24.402461Z–13:12:26.058185Z, exit0; actual in-process affinity[0] and RLIMIT_AS4294967296 recorded. All five possible imported tool/test source hashes and byte counts were identical before/after. Probe script, stdout log, results and synthetic fixture trees are retained beside this review. No test-count aggregation with the author campaign.

Source review covered native command grammar, declared source and identity joins, resource ancestry and arithmetic, partitions, CUDA mandatory/optional driver paths, finite P5 collector closure and phase/role joins. The two findings above are concrete current-slice defects; absence of further findings is not whole-chain qualification. Actual P3→P2→P4→P5, full live strict core/replay/fork/producer/pair graphs, live phase_common/guard custody, abrupt-death cleanup, APP source assertions and actual CUDA remain UNRUN. The separately owed new externally pinned P2 capture manifest/wait/lease integration is not implemented/adopted here and is not reclassified as an optional requirement.
