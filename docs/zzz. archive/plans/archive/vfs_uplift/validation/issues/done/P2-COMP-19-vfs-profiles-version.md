# [COMP-19] VFSProfilesConfig Missing Version Field

**Priority:** P2 (Minor)
**Category:** Compiler / VFS
**Status:** MISSING
**Effort:** 30 minutes

## Description

`VFSProfilesConfig` schema is missing `version` field, unlike other config schemas (EffectsCatalogConfig, ItemsCatalogConfig, DriveAsCodeConfig all have version fields). This creates inconsistency in schema versioning and makes future schema migrations harder.

## Current State

**Inconsistent versioning:**

```python
# src/townlet/items/schema.py
@dataclass
class ItemsCatalogConfig:
    version: str  # ✅ Has version field
    items: Dict[str, ItemDefinition]
    spawn_rules: List[SpawnRule]

# src/townlet/effects/schema.py
@dataclass
class EffectsCatalogConfig:
    version: str  # ✅ Has version field
    effects: Dict[str, EffectDefinition]

# src/townlet/environment/dac_schema.py
@dataclass
class DriveAsCodeConfig:
    version: str  # ✅ Has version field
    modifiers: Dict[str, ModifierSpec]
    extrinsic: ExtrinsicSpec
    # ...

# src/townlet/vfs/schema.py
@dataclass
class VFSProfilesConfig:
    # ❌ Missing version field
    global_profile: Optional[GlobalProfile]
    agent_profiles: Dict[str, AgentProfile]
    item_profiles: Dict[str, ItemProfile]
```

**Current configs:**
```yaml
# vfs_profiles.yaml (in all L0-L3 configs)
# No version field currently
global_profile:
  variables: ...
```

**Desired:**
```yaml
# vfs_profiles.yaml
version: "1.0"  # Explicit schema version
global_profile:
  variables: ...
```

## Required Implementation

### 1. Add Version Field to Schema (5 minutes)

**File:** `src/townlet/vfs/schema.py`

**Changes:**
```python
@dataclass
class VFSProfilesConfig:
    """VFS profiles configuration (global, agent, item scopes)."""
    version: str  # NEW: Schema version for migration tracking
    global_profile: Optional[GlobalProfile] = None
    agent_profiles: Dict[str, AgentProfile] = field(default_factory=dict)
    item_profiles: Dict[str, ItemProfile] = field(default_factory=dict)
```

### 2. Update All Config Files (15 minutes)

**Files to update:**
- `configs/L0_0_minimal/vfs_profiles.yaml`
- `configs/L0_5_dual_resource/vfs_profiles.yaml`
- `configs/L1_full_observability/vfs_profiles.yaml`
- `configs/L2_partial_observability/vfs_profiles.yaml`
- `configs/L3_temporal_mechanics/vfs_profiles.yaml`
- `configs/templates/vfs_profiles.yaml` (template)
- Any test fixture configs with VFS profiles

**Change (add to top of each file):**
```yaml
version: "1.0"
```

### 3. Add Version Validation (5 minutes)

**File:** `src/townlet/vfs/profiles.py`

**Optional: Add version validation in compiler:**
```python
class VFSProfileCompiler:
    SUPPORTED_VERSIONS = ["1.0"]

    @classmethod
    def compile(cls, config: VFSProfilesConfig) -> CompiledVFSProfiles:
        """Compile VFS profiles configuration."""

        # Validate version
        if config.version not in cls.SUPPORTED_VERSIONS:
            raise ValidationError(
                f"Unsupported VFS profiles version '{config.version}'. "
                f"Supported versions: {', '.join(cls.SUPPORTED_VERSIONS)}"
            )

        # Existing compilation logic...
```

### 4. Update Documentation (5 minutes)

**File:** `docs/config-schemas/variables.md`

**Add version field to schema documentation:**
```markdown
## VFS Profiles Configuration Structure

\```yaml
version: "1.0"  # Required - schema version for migration tracking

global_profile:
  variables: ...

agent_profiles:
  player:
    variables: ...

item_profiles:
  consumable:
    variables: ...
\```

### Schema Version History

- **1.0** (2025-11-21): Initial VFS profiles schema
  - Global, agent, item scopes
  - Expression language support
  - Normalization and access control
```

## Acceptance Criteria

- [ ] `VFSProfilesConfig` has `version: str` field
- [ ] All L0-L3 config `vfs_profiles.yaml` files have `version: "1.0"`
- [ ] Template `vfs_profiles.yaml` has `version: "1.0"`
- [ ] All test fixture VFS profile configs updated
- [ ] Optional: Version validation in VFSProfileCompiler
- [ ] Documentation updated with version field
- [ ] Schema version history documented
- [ ] All configs compile successfully with new version field
- [ ] No regression in VFS functionality

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-compiler.md
**Schema:** `src/townlet/vfs/schema.py:VFSProfilesConfig`
**Config files:** All curriculum level configs with `vfs_profiles.yaml`

## Implementation Notes

**Why P2 (not P1/P0):** Schema versioning is good practice but not critical. Current system works without explicit versioning. This is about consistency and future-proofing for schema migrations.

**Schema Versioning Purpose:**
1. **Migration tracking:** When schema changes, version bump signals migration needed
2. **Backward compatibility:** Can detect old schema versions and apply migrations
3. **Consistency:** All major config files should have version fields
4. **Documentation:** Clear history of schema changes over time

**Version Numbering:**
- Use semantic versioning: "MAJOR.MINOR" (e.g., "1.0", "1.1", "2.0")
- Major version: Breaking schema changes (field removed, field type changed)
- Minor version: Additive changes (new optional field, new enum value)
- Current version: "1.0" (initial VFS profiles schema from VFS uplift)

**Future Schema Evolution Examples:**
- **1.1**: Add tensor types (tensor1d/2d/Nd) → minor version bump
- **1.2**: Add reference type resolution → minor version bump
- **2.0**: Remove deprecated field, change field type → major version bump

**Version Validation Strategy:**
- Option 1 (strict): Reject unknown versions → forces explicit support for new versions
- Option 2 (lenient): Warn on unknown versions → allows forward compatibility
- Recommendation: Strict validation (fail fast on version mismatch)

**Migration Path (when needed in future):**
```python
class VFSProfileMigrator:
    """Migrate VFS profiles configs between schema versions."""

    @staticmethod
    def migrate(config: dict, from_version: str, to_version: str) -> dict:
        """Migrate config from old version to new version."""
        if from_version == "1.0" and to_version == "1.1":
            # Example: Add default values for new fields in 1.1
            return VFSProfileMigrator._migrate_1_0_to_1_1(config)
        # Add more migration paths as schema evolves
```

**Testing:**
- Unit test: VFSProfilesConfig with version field parses correctly
- Integration test: All L0-L3 configs compile with version field
- Validation test: Unsupported version raises clear error
- Test: Missing version field raises validation error (make it required)

**Config File Updates:**
All `vfs_profiles.yaml` files should start with:
```yaml
version: "1.0"

global_profile:
  # existing content...
```

## References

- Schema file: `src/townlet/vfs/schema.py:VFSProfilesConfig` (add version field)
- Compiler: `src/townlet/vfs/profiles.py:VFSProfileCompiler` (add version validation)
- Config files: All `configs/*/vfs_profiles.yaml` files (add version: "1.0")
- Documentation: `docs/config-schemas/variables.md` (document version field)
- Related: Schema versioning patterns in other config types (effects, items, DAC)
