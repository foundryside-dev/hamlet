# NR-2 final guard source addendum

2026-11-14. Independent reviewer task `/root/pw04_native_replay_astra_review`. This new addendum preserves both earlier review records. Only the requested PER guard was read; no other code, Git, imports or runtime execution was performed. No production/test source was edited.

Final PER body: `src/townlet/training/prioritized_replay_buffer.py`,1377 lines, SHA-256 `ecf9ea033c23142aea49ffc47c7ad39a51c4635ef3cdf7df8f550d1fca4154fc`. The existing five-body scope totals4766 lines with the previously reviewed companion bodies. Removing just guard lines1314–1320 in a streamed hash calculation reproduces the original PER hash `673c2ffb240604c3134836c8742394f978e73f195eb73750410a817452ef2b73`, confirming no other production change relative to the original review. No source copy was created.

The actual guard short-circuits in this order: Mapping requirement; explicit `format_version` membership; exact Python int type; equality with current version6. For ordinary transport mappings, a missing key reaches the intended ValueError without indexing the absent key. Non-mappings refuse before membership/indexing. Historical4/5, bools, float6 and integer subclasses still refuse. Removing `.get` does not introduce a fallback or implicit version.

The guard remains after genuine parent revalidation inside the fresh prepare device operation and before `_prepare_serialized`, reverse-map construction and native-data issuance. Generic historical routes remain unchanged. NR-2 remains addressed in this final source; no new P1/P2 identified from the adjustment.

Root reports R174 had540 passing tests before this tiny change and that the `.get` introduced an extra defaults-guard violation (601 against600). Those are root-supplied earlier-candidate outcomes, not independently executed here. R175 targeted runtime remains pending at issuance; neither R174 nor this source review establishes a pass for the final hash. All previous runtime, CUDA and package qualification limits remain unchanged.
