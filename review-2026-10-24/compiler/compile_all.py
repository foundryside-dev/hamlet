"""Compile every pack/level under configs/ (no cache) and report outcome."""
import sys, traceback
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
root = Path("configs")
packs = sorted({p.parent.parent for p in root.rglob("levels/*") if p.is_dir() and p.parent.name == "levels"})
for pack in packs:
    for level in sorted(d.name for d in (pack / "levels").iterdir() if d.is_dir()):
        try:
            u = UniverseCompiler().compile(pack, primary_level=level, use_cache=False)
            lv = u.get_level(level)
            print(f"OK   {pack}:{level} dims={lv.token_spec.total_dims} schema={lv.token_type_schema_hash[:8]} layout={lv.layout_hash[:8]} items={'y' if u.items_catalog else 'n'} aff={len(lv.affordances.affordances)}")
        except Exception as exc:
            msg = str(exc).splitlines()[0][:160] if str(exc) else type(exc).__name__
            print(f"FAIL {pack}:{level} {type(exc).__name__}: {msg}")
