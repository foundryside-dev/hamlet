# Declaration discovery and authoring transport

Declaration-store Cut A supplies content discovery; Cut B supplies the single canonical
[variable contract](variables.md). Configuration DTOs form the closed content vocabulary.
This authoring path does not establish BAC cognition, all runtime contracts, rendering or convergence.

## Scope and discovery

The compiler reads every `.yaml` and `.yml` document recursively within the pack, excluding
`.compiled`. A file can contain multiple documents separated by `---`, or a document can contain
several existing wrapped sections. Unknown, ambiguous, malformed or misplaced content is a
compile error; arbitrary stray YAML is not silently ignored. Directory symlinks, escaping
transports and broken YAML symlinks are refused; recursive YAML aliases are also refused.

Files outside `levels/` belong to pack scope. Files under `levels/<id>/` belong to that level;
extra subfolders within either scope are transport. For example,
`levels/L0/mechanics/rewards.yml` can carry the same `drive:` declaration as the conventional
`levels/L0/drive.yaml`. Moving a level declaration out of its scope changes its meaning or makes
it invalid. There is no filename reader, alias list or compatibility path.

## Closed declaration families

Required families are checked after discovery and merge. These are declarations, not required
filenames. A recognized shape still undergoes its existing strict DTO validation: recognition
does not permit omitted required fields or extra keys.

| Scope | Family | Existing content shape | Required |
| --- | --- | --- | --- |
| Pack | Experiment | `experiment:` mapping | Yes |
| Pack | Stratum | `stratum:` mapping | Yes |
| Pack | Environment | `environment:` mapping | Yes |
| Pack | Actions | `actions:` mapping | Yes |
| Pack | Brain | Bare configuration identified by `architecture` and `optimizer` | Yes |
| Pack | Variables | `variables:` mapping with explicit declarations and evaluator settings | Yes |
| Pack | Item catalog | `items:` mapping containing `item_types` | No |
| Pack | Effects | Bare configuration identified by `effect_definitions` | No |
| Pack | Transition rules | Bare configuration identified by `social_residue` | No |
| Pack | Action labels | Bare configuration identified by `custom` | No |
| Pack | Observer presentation | Bare `version` with `meters` and `affordances` mappings | No |
| Level | Curriculum | `curriculum:` mapping | Yes |
| Level | Meters and cascades | `bars:` mapping | Yes |
| Level | Affordances | `affordances:` mapping | Yes |
| Level | Reward drive | `drive:` mapping | Yes |
| Level | Training | `training:` mapping | Yes |
| Level | Brain override | Complete bare brain configuration | No |
| Level | Item appearance | Bare `version` with `items` list | No |

Only the listed wrapper and bare shapes are accepted; there are no wrapper aliases.
Variables use their single wrapped canonical contract. A level brain replaces the pack brain completely; it is not a partial
configuration patch. Empty required families remain explicit rather than becoming defaults.

A file combining two wrapped sections can look like this schematic excerpt:

```yaml
# levels/L0/mechanics.yml — include every field required by each family DTO
bars:
  version: "1.0"
  # ... complete meter and cascade declarations ...
---
drive:
  version: "1.0"
  # ... complete reward declaration ...
```

The omitted fields make this an illustration of transport, not a runnable pack. The family
references and shipped packs supply full field examples.

## Identity, fragments and order

Singleton identity is `(scope, family)`. Two singleton declarations collide even when their
values are identical. Named catalog entries use the existing identifier (`name`, `id` or profile
name), qualified by family/profile; cascades use their ordered source/target pair. Duplicate
entries fail with **both actual declaring `file:line` origins**. Different families and distinct
profile namespaces retain their own identities; filename changes do not create new entities.

Catalog fragments merge in sorted pack-relative path order, then document order within each
file. Each authored array keeps its order. Repeated structural headers must agree; fragments are
not last-writer-wins patches. Item appearance remains a singleton per level because its ordered
rules have no declared rule identifier.

Action-label keys are explicit YAML integers; quoted numeric keys are refused. Two keys
that would resolve to the same numeric identifier collide before any coercion can overwrite one.
The variable catalog has one explicit initialization, lifetime and exposure contract. Historical
profile and static-overlay shapes are refused. See [the variable reference](variables.md).

Array ordering is part of the existing semantics and ABI. Do not alphabetize entity arrays to
make discovery appear deterministic. Moving fragments so their relative order changes can
change semantics. With equivalent content and ordering, transport relocation may change
`metadata.config_hash` while preserving compiled semantic hashes. Source locations continue to
identify the real document after relocation or combination.

## Clock period reference

An active level can use a single authored clock period:

```yaml
curriculum:
  version: "1.0"
  active_vision: global
  vision_range: 0.5
  active_temporal: true
  day_length:
    period_of: day_phase
```

`day_phase` must identify a declared global temporal variable derived from ambient engine
`tick`, with cyclical normalization. Discovery resolves its normalization `period` before
constructing the existing curriculum DTO. The period must be finite, positive and integral;
missing, ambiguous or wrong-kind targets refuse. The resulting runtime `day_length` is the same
integer value the DTO consumed before this front-end reference existed.

If a pack declares the coupled ambient-tick clock, an active literal day length supplies a
second authority for its period. Author the reference instead: equal or conflicting duplicated
clock facts are refused with both origins. This does not ban a literal day length in a world
with no such declared clock. Inactive levels continue to
state `active_temporal: false` and `day_length: null`; they do not acquire active clock behavior
because a pack-level clock variable exists.

The reference changes authoring authority only. It does not redesign time units, clock runtime,
normalization, observation or reward semantics.

## Observer metadata boundary

Discovery recognizes and validates optional presentation metadata against `PresentationConfig`,
so it has a disposition rather than being stray YAML. It contributes to transport
`metadata.config_hash` but does not become an execution product or enter semantic hashes.

The live observer's separate presentation adapter still loads the conventional pack-root
`presentation.yaml`. Cut A changes the compiler front end, not that UI loader. Relocating or
combining a presentation declaration is accepted by discovery but does not make the observer
follow it; display transport is a UX follow-on. Keep presentation in its conventional file when
using that adapter. See [presentation configuration](presentation.md).

## References and acceptance boundary

- [Compiler front end](../architecture/COMPILER.md)
- [Cut A implementation plan](../plans/2026-10-01-declaration-store-cut-a.md)
- [PDR-0117: files are transport](../product/decisions/0117-files-are-transport-declarations-are-the-unit.md)

Functional acceptance must compare the baseline semantic hashes and prove discovery, merge,
source diagnostics and clock resolution. The owner extended the Cut A date; its accepted
checkpoint is recorded in PDR-0149. Cut B has its own evidence gate in PRD-0003. Neither
authoring checkpoint establishes full compiler completion or learned-scenario convergence.
