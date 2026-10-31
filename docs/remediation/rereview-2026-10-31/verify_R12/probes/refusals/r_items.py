"""Item 3d: item-state dtype cast: bool and every ref type in item profiles; read/write; not/and/or/comparisons."""
import sys
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/vfs_runtime/probes")
from common import *  # noqa
import harness
from harness import make_pack_from, edit_yaml, REPO
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/items3d"); harness.PACKS.mkdir(parents=True, exist_ok=True)
import torch
ITEMS = REPO / "configs" / "test" / "items_smoke"

def iv(id_, type_, init):
    return {"id": id_, "readable_by": ["engine", "agent"], "writable_by": ["engine"], "scope": "item", "type": type_, "lifetime": "episode",
            "semantic_type": "custom", "exposed_to": [], "profile": "food", "initial_value": init}

STATE = [iv("flag", "bool", False), iv("own", "agent_ref", None), iv("iref", "item_ref", None), iv("aref", "affordance_ref", None),
         iv("eref", "effect_ref", None), iv("own1", "agent_ref", -1), iv("aref0", "affordance_ref", 0), iv("cnt", "scalar", 0.0)]

def build(name, on_use, state=STATE):
    def mutate(dest):
        edit_yaml(dest / "variables.yaml", lambda p: p["variables"]["declarations"].extend(state))
        def items_(p):
            for it in p["items"]["item_types"]:
                if it["id"] == "apple":
                    it["interactions"]["on_use"] = on_use
        edit_yaml(dest / "items.yaml", items_)
    return make_pack_from(name, ITEMS, mutate)

def use_apple(u, n_use=2):
    env = build_env(u, num_agents=2, level="L0_smoke")
    names = [a.name for a in env.action_space.actions]
    ap = [i for i in env.item_manager.items_in_world(0) if i.item_type == "apple"][0]
    env.positions[0] = torch.as_tensor(ap.position, dtype=env.positions.dtype)
    a = acts(env, "WAIT"); a[0] = action_index(env, "GET"); env.step(a)
    out = []
    for _ in range(n_use):
        a = acts(env, "WAIT"); a[0] = action_index(env, "USE_SLOT_0"); env.step(a)
        r = env.vfs_registry
        out.append({k: r.read_item("food", k, ap.vfs_index, reader="engine") for k in ["flag", "cnt", "own", "aref0"]})
    return out

CASES = {
  "not item.flag -> toggle flag": [{"if": "not item.flag", "then": [{"modify": "item.flag", "value": "not item.flag"}], "else": [{"modify": "item.flag", "value": "not item.flag"}]}],
  "item.flag and true": [{"if": "item.flag and true", "then": [{"modify": "item.cnt", "value": "item.cnt + 10.0"}], "else": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}]}],
  "item.flag or item.flag": [{"if": "item.flag or item.flag", "then": [], "else": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}]}],
  "item.flag == false": [{"if": "item.flag == false", "then": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}], "else": []}],
  "where(item.flag, 2.0, 1.0)": [{"modify": "item.cnt", "value": "item.cnt + where(item.flag, 2.0, 1.0)"}],
  "item.own == item.own1 (agent_ref)": [{"if": "item.own == item.own1", "then": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}], "else": []}],
  "item.iref == item.iref (item_ref)": [{"if": "item.iref == item.iref", "then": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}], "else": []}],
  "item.aref == item.aref0 (affordance_ref)": [{"if": "item.aref == item.aref0", "then": [], "else": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}]}],
  "item.eref == item.eref (effect_ref)": [{"if": "item.eref == item.eref", "then": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}], "else": []}],
  "item.own != item.own1": [{"if": "item.own != item.own1", "then": [], "else": [{"modify": "item.cnt", "value": "item.cnt + 1.0"}]}],
  "write own <- own1 (ref write)": [{"modify": "item.own", "value": "item.own1"}, {"modify": "item.cnt", "value": "item.cnt + 1.0"}],
  "write aref0 <- aref0": [{"modify": "item.aref0", "value": "item.aref0"}, {"modify": "item.cnt", "value": "item.cnt + 1.0"}],
  "bar.energy > 0.5 and not item.flag": [{"if": "bar.energy > 0.5 and not item.flag", "then": [{"modify": "item.flag", "value": "true"}], "else": []}],
  "switch on item.flag": [{"switch": "item.flag", "cases": [{"when": "true", "do": [{"modify": "item.cnt", "value": "item.cnt + 5.0"}]}], "default": [{"modify": "item.flag", "value": "true"}]}],
}
for label, on_use in CASES.items():
    p = build("it", on_use)
    try:
        u = compile_pack(p, level="L0_smoke")
    except Exception as e:
        msg = str(e); i = msg.find(" - ", msg.find("[")); print(f"{label:42} REFUSED {msg[msg.find('['):msg.find(']')+1]} {msg[i+3:i+170]}"); continue
    try:
        print(f"{label:42} RAN {use_apple(u)}")
    except Exception as e:
        import traceback; tb = traceback.extract_tb(e.__traceback__)[-1]
        print(f"{label:42} RUNTIME {type(e).__name__} @{Path(tb.filename).name}:{tb.lineno}: {str(e)[:150]}")
