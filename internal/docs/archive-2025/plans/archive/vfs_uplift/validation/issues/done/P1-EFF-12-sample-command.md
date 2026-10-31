# P1-EFF-12: Sample Command for Stochastic Effects Not Implemented

**Priority:** P1 (Important - Can Defer)
**Category:** Effects System
**Estimated Effort:** 1 day
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The effects system lacks a dedicated `sample` command for stochastic sampling from distributions. Currently, stochastic behavior requires using `random()` function in expressions, which is less intuitive for complex sampling patterns.

**Current Workaround:**
```yaml
# Use random() in modify expressions
on_spawn:
  - command: modify
    target: "self.bar.loot_value"
    value: "10.0 + random() * 50.0"  # Uniform [10, 60]
```

**Desired Syntax:**
```yaml
on_spawn:
  - command: sample
    distribution: uniform
    params:
      min: 10.0
      max: 60.0
    store_in: "self.bar.loot_value"

  # Or more advanced:
  - command: sample
    distribution: normal
    params:
      mean: "target.bar.base_damage"
      std: 5.0
    store_in: "temp.sampled_damage"
```

**Impact:**
- Less intuitive for complex distributions (normal, lognormal, etc.)
- Cannot easily sample from discrete distributions (categorical, multinomial)
- **Not a blocker:** Workaround via `random()` in expressions works for simple cases

**Evidence:**
- Agent 3 (Effects) report, section EFF-12
- Design doc mentioned stochastic commands but not fully implemented
- No `SAMPLE` command type in `CommandType` enum

---

## Why This is P1 (Not P0)

**This is NOT a blocker because:**
- Simple stochastic behavior achievable via `random()` function
- All current use cases (loot drops, critical hits) covered by expressions
- No runtime errors - system works without dedicated sample command

**This IS important because:**
- Pedagogical value: Stochastic reward shaping is key RL concept
- Clean syntax: `sample` command more readable than expression hacks
- Advanced distributions: Normal, lognormal, categorical not easily expressed

---

## Design Considerations

### Supported Distributions

```python
class Distribution(Enum):
    UNIFORM = "uniform"        # Continuous [min, max]
    NORMAL = "normal"          # Gaussian(mean, std)
    LOGNORMAL = "lognormal"    # Lognormal(mean, std)
    BERNOULLI = "bernoulli"    # Coin flip(p)
    CATEGORICAL = "categorical"  # Discrete choice(probs)
    EXPONENTIAL = "exponential"  # Exponential(rate)
```

### Reproducibility

**Critical:** Must use seeded RNG for deterministic sampling during training.

```python
# In ExecutionContext
self.rng = torch.Generator()
self.rng.manual_seed(self.seed + self.step)  # Deterministic per-step
```

---

## How to Fix

### Step 1: Add Command Type (15 minutes)

**File:** `src/townlet/effects/schema.py`

```python
class CommandType(Enum):
    MODIFY = "modify"
    # ... existing types ...
    SAMPLE = "sample"  # ADD THIS

class Distribution(Enum):
    UNIFORM = "uniform"
    NORMAL = "normal"
    BERNOULLI = "bernoulli"
    # ... others ...
```

### Step 2: Implement Execution (4 hours)

**File:** `src/townlet/effects/executor.py`

```python
def execute_sample(self, cmd: CommandNode):
    """Sample from distribution and store result."""
    distribution = cmd.params['distribution']
    params = cmd.params['params']
    store_in = cmd.params['store_in']

    # Get or create seeded RNG
    if not hasattr(self.context, 'rng'):
        self.context.rng = torch.Generator()
        self.context.rng.manual_seed(self.context.seed)

    # Sample based on distribution
    if distribution == 'uniform':
        min_val = self.evaluate_expression(params['min'])
        max_val = self.evaluate_expression(params['max'])
        sample = torch.rand(self.batch_size, generator=self.context.rng)
        value = min_val + sample * (max_val - min_val)

    elif distribution == 'normal':
        mean = self.evaluate_expression(params['mean'])
        std = self.evaluate_expression(params['std'])
        sample = torch.randn(self.batch_size, generator=self.context.rng)
        value = mean + std * sample

    elif distribution == 'bernoulli':
        p = self.evaluate_expression(params['p'])
        sample = torch.rand(self.batch_size, generator=self.context.rng)
        value = (sample < p).float()

    elif distribution == 'categorical':
        probs = [self.evaluate_expression(p) for p in params['probs']]
        probs_tensor = torch.stack(probs, dim=-1)  # [batch, n_categories]
        # Sample categorical using Gumbel-max trick for GPU efficiency
        gumbel = -torch.log(-torch.log(torch.rand_like(probs_tensor, generator=self.context.rng)))
        value = (probs_tensor + gumbel).argmax(dim=-1).float()

    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    # Store sampled value
    self.set_value(store_in, value)
```

### Step 3: Add Schema Validation (1 hour)

**File:** `src/townlet/config/effects_config.py`

```python
class SampleCommandConfig(BaseModel):
    command: Literal["sample"]
    distribution: Literal["uniform", "normal", "bernoulli", "categorical", "exponential", "lognormal"]
    params: Dict[str, Any]  # Distribution-specific parameters
    store_in: str  # VFS path to store sampled value

    @validator('params')
    def validate_params(cls, v, values):
        dist = values.get('distribution')
        if dist == 'uniform':
            assert 'min' in v and 'max' in v, "uniform requires min and max"
        elif dist == 'normal':
            assert 'mean' in v and 'std' in v, "normal requires mean and std"
        # ... validate other distributions ...
        return v
```

### Step 4: Write Tests (2 hours)

**File:** `tests/test_townlet/unit/effects/test_sample_command.py` (NEW)

```python
def test_sample_uniform_distribution():
    """Verify uniform sampling produces values in range."""
    cmd = CommandNode(
        type=CommandType.SAMPLE,
        params={
            'distribution': 'uniform',
            'params': {'min': 0.0, 'max': 10.0},
            'store_in': 'temp.value'
        }
    )

    executor.execute(cmd)

    value = executor.context.temp_storage['value']
    assert (value >= 0.0).all() and (value <= 10.0).all()

def test_sample_reproducibility():
    """Verify seeded sampling is deterministic."""
    context1 = ExecutionContext(seed=42)
    executor1 = CommandExecutor(catalog, context1)
    executor1.execute(sample_cmd)
    value1 = executor1.context.temp_storage['value']

    context2 = ExecutionContext(seed=42)
    executor2 = CommandExecutor(catalog, context2)
    executor2.execute(sample_cmd)
    value2 = executor2.context.temp_storage['value']

    torch.testing.assert_close(value1, value2)  # Same seed = same samples

def test_sample_normal_distribution():
    """Verify normal sampling matches expected distribution."""
    # Sample 10000 times and check mean/std
    ...
```

### Step 5: Document (1 hour)

**File:** `docs/config-schemas/effects.md`

```markdown
### Stochastic Sampling

The `sample` command enables stochastic effects with reproducible sampling:

```yaml
on_loot_drop:
  - command: sample
    distribution: normal
    params:
      mean: "target.vfs.base_loot_value"
      std: 10.0
    store_in: "temp.loot_amount"

  - command: modify
    target: "self.bar.gold"
    value: "{{ temp.loot_amount }}"
```

#### Supported Distributions

| Distribution | Parameters | Example |
|--------------|------------|---------|
| `uniform` | `min`, `max` | Random [0, 100] |
| `normal` | `mean`, `std` | Gaussian damage roll |
| `bernoulli` | `p` | Critical hit (20% chance) |
| `categorical` | `probs` | Random item type |

#### Reproducibility

Sampling is deterministic per training run using seeded RNG. Same seed = same samples.
```

---

## Acceptance Criteria

- [ ] `SAMPLE` added to `CommandType` enum
- [ ] Execute logic for uniform, normal, bernoulli, categorical distributions
- [ ] Seeded RNG ensures reproducibility
- [ ] Schema validation for sample command params
- [ ] Tests verify distributions match expected statistics
- [ ] Tests verify reproducibility (same seed = same samples)
- [ ] Documentation with examples for each distribution

---

## Files to Modify

1. `src/townlet/effects/schema.py` - Add SAMPLE type and Distribution enum
2. `src/townlet/effects/executor.py` - Implement sampling logic
3. `src/townlet/config/effects_config.py` - Add schema validation
4. `tests/test_townlet/unit/effects/test_sample_command.py` (NEW) - Tests
5. `docs/config-schemas/effects.md` - Document sampling patterns

---

## Related Issues

- Related: P1-EFF-11 (event command)
- Related: P1-VFS-1 (expression operators - random() already exists)
- Blocking: None (optional feature)

---

## Notes

- **Reproducibility is critical:** Must use seeded RNG for RL training
- **GPU-native:** Use torch.rand/randn for vectorized sampling
- **Gumbel-max trick:** Efficient categorical sampling on GPU
- **Non-blocking:** Workaround via `random()` in expressions sufficient for now
- **Future:** Could add more distributions (beta, gamma, poisson) if needed
- Consider adding `sample_and_clamp` for bounded normal distributions
