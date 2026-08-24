# [DOC-6] Reference Config v2.1

**Priority:** P1 (Important)
**Category:** Documentation
**Status:** UNCLEAR
**Effort:** 4 hours

## Description

Cannot locate reference configuration file for v2.1 schema. Documentation mentions "reference-config-v2.1-complete.yaml" but file not found in repository. Need comprehensive annotated reference config showing all v2.1 schema features with inline documentation.

## Current State

**Search attempts:**
```bash
find . -name "*reference*config*"
grep -r "reference.*config" docs/
```

**Potential locations checked:**
- `configs/templates/` - template configs exist but not comprehensive reference
- `docs/config-schemas/` - schema docs exist but no complete reference config
- `configs/reference/` - directory doesn't exist
- Root `configs/` - no reference config file

**Alternative names searched:**
- reference-config-v2.1-complete.yaml
- reference-config.yaml
- config-v21-reference.yaml
- complete-config-example.yaml

**Current workaround:** Users must piece together reference from:
- Template configs in `configs/templates/`
- Curriculum level configs (L0-L3)
- Schema documentation in `docs/config-schemas/`

## Required Implementation

### Option A: Locate Existing File (1 hour)

**If file exists but misnamed/misplaced:**
1. Expand search to alternate names and locations
2. Check git history for deleted/moved reference configs
3. Search documentation for actual file name
4. Move to standard location: `configs/reference/config-v2.1-complete.yaml`
5. Update documentation references

### Option B: Create New Reference Config (3-4 hours)

**If file doesn't exist, create comprehensive reference:**

**File:** `configs/reference/config-v2.1-complete.yaml`

**Structure (annotated with inline comments):**

```yaml
# Complete Reference Configuration for HAMLET v2.1 Schema
# This file demonstrates ALL available configuration options
# Each field includes inline documentation and example values

# ============================================================================
# SUBSTRATE CONFIGURATION
# ============================================================================
substrate:
  type: "grid"  # Options: grid, grid3d, gridnd, continuous, continuousnd, aspatial
  dimensions: 2
  grid_size: [10, 10]  # Width × Height for 2D grid
  boundary_mode: "clamp"  # Options: clamp, wrap, bounce, sticky
  distance_metric: "manhattan"  # Options: manhattan, euclidean, chebyshev

  # Encoding affects value range, not dimensionality (always 2 dims for Grid2D)
  encoding:
    mode: "relative"  # Options: relative (default), scaled, absolute
    # relative: [0,1] normalized - best for transfer learning, required for POMDP
    # scaled: [0, grid_size] - value range conveys grid size
    # absolute: raw unnormalized - for physical simulation

# ============================================================================
# BARS (METERS) CONFIGURATION
# ============================================================================
bars:
  energy:
    display_name: "Energy"
    initial_value: 1.0
    min_value: 0.0
    max_value: 1.0
    decay_rate: 0.01  # Per-tick decay
    critically_low_threshold: 0.2
    low_threshold: 0.4
    high_threshold: 0.8

  health:
    display_name: "Health"
    initial_value: 1.0
    min_value: 0.0
    max_value: 1.0
    decay_rate: 0.005
    critically_low_threshold: 0.15
    low_threshold: 0.3
    high_threshold: 0.9

  # Add all 8 bars with full configuration...

# ============================================================================
# CASCADES (BAR RELATIONSHIPS)
# ============================================================================
cascades:
  - trigger_bar: "energy"
    trigger_condition: "below_critically_low"
    affected_bar: "health"
    effect: "decrease"
    magnitude: 0.02
    description: "Low energy damages health"

# ============================================================================
# AFFORDANCES (INTERACTIONS)
# ============================================================================
affordances:
  food:
    display_name: "Food"
    interaction_effects:
      energy: 0.3
      satiation: 0.2
    emoji: "🍎"

  bed:
    display_name: "Bed"
    interaction_effects:
      energy: 0.5
      mood: 0.1
    emoji: "🛏️"

# ============================================================================
# ENABLED ACTIONS
# ============================================================================
enabled_actions:
  action_labels: "gaming"  # Options: gaming, 6dof, cardinal, math
  custom_actions:
    - name: "REST"
      description: "Recover energy slowly"
      energy_recovery: 0.05
    - name: "MEDITATE"
      description: "Improve mood"
      mood_boost: 0.1

# ============================================================================
# VFS (VARIABLE & FEATURE SYSTEM)
# ============================================================================
vfs_profiles:
  version: "1.0"

  global_profile:
    variables:
      is_raining:
        type: bool
        default: false
        access_control:
          readers: [agent, engine]
          writers: [engine]

      danger_level:
        type: int
        default: 0
        normalization:
          mode: "min_max"
          range: [0, 10]
        access_control:
          readers: [agent, engine]
          writers: [engine, bac]

  agent_profiles:
    player:
      variables:
        experience_points:
          type: int
          default: 0
          expression: "vfs:kills * 10 + vfs:items_collected * 5"
          normalization:
            mode: "min_max"
            range: [0, 1000]
          access_control:
            readers: [agent, engine]
            writers: [actions, bac]

  item_profiles:
    consumable:
      variables:
        stack_count:
          type: int
          default: 1
          normalization:
            mode: "min_max"
            range: [1, 99]
        quality:
          type: float
          default: 1.0
          normalization:
            mode: "z_score"
            mean: 1.0
            std_dev: 0.2

# ============================================================================
# EFFECTS CATALOG
# ============================================================================
effects_catalog:
  version: "1.0"

  effects:
    regeneration:
      reapply_policy: "stack"
      duration: 100
      commands:
        - type: "modify"
          target: "self"
          path: "bar.health"
          operation: "add"
          value: 0.01

    poisoned:
      reapply_policy: "renew"
      duration: 50
      commands:
        - type: "modify"
          target: "self"
          path: "bar.health"
          operation: "subtract"
          value: 0.02

# ============================================================================
# ITEMS CATALOG
# ============================================================================
items_catalog:
  version: "1.0"

  items:
    apple:
      display_name: "Apple"
      description: "A crisp red apple"
      vfs_profile: "consumable"
      initial_state:
        stack_count: 1
        quality: 1.0
      interactions:
        - command: "USE"
          effects:
            - type: "modify"
              target: "self"
              path: "bar.energy"
              operation: "add"
              value: 0.2
            - type: "modify"
              target: "self"
              path: "bar.satiation"
              operation: "add"
              value: 0.15
          deny_pickup: false

  spawn_rules:
    - item_type: "apple"
      quantity: 10
      placement:
        mode: "random"
      schedule:
        type: "periodic"
        period: 100
      when: "vfs:is_not_winter"  # Conditional spawning
      max_total: 50

# ============================================================================
# ITEMS APPEARANCE
# ============================================================================
items_appearance:
  apple:
    emoji: "🍎"
    color: "#FF0000"

# ============================================================================
# DRIVE AS CODE (REWARD FUNCTION)
# ============================================================================
drive_as_code:
  version: "1.0"

  modifiers:
    energy_crisis:
      type: "range"
      source: "bar:energy"
      ranges:
        - range: [0.0, 0.2]
          multiplier: 0.1  # Suppress intrinsic when energy critically low
        - range: [0.2, 1.0]
          multiplier: 1.0

  extrinsic:
    type: "constant_base_with_shaped_bonus"
    base: 0.1
    bonuses:
      - bar: "energy"
        weight: 0.3
      - bar: "health"
        weight: 0.5

  intrinsic:
    strategy: "adaptive_rnd"
    base_weight: 0.1
    apply_modifiers: ["energy_crisis"]
    annealing:
      threshold: 100.0
      target_weight: 0.01

  shaping:
    - type: "approach_reward"
      affordance: "food"
      max_distance: 5.0
      weight: 0.05

  composition:
    normalize: false
    clip: null
    log_components: true
    log_modifiers: true

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================
training:
  # Q-Learning
  use_double_dqn: true  # Double DQN vs Vanilla DQN
  gamma: 0.99

  # Exploration
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay_steps: 100000

  # Experience Replay
  replay_buffer_size: 100000
  batch_size: 512
  min_replay_size: 10000

  # Network Updates
  learning_rate: 0.0001
  target_network_update_frequency: 1000
  gradient_clip_max_norm: 10.0

  # Training Loop
  num_episodes: 1000
  max_episode_length: 1000

  # Logging
  log_frequency: 100
  checkpoint_frequency: 1000
  tensorboard_log_dir: "runs/"

# ============================================================================
# CURRICULUM (OPTIONAL)
# ============================================================================
curriculum:
  type: "adversarial"  # Options: adversarial, static
  difficulty_metric: "mean_survival_time"
  difficulty_target: 500
  difficulty_adjustment_rate: 0.1

# ============================================================================
# POPULATION (OPTIONAL)
# ============================================================================
population:
  num_agents: 512
  vectorized: true

# ============================================================================
# POMDP (PARTIAL OBSERVABILITY)
# ============================================================================
pomdp:
  enabled: true
  vision_range: 2  # 5×5 local window

# ============================================================================
# TEMPORAL MECHANICS
# ============================================================================
temporal:
  enabled: true
  ticks_per_day: 24
  starting_hour: 6
```

**Size estimate:** ~500-800 lines (comprehensive with comments)

### 3. Documentation Updates (1 hour)

Update all documentation references to point to correct file:
- `docs/config-schemas/*.md` - update file path references
- `docs/guides/*.md` - update example references
- `CLAUDE.md` - add reference to complete config
- README - add "See complete reference config" link

### 4. Validation (30 minutes)

- Validate reference config compiles successfully
- Test with UniverseCompiler
- Verify all fields documented in schema docs appear in reference config
- Check completeness: every schema field should have example

## Acceptance Criteria

**If file located:**
- [ ] Reference config file found and moved to standard location
- [ ] Documentation updated with correct file path
- [ ] File validates successfully with UniverseCompiler

**If file created:**
- [ ] Complete reference config created with all v2.1 schema features
- [ ] Inline comments document every field and option
- [ ] File organized by subsystem with clear section headers
- [ ] Reference config validates successfully with UniverseCompiler
- [ ] All schema fields from docs represented in reference config
- [ ] Documentation updated to reference new file
- [ ] Example values are realistic and pedagogically useful

**Both cases:**
- [ ] File location: `configs/reference/config-v2.1-complete.yaml`
- [ ] Documentation references updated
- [ ] Users can find reference config from schema docs
- [ ] Reference config is single source of truth for "what's possible"

## Evidence

**Source Report:** gap-report-final.md (lines 55-68, 314), gap-report-testing-docs.md
**Schema Docs:** `docs/config-schemas/*.md` (mention reference config but file not found)

## Implementation Notes

**Why P1 (not P0):** Not a functional blocker. Users can piece together complete config from templates and schema docs, but reference config improves discoverability and reduces confusion.

**Reference Config Purpose:**
1. **Discoverability:** "What options are available?" → Browse reference config
2. **Copy-Paste:** Start new config by copying reference and removing unneeded sections
3. **Validation:** "Is my config complete?" → Compare against reference
4. **Teaching:** "How do I use this feature?" → See example in reference config

**Alternative to Reference Config:**
- Interactive config builder (web tool) - future enhancement
- Config generator CLI (scaffolding tool) - future enhancement
- For now: Comprehensive annotated reference config is most practical

**Organization Strategy:**
- Group by subsystem (substrate, bars, VFS, effects, items, drive_as_code, training)
- Include ALL options (even if rarely used)
- Inline comments explain each field's purpose and options
- Use realistic example values (not just type-correct but pedagogically useful)

**Completeness Check:**
Compare reference config against schema docs to ensure coverage:
- `docs/config-schemas/substrate.md` → substrate section complete?
- `docs/config-schemas/bars.md` → bars section complete?
- `docs/config-schemas/variables.md` → VFS section complete?
- `docs/config-schemas/effects.md` → effects section complete?
- `docs/config-schemas/items.md` → items section complete?
- `docs/config-schemas/drive_as_code.md` → DAC section complete?
- `docs/config-schemas/training.md` → training section complete?

## References

- Target location: `configs/reference/config-v2.1-complete.yaml` (to be created/located)
- Schema docs: `docs/config-schemas/*.md` (source for comprehensive field list)
- Template configs: `configs/templates/*.yaml` (partial examples)
- Validation: `src/townlet/universe/compiler.py` (validate reference config compiles)
