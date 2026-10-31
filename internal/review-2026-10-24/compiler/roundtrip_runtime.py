import msgpack, torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compiled import CompiledUniverse
from townlet.environment.vectorized_env import VectorizedHamletEnv
pack, level = "configs/test/items_smoke", "L0_smoke"
fresh = UniverseCompiler().compile(Path(pack), primary_level=level, use_cache=False)
loaded = CompiledUniverse.from_dict(msgpack.unpackb(msgpack.packb(fresh.to_dict(), use_bin_type=True), raw=False, strict_map_key=False))
cached = UniverseCompiler().compile(Path(pack), primary_level=level, use_cache=True)  # writes then... second call serves
cached = UniverseCompiler().compile(Path(pack), primary_level=level, use_cache=True)
for tag, u in (("fresh", fresh), ("from_dict", loaded), ("compile(use_cache=True) 2nd call", cached)):
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=2, device="cpu")
    env.reset()
    im = env.item_manager
    active = None
    for attr in ("active", "active_mask", "alive", "item_active", "num_active"):
        if hasattr(im, attr):
            v = getattr(im, attr); active = (attr, int(v.sum().item()) if torch.is_tensor(v) else v); break
    if active is None:
        active = [(k, int(v.sum().item())) for k, v in vars(im).items() if torch.is_tensor(v) and v.dtype == torch.bool]
    print(f"{tag:35s} items_appearance={'present' if u.all_levels[level].items_appearance is not None else 'None':8s} items active after reset: {active}")
