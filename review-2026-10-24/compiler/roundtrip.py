"""Fresh compile vs msgpack round-trip: diff every field; check items_appearance survives; runtime item spawn."""
import dataclasses, shutil, tempfile
from pathlib import Path
import msgpack, torch
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compiled import CompiledUniverse
from townlet.environment.vectorized_env import VectorizedHamletEnv

for pack, level in [("configs/test/items_smoke", "L0_smoke"), ("configs/default_curriculum", "L3_temporal_mechanics")]:
    print("=====", pack, level)
    fresh = UniverseCompiler().compile(Path(pack), primary_level=level, use_cache=False)
    payload = msgpack.packb(fresh.to_dict(), use_bin_type=True)
    loaded = CompiledUniverse.from_dict(msgpack.unpackb(payload, raw=False, strict_map_key=False))
    print("to_dict equal after round trip:", fresh.to_dict() == loaded.to_dict())
    # top-level field diff
    for f in dataclasses.fields(CompiledUniverse):
        a, b = getattr(fresh, f.name), getattr(loaded, f.name)
        if f.name in ("all_levels", "metadata"):
            continue
        try:
            same = a == b
        except Exception as exc:
            same = f"cmp-error {exc}"
        if same is not True:
            print(f"  TOP DIFF {f.name}: fresh={type(a).__name__} loaded={type(b).__name__} same={same}")
    for name in fresh.all_levels:
        fl, ll = fresh.all_levels[name], loaded.all_levels[name]
        for f in dataclasses.fields(CompiledUniverse.LevelMetadata):
            a, b = getattr(fl, f.name), getattr(ll, f.name)
            if f.name == "optimization_data":
                same = a.cascade_data == b.cascade_data and a.modulation_data == b.modulation_data and all(
                    (x is None and y is None) or (x is not None and y is not None and torch.equal(x, y))
                    for x, y in zip(a.affordance_position_map.values(), b.affordance_position_map.values()))
            elif f.name == "transition_schedule":
                same = "skipped"
            else:
                try:
                    same = a == b
                except Exception as exc:
                    same = f"cmp-error {exc}"
            if same is not True:
                print(f"  LEVEL[{name}] DIFF {f.name}: fresh={str(a)[:80]!r} loaded={str(b)[:80]!r}")
    # items_appearance when_ast
    fl = fresh.all_levels[level]
    if fl.items_appearance is not None:
        print("  fresh when_ast:", [getattr(r, 'when_ast', 'n/a') is not None for r in fl.items_appearance.items])
    print("  metadata equal except compiled_at:", {k: v for k, v in dataclasses.asdict(fresh.metadata).items() if k != "compiled_at"} == {k: v for k, v in dataclasses.asdict(loaded.metadata).items() if k != "compiled_at"})
    # runtime effect
    for tag, u in (("fresh", fresh), ("loaded", loaded)):
        env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=2, device="cpu")
        env.reset()
        im = env.item_manager
        n = None
        if im is not None:
            for attr in ("num_items", "item_count", "active_count"):
                if hasattr(im, attr):
                    n = getattr(im, attr)
                    n = n() if callable(n) else n
                    break
            if n is None:
                n = {k: (v.sum().item() if torch.is_tensor(v) else v) for k, v in vars(im).items() if torch.is_tensor(v) and v.dtype == torch.bool}
        print(f"  {tag}: items_appearance={'present' if u.all_levels[level].items_appearance is not None else 'None'} item_manager={'present' if im is not None else 'None'} items_after_reset={n}")
