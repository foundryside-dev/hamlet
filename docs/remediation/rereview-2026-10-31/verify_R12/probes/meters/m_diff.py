"""Item 2: world-0 differential with meter rules. N worlds, 64 steps; world 0 perturbed vs not; worlds 1..N-1 must be bitwise identical."""
import sys
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness, townlet
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/meters"); harness.PACKS.mkdir(parents=True, exist_ok=True)
import torch

def decls(v):
    v["declarations"] += [
        decl("is_night", scope="global", type="bool", initial_value=False, expression="tick % 24 >= 18 or tick % 24 < 6"),
        decl("stress", scope="agent", type="scalar", initial_value=0.0),
        decl("gcount", scope="global", type="scalar", initial_value=0.0),
    ]
rules_ = [
    rule("night_hunger", [rwrite("bar.satiation", "-0.03")], condition="is_night"),
    rule("tired_mood", [rwrite("bar.mood", "-0.02", condition="bar.energy < 0.97"), rwrite("stress", "1.0", condition="bar.energy < 0.97")]),
    rule("stress_hurts", [rwrite("bar.health", "-0.01 * stress", clamp=[0.0, 1.0])], phase="clamp_and_validate"),
    rule("money_rule", [rwrite("bar.money", "bar.money + 0.5", composition="overwrite")], phase="apply_passive_depletion"),
    rule("count", [rwrite("gcount", "1.0")], phase="apply_threshold_cascades"),
]
p = make_pack("diff", variables=decls, rules=rules_)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
def run(perturb):
    u = compile_pack(p)
    torch.manual_seed(7)
    env = build_env(u, N)
    g = torch.Generator().manual_seed(11); g0 = torch.Generator().manual_seed(99)
    rec = []
    for k in range(64):
        a = torch.randint(0, env.action_dim, (N,), generator=g)
        a0 = torch.randint(0, env.action_dim, (1,), generator=g0)
        if perturb: a[0] = a0[0]
        obs, r, d, info = env.step(a)
        snap = {"obs": obs.clone(), "r": r.clone(), "d": d.clone(), "meters": env.meters.clone(), "pos": env.positions.clone()}
        for vid in ["is_night", "stress", "gcount", "tick"]:
            snap[vid] = env.vfs_registry.get(vid, reader="engine").clone()
        rec.append(snap)
    return rec
A, B = run(False), run(True)
first = {}
w0diff = 0
for k, (x, y) in enumerate(zip(A, B)):
    for key in x:
        if key == "tick": continue
        xa, ya = x[key], y[key]
        if xa.dim() == 0: continue
        if not torch.equal(xa[1:], ya[1:]) and key not in first: first[key] = k
        if not torch.equal(xa[:1], ya[:1]): w0diff += 1
print(f"N={N}: world0 differs on {w0diff} key-ticks (perturbation took effect); worlds 1..N-1 first divergence: {first or 'NONE'}")
print("deaths A", int(A[-1]['d'].sum()), "B", int(B[-1]['d'].sum()), "satiation final A", A[-1]['meters'][:, 2].tolist())
