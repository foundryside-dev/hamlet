# Task: Analyze State Systems

## Assigned Subsystems (Group 3)
1. **vfs** - Variable & Feature System (state management)
2. **world** - Expression language (runtime computations)
3. **substrate** - Spatial/aspatial substrates

## Context
- **Workspace**: `docs/arch-analysis-2025-11-24-0045/`
- **Read**: `01-discovery-findings.md` (holistic assessment)
- **Write to**: `02-subsystem-catalog.md` (append your section under "## Group 3: State Systems")
- **Source root**: `src/townlet/`

## Expected Output

For EACH of the 3 subsystems, provide:

### 1. Subsystem Overview
- **Name**: [subsystem name]
- **Location**: `src/townlet/[directory]/`
- **Primary Responsibility**: [1-2 sentence description]

### 2. Key Components
List 3-5 most important files/classes with brief descriptions:
- `file_name.py`: [purpose]
- `ClassName`: [responsibility]

### 3. Dependencies
- **Inbound** (who depends on this subsystem): [list subsystems]
- **Outbound** (this subsystem depends on): [list subsystems]
- **External libraries**: [PyParsing, PyTorch, etc.]

### 4. Patterns & Design Decisions
- Architectural patterns observed
- Key design decisions and rationale
- Performance considerations

### 5. Integration Points
- How state is managed and accessed
- Expression evaluation pipeline
- Substrate abstraction and implementations

### 6. Confidence Level
- **HIGH/MEDIUM/LOW** with justification

## Validation Criteria

Before submitting, verify:
- [ ] All 3 subsystems documented with complete sections
- [ ] Confidence level marked for each subsystem
- [ ] Dependencies are specific
- [ ] Key components include actual file/class names from codebase
- [ ] Integration points describe state flow and computation execution

## Special Notes

**Focus areas for this group**:
- **vfs**: schema.py (Pydantic schemas), registry.py (runtime storage), observation_builder.py, evaluator.py
- **world**: expression/parser.py, expression/evaluator.py, expression/type_checker.py, expression/ast_nodes.py
- **substrate**: base.py (abstraction), grid2d.py, grid3d.py, gridnd.py, continuous.py, aspatial.py, factory.py

**Critical questions to answer**:
- How does VFS manage variable scopes (global, agent, agent_private)?
- What access control does VFS enforce?
- How are expressions parsed and evaluated?
- What's the substrate abstraction interface?
- How do different substrate implementations differ?
