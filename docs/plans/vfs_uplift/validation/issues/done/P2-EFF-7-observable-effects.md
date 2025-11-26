# [EFF-7] Observable Effects in Observations

**Priority:** P2 (Minor)
**Category:** Effects
**Status:** PARTIAL
**Effort:** 4 hours

## Description

Effects system has `observable` field in schema but it's not wired into observation builder. Agents cannot observe which effects are currently active (on themselves or others). This blocks agents from learning effect-aware strategies (e.g., "don't attack enemy with shield effect active").

## Current State

**Schema support (exists):**
```python
# src/townlet/effects/schema.py
@dataclass
class EffectDefinition:
    reapply_policy: str
    duration: int
    commands: List[EffectCommand]
    observable: bool = True  # ✅ Field exists
```

**Runtime tracking (exists):**
- EffectManager tracks active effects per agent
- Effects have ID, type, remaining duration, observable flag
- Located in `src/townlet/effects/manager.py`

**Observation integration (missing):**
- ObservationBuilder doesn't include active effects
- Agents have no visibility into which effects are active
- Cannot condition behavior on effect state

**Use cases blocked:**
- Combat: Agent can't see enemy has shield effect active
- Cooperation: Agent can't see ally has boost effect (coordinate better)
- Self-awareness: Agent can't see own poisoned status (take antidote)
- Strategy: Agent can't learn "attack targets without shield effect"

## Required Implementation

### 1. Add Effect Slots to ObservationBuilder (2-3 hours)

**File:** `src/townlet/vfs/observation_builder.py`

**Design decision:**
- Fixed-size effect observation (5-10 slots per agent)
- Each slot: [effect_type_id, remaining_duration, observable_flag]
- Empty slots filled with zeros
- Enables transfer learning (fixed obs dim across configs)

**Implementation:**
```python
class ObservationBuilder:
    EFFECT_SLOTS = 5  # Max observable effects per agent

    def build_observations(self, env_state) -> torch.Tensor:
        """Build observations including active effects."""

        # Existing: bars, affordances, VFS, position
        obs_components = []

        # ... existing observation components ...

        # NEW: Active effects observation
        if self.include_effects:
            effect_obs = self._build_effects_observation(
                env_state.effect_manager,
                num_agents=env_state.num_agents
            )
            obs_components.append(effect_obs)

        return torch.cat(obs_components, dim=1)

    def _build_effects_observation(
        self,
        effect_manager: EffectManager,
        num_agents: int
    ) -> torch.Tensor:
        """Build effect observation tensor.

        Returns:
            Tensor of shape [num_agents, EFFECT_SLOTS * 3]
            Each slot: [effect_type_id, remaining_duration, is_active]
        """
        device = self.device
        slots = self.EFFECT_SLOTS

        # Initialize empty slots: [num_agents, slots, 3]
        effect_obs = torch.zeros(num_agents, slots, 3, device=device)

        # Fill slots with active effects
        for agent_idx in range(num_agents):
            active_effects = effect_manager.get_active_effects(agent_idx)

            # Filter to observable effects only
            observable = [e for e in active_effects if e.observable]

            # Take first N effects (up to EFFECT_SLOTS)
            for slot_idx, effect in enumerate(observable[:slots]):
                effect_obs[agent_idx, slot_idx, 0] = effect.type_id  # Effect type (cataloged)
                effect_obs[agent_idx, slot_idx, 1] = effect.remaining_duration / effect.total_duration  # Normalized
                effect_obs[agent_idx, slot_idx, 2] = 1.0  # Is active flag

        # Flatten slots: [num_agents, slots * 3]
        return effect_obs.reshape(num_agents, slots * 3)

    def calculate_observation_dim(self) -> int:
        """Calculate total observation dimension including effects."""
        dim = 0

        # ... existing dimensions ...

        if self.include_effects:
            dim += self.EFFECT_SLOTS * 3  # (type_id, duration, is_active) per slot

        return dim
```

### 2. Effect Type ID Mapping (1 hour)

**File:** `src/townlet/effects/catalog.py`

**Add effect type enumeration:**
```python
class EffectCatalog:
    def __init__(self, effects: Dict[str, CompiledEffect]):
        self.effects = effects

        # NEW: Map effect names to integer IDs (for observation encoding)
        self.effect_name_to_id: Dict[str, int] = {
            name: idx for idx, name in enumerate(sorted(effects.keys()))
        }
        self.effect_id_to_name: Dict[int, str] = {
            idx: name for name, idx in self.effect_name_to_id.items()
        }

    def get_effect_id(self, effect_name: str) -> int:
        """Get integer ID for effect name."""
        return self.effect_name_to_id.get(effect_name, -1)  # -1 = unknown effect

    def get_effect_name(self, effect_id: int) -> str:
        """Get effect name from integer ID."""
        return self.effect_id_to_name.get(effect_id, "unknown")
```

### 3. Configuration (30 minutes)

**File:** `src/townlet/universe/compiled.py`

**Add effects observation config:**
```python
@dataclass
class CompiledUniverse:
    # ... existing fields ...

    # NEW: Effects observation config
    include_effects_in_observations: bool = True
    max_observable_effects: int = 5
```

**File:** Config files (optional override)

```yaml
# substrate.yaml (or new observation_config.yaml)
observations:
  include_effects: true
  max_effect_slots: 5  # Override default
```

### 4. Integration with EffectManager (1 hour)

**File:** `src/townlet/effects/manager.py`

**Add helper method:**
```python
class EffectManager:
    def get_active_effects(self, agent_idx: int) -> List[ActiveEffect]:
        """Get all active effects for an agent."""
        return [
            effect for effect in self.active_effects
            if effect.target_agent == agent_idx
        ]

    def get_observable_effects(self, agent_idx: int) -> List[ActiveEffect]:
        """Get observable effects for an agent."""
        return [
            effect for effect in self.get_active_effects(agent_idx)
            if effect.observable
        ]
```

### 5. Testing (1-2 hours)

**File:** `tests/test_townlet/unit/vfs/test_observable_effects.py` (new)

**Test cases:**
```python
def test_effects_in_observations():
    """Test active effects included in observations."""
    env = create_env_with_effects()
    env.effect_manager.add_effect("regeneration", agent_idx=0, duration=100)

    obs = env.get_observations()

    # Check effect observation shape
    assert obs.shape[1] >= ObservationBuilder.EFFECT_SLOTS * 3

    # Check regeneration effect is visible
    effect_start_idx = env.obs_builder.effect_obs_start_idx
    effect_obs = obs[0, effect_start_idx:effect_start_idx + 15]  # 5 slots * 3 dims
    assert torch.any(effect_obs != 0)  # At least one effect active

def test_empty_effect_slots():
    """Test observation with no active effects (all zeros)."""
    env = create_env_with_effects()
    # No effects added

    obs = env.get_observations()
    effect_start_idx = env.obs_builder.effect_obs_start_idx
    effect_obs = obs[0, effect_start_idx:effect_start_idx + 15]

    assert torch.all(effect_obs == 0)  # All slots empty

def test_multiple_effects_fill_slots():
    """Test multiple effects fill observation slots."""
    env = create_env_with_effects()
    env.effect_manager.add_effect("regeneration", agent_idx=0, duration=100)
    env.effect_manager.add_effect("poisoned", agent_idx=0, duration=50)
    env.effect_manager.add_effect("shield", agent_idx=0, duration=200)

    obs = env.get_observations()
    effect_start_idx = env.obs_builder.effect_obs_start_idx
    effect_obs = obs[0, effect_start_idx:effect_start_idx + 15]

    # Count non-zero slots (is_active flag)
    active_slots = (effect_obs[2::3] == 1.0).sum()  # Every 3rd element is is_active
    assert active_slots == 3  # 3 effects active

def test_effect_type_id_encoding():
    """Test effect types encoded as integer IDs."""
    catalog = create_effect_catalog()
    assert catalog.get_effect_id("regeneration") >= 0
    assert catalog.get_effect_id("poisoned") >= 0
    assert catalog.get_effect_id("unknown_effect") == -1

def test_non_observable_effects_excluded():
    """Test effects with observable=False not in observations."""
    env = create_env_with_effects()
    env.effect_manager.add_effect("regeneration", agent_idx=0, duration=100)
    env.effect_manager.add_effect("hidden_debuff", agent_idx=0, duration=50)  # observable=False

    obs = env.get_observations()
    effect_start_idx = env.obs_builder.effect_obs_start_idx
    effect_obs = obs[0, effect_start_idx:effect_start_idx + 15]

    # Only 1 effect visible (regeneration)
    active_slots = (effect_obs[2::3] == 1.0).sum()
    assert active_slots == 1

def test_max_slots_exceeded():
    """Test behavior when more effects than slots."""
    env = create_env_with_effects()
    # Add 10 effects (more than 5 slots)
    for i in range(10):
        env.effect_manager.add_effect(f"effect_{i}", agent_idx=0, duration=100)

    obs = env.get_observations()
    effect_start_idx = env.obs_builder.effect_obs_start_idx
    effect_obs = obs[0, effect_start_idx:effect_start_idx + 15]

    # Only 5 effects visible (slot limit)
    active_slots = (effect_obs[2::3] == 1.0).sum()
    assert active_slots == 5
```

## Acceptance Criteria

- [ ] ObservationBuilder includes active effects in observations
- [ ] Fixed-size effect slots (default 5 slots per agent)
- [ ] Each slot encodes: [effect_type_id, remaining_duration, is_active]
- [ ] Empty slots filled with zeros
- [ ] Effect type IDs mapped from effect catalog (deterministic ordering)
- [ ] Non-observable effects (observable=False) excluded
- [ ] Max slots limit enforced (take first N effects)
- [ ] Observation dimension calculation includes effect slots
- [ ] Configuration option to enable/disable effect observations
- [ ] 10+ tests covering effect observations, empty slots, slot limits, observable filtering
- [ ] Documentation updated with effect observation format

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-effects.md
**Schema:** `src/townlet/effects/schema.py:EffectDefinition.observable` (field exists)
**Current limitation:** Not wired into observation builder

## Implementation Notes

**Why P2 (not P1/P0):** Visualization and agent self-awareness feature. Effects work correctly, agents just can't observe them. Needed for effect-aware strategies in advanced curriculum levels, but not critical for Phase 1-3.

**Design Rationale:**

1. **Fixed Slots (not dynamic):**
   - Ensures constant observation dimension (transfer learning)
   - Simpler than dynamic padding/masking
   - Max 5-10 effects per agent is reasonable assumption

2. **Slot Encoding:**
   - `effect_type_id`: Which effect (0-N based on catalog)
   - `remaining_duration`: Normalized [0, 1] (0 = expired, 1 = just started)
   - `is_active`: Binary flag (1 = slot occupied, 0 = empty)

3. **Effect Type IDs:**
   - Deterministic ordering (sorted by effect name)
   - Consistent across training runs
   - Enables transfer learning (same effect = same ID)

**Observation Dimension Impact:**
- 5 slots × 3 dims = 15 additional dimensions
- Minimal compared to typical obs (L1: 29 dims → 44 dims)
- Acceptable for fixed vocabulary

**Alternative Designs Considered:**

1. **Dynamic effect count:**
   - Pros: More flexible, no slot limit
   - Cons: Variable obs dim, breaks transfer learning
   - Rejected: Fixed dim more important

2. **One-hot effect encoding:**
   - Pros: Clear binary flags per effect type
   - Cons: Obs dim grows with effect catalog size
   - Rejected: Slot-based more scalable

3. **Aggregated effect stats:**
   - Pros: Compact (e.g., "total effect power", "debuff count")
   - Cons: Loses specific effect information
   - Rejected: Too lossy for strategic decisions

**Use Case Examples:**

**Combat Strategy:**
```
Agent observes enemy has shield effect active (slot 0: type_id=3, duration=0.8, active=1)
→ Learn to avoid attacking shielded enemies (low reward)
```

**Self-Awareness:**
```
Agent observes self is poisoned (slot 1: type_id=5, duration=0.3, active=1)
→ Learn to seek antidote or healing affordance
```

**Cooperation:**
```
Agent observes ally has boost effect (slot 0: type_id=7, duration=0.9, active=1)
→ Learn to coordinate with boosted allies (higher success rate)
```

**Slot Priority (when more effects than slots):**
- Option 1: Newest effects first (FIFO)
- Option 2: Longest duration first (most relevant)
- Option 3: Highest priority effects (configurable priority field)
- Recommendation: Newest effects first (simple, predictable)

## References

- ObservationBuilder: `src/townlet/vfs/observation_builder.py` (add effect observation)
- EffectManager: `src/townlet/effects/manager.py` (add helper methods)
- EffectCatalog: `src/townlet/effects/catalog.py` (add type ID mapping)
- Schema: `src/townlet/effects/schema.py:EffectDefinition.observable`
- Test file: `tests/test_townlet/unit/vfs/test_observable_effects.py` (to be created)
- Documentation: `docs/config-schemas/effects.md` (add observable field explanation)
