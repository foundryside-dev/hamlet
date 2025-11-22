# P1-RUN-9: Checkpoint Serialization Missing Item VFS State

**Priority:** P1 (Important - Should Fix)
**Category:** Runtime Integration
**Estimated Effort:** 2 days
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

Checkpoint serialization does not include item VFS state, meaning that when a checkpoint is saved and loaded, items lose their VFS variable state (e.g., `item.vfs.durability`, `item.vfs.enchantment_level`).

**Impact:**
- Cannot resume training with items that have VFS state
- Item VFS variables reset to initial values on checkpoint load
- Breaks reproducibility for experiments using item VFS

**Evidence:**
- Agent 5 (Runtime Integration) found no `registry.item_vfs` in checkpoint save/load paths
- File: `src/townlet/training/state.py` (checkpoint serialization)
- No test coverage for item VFS checkpoint roundtrip

---

## How to Fix

### Step 1: Add item_vfs to Checkpoint State (4 hours)

**File:** `src/townlet/training/state.py`

Add item VFS tensor to checkpoint dictionary:

```python
# In save_checkpoint function
checkpoint_dict = {
    'q_network': q_network.state_dict(),
    'target_network': target_network.state_dict(),
    'optimizer': optimizer.state_dict(),
    'step': step,
    'episode': episode,
    'registry_global': registry.global_vfs,     # Existing
    'registry_agent': registry.agent_vfs,       # Existing
    'registry_item': registry.item_vfs,         # ADD THIS
    ...
}

# In load_checkpoint function
if 'registry_item' in checkpoint:
    registry.item_vfs = checkpoint['registry_item']
else:
    # Backward compatibility: initialize empty if missing
    registry.item_vfs = torch.zeros_like(registry.item_vfs)
```

### Step 2: Update DemoRunner Checkpoint Loading (2 hours)

**File:** `src/townlet/demo/runner.py`

Ensure `DemoRunner.load_checkpoint()` restores item VFS state:

```python
def load_checkpoint(self):
    checkpoint = torch.load(self.checkpoint_path)

    # Existing: Load Q-network, optimizer, etc.
    ...

    # ADD: Restore item VFS if present
    if 'registry_item' in checkpoint:
        self.population.vfs_registry.item_vfs = checkpoint['registry_item']
```

### Step 3: Write Roundtrip Test (4 hours)

**File:** `tests/test_townlet/unit/training/test_checkpoint_item_vfs.py` (NEW)

```python
def test_checkpoint_preserves_item_vfs_state():
    """Verify item VFS state survives checkpoint save/load."""
    # Setup: Create env with items that have VFS state
    config = HamletConfig.from_directory("configs/items_smoke")
    env = VectorizedHamletEnv(config, n_envs=4)

    # Spawn items with VFS state
    item_id = env.item_manager.spawn_item(
        item_type="sword",
        position=(5, 5),
        vfs_state={"durability": 0.75, "sharpness": 2.5}
    )

    # Save checkpoint
    original_item_vfs = env.registry.item_vfs.clone()
    save_checkpoint("test_checkpoint.pt", registry=env.registry)

    # Modify state (simulate training)
    env.registry.item_vfs[item_id, 0] = 0.5  # Reduce durability

    # Load checkpoint
    load_checkpoint("test_checkpoint.pt", registry=env.registry)

    # Verify item VFS restored
    torch.testing.assert_close(env.registry.item_vfs, original_item_vfs)
    assert env.registry.item_vfs[item_id, 0] == 0.75  # durability restored
```

### Step 4: Integration Test (2 hours)

**File:** `tests/test_townlet/integration/test_checkpoint_items_e2e.py` (NEW)

Test full training loop with checkpoint save/load and item VFS.

---

## Acceptance Criteria

- [ ] `registry.item_vfs` included in checkpoint save
- [ ] `registry.item_vfs` restored on checkpoint load
- [ ] Backward compatibility: old checkpoints without item_vfs don't crash
- [ ] Unit test: `test_checkpoint_preserves_item_vfs_state` passes
- [ ] Integration test: Full training loop with items + checkpoint works
- [ ] DemoRunner correctly loads item VFS from checkpoints

---

## Files to Modify

1. `src/townlet/training/state.py` - Add item_vfs to checkpoint dict
2. `src/townlet/demo/runner.py` - Load item_vfs in DemoRunner
3. `tests/test_townlet/unit/training/test_checkpoint_item_vfs.py` (NEW)
4. `tests/test_townlet/integration/test_checkpoint_items_e2e.py` (NEW)

---

## Related Issues

- Blocking: None
- Blocked by: None
- Related: P1-RUN-12 (integration test failures)

---

## Notes

- Backward compatibility is important: Old checkpoints without `registry_item` should initialize empty tensor, not crash
- Consider adding checkpoint version field for future schema changes
- Item VFS tensor shape: `[max_items, vfs_profile_dim]`
