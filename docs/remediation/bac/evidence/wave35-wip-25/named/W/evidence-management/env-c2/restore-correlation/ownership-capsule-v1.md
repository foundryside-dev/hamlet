# C3 prepared-world ownership supplier v1

2026-11-14. Static source supplier by Astra; no execution or implementation approval. This closes the requested defining-body ownership question, not ENV/core implementation review. Root authorized exactly two additional whole bodies. Both were measured and hashed before inspection; the cumulative packet is five files / 3640 source lines.

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/config/exploration_policy.py` | 1343 | `5c5410d8bf6213f42cab3b18925efb164eec4670dd7f8c10b31af305f8a32363` |
| `src/townlet/exploration/scoped_curiosity.py` | 1492 | `110d640bdb607fd58d6e991dba49da2cc5236f169cc4c1db45627db6b8082f7c` |
| `src/townlet/exploration/parent_custody.py` | 239 | `1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f` |
| `src/townlet/config/world_roster.py` | 312 | `1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33` |
| `src/townlet/vfs/random_draws.py` | 254 | `751e5766b5efd99a79ccc86c410d76534c397ed9ece59ca67cf2ae4fd83ef676` |

The first three bodies were already owned; only the last two were added this iteration. ENV/helper/core/CP/native/test bodies were not added. ENV issuance and metadata are attributed to `env-independent-design-review-v2.md` SHA256 `3b348e8d60732309fc22077ff91b8765bb9bd6448b53fc61ca32772dadbb7280`. Core currency is attributed to `core-currency-supplier-v1.md` SHA256 `b24eab4821f3b5bf73d663acd8dc5e8733838e93b9bb2327cf727f3b72a7395b`.

## Defining-body facts

References in this section are to `world_roster.py` at the hash above.

- `WorldRecord`93–112 is a frozen, identity-equality dataclass. `__getattr__`102–108 passes public payload values through `owned_value`; `payload`110–112 returns a fresh dictionary with owned values. These public accessors do not expose the original mutable list/dictionary/tensor leaves. Frozen dataclass status is cooperative Python API protection, not protection against private/object-level mutation.
- `owned_value`128–144 deliberately preserves opaque `WorldRecord`, reservation and accepted-capability identities. Tensor values are detached/cloned. Mapping/list/tuple values are recursively copied; `_FrozenList`124 transports back to an ordinary list. Only the supported primitive scalars are returned directly. Unsupported value types refuse.
- `frozen_value`147–156 recursively builds a new `MappingProxyType`, `_FrozenList` or tuple. Other values pass through `owned_value`. Thus its containers are immutable and owned; **not every possible leaf is immutable**. A Tensor leaf is a newly owned mutable Tensor; an opaque WorldRecord leaf preserves capability identity.
- `same_value`159–183 is not a suitable callback currentness primitive: it can call tensor equality, recursively traverse payloads and invoke ownership accessors.
- `validate_world_snapshot`186–312 validates the exact world-lifecycle-v4 key set, roster/semantic/seed/binding/cursor/VFS/history relationships, and returns recursively owned material. INITIAL254–263 requires the initial zero/history/binding conditions. COMPLETED264–312 validates its actual history and last-closed structure. `last_closed_episode.completion_content` is a required key but has no further type/content validation here. Consequently this validator does **not** prove that every accepted completed payload is a tree of immutable primitive values. A proposed primitive-only seal must not silently narrow this existing parser capability.

References below are to `vfs/random_draws.py` at the hash above.

- `VFSWorldContext`79–96 validates the actual nonnegative exact integer seed, exact tuple of unique nonempty exact string world IDs, and matching exact integer sequence tuple. The context is frozen.
- `VFSRandomness`116–133 holds that context and derives immutable world keys. `state`135–143 constructs a fresh dictionary containing primitive schema/domain/seed values and fresh world-ID/sequence lists. It does not read or advance a generator, construct a Tensor, issue an owner capability or enter a custody operation.
- `validate_state`145–158 validates exact keys/schema/domain/list representation, reconstructs a validated context and compares it to the expected context. The ordinary built-in mapping profile is pure Python metadata validation. Arbitrary caller-supplied Mapping implementations can run their own access methods; this is not a blanket purity promise for user-defined objects.
- Tensor-producing draw methods are separate later methods. The purity of `state()` is not a claim that every VFS method is tensor-free or that a whole simulator is independently restored.

## Concrete consequence for C3

Retain an issuer-owned preparation seal at the genuine ENV issuance cut. It links the **exact issued record and original private `_payload` object identity** to the already-validated receiving metadata. Keep a separate immutable metadata projection for the callback predicate: actual receiving seed, exact lane-ID tuple, semantic identity, issuing generation/revision and genuine owner/binding identities. Do not reconstruct that projection through public accessors during a callback. The preparation already owns its payload containers and Tensor copies; public access does not mutate those copies. Preserve opaque nested capability identities and their existing meaning rather than claiming that they become primitive content.

The mandatory callback check authenticates the real scope, issuer weak registry/seal and metadata, then checks original private payload identity. It neither traverses payload leaves nor invokes accessors/`same_value`/Tensor operations. Content and independent journal/cadence comparisons remain the actual existing preparation/consumer comparisons. This is authority/currentness checking under the supported cooperative API, not raw-private-mutation detection or a second portable snapshot validator. No new payload schema restriction, device/profile restriction, physical-state freeze or serialization format is needed.

A fresh ENV implementer must store seals without retaining otherwise dead records through weak-registry value cycles. An active composed attempt may strongly retain its selected genuine record and owners; unrelated ordinary preparations remain valid. Successful preparation, not a caller-created seal or equal-valued record, establishes authority.

## Limits

These are actual source-qualified ownership facts for the stated five-file packet. ENV's call-site issuance and fresh-bound field mapping remain independently supplied, not inspected here. No imports, tests, probes, source writes, Git operations, copied implementation, delegation or new checkout occurred. Callback purity applies to the proposed metadata path; existing public accessors may allocate device Tensor copies and therefore must not be used to implement that path.
