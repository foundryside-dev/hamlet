import sys, os, logging, warnings
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
from pathlib import Path
WT = Path(sys.argv[1]); sys.path.insert(0, str(WT / "src"))
from townlet.universe.compiler import UniverseCompiler
from collections import Counter
c = Counter(); refused = []; others = []
for levels in sorted(WT.glob("configs/**/levels")):
    if ".compiled" in str(levels): continue
    pack = levels.parent
    for lv in sorted(p.name for p in levels.iterdir() if p.is_dir()):
        try:
            u = UniverseCompiler().compile(pack, primary_level=lv, use_cache=False)
            h = u.get_level(lv).token_type_schema_hash
            c[h] += 1
            if h != "de093a6e9f59924e": others.append((str(pack.relative_to(WT)), lv, h))
        except Exception as e:
            refused.append((str(pack.relative_to(WT)), lv, type(e).__name__, str(e).splitlines()[0][:100]))
print("hash counts:", dict(c)); print("non-matching:", others); print("refused:", len(refused))
for r in refused: print("  ", r)
