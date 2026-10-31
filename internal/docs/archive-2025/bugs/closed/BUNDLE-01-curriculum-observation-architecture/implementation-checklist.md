# Config v2.1 Implementation Checklist

**Branch**: feature/config-v2.1
**Status**: ✅ COMPLETE
**Date Completed**: 2025-11-15

## Phase 0: Prerequisites
- [x] Create BarsV2Config DTO
- [x] Create AffordancesV2Config DTO
- [x] Create TrainingV2Config DTO

## Phase 1: Setup & Safety Net
- [x] Create feature branch
- [x] Archive old configs
- [x] Capture baseline test results
- [x] Create implementation checklist

## Phase 2: Create Model Config from Template
- [x] Create directory structure
- [x] Extract experiment.yaml from reference
- [x] Extract stratum.yaml from reference
- [x] Extract environment.yaml from reference
- [x] Extract actions.yaml from reference
- [x] Extract agent.yaml from reference
- [x] Extract curriculum.yaml from reference (L1)
- [x] Extract bars.yaml from reference (L1)
- [x] Extract affordances.yaml from reference (L1)
- [x] Extract training.yaml from reference (L1)

## Phase 3: DTO Creation
- [x] Create experiment_config.py
- [x] Create stratum_config.py
- [x] Create environment_config.py
- [x] Create actions_config.py
- [x] Create agent_config.py
- [x] Create curriculum_config.py
- [x] Test DTOs load successfully

## Phase 4: Compiler Updates
- [x] Update compiler to detect v2.1 structure
- [x] Implement Stage 1: Load hierarchical structure
- [x] Implement Stage 2: Cross-curriculum vocabulary validation
- [x] Create CompiledUniverseV21 return type
- [x] Compiler returns successfully (not NotImplementedError)

## Phase 5: CompiledUniverse Return
- [x] Created CompiledUniverseV21 dataclass
- [x] Compiler returns CompiledUniverseV21
- [x] Test: compile(configs/default_curriculum) works

## Phase 6: Remaining Levels
- [x] Convert L0_0_minimal (global vision, no temporal)
- [x] Convert L0_5_dual_resource (global vision, no temporal)
- [x] Convert L2_partial_observability (local vision, no temporal)
- [x] Convert L3_temporal_mechanics (global vision, temporal active)
- [x] All 5 levels compile and validate

## Phase 7: Cleanup & Validation
- [x] Final validation (all 5 levels)
- [x] Remove archived configs
- [x] Update implementation checklist
- [x] Ready for next steps

## Summary

**Deliverables**:
- ✅ 9 new Pydantic DTOs created
- ✅ 25 YAML config files created (5 shared + 20 curriculum)
- ✅ Compiler updated with v2.1 support (auto-detection)
- ✅ CompiledUniverseV21 return type
- ✅ All 5 curriculum levels migrated
- ✅ Vocabulary consistency enforced

**Architecture**:
- Hierarchical config structure (experiment → levels)
- WHAT vs HOW split (vocabulary vs parameters)
- Support/Active pattern (transfer learning ready)
- Cross-curriculum vocabulary validation

**Next Steps**:
- Update remaining code to use CompiledUniverseV21
- Implement full observation spec builder (optional)
- Update tests to use v2.1 configs
- Consider merging to main
