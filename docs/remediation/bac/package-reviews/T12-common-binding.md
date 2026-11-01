# Review provenance

Final scoped source/spec review or common-candidate binding. The final binding uses tested tree `42bf1b690f523ed2bb8bf47d12f53d00ea6cb93c`, identical to qualified source release `07ce97550cf2f9dae67cb56d1d8014218c39d523`; earlier identities in the body retain their original meaning.

Original artifact `T12-r5-common-binding.md`, SHA256 `6655a5ab1580b065d0fee3a11e4bb4ef41822da3311b58011b75da710070c766`, retained unchanged. This portable rendering normalizes execution paths. Runtime results are coordinator-attributed unless the body explicitly records reviewer execution.

# T12 R5 common-candidate binding

The T12 R3 scoped static source/design PASS is rebound to the common frozen R5 candidate `e9d41bceb2d4a817b4f085a90ad123778858318e`, based on HEAD `44e9d494eb94da1450b3e7a1832acea23dbbdb8e`, recorded in `wave06/green-r5-candidate.json`. The five reviewed sources are byte-identical to the R3 reviewed packet. This is an identity binding, not another review cycle or an expansion of the verdict.

| Reviewed whole source | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/sequential_replay_buffer.py |1237|14196e7109120682476736e927076ca2dcd9926cdda206cac1ab4641189e3ea5|
| src/townlet/training/historical_checkpoint.py |666|013fe456f867bc9b5e28ab95ee9b07e5b0fa155653abfd07de3a35159c969761|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| tests/test_townlet/regressions/bac/test_sequence_history.py |819|5b4626bc9557bbd86a5b25dad5e2cbf2b7ae49d211c2b6d125bdbd1c2386a7dc|

Exactly five sources, 3238 lines. The historical `T12-astra-review-r3.md` is preserved at SHA256 `b41bc1fb30ea55da73015df98360c5fce376441d4783d85934f3a9ac7df51834`.

Root reports actual R4 qualification: 69 regression plus 46 unit cases = 115 PASS; 42 current-consumer cases PASS; all five cheap guards PASS. These results are root-executed evidence, not reviewer runtime or a new R5 execution claim. The separately added native-proof source was not read; it has an independently assigned reviewer. Native-proof and full-repository qualification remain pending at binding dispatch.

The producer conclusion remains bounded: approved inspection transport repairs second-save archive loss without erasing or relabeling newly authored legacy rows, retains exact history-free5 and qualified6 contracts, and prepares ownership/validation/materialization before installation. No new confirmed P1/P2 is introduced by this byte-identical slice. Prepared states remain internal transfer objects subject to the documented quiescent-destination caller contract, not opaque revision-bound single-use capabilities.

T14/native consumers must actually recognize and preserve the distinct unqualified inspection transport. Current-consumer success does not establish complete T24/T25 admission, outer archive registry reconciliation/single accounting, or atomic learned-state/resource/RNG orchestration. Those remain REQUIRED OPEN, as do the other integration limits recorded in R3. No whole-BAC, package, release, native-admission or full-suite PASS is claimed.

Before and after this prose write, read-only `GIT_OPTIONAL_LOCKS=0 git diff --cached --quiet e9d41bceb2d4a817b4f085a90ad123778858318e` and unstaged tracked-diff checks passed; HEAD and all five source hashes/counts matched. The historical review hash stayed unchanged. This report is ignored. No project imports/runtime/tests, sixth source/helper, source/index/staging/commit changes, branch/worktree/copies/deletion or subdelegation occurred. Only this prose binding was written. Existing project/session authority applies; no failed proposed governance rule supplies either a grant or restriction. Reviewer is stationary.
