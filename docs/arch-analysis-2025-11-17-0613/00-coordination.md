# System Archaeologist - Migration Assessment Coordination Plan

## Analysis Plan

**Objective**: Deep dive into HAMLET system architecture to assess migration progress from legacy configuration systems to new specification.

**Scope**:
- Primary subsystems: Compiler (UAC), Environmental Vectorizer, Trainer
- Secondary subsystems: Population, Config DTOs, VFS, DAC Runtime
- Migration assessment: Legacy (hamletconfig, raw config 1.0) → New (configs/reference_config)

**Strategy**: PARALLEL with phased validation
- Phase 1: Holistic discovery (30 min) - Map all subsystems, identify legacy patterns
- Phase 2: Parallel subsystem analysis (1 hour) - 5-7 parallel subagents for major subsystems
- Phase 3: Cross-cutting analysis (30 min) - Legacy code identification, gap analysis
- Phase 4: Synthesis and recommendations (30 min)

**Time constraint**: ~2.5 hours total, thorough analysis with quality gates

**Complexity estimate**: HIGH
- Large codebase (~20K+ LOC in townlet/)
- Complex migration story (multiple config versions)
- Need to assess declarative spec coverage vs. implementation
- Critical project constraints (no backwards compatibility, no defaults)

## Execution Log

- [2025-11-17 06:13] Created workspace docs/arch-analysis-2025-11-17-0613/
- [2025-11-17 06:13] Writing coordination plan
- [2025-11-17 06:13] NEXT: Holistic assessment - directory structure, entry points, subsystem identification

## Subsystems to Analyze

Based on CLAUDE.md and user request:

1. **Compiler** (UAC) - `src/townlet/universe/compiler.py` - Seven-stage pipeline
2. **Environment Vectorizer** - `src/townlet/environment/vectorized_env.py` - VectorizedHamletEnv
3. **Trainer** - Training loop and checkpoint management
4. **Population** - `src/townlet/population/vectorized.py` - VectorizedPopulation
5. **Config DTOs** - `townlet.config.*` - DTO layer enforcing no-defaults
6. **VFS Runtime** - Variable & Feature System integration
7. **DAC Runtime** - Drive As Code reward engine

## Migration Assessment Focus

**Legacy artifacts to identify:**
- hamletconfig references
- Raw config 1.0 patterns
- Hardcoded defaults (violates no-defaults principle)
- Optional fields that should be required
- Backwards compatibility code (violates zero-user principle)

**New spec coverage:**
- Which settings in configs/reference_config/ are used by implementation?
- Which implementation features lack config specification?
- Where are config values loaded and validated?

## Validation Gates

- Gate 1: Discovery findings completeness check
- Gate 2: Subsystem catalog contract compliance
- Gate 3: Migration assessment accuracy
- Gate 4: Final report actionability

## Success Criteria

Deliverable must identify:
1. Migration completion status per subsystem (%)
2. Specific legacy code requiring removal (file:line references)
3. Functional gaps with remediation approach
4. Config specification gaps (settings missing from reference configs)
