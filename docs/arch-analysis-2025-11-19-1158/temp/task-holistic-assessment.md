# Task: Holistic Assessment of HAMLET Townlet Codebase

## Context
- **Workspace**: `docs/arch-analysis-2025-11-19-1158/`
- **Read**: `00-coordination.md` (coordination plan)
- **Write to**: `01-discovery-findings.md`
- **Scope**: `src/townlet/` only (28K LOC, 13 subsystems)
- **Exclusions**: `docs/` (per user request), `hamlet/` (doesn't exist - obsolete)

## Objective

Perform systematic holistic assessment of the HAMLET Townlet codebase to understand:
1. **Directory structure** - Organization pattern (feature? layer? domain?)
2. **Entry points** - Main files, API definitions, CLI entry points
3. **Technology stack** - Languages, frameworks, dependencies (check pyproject.toml, requirements, imports)
4. **Subsystem identification** - Identify 4-12 major cohesive groups with clear boundaries

## Expected Output

Write `01-discovery-findings.md` following the documentation contract from `analyzing-unknown-codebases.md`:

### Required Sections

1. **Project Overview**
   - Name, purpose (from CLAUDE.md context if needed)
   - Primary language, frameworks
   - Approximate size (files, LOC)

2. **Directory Structure**
   - High-level organization (with tree diagram if helpful)
   - Organizational pattern (feature-based? layer-based? domain-based?)

3. **Technology Stack**
   - Languages (Python version if detectable)
   - Frameworks (PyTorch, JAX, etc. - check imports)
   - Key dependencies (from pyproject.toml or imports)
   - Build/packaging tools (uv, pip, etc.)

4. **Entry Points**
   - CLI entry points (scripts/, __main__.py)
   - API servers (if any)
   - Configuration entry points

5. **Subsystem Inventory** (Preliminary)
   - List 4-12 major subsystems with:
     - Name
     - Location (path)
     - Suspected responsibility (1-2 sentences)
     - Confidence level (High/Medium/Low - based on directory names and quick file scans)

6. **Initial Observations**
   - Architectural patterns noticed
   - Interesting design choices
   - Questions or uncertainties

7. **Recommended Analysis Approach**
   - Confirm: Sequential or Parallel analysis?
   - Priority subsystems (if any need deep-dive first)

## Validation Criteria

- [ ] All required sections present
- [ ] Technology stack verified (not guessed) - check actual files
- [ ] Subsystem list has 4-12 items (not just directory listing)
- [ ] Confidence levels marked for each subsystem
- [ ] No placeholder text ("[TODO]", "[Fill in]")
- [ ] Organizational pattern identified with reasoning

## Notes

- **Focus on CODE** - user specifically requested code analysis, not docs
- **Preliminary assessment** - detailed subsystem analysis comes in next phase
- **Confidence-based** - mark uncertainty levels, don't fabricate details
- This is HOLISTIC - breadth over depth at this stage
- Project context: Pedagogical Deep RL environment (GPU-native vectorized training)
- Pre-release status: Zero users, aggressive refactoring expected
