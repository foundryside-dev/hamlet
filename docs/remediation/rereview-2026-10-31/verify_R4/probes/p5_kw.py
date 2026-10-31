"""Area 5: keyword parsing (D1) — prefixes, suffixes, mixes, if/then/else; and every shipped pack's expression ASTs at
f3a6d115 vs 636192e0 (run with WT=<worktree> to point at either; writes a JSON of canonical AST reprs)."""
import os, sys, json, re
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
HERE = Path(__file__).resolve().parent
WT = Path(os.environ.get("WT", str(HERE.parent / "wt"))).resolve(); sys.path.insert(0, str(WT / "src"))
import townlet, yaml
assert str(WT) in townlet.__file__, townlet.__file__
from townlet.world.expression.parser import ExpressionParser
P = ExpressionParser()

def canon(node):
    return re.sub(r"(line|column|type_annotation)=[^,)]*, ?", "", repr(node))

if len(sys.argv) > 1 and sys.argv[1] == "dump":
    out = {}
    for f in sorted((WT / "configs").rglob("*.y*ml")):
        if ".compiled" in f.parts: continue
        try:
            docs = list(yaml.safe_load_all(open(f)))
        except Exception:
            continue
        def leaves(v, path):
            if isinstance(v, str): yield path, v
            elif isinstance(v, dict):
                for k, c in v.items(): yield from leaves(c, f"{path}.{k}")
            elif isinstance(v, list):
                for i, c in enumerate(v): yield from leaves(c, f"{path}[{i}]")
        for d in docs:
            for path, text in leaves(d, str(f.relative_to(WT))):
                try:
                    out[path] = canon(P.parse(text))
                except Exception as e:
                    out[path] = "NOPARSE"
    json.dump(out, open(sys.argv[2], "w"), indent=0, sort_keys=True)
    print("dumped", len(out), "string leaves from", WT.name, "parsed:", sum(v != "NOPARSE" for v in out.values()))
    sys.exit(0)

print("townlet at", townlet.__file__)
cases = ["notable", "cannot", "untrue", "band", "door", "motif", "iffy", "heathen", "elsewhere", "truest", "falsehood", "andy", "orb", "then_x", "x_if", "true1", "not2",
         "if1", "_not", "_if", "ifx", "xif", "notnot", "andand", "oror", "true_false", "elseif", "thenelse",
         "notable and not able or orbit", "not notable", "not not able", "if iffy then thenx else elsewhere", "true_count + false_alarm",
         "truex or true", "a and b or not c", "if a > 1.0 then 2.0 else 3.0", "if a then (if b then 1.0 else 2.0) else 3.0",
         "a andb", "a and(b)", "not(x)", "if(x)then(1.0)else(2.0)", "a and\tb", "a  or  b", "(a)and(b)", "1.0+iffy", "-notable", "not -able",
         "true and false", "truefalse", "nottrue", "not true", "x.notable", "bar.not_energy", "item.iffy", "if x then true else false",
         "ifx then 1.0 else 2.0", "if x then1.0 else 2.0", "if x then 1.0 else2.0", "if x then 1.0 elsex"]
for s in cases:
    try:
        print(f"  {s!r:45} -> {canon(P.parse(s))}"[:200])
    except Exception as e:
        print(f"  {s!r:45} -> ERROR {str(e)[:110]}")
