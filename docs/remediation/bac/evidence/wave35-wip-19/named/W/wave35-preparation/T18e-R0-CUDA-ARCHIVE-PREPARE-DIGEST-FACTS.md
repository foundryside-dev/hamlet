# Archive preparation digest supplier facts

Root source-verified, 2026-11-13. This is a read-only supplier capsule for the bounded clone-stability test author; it grants no family body read or source edit.

- historical_checkpoint.py615–616 `_record` clones every dataclass field, including source_digest, with `_clone`.
- Flat `_prepare_serialized`764–765 validates then materializes. `_materialize_serialized` current-state branch710–731 creates each archive record with history._record, clones the resulting mapping, then revalidates before allocation. `_own_archive`219–222 also records/reconstructs an archive.
- PER `_prepare_serialized`1251–1252 likewise validates then materializes. Its current-state branch1198–1207 records each archive, clones and revalidates. `_own_archive`440–443 also records/reconstructs it.
- Consequently an accepting digest Tensor subclass that loses its comparison subclass on detach/clone is not an established public-prepare-success fixture. Direct helper acceptance and raw validation do not prove materialization acceptance.

Root fixture ruling: preserve both raw validate-plan/prepare-plan missing-digest-device witnesses with the accepting comparison operand, plus their direct-helper positives. For the new public prepare success variant, retain the original genuine canonical digest string from the valid four-row archive instead of replacing it with the accepting comparison subclass. The count-changing source_formats/sibling hook restores the original four-row metadata, so that original digest is the appropriate source-established oracle through record/clone/revalidation. Its expected source inventory omits the now-absent digest device1 but retains archive2/live3 and prepare target4. Public validate may retain the accepting comparison fixture. All original757 nodes and10children remain. These new public cases remain B-dependent UNRUN until activation; qualify the genuine digest helper fixture now, before asserting later public success. This adjusts an unexecuted fixture, not runtime capability or required preparation coverage.

Exact source seals:
- src/townlet/training/historical_checkpoint.py: `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4`
- src/townlet/training/replay_buffer.py: `683e0b9b0f500cc523391b8574acbfc31bf8dc8a36d92ad0547323621261838d`
- src/townlet/training/prioritized_replay_buffer.py: `7a76183ded0712103c81ebd31b3e05425b3738e9338689cacfbefbc8fd493a29`
