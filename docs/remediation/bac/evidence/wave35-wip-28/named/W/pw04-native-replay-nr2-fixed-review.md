# NR-2 fixed-source independent review

2026-11-14. Independent reviewer task `/root/pw04_native_replay_astra_review`; source-only follow-up to `pw04-native-replay-independent-review.md`, whose SHA-256 remains `fbc50ccf27e18f10ddbe949947fe1aa34c76417a47d483a7ac343d6f9f172b7e`. That original review was not edited. No application imports, tests, runtime experiments, Git operations, branches, worktrees or source copies were performed. Only this new report was authored.

Disposition: NR-2 is addressed in the inspected source. No remaining P1/P2 is identified in the previously bounded native PER/SEQ source scope. Fixed-candidate runtime qualification remains pending R174; this source disposition is not a GREEN result, CUDA qualification or package acceptance.

## Exact candidate and change boundary

The same five complete bodies now total4765 lines, below5000. Unchanged SEQ, shared contract and SEQ tests retain their original hashes. For independent change verification without Git or source copies, removing only PER lines1314–1319 in a streamed hash calculation reproduced its original hash `673c2ffb240604c3134836c8742394f978e73f195eb73750410a817452ef2b73`; hashing the first196 lines of the PER test reproduced its original hash `e84542160183338fa48d386ac3ac26d841611c94d9f358de937b8c2730e6d7fd`. Thus the production delta is exactly the six inspected guard lines, and the test delta is exactly the35 appended lines. No previously reviewed generic route changed.

| Path | Whole-body lines | SHA-256 |
| --- | ---: | --- |
| src/townlet/training/prioritized_replay_buffer.py | 1376 | 0d4394a90cda0cbcf5b65df16ed122cdbae397ada95940403eb8acc4b5c58fad |
| src/townlet/training/sequential_replay_buffer.py | 2020 | 7c474611cb917c72862774b4bc1f8468de4765a8896064d2a1c575e5183d4d0c |
| src/townlet/training/replay_contract.py | 949 | de14dd2005934bee6f564f0aaca532bfefcd962d62a76a3a93efdb60274196c8 |
| tests/test_townlet/regressions/bac/test_native_prioritized_replay_data.py | 231 | 21a5d874a32da714b79d625c09cf5be2190f13aeac061a97947f0733b25fbc89 |
| tests/test_townlet/regressions/bac/test_native_sequential_replay_data.py | 189 | 3197b615625881259acd748a2722fe9fd028d440019b7b0d875941faef184725 |

## Repair assessment

`prioritized_replay_buffer.py:1314` now requires a Mapping, an exact Python int format version, and equality with `PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION` (6). Missing versions, bools, float6, integer subclasses and historical4/5 cannot satisfy this guard. Refusal occurs after genuine parent revalidation inside the fresh real prepare device operation, before generic materialization, reverse-map creation and native-record issuance. It does not bypass admission or completion handling and grants no new publication authority. Existing inventory planning may still inspect the transport before the guard, but no historical candidate is issued or published by that planning.

The two original counterexamples are therefore stopped before format5 can substitute physical-slot IDs/external sampling and before format4 can archive rows and replace active storage with an empty candidate. The generic validator/materializer and their separately supported historical paths remain byte-identical. Current6 still follows the previous complete owned materialization and one-use installer path.

The appended regression parameterizes versions4/5 using a genuine current parent plan, removes exactly the fields absent from the selected historical schema, proves generic validation accepts each transport, and then requires native refusal with an explicit current6 diagnostic. It checks receiver serialization remains unchanged. This isolates the intended distinction and avoids a fake-parent or malformed-schema false positive. The added test does not itself assert ambient RNG unchanged; unchanged invocation/materialization boundaries and the previously reviewed staging coverage do not substitute for any runtime evidence root still requires.

## Runtime provenance and remaining scope

Root reports R173 observed `DID NOT RAISE` for each historical transport before this guard, after generic validation passed; R172 had39 native tests passing, and R173 had four real runner profiles passing. Those outcomes were supplied by root, not executed or independently observed here. They belong to their exact prior candidates and cannot establish this later fixed candidate passed. R174 remains pending at report issuance.

All original review limits remain: actual C publication/consumption and failure completion evidence, complete nonempty state/sample/priority continuation, next real learner update, applicable CUDA hardware and package gates remain root-owned. No additional finding or optional P3 is raised by this six-line repair.
