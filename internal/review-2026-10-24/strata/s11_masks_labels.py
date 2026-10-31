import yaml, shutil, sys, torch
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.substrate.grid2d import Grid2DSubstrate
print("== (f) zero legal actions: 1x1 clamp grid, no affordance underfoot, no custom WAIT")
u = UniverseCompiler().compile(Path("configs/trial_k_cold"), primary_level="L0_cold")
env = VectorizedHamletEnv.from_universe(u, level_name="L0_cold", num_agents=1, device="cpu"); env.reset()
names = {a.id: a.name for a in env.action_space.actions}
env.substrate = Grid2DSubstrate(1, 1, "clamp", "manhattan", enable_diagonals=False); env.action_mask_builder.substrate = env.substrate
env.positions = torch.tensor([[0, 0]]); env.affordances = {}
m = env.get_action_masks(); print("  legal:", [names[i] for i in range(m.shape[1]) if m[0, i]], "(WAIT is custom in this pack; drop it and the row is all-False)")
m2 = m.clone(); m2[0, env.action_ids["WAIT"]] = False; print("  without custom WAIT legal count:", int(m2.sum()))
print("== GridND: no boundary masking at all (clamp bump allowed, movement cost charged)")
u = UniverseCompiler().compile(Path("configs/test/gridnd_4d_pack"), primary_level="L0_test")
env = VectorizedHamletEnv.from_universe(u, level_name="L0_test", num_agents=1, device="cpu"); env.reset()
env.positions = torch.zeros((1, 4), dtype=torch.long)
m = env.get_action_masks(); names = {a.id: a.name for a in env.action_space.actions}
print("  at origin masked-out:", [names[i] for i in range(m.shape[1]) if not m[0, i]])
e0 = env.meters.clone(); env.step(torch.tensor([env.action_ids["DIM0_NEG"]]))
print("  after DIM0_NEG bump at origin: pos", env.positions.tolist(), " meter delta", (env.meters - e0)[0].tolist())
print("== labels: substrate UP has delta [0,-1]; presets label it as +Y")
for preset in ("cardinal", "math", "gaming"):
    dst = Path(sys.argv[1]) / f"trialk_{preset}"
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(Path("configs/trial_k_cold"), dst, ignore=shutil.ignore_patterns(".compiled"))
    a = dst / "actions.yaml"; a.write_text(a.read_text().replace("preset: cardinal", f"preset: {preset}"))
    u = UniverseCompiler().compile(dst, primary_level="L0_cold"); lvl = u.get_level("L0_cold")
    acts = {x.id: x for x in lvl.runtime_action_space.actions}
    print(f"  {preset}:", [(acts[i].name, acts[i].delta, lab) for i, lab in lvl.action_metadata.labels.items() if acts[i].delta])
