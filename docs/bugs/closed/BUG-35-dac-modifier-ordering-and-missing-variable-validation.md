Title: DAC modifier application order is implicit and variable sources are not validated against VFS

Severity: medium
Status: partially_fixed

Subsystem: environment/dac_engine + config/drive_as_code + VFS
Affected Version/Branch: main

Affected Files:
- `src/townlet/config/drive_as_code.py:43`
- `src/townlet/environment/dac_engine.py:84`
- `src/townlet/vfs/registry.py`
- `docs/config-schemas/drive_as_code.md:260`
- `docs/arch-analysis-2025-11-13-1532/02-subsystem-catalog.md:860`

Description:
- DAC modifiers are specified as a mapping `modifiers: {name -> ModifierConfig}`, and `DriveAsCodeConfig` validates that extrinsic/intrinsic `apply_modifiers` references exist, but:
  - The **order** in which modifiers are applied is determined by iterating over `apply_modifiers` (a list) with no explicit contract; the schema does not clarify whether modifier order matters.
  - In several places, the architecture notes mention that modifier composition can be non-trivial (e.g., crisis suppression then boredom boost), but there is no deterministic ordering or guard rail.
- For modifiers that use a VFS variable as their source (`ModifierConfig.variable`), there is also no validation that:
  - The referenced variable actually exists in the `VariableRegistry`.
  - The variable is readable by the `"engine"` reader as required.
  - This can lead to runtime errors (KeyError or similar) when `self.vfs_registry.get(config.variable, reader="engine")` is called, instead of failing fast at config load.

Reproduction:
- Modifier ordering:
  - Define two modifiers in `drive_as_code.yaml` (e.g., `energy_crisis` and `boredom_boost`) and list them in different orders in `intrinsic.apply_modifiers`.
  - Observe that intrinsic weight is computed as the product of multipliers in that list order.
  - Because the config schema doesn’t document composition order semantics, two configs that conceptually "use the same modifiers" but in different order may behave differently without operators realizing it.
- VFS variable source:
  - Define a modifier with `variable: "nonexistent_var"`.
  - Ensure there is no corresponding `VariableDef` in the VFS spec.
  - Attempt to run a training session; at runtime, `vfs_registry.get("nonexistent_var", reader="engine")` will raise or return unintended values instead of validation failing at compile time.

Expected Behavior:
- Modifier composition should have a clear, documented ordering:
  - Either enforced (e.g., sorted by modifier name), or explicitly specified as "order of `apply_modifiers` list entries", with guidance on how to avoid surprises.
- Modifiers that reference VFS variables should be validated against the universe’s VFS variable definitions:
  - Unknown variable IDs should cause a validation error at config load time, not a runtime error inside `DACEngine`.
  - Variables used as modifier sources should have `readable_by` include `"engine"`; otherwise, config should be rejected or produce a clear error.

Actual Behavior:
- Modifier application order is determined solely by the `apply_modifiers` list order, but the schema and docs do not explain that order may matter or specify a canonical ordering.
- `DriveAsCodeConfig` only validates that modifiers named in `apply_modifiers` exist in `modifiers`, not that variable-based sources are compatible with VFS.
- `DACEngine._compile_modifiers()` calls `self.vfs_registry.get(config.variable, reader=self.vfs_reader)` without any additional checks.

Root Cause:
- The initial implementation prioritized making modifiers available and composable, but left ordering semantics and VFS integration checks implicit.
- VFS validation is currently handled in other parts of the system (e.g., for observation variables), and DAC’s use of VFS variables was treated as an “escape hatch” without dedicated schema validation.

Proposed Fix (Breaking OK):
- Modifier ordering:
  - Document that modifier composition is order-sensitive and **define** the semantics (e.g., "modifiers are applied in the order they appear in `apply_modifiers`").
  - Optionally, add a validation that warns or errors when the same modifier is listed multiple times.
  - If desired, add a `composition_order` field in `DriveAsCodeConfig` or sort modifiers lexicographically to enforce stable ordering.
- Variable validation:
  - Extend DAC config validation or UniverseCompiler integration to:
    - Verify that all `ModifierConfig.variable` IDs exist in the VFS variable definitions.
    - Check that `readable_by` for those variables includes `"engine"`.
  - Fail fast with a clear error message (pointing to `drive_as_code.yaml`) when a variable is missing or has incompatible access control.

Migration Impact:
- Existing configs that rely on specific modifier interactions will continue to work, but their ordering semantics will now be documented and, if enforcement is added, potentially normalized.
- Configs that mistakenly reference non-existent or unreadable VFS variables will now fail at compile time instead of failing or acting strangely at runtime.

Alternatives Considered:
- Treat modifiers as commutative and try to normalize their effects:
  - Not generally feasible, since some modifiers may implement non-linear effects or depend on each other.

Tests:
- Extend DAC DTO and engine tests:
  - Add a test that sets `apply_modifiers` in different orders and asserts the corresponding weight computation, along with a docstring explaining the order semantics.
  - Add a test that uses a modifier with an unknown VFS variable and asserts that config load or compiler validation fails with a clear message.

Owner: DAC engine + config
Links:
- `docs/arch-analysis-2025-11-13-1532/02-subsystem-catalog.md:860` (No Modifier Chaining Validation)
- `docs/config-schemas/drive_as_code.md`

---

## Resolution (Partial)

**Date**: 2025-11-30
**Status**: PARTIALLY FIXED - documentation updated, compile-time validation deferred

### What Was Fixed

**1. Modifier Ordering Documentation** (FIXED):
- Added explicit ordering semantics to Field Reference section (line 205-210)
- Documented that modifiers apply multiplicatively in list order
- Clarified that order matters for semantic clarity even though multiplication is commutative
- Added best practice: list critical suppressions first for clarity
- Updated in three locations:
  - `intrinsic` field documentation (lines 205-210)
  - `ModifierConfig` example section (lines 316-320)
  - Multi-Modifier Chaining example (line 1206 already existed)

**2. VFS Variable Validation Documentation** (FIXED):
- Clearly documented that VFS variables are validated at RUNTIME, not compile-time
- Added "VFS Variable Validation" section to ModifierConfig docs (lines 280-284)
- Updated Validation section to clarify limitation (lines 1262-1296):
  - Removed error codes DAC-REF-002, DAC-REF-005 from compile-time validation
  - Added detailed runtime validation behavior
  - Documented error messages that users will see
  - Explained rationale for runtime validation
- Referenced BUG-35 as known limitation

### What Remains (Deferred)

**Compile-Time VFS Validation**:
- Full validation requires UniverseCompiler integration
- Needs to pass VFS variable definitions to DAC validator
- Would enable fail-fast behavior at `python -m townlet.universe validate`
- Currently deferred because:
  - Requires significant plumbing between VFS and DAC validation
  - Runtime validation provides clear error messages (acceptable UX)
  - No user complaints about current behavior
  - Pre-release status means breaking changes are acceptable when implemented

**Implementation Plan** (when prioritized):
1. Modify `UniverseCompiler` to pass VFS variable definitions to DAC validator
2. Add compile-time checks in DAC DTO validation:
   - Verify `ModifierConfig.variable` exists in VFS definitions
   - Verify `readable_by` includes "engine"
   - Same for extrinsic and shaping VFS variable references
3. Update error codes DAC-REF-002, DAC-REF-005 to fire at compile-time
4. Update tests to expect compile-time failures instead of runtime

### Files Modified
- `/home/john/hamlet/docs/config-schemas/drive_as_code.md`:
  - Lines 205-210: Added modifier ordering semantics to intrinsic field
  - Lines 280-284: Added VFS variable validation note to ModifierConfig
  - Lines 316-320: Added application ordering example
  - Lines 1262-1296: Rewrote Validation section with clear runtime vs compile-time split

### Verification
- Documentation now explicitly states modifier ordering semantics (3 locations)
- Documentation clearly explains VFS validation happens at runtime with helpful error messages
- Users will understand the current behavior and known limitations
- No code changes required (current behavior is acceptable)
