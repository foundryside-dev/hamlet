import sys; sys.path.insert(0, sys.argv[1])
from hashlib_common import *
from pathlib import Path
from townlet.training.checkpoint_utils import attach_universe_metadata, assert_checkpoint_identity, CHECKPOINT_FORMAT_VERSION
work = Path(sys.argv[2])
base = copy("configs/test/items_smoke", work/"base")
u0 = UniverseCompiler().compile(base, primary_level="L0_smoke", use_cache=False)
ck = {"version": CHECKPOINT_FORMAT_VERSION}
attach_universe_metadata(ck, u0)
for name, fn in [
  ("effect body wear_and_tear 1.0*intensity -> 50.0*intensity", lambda d: sub(d/"effects.yaml", '"item.condition - (1.0 * intensity)"', '"item.condition - (50.0 * intensity)"')),
  ("appearance apples 3 -> 9, period 100 -> 5", lambda d: (sub(d/"levels/L0_smoke/items.yaml", "spawn_count: 3", "spawn_count: 9"), sub(d/"levels/L0_smoke/items.yaml", "period: 100", "period: 5"))),
  ("control: item on_use change", lambda d: sub(d/"items.yaml", "value: bar.energy + 0.3", "value: bar.energy + 0.4")),
]:
    d = copy(base, work/"e")
    fn(d)
    u1 = UniverseCompiler().compile(d, primary_level="L0_smoke", use_cache=False)
    try:
        r = assert_checkpoint_identity(ck, u1, force_new_vfs=False)
        print(f"{name}: ACCEPTED (returned {r})")
    except Exception as e:
        print(f"{name}: REFUSED {type(e).__name__}: {str(e)[:160]}")
