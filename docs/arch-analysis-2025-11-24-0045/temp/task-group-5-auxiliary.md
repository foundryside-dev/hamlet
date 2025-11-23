# Task: Analyze Auxiliary Subsystems

## Assigned Subsystems (Group 5)
1. **curriculum** - Training curriculum strategies
2. **exploration** - Exploration strategies (RND, epsilon-greedy, adaptive)
3. **demo** - Demo runner, inference server, database
4. **recording** - Episode recording and replay

## Context
- **Workspace**: `docs/arch-analysis-2025-11-24-0045/`
- **Read**: `01-discovery-findings.md` (holistic assessment)
- **Write to**: `02-subsystem-catalog.md` (append your section under "## Group 5: Auxiliary Systems")
- **Source root**: `src/townlet/`

## Expected Output

For EACH of the 4 subsystems, provide:

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
- **External libraries**: [FastAPI, WebSockets, etc.]

### 4. Patterns & Design Decisions
- Architectural patterns observed
- Key design decisions and rationale
- How these systems augment the core training loop

### 5. Integration Points
- How curriculum affects training difficulty
- How exploration strategies influence action selection
- How demo/recording integrate with training

### 6. Confidence Level
- **HIGH/MEDIUM/LOW** with justification

## Validation Criteria

Before submitting, verify:
- [ ] All 4 subsystems documented with complete sections
- [ ] Confidence level marked for each subsystem
- [ ] Dependencies are specific
- [ ] Key components include actual file/class names from codebase
- [ ] Integration points describe auxiliary system roles

## Special Notes

**Focus areas for this group**:
- **curriculum**: base.py, adversarial.py, static.py, factory.py
- **exploration**: rnd.py, adaptive_intrinsic.py, epsilon_greedy.py, action_selection.py
- **demo**: runner.py, unified_server.py, live_inference.py, database.py
- **recording**: recorder.py, replay.py, video_export.py, video_renderer.py

**Critical questions to answer**:
- What curriculum strategies are available?
- How does curriculum progression work?
- What exploration strategies are implemented?
- How does RND (Random Network Distillation) work?
- What does the demo runner coordinate?
- How does the inference server communicate with the frontend?
- What gets recorded during training?
- How are episodes replayed?
