"""Item 5: effects_hash / items_appearance_hash move on semantic edits, hold on null edits."""
import sys, shutil, logging, warnings
logging.disable(logging.CRITICAL); warnings.filterwarnings("ignore")
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
W = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/hashes")
SRC = Path("configs/test/items_smoke"); LV = "L0_smoke"
KEYS = ["effects_hash", "items_hash", "variables_hash", "actions_hash"]
LKEYS = ["items_appearance_hash", "affordances_hash", "vfs_hash", "observation_schema_hash"]
def build(edits):
    d = W / "p"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(SRC, d, ignore=shutil.ignore_patterns(".compiled"))
    for e in edits:
        f, op = e[0], e[1]
        p = d / f
        if op == "sub":
            t = p.read_text(); assert e[2] in t, (f, e[2]); p.write_text(t.replace(e[2], e[3], 1))
        elif op == "write":
            p.parent.mkdir(parents=True, exist_ok=True); p.write_text(e[2])
        elif op == "move":
            q = d / e[2]; q.parent.mkdir(parents=True, exist_ok=True); p.rename(q)
    try:
        u = UniverseCompiler().compile(d, primary_level=LV, use_cache=False)
    except CompilationError as ex:
        return "REFUSED " + f"{ex.issues[0].code} {ex.issues[0].message[:120]}"
    lv = u.get_level(LV)
    return {**{k: getattr(u, k) for k in KEYS}, **{k: getattr(lv, k) for k in LKEYS}}
base = build([])
EFF, APP = "effects.yaml", f"levels/{LV}/items.yaml"
SEM = {
 "effect body 1.0->1.5": [(EFF, "sub", "(1.0 * intensity)", "(1.5 * intensity)")],
 "effect body op - -> +": [(EFF, "sub", "item.condition - 5.0", "item.condition + 5.0")],
 "effect duration 10->11": [(EFF, "sub", "duration: 10", "duration: 11")],
 "effect reapply renew->stack (wear)": [(EFF, "sub", "duration: 10\n    reapply_policy: renew", "duration: 10\n    reapply_policy: stack")],
 "effect observable true->false (wear)": [(EFF, "sub", "reapply_policy: renew\n    observable: true", "reapply_policy: renew\n    observable: false")],
 "budget item 4->5": [(EFF, "sub", "item: 4", "item: 5")],
 "effect scope item->agent (item_break)": [(EFF, "sub", 'id: "item_break"\n    scope: item', 'id: "item_break"\n    scope: agent'), (EFF, "sub", "agent: 0", "agent: 2"), (EFF, "sub", 'value: "0.0"', 'value: "bar.energy"'), (EFF, "sub", "modify: item.condition\n        value: \"bar.energy\"", "modify: bar.energy\n        value: \"bar.energy\"")],
 "nested spawn_effect intensity 1.0->2.0": [(EFF, "sub", 'on_spawn:\n      - modify: item.condition\n        value: "item.condition - 5.0"', 'on_spawn:\n      - spawn_effect: food_decay\n        target: self\n        intensity: 1.0'), ],
 "effect order swap (wear <-> item_degradation)": None,
 "id rename food_decay->food_rot": [(EFF, "sub", '"food_decay"', '"food_rot"')],
 "spawn_count 3->4": [(APP, "sub", "spawn_count: 3", "spawn_count: 4")],
 "period 100->101": [(APP, "sub", "period: 100", "period: 101")],
 "schedule periodic->poisson": [(APP, "sub", "type: periodic\n      period: 100", "type: poisson\n      rate: 0.1")],
 "placement random->grid": [(APP, "sub", "spawn_count: 3       # Spawn 3 apples at level start\n    placement:\n      mode: random", "spawn_count: 3\n    placement:\n      mode: grid\n      grid_spacing: 2")],
 "add when predicate": [(APP, "sub", "  - item_type: medkit\n    spawn_count: 1", "  - item_type: medkit\n    when: 'bar.health < 0.5'\n    spawn_count: 1")],
 "max_total add": [(APP, "sub", "  - item_type: medkit\n    spawn_count: 1", "  - item_type: medkit\n    max_total: 3\n    spawn_count: 1")],
 "rule order swap apple<->medkit": None,
}
# nested intensity needs two-step: baseline-with-spawn vs changed
NULL = {
 "comments + blank lines (effects)": [(EFF, "sub", "  # Effect that decays an item faster\n", "  # changed comment\n\n\n")],
 "respace expression": [(EFF, "sub", '"item.condition - (1.0 * intensity)"', '"item.condition-(1.0*intensity)"')],
 "redundant parens removed": [(EFF, "sub", '"item.condition - (1.0 * intensity)"', '"item.condition - 1.0 * intensity"')],
 "unquote id": [(EFF, "sub", 'id: "wear_and_tear"', 'id: wear_and_tear')],
 "key reorder in definition": [(EFF, "sub", '    scope: item\n    duration: 10\n', '    duration: 10\n    scope: item\n')],
 "budget key reorder": [(EFF, "sub", "  global: 0\n  agent: 0\n  item: 4\n", "  item: 4\n  agent: 0\n  global: 0\n")],
 "flow list": [(EFF, "sub", "    on_spawn: []\n\n    on_tick:\n      - modify: item.condition\n        value: \"item.condition - (1.0 * intensity)\"", "    on_spawn: []\n    on_tick: [{modify: item.condition, value: \"item.condition - (1.0 * intensity)\"}]")],
 "move effects.yaml -> mechanics/fx.yml": [(EFF, "move", "mechanics/fx.yml")],
 "int vs float literal 1.0 -> 1": [(EFF, "sub", "(1.0 * intensity)", "(1 * intensity)")],
 "duration 10 -> 10.0?": [(EFF, "sub", "duration: 10", "duration: 10.0")],
 "appearance comments": [(APP, "sub", "  # Respawn every 100 ticks", "  # x")],
 "appearance key reorder": [(APP, "sub", "  - item_type: apple\n    spawn_count: 3       # Spawn 3 apples at level start\n", "  - spawn_count: 3\n    item_type: apple\n")],
 "move appearance -> levels/L0_smoke/mechanics/spawn.yml": [(APP, "move", f"levels/{LV}/mechanics/spawn.yml")],
}
def show(label, edits):
    r = build(edits)
    if isinstance(r, str): print(f"{label:52} {r}"); return
    moved = [k for k in r if r[k] != base[k]]
    print(f"{label:52} moved: {moved}")
print("base", {k: (v[:10] if v else v) for k, v in base.items()})
print("--- SEMANTIC (each should move effects_hash or items_appearance_hash)")
for k, e in SEM.items():
    if e is None: continue
    show(k, e)
# order swaps
t = (SRC / EFF).read_text(); a0 = t.index("  # Effect that wears"); a1 = t.index("  # Effect that reads item VFS"); a2 = t.index("  # Effect that breaks")
show("effect order swap (wear <-> item_degradation)", [(EFF, "write", t[:a0] + t[a1:a2] + t[a0:a1] + t[a2:])])
t = (SRC / APP).read_text(); b0 = t.index("  - item_type: apple"); b1 = t.index("  - item_type: medkit"); b2 = t.index("  - item_type: coin")
show("rule order swap apple<->medkit", [(APP, "write", t[:b0] + t[b1:b2] + t[b0:b1] + t[b2:])])
# nested intensity: compare 1.0 vs 2.0 directly
nest = [(EFF, "sub", 'on_spawn:\n      - modify: item.condition\n        value: "item.condition - 5.0"', 'on_spawn:\n      - spawn_effect: food_decay\n        target: self\n        intensity: 1.0')]
r1 = build(nest); r2 = build([(EFF, "sub", nest[0][2], nest[0][3].replace("intensity: 1.0", "intensity: 2.0"))])
print(f"{'nested spawn_effect intensity 1.0 vs 2.0':52}", r1 if isinstance(r1, str) else ("moved effects_hash" if r1["effects_hash"] != r2["effects_hash"] else "DID NOT MOVE effects_hash"))
print("--- NULL (neither should move)")
for k, e in NULL.items(): show(k, e)
print("--- fragment moves")
t = (SRC / EFF).read_text(); i_fd = t.index("  # Effect that decays an item faster"); i_bud = t.index("# Per-scope budget")
food = t[i_fd:i_bud]
rest = t[:i_fd] + t[i_bud:]
show("split: food_decay -> zz_more_effects.yaml (order kept)", [(EFF, "write", rest), ("zz_more_effects.yaml", "write", 'version: "1.0"\neffect_definitions:\n' + food)])
show("split: food_decay -> aa_more_effects.yaml (merged order changes)", [(EFF, "write", rest), ("aa_more_effects.yaml", "write", 'version: "1.0"\neffect_definitions:\n' + food)])
