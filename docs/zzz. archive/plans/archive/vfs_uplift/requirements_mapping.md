# Requirements Mapping: Validation Framework → Master Requirements

This document maps the 89 additional validation framework requirements to the master requirements file, identifying gaps.

## Already Covered in Master

### CMD Requirements
- CMD-SWITCH-1,2,3 → **CMD-REQ-004** (Switch semantics)
- CMD-FOREACH-1,2,3,4,5 → **CMD-REQ-005** (for_each semantics)
- CMD-PARALLEL-1,2,3 → **CMD-REQ-006** (Parallel semantics)
- CMD-REDUCE-1,2,3 → **CMD-REQ-007** (Reduce constraints)
- CMD-DELAY-1,2,3,4,5 → **CMD-REQ-008** (Delay scheduler semantics)
- CMD-EMIT-1 → **CMD-REQ-009** (Emit event command)
- CMD-WHILE-1 → **NOT IN MASTER** ❌

### LIMITS Requirements
- LIMITS-1,3,4 → **CMD-REQ-002** (Command runtime caps)
- LIMITS-2 → **CMD-REQ-003** (Effect spawn depth cap)
- LIMITS-5,6,7 → **LIMIT-REQ-001** (Resource count limits)

### VFS-EXT Requirements
- VFS-EXT-1 → **VFS-REQ-003** (Expression XOR initial_value)
- VFS-EXT-3,4,5,6 → **VFS-REQ-006** (Profile metadata & exposure)
- VFS-EXT-7 → **VFS-REQ-004** (Evaluation order)
- VFS-EXT-8 → **ITEM-REQ-008** (Item VFS defaults)
- VFS-EXT-2 → **NOT IN MASTER** ❌ (Update rule DSL future)

### ITEM-EXT Requirements
- ITEM-EXT-1,2,3,4 → **ITEM-REQ-005** (Spawn rules coverage)
- ITEM-EXT-5 → **ITEM-REQ-006** (Conditional spawn predicates)
- ITEM-EXT-11 → **ITEM-REQ-009** (Item-scoped custom verbs)
- ITEM-EXT-13,14 → **ITEM-REQ-005** (Fixed/random placement in spawn rules)
- ITEM-EXT-6 → **NOT IN MASTER** ❌ (Item tags)
- ITEM-EXT-7 → **NOT IN MASTER** ❌ (Item visual metadata)
- ITEM-EXT-8 → **NOT IN MASTER** ❌ (Holder agent tracking)
- ITEM-EXT-9 → **NOT IN MASTER** ❌ (Item durability/charges)
- ITEM-EXT-10 → **NOT IN MASTER** ❌ (Item spoilage/decay)
- ITEM-EXT-12 → **NOT IN MASTER** ❌ (Exclusive vs shared items)
- ITEM-EXT-15 → **NOT IN MASTER** ❌ (Item instance ID tracking)
- ITEM-EXT-16 → **NOT IN MASTER** ❌ (Item spawn timing)

### COMP-EXT Requirements
- COMP-EXT-1 → **COMP-REQ-005** (Profile load gating)
- COMP-EXT-6 → **COMP-REQ-006** (Strict variables_reference scope)
- COMP-EXT-7,8 → **COMP-REQ-007** (Error UX with context)
- COMP-EXT-2 → **NOT IN MASTER** ❌ (Feature flagging)
- COMP-EXT-3 → **NOT IN MASTER** ❌ (Experiment vs level file layout)
- COMP-EXT-4 → **NOT IN MASTER** ❌ (Hashing for provenance)
- COMP-EXT-5 → **NOT IN MASTER** ❌ (Per-level metadata)

### EFF-EXT Requirements
- EFF-EXT-1 → **EFF-REQ-006** (on_interrupt hook)
- EFF-EXT-2 → **EFF-REQ-005** (Observable effects via VFS)
- EFF-EXT-3 → **EFF-REQ-007** (Affordance availability commands)
- EFF-EXT-4 → **EFF-REQ-008** (Cascade trigger command)
- EFF-EXT-6 → **EFF-REQ-009** (Sample command with weights)
- EFF-EXT-5 → **CMD-REQ-009** (Event emission - covered)
- EFF-EXT-7 → **NOT IN MASTER** ❌ (Random chance conditionals)
- EFF-EXT-8 → **NOT IN MASTER** ❌ (Effect metadata in catalog)

### RUN-EXT Requirements
- RUN-EXT-2 → **VFS-REQ-005** (ExecutionContext VFS access)
- RUN-EXT-3 → **OBS-REQ-005** (Mask unused item slots)
- RUN-EXT-5 → **OBS-REQ-004** (No zero-stub item VFS)
- RUN-EXT-6 → **RUN-REQ-001** (Debug instrumentation)
- RUN-EXT-7 → **RUN-REQ-002** (Runtime assertions)
- RUN-EXT-1 → **NOT IN MASTER** ❌ (Eager fallback mode)
- RUN-EXT-4 → **NOT IN MASTER** ❌ (Profile-driven obs dimensions)

### TEST-EXT Requirements
- TEST-EXT-1 → **OBS-REQ-003** (Obs dim stability)
- TEST-EXT-2 through TEST-EXT-8 → **NOT IN MASTER** ❌

### DOC-EXT Requirements
- DOC-EXT-1 through DOC-EXT-7 → **NOT IN MASTER** ❌

## Missing Requirements Count

**Total Missing: 30 requirements**

### Breakdown:
- CMD: 1 (CMD-WHILE-1)
- VFS: 1 (VFS-EXT-2)
- ITEM: 8 (ITEM-EXT-6,7,8,9,10,12,15,16)
- COMP: 4 (COMP-EXT-2,3,4,5)
- EFF: 2 (EFF-EXT-7,8)
- RUN: 2 (RUN-EXT-1,4)
- TEST: 7 (TEST-EXT-2,3,4,5,6,7,8)
- DOC: 7 (All DOC-EXT)

## Next Steps

Add these 30 missing requirements to master_requirements.md using proper ID sequence and table format.
