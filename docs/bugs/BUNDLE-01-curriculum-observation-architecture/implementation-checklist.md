# Config v2.1 Implementation Checklist

**Branch**: feature/config-v2.1
**Status**: In Progress
**Target**: All tests passing with v2.1 hierarchical configs

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
- [ ] Create directory structure
- [ ] Extract experiment.yaml from reference
- [ ] Extract stratum.yaml from reference
- [ ] Extract environment.yaml from reference
- [ ] Extract actions.yaml from reference
- [ ] Extract agent.yaml from reference
- [ ] Extract curriculum.yaml from reference
- [ ] Extract bars.yaml from reference
- [ ] Extract affordances.yaml from reference
- [ ] Extract training.yaml from reference

## Phase 3: DTO Creation
- [ ] Create experiment_config.py
- [ ] Create stratum_config.py
- [ ] Create environment_config.py
- [ ] Create actions_config.py
- [ ] Create agent_config.py
- [ ] Create curriculum_config.py
- [ ] Test DTOs load successfully

## Phase 4: Compiler Updates
- [ ] Update compiler main entry point
- [ ] Implement Stage 1: Load hierarchical structure
- [ ] Implement Stage 2: Cross-curriculum validation
- [ ] Update Stage 5: Observation spec with support/active pattern
- [ ] Delete old config loading code

## Phase 5: Test Updates
- [ ] Update compiler tests
- [ ] Update config DTO tests
- [ ] Update integration tests
- [ ] All L1 tests passing

## Phase 6: Remaining Levels
- [ ] Convert L0_0_minimal
- [ ] Convert L0_5_dual_resource
- [ ] Convert L2_partial_observability
- [ ] Convert L3_temporal_mechanics
- [ ] All tests passing

## Phase 7: Cleanup & Validation
- [ ] Remove archived configs
- [ ] Update BUNDLE-01 documentation
- [ ] Final test run
- [ ] Merge to main
