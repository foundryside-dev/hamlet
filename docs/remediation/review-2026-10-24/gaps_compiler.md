## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_compiler.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| C1 | P1 | Artifact never serializes `items_appearance`; cached compiles run item-less worlds | F1 |
| C2 | P1 | Five pack hashes plus `config_hash` stamped and compared by nobody; stratum edits resume silently | F2, hamlet-2dde1015fe |
| C3 | P2 | Item catalog nullified on `max_items_per_agent == 0` or `max_items_in_world == 0`, misleading refusal | F3, hamlet-45f501e15b |
| C4 | P2 | Required fields with zero consumers across experiment, environment, training and DAC DTOs; `capability_config.py` whole | F4 |
| C5 | P2 | `RecordingConfig` is `extra="allow"`; typos enter `training_hash` | F5 |
| C6 | P2 | `metadata.py:72` branches on `"money"`; fills dead fields | F6 |
| C7 | P2 | `presentation` discovered by content at compile, read by filename at runtime | F7 |
| C8 | P2 | No discriminator for parameter-identical variables; affordances and effects never checked | hamlet-2aca57c0f0, effects F15 |
| C9 | P2 | `inspect --format json` omits row layout and offsets | hamlet-53bce4af41 |
| C10 | P3 | CLI refusals as tracebacks | F8 |
| C11 | P3 | Cache fingerprint path- and cwd-blind; `inspect` never checks freshness | F9 |
| C12 | P3 | Effects DTO residual defaults | F10 |
| C13 | P3 | Residue: dead constant, dead whitelist entries, un-compilable fixture, dead script path, zero-caller methods | F11 |
| C14 | P3 | Two wall-clock ratio asserts in the default selection | hamlet-f9090ec3e8 |
