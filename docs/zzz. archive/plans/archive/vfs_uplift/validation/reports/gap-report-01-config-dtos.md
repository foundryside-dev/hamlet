# Gap Report 01: Config & DTOs

**Agent:** 1
**Scope:** CFG-REQ-001..002, DTO-REQ-001
**Total Requirements:** 3
**Baseline Commit:** b085877dd45ffb9647a2bc3295ee6ce8c94ad845
**Date:** 2025-11-23

## Summary
- ✅ DONE: 3
- 🟡 PARTIAL: 0
- ❌ MISSING: 0
- 📝 N/A: 0

## Requirements Analysis

### CFG-REQ-001: Items config split
**Source:** 2025-11-18-items-and-vfs-profiles.md §3.1
**Requirement:** Items use experiment-level catalog (`configs/<exp>/items.yaml`) for types/interactions and level-level files for spawn/inventory; no implicit defaults.

**Status:** ✅ DONE

**Evidence:**

**Implementation:**
- DTO Location: `/home/john/hamlet/src/townlet/config/items_config.py`
  - `ItemsCatalogConfig` (lines 221-263): Experiment-level catalog with version, item_types, max_items_per_agent, max_items_in_world
  - `ItemTypeConfig` (lines 138-219): Item type definition with id, vfs_profile, interactions, duration, cooldown
  - `ItemsAppearanceConfig` (lines 386-397): Level-specific spawn rules
  - `ItemAppearanceRuleConfig` (lines 340-384): Spawn rule with item_type, spawn_count, placement, schedule
  - All DTOs use `extra="forbid"` (lines 25, 84, 141, 224, 269, 316, 343, 389)
  - Required fields use `Field(...)` pattern (lines 164, 226, 233, 235, 345, 347, 391)

**Config Files:**
- Experiment-level: `/home/john/hamlet/configs/test/items_smoke/items.yaml` (catalog with 3 item types)
- Level-specific: `/home/john/hamlet/configs/test/items_smoke/levels/L0_smoke/items.yaml` (appearance with 3 spawn rules)
- 20+ config packs found using the split structure

**Tests:**
- Unit tests: `/home/john/hamlet/tests/test_townlet/unit/items/test_items_dto.py` (18 tests)
  - `test_item_type_minimal` (line 17): Validates required fields
  - `test_items_catalog_minimal` (line 93): Validates experiment-level catalog
  - `test_items_appearance_minimal` (line 148): Validates level-specific appearance
  - `test_items_catalog_requires_version_and_limits` (line 232): Validates no defaults for version/limits
  - `test_items_catalog_rejects_unknown_fields` (line 265): Validates `extra="forbid"`
  - `test_items_catalog_from_yaml` (line 192): Validates loading from YAML
  - `test_items_appearance_from_yaml` (line 212): Validates loading level appearance
- Integration coverage: 15+ test files reference `ItemsCatalogConfig` or `ItemsAppearanceConfig`

**Compiler Integration:**
- Scoping validation: `/home/john/hamlet/src/townlet/universe/compiler.py:526` enforces `items.yaml` at experiment root
- Level validation: Line 551-568 allows level `items.yaml` only for v1.0 ItemsAppearance schema
- Required files check: Line 660 enforces `items.yaml` at experiment level
- Item profile validation: `_validate_item_profile_bindings` (line 1371) ensures item vfs_profile exists
- CompiledUniverse field: `/home/john/hamlet/src/townlet/universe/compiled.py:80` stores `items_catalog: ItemsCatalogConfig | None`
- Serialization: Lines 199, 313 handle catalog serialization/deserialization

**Documentation:**
- Schema docs: `/home/john/hamlet/docs/config-schemas/items.md`
  - File structure: Lines 64-98 document catalog vs appearance split
  - Catalog schema: Lines 74-91
  - Appearance schema: Lines 93-110
  - Complete examples with 3 item archetypes (consumable, durable, collectible)
  - Explicit "no defaults" emphasis in schema documentation

**Error Handling:**
- Unknown item_type reference: Compiler line 1130-1135 raises UAC-RES-ITEM error
- Missing vfs_profile: `_validate_item_profile_bindings` validates profile bindings
- Duplicate IDs: `ItemsCatalogConfig.validate_unique_ids` validator (line 239)
- Invalid fields: `extra="forbid"` rejects unknown fields

**Gaps:** None identified

---

### CFG-REQ-002: VFS profiles file
**Source:** 2025-11-18-items-and-vfs-profiles.md §3.3
**Requirement:** Experiment-level `vfs_profiles.yaml` defines scoped profiles (global/agent/item) with IDs, deps, update rule placeholder, obs mapping; fails on missing refs.

**Status:** ✅ DONE

**Evidence:**

**Implementation:**
- DTO Location: `/home/john/hamlet/src/townlet/config/vfs_profiles_config.py`
  - `VFSProfilesConfig` (lines 276-302): Top-level config with version, global_profile, agent_profile, item_profiles
  - `GlobalVFSProfileConfig` (lines 90-110): Global scope with variables list
  - `AgentVFSProfileConfig` (lines 185-205): Agent scope with variables list
  - `ItemVFSProfileConfig` (lines 251-273): Item scope with profile_name and variables
  - `GlobalVFSVariableConfig` (lines 20-88): Global variable with name, type, initial_value/expression, deps
  - `AgentVFSVariableConfig` (lines 113-182): Agent variable with name, type, initial_value/expression, deps
  - `ItemVFSVariableConfig` (lines 208-248): Item variable with name, type, initial_value/expression
  - All DTOs use `extra="forbid"` (lines 87, 110, 182, 205, 248, 273, 302)
  - XOR validation: `validate_value_xor_expression` (lines 50, 145, 230) enforces exactly one of initial_value/initial_value_mode/expression

**Config Files:**
- Experiment-level: `/home/john/hamlet/configs/test/vfs_profiles_smoke/vfs_profiles.yaml`
  - Global profile with 2 variables (day_count, is_night)
  - Agent profile with 3 variables (motivation, is_crisis, crisis_duration)
  - Item profiles: 2 profiles (food_stats, weapon_stats) with 2 variables each
- 10+ config packs found using vfs_profiles.yaml

**Tests:**
- Unit tests: `/home/john/hamlet/tests/test_townlet/unit/config/test_vfs_profiles_dto.py` (19 tests)
  - `test_global_vfs_variable_with_initial_value` (line 17): Static variable validation
  - `test_global_vfs_variable_with_expression` (line 32): Computed variable validation
  - `test_global_vfs_variable_requires_value_or_expression` (line 47): XOR validation
  - `test_global_vfs_variable_rejects_both` (line 57): Rejects both initial_value and expression
  - `test_agent_vfs_profile_unique_names` (line 107): Validates unique names within profile
  - `test_item_vfs_variable_with_expression` (line 132): Item expression support
  - `test_vfs_profiles_config_complete` (line 171): Full profile loading
  - `test_vfs_profiles_config_optional_sections` (line 200): Optional profiles
  - `test_vfs_profiles_config_requires_supported_version` (line 214): Version validation

**Compiler Integration:**
- Compilation: `/home/john/hamlet/src/townlet/universe/compiler.py:165` `_compile_vfs_profiles` method
- Scoping validation: Line 526 enforces `vfs_profiles.yaml` at experiment root
- Required files check: Line 660 requires `vfs_profiles.yaml` at experiment level
- CompiledUniverse field: `/home/john/hamlet/src/townlet/universe/compiled.py:83-84` stores `compiled_vfs_profiles: CompiledVFSProfiles | None`
- Serialization: Lines 200-201, 314-315 handle profile serialization/deserialization with helpers at lines 474-526
- Expression schema: Line 255 `_build_vfs_expression_schema` integrates VFS vars into expression type checking

**Documentation:**
- Schema docs: `/home/john/hamlet/docs/config-schemas/vfs-profiles.md`
  - Overview: Lines 1-50 explain purpose, benefits, and file location
  - Schema structure: Lines 59-74 document version and three profile types
  - Variable scopes: Lines 80-89 explain global/agent/item scopes
  - Examples: Line 96+ provide complete examples for each scope
  - Type system: Documents primitives, references, tensors
  - Expression support: Documents initial_value vs expression XOR constraint

**Error Handling:**
- Missing vfs_profiles.yaml: Compiler line 660-668 raises error if file missing
- Duplicate variable names: Validators at lines 100, 195, 262 reject duplicates
- Duplicate profile names: Validator at line 292 rejects duplicate item profile names
- XOR violation: Validators at lines 50, 145, 230 enforce exactly one init source
- Tensor shape validation: Lines 66-85, 160-180 validate tensor types require shape
- Unknown fields: `extra="forbid"` rejects unknown fields

**Gaps:** None identified

---

### DTO-REQ-001: DTOs with no defaults
**Source:** 2025-11-18-items-and-vfs-profiles.md §4.1
**Requirement:** Add Pydantic DTOs for items and vfs profiles with `extra="forbid"`, explicit required behavioral fields, and validators for deps/ranges/refs.

**Status:** ✅ DONE

**Evidence:**

**Implementation:**
- Items DTOs: `/home/john/hamlet/src/townlet/config/items_config.py`
  - `extra="forbid"` on all 8 DTOs (lines 25, 84, 141, 224, 269, 316, 343, 389)
  - Required fields use `Field(...)` pattern:
    - `ItemTypeConfig.id` (line 164)
    - `ItemTypeConfig.vfs_profile` (line 166)
    - `ItemTypeConfig.interactions` (line 171)
    - `ItemTypeConfig.name` (line 143)
    - `ItemTypeConfig.icon` (line 148)
    - `ItemTypeConfig.tags` (line 154)
    - `ItemsCatalogConfig.version` (line 226)
    - `ItemsCatalogConfig.item_types` (line 228)
    - `ItemsCatalogConfig.max_items_per_agent` (line 233)
    - `ItemsCatalogConfig.max_items_in_world` (line 235)
    - `ItemAppearanceRuleConfig.item_type` (line 345)
    - `ItemAppearanceRuleConfig.spawn_count` (line 347)
    - `ItemsAppearanceConfig.version` (line 391)
  - Validators:
    - `validate_id` (line 193): Item ID format validation
    - `validate_tags` (line 203): Tags validation
    - `validate_metadata_str` (line 212): Name/icon validation
    - `validate_unique_ids` (line 238): Unique item type IDs
    - `validate_commands` (line 111): Effects command validation
    - `validate_name` (line 34): Custom command name validation
    - `validate_effects` (line 44): Custom command effects validation

- VFS Profiles DTOs: `/home/john/hamlet/src/townlet/config/vfs_profiles_config.py`
  - `extra="forbid"` on all 7 DTOs (lines 87, 110, 182, 205, 248, 273, 302)
  - Required fields (no defaults for behavioral parameters):
    - All variable configs require `name` and `type` (no Field default)
    - Version required: `version: Literal["1.0"]` (line 285)
    - Profile name required for item profiles: `profile_name: str` (line 258)
  - Validators:
    - `validate_value_xor_expression` (lines 50-63, 145-158, 230-239): Enforces XOR between initial_value/initial_value_mode/expression
    - `validate_tensor_shape` (lines 66-85, 160-180): Tensor type shape validation
    - `validate_unique_names` (lines 100-108, 195-203, 262-271): Unique variable names within profile
    - `validate_unique_profile_names` (lines 292-299): Unique item profile names
    - `validate_tensor_disallowed` (lines 242-246): Rejects unsupported tensor types for item profiles

**Tests - No Defaults Validation:**
- Items: `/home/john/hamlet/tests/test_townlet/unit/items/test_items_dto.py`
  - `test_items_catalog_requires_version_and_limits` (line 232): Validates missing version or limits raises ValidationError
  - `test_items_catalog_rejects_unknown_fields` (line 265): Validates `extra="forbid"` with unknown_field
- VFS Profiles: `/home/john/hamlet/tests/test_townlet/unit/config/test_vfs_profiles_dto.py`
  - `test_global_vfs_variable_requires_value_or_expression` (line 47): Missing both raises ValidationError
  - `test_global_vfs_variable_rejects_both` (line 57): Providing both raises ValidationError
  - `test_vfs_profiles_config_requires_supported_version` (line 214): Invalid version raises ValidationError

**Validator Coverage:**
- Items: 7 validators covering ID format, tags, metadata, unique IDs, commands, effects
- VFS Profiles: 5 validators covering XOR constraint, tensor shapes, unique names, unsupported types
- All validators raise clear ValueError with descriptive messages

**Documentation:**
- Items: `/home/john/hamlet/docs/config-schemas/items.md` emphasizes "no defaults" principle
- VFS Profiles: `/home/john/hamlet/docs/config-schemas/vfs-profiles.md` documents required fields and validators
- Both docs provide clear examples of minimal valid configs

**Error Handling:**
- Pydantic ValidationError with clear messages for:
  - Missing required fields
  - Unknown fields (extra="forbid")
  - Invalid field values (validators)
  - XOR constraint violations (VFS profiles)
  - Duplicate names/IDs
  - Type mismatches

**Gaps:** None identified

---

## Recommendations

All three requirements are fully implemented with complete test coverage, documentation, and compiler integration. No action items required.

**Quality Assessment:**
- Implementation: ✅ Complete with proper DTOs, validators, and error handling
- Tests: ✅ 37 unit tests (18 items + 19 VFS profiles) with happy path and error cases
- Integration: ✅ Compiler enforces scoping, validates references, includes in CompiledUniverse
- Documentation: ✅ Schema docs exist with examples and "no defaults" emphasis
- Error Handling: ✅ Clear ValidationError messages for all failure modes

**Notes:**
- The "no defaults" principle is consistently applied across all DTOs
- `extra="forbid"` prevents config drift from unknown fields
- Required behavioral fields use `Field(...)` pattern
- XOR constraint for VFS profiles enforces exactly one initialization method
- Compiler integration ensures config split is enforced at compile time
- 20+ config packs demonstrate practical usage of both systems
