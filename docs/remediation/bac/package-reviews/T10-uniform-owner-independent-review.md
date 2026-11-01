# Uniform owner alignment independent static review

Verdict: PASS for the bounded test-maintenance changes. No concrete P1/P2 defect or newly vacuous corruption control found in those changes. This is not a runtime pass, full T10 approval, or whole-BAC acceptance.

Review basis: HEAD 214408b107730b4511b8a690541569aeca4b7b67; supplied staged identity 6d27f905fac6e6942db2708db6415db3c5c8fb53. Read all four allowed source files (3011 charged lines), their HEAD-relative test diff and production diff context, T10/P2 plan prose, task T10 metadata, INTERFACE-CLARIFICATION.md and PRESERVATION-SUPPLEMENT.md. No additional implementation/test source was opened. No project imports, tests, probes, code/index edits, checkout creation or delegation occurred. Only this ignored review note was written.

Verified on-disk SHA256 identities:

- src/townlet/training/replay_buffer.py (637): a5cfd50d629f2f669f6252208c40725a97115780bc1cf6e1c8ae8a344159b99f
- tests/test_townlet/unit/training/test_replay_buffers.py (1619): 61b688ea5fa7ef31d023b76b9ea3e48cc57e27787a19bee21eacd10071d647d9
- tests/test_townlet/unit/training/test_replay_buffer_components.py (419): 639e83cdf9a050a97edb0417aba1a89b507e329b2bfe2e4a438ce71ea8e3b6ce
- tests/test_townlet/properties/test_replay_buffer_properties.py (336): 5678e826ce7fcb0574deb23441cc54b9e355b3c7adc446595269e2d7ae628a17

The current artifact assertions correctly move uniform4 to uniform5 and enumerate the complete closed key set, including action width/mode, successor masks, legality, component presence and archives. Exact-integer rejection uses current5.0 and True; future rejection uses6. Unsupported1/2/3/missing-version controls remain explicit and their regexes identify the version refusal rather than accepting unrelated malformed-payload failure. Existing wrong-kind, missing/unknown-key and tensor-dtype/shape corruption controls remain intact and operate on current serialized payloads.

New expected values match the public unconstrained producers used by these tests: no action width/masks, false legality, no archives, true presence for provided components and false presence/None serialization for absent components. Restore intentionally recreates zero storage placeholders for wholly absent components, so the property test's storage comparisons remain meaningful. The two exact memory assertions add four capacity-sized bool columns (one legality and three component-presence), with no mask allocation for these unconstrained inputs; arithmetic is 690 bytes for capacity10/obs_dim5. Existing component, circular order, full-buffer sampling and restore assertions are retained. Recurrent tests are unchanged and their formats are not conflated with uniform5.

The original insufficient-size diagnostic assertion at test_replay_buffers.py:289 is intentionally unchanged. The reviewed production _indices message lacks '<', so that known owner failure still requires its production repair; the test-maintenance PASS does not hide or waive it. The supplied original native fixture preservation and separate HC callback results are coordinator evidence, not independently executed or revalidated here. Archive/mixed-mask feature regressions outside this four-file scope remain owned by their separate reviews and gates.
