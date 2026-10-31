import sys; sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
from h import *
import torch
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.environment.dac_engine import DACEngine
from townlet.vfs.registry import VariableRegistry
reg = VariableRegistry(variables=[], num_agents=2, device=torch.device("cpu"), max_items=0, num_affordances=0, item_profiles=None, num_zones=0, num_groups=0, num_message_slots=0)
def mk(extra_extr=None, **kw):
    cfg = {"version": "1.0",
      "modifiers": {"m": {"bar": "b0", "ranges": [{"name": "lo", "min": 0.0, "max": 0.5, "multiplier": 0.0}, {"name": "hi", "min": 0.5, "max": 1.0, "multiplier": 1.0}]}},
      "extrinsic": {"type": "constant_base_with_shaped_bonus", "base_reward": 0.01, "bar_bonuses": [{"bar": "b0", "center": 0.0, "scale": 0.5}], "variable_bonuses": [], "apply_modifiers": []},
      "intrinsic": {"strategy": "rnd", "base_weight": 0.1, "apply_modifiers": ["m"]},
      "shaping": [{"type": "efficiency_bonus", "weight": 2.0, "bar": "b0", "threshold": 0.7}],
      "composition": {"normalize": False, "clip": None, "log_components": False, "log_modifiers": False}}
    if extra_extr: cfg["extrinsic"] = extra_extr
    cfg.update(kw)
    return DACEngine(DriveAsCodeConfig(**cfg), reg, torch.device("cpu"), 2, {"b0": 0, "b1": 1})
meters = torch.tensor([[0.3, 0.9], [0.8, 0.9]]); raw = torch.tensor([1.0, 1.0]); sc = torch.zeros(2, dtype=torch.long)
e = mk()
for dones in (torch.tensor([False, False]), torch.tensor([False, True])):
    tot, w, comp = e.calculate_rewards(step_counts=sc, dones=dones, meters=meters, intrinsic_raw=raw)
    print("dones", dones.tolist(), "total", [round(x, 4) for x in tot.tolist()], "expected [0.16, 2.51] / [0.16, 0.0]; weights", w.tolist(), {k: [round(x,4) for x in v.tolist()] for k, v in comp.items()})
print("--- trap: base_reward 0.0")
e = mk({"type": "constant_base_with_shaped_bonus", "base_reward": 0.0, "bar_bonuses": [], "variable_bonuses": [], "apply_modifiers": []}, shaping=[], intrinsic={"strategy": "none", "base_weight": 0.0, "apply_modifiers": []})
print("base_reward 0.0 -> extrinsic", e.calculate_rewards(step_counts=sc, dones=torch.zeros(2, dtype=torch.bool), meters=meters, intrinsic_raw=raw)[2]["extrinsic"].tolist(), "(expected [0,0])")
e = mk({"type": "multiplicative", "base": 0.0, "bars": ["b0"], "apply_modifiers": []}, shaping=[], intrinsic={"strategy": "none", "base_weight": 0.0, "apply_modifiers": []})
print("multiplicative base 0.0 -> extrinsic", e.calculate_rewards(step_counts=sc, dones=torch.zeros(2, dtype=torch.bool), meters=meters, intrinsic_raw=raw)[2]["extrinsic"].tolist(), "(expected [0,0])")
e = mk({"type": "constant_base_with_shaped_bonus", "bar_bonuses": [], "variable_bonuses": [], "apply_modifiers": []}, shaping=[], intrinsic={"strategy": "none", "base_weight": 0.0, "apply_modifiers": []})
print("constant_base with base_reward omitted -> extrinsic", e.calculate_rewards(step_counts=sc, dones=torch.zeros(2, dtype=torch.bool), meters=meters, intrinsic_raw=raw)[2]["extrinsic"].tolist(), "(hidden default)")
print("--- cross-strategy fields silently ignored")
e = mk({"type": "multiplicative", "base": 1.0, "bars": ["b0"], "bar_bonuses": [{"bar": "b1", "center": 0.0, "scale": 100.0}], "apply_modifiers": []}, shaping=[], intrinsic={"strategy": "none", "base_weight": 0.0, "apply_modifiers": []})
print("multiplicative + bar_bonuses(scale 100) -> extrinsic", e.calculate_rewards(step_counts=sc, dones=torch.zeros(2, dtype=torch.bool), meters=meters, intrinsic_raw=raw)[2]["extrinsic"].tolist())
try:
    e = mk({"type": "vfs_variable", "variable": "nope_var", "apply_modifiers": []}, shaping=[], intrinsic={"strategy": "none", "base_weight": 0.0, "apply_modifiers": []})
    print("vfs_variable with `variable:` only -> extrinsic", e.calculate_rewards(step_counts=sc, dones=torch.zeros(2, dtype=torch.bool), meters=meters, intrinsic_raw=raw)[2]["extrinsic"].tolist(), "(variable field never read)")
except Exception as ex:
    print("vfs_variable with variable: refused", ex)
print("--- modifier on raw (unnormalized) meters: trial002 money_crisis")
u, env = compile("configs/trial002_money_log_gdp", "L0_money")
mi = env.meter_name_to_index["money"]
env.reset()
for money in (1.0, 5.0, 1000.0):
    env.meters[:, mi] = money
    tot, w, comp = env.dac_engine.calculate_rewards(step_counts=env.step_counts, dones=env.dones, meters=env.meters, intrinsic_raw=torch.ones(2))
    print(f"money raw={money} (normalized minmax {(money-1)/999999:.2e}): money_crisis multiplier -> intrinsic_weight {w.tolist()}")
print("bar bounds money:", env.meter_bounds_min[mi].item(), env.meter_bounds_max[mi].item(), "modifiers in drive:", list(env.level.drive.modifiers), "intrinsic.apply_modifiers", env.level.drive.intrinsic.apply_modifiers)
