import sys; sys.path.insert(0, sys.argv[1])
from hashlib_common import *
from pathlib import Path
work = Path(sys.argv[2])
A = "levels/L0_smoke/items.yaml"
edits = [
 ("item on_use 0.3 -> 0.4", "sem", lambda d: sub(d/"items.yaml", "value: bar.energy + 0.3", "value: bar.energy + 0.4")),
 ("item on_use respaced", "null", lambda d: sub(d/"items.yaml", "value: bar.energy + 0.3", "value: bar.energy+0.3")),
 ("item description edit", "doc", lambda d: sub(d/"items.yaml", "Restores energy when used", "Restores energy")),
 ("item cooldown 50 -> 60", "sem", lambda d: sub(d/"items.yaml", "cooldown: 50", "cooldown: 60")),
 ("appearance spawn_count 3 -> 4", "sem", lambda d: sub(d/A, "spawn_count: 3", "spawn_count: 4")),
 ("appearance period 100 -> 50", "sem", lambda d: sub(d/A, "period: 100", "period: 50")),
 ("appearance coin spawn 0 -> 2", "sem", lambda d: sub(d/A, "spawn_count: 0", "spawn_count: 2")),
 ("effect wear_and_tear 1.0 -> 2.0", "sem", lambda d: sub(d/"effects.yaml", '"item.condition - (1.0 * intensity)"', '"item.condition - (2.0 * intensity)"')),
 ("effect wear_and_tear respaced", "null", lambda d: sub(d/"effects.yaml", '"item.condition - (1.0 * intensity)"', '"item.condition-(1.0*intensity)"')),
 ("effect duration 10 -> 11", "sem", lambda d: sub(d/"effects.yaml", "duration: 10", "duration: 11")),
 ("max_active_effects item 4 -> 5", "sem", lambda d: sub(d/"effects.yaml", "item: 4", "item: 5")),
]
run_matrix(Path("configs/test/items_smoke"), "L0_smoke", edits, work)
