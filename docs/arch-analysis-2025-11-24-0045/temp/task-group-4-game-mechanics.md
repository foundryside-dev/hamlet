# Task: Analyze Game Mechanics Subsystems

## Assigned Subsystems (Group 4)
1. **effects** - Effect system (compiler, executor, scheduler)
2. **items** - Item system (inventory, instances, action handlers)

## Context
- **Workspace**: `docs/arch-analysis-2025-11-24-0045/`
- **Read**: `01-discovery-findings.md` (holistic assessment)
- **Write to**: `02-subsystem-catalog.md` (append your section under "## Group 4: Game Mechanics")
- **Source root**: `src/townlet/`

## Expected Output

For EACH of the 2 subsystems, provide:

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
- **External libraries**: [if any]

### 4. Patterns & Design Decisions
- Architectural patterns observed
- Key design decisions and rationale
- How effects/items integrate with environment

### 5. Integration Points
- How effects are triggered and executed
- How items are managed in inventory
- Integration with VFS and environment

### 6. Confidence Level
- **HIGH/MEDIUM/LOW** with justification

## Validation Criteria

Before submitting, verify:
- [ ] All 2 subsystems documented with complete sections
- [ ] Confidence level marked for each subsystem
- [ ] Dependencies are specific
- [ ] Key components include actual file/class names from codebase
- [ ] Integration points describe game mechanics flow

## Special Notes

**Focus areas for this group**:
- **effects**: compiler.py, executor.py, scheduler.py, parser.py, manager.py, catalog.py, schema.py
- **items**: manager.py, inventory.py, instance.py, action_handlers.py

**Critical questions to answer**:
- How are effects defined, compiled, and executed?
- What's the lifecycle of an effect (trigger → execution → result)?
- How does the effect scheduler work?
- How do items interact with the inventory system?
- What actions can agents perform with items?
- How do effects and items relate to each other?
