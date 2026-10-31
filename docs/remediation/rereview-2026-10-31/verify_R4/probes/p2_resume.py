"""Area 2: resume through a real DemoRunner save/load, draws compared tick by tick with an uninterrupted run."""
import logging, shutil, yaml, torch
logging.disable(logging.CRITICAL)
from harness import *  # noqa
from harness import HERE, WT, make_pack, decl, rule, rwrite, write
print("townlet at", __import__("townlet").__file__)
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.demo.runner import DemoRunner
LEVEL = "L1_full_observability"
STEPS = 6; N = 2

def variables(v):
    v["declarations"].extend([
        decl("g_rand", scope="global", initial_value=0.0, expression="uniform()"),
        decl("a_rand", initial_value=0.0, expression="normal_dist()"),
        decl("g_target", scope="global", initial_value=0.0), decl("a_target", initial_value=0.0),
    ])
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST":
            ca["writes"] = [write("a_target", "uniform(-1.0, 0.0)", composition="overwrite")]
pack = make_pack("resume", variables=variables, actions=actions, rules=[rule("rg", [rwrite("g_target", "uniform(0.0, 3.0)", composition="overwrite")])])
t = pack / "levels" / LEVEL / "training.yaml"; d = yaml.safe_load(open(t))
d["training"]["population"]["size"] = N
d["training"]["training_loop"]["max_steps_per_episode"] = STEPS
d["training"]["replay_buffer"]["min_size"] = 4; d["training"]["replay_buffer"]["batch_size"] = 2
yaml.safe_dump(d, open(t, "w"), sort_keys=False)

LOG = []
_step = VectorizedHamletEnv.step
def logged_step(self, actions, *a, **k):
    out = _step(self, actions, *a, **k)
    r = self.vfs_registry
    LOG.append((self.vfs_randomness.episode, self.global_tick, r.get("g_rand", reader="engine").clone(), r.get("a_rand", reader="engine").clone(), r.get("g_target", reader="engine").clone()))
    return out
VectorizedHamletEnv.step = logged_step

def run(tag, max_episodes, fresh=True, interval=100):
    global LOG; LOG = []
    root = HERE / "work_resume" / tag
    if fresh: shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    DemoRunner.CHECKPOINT_INTERVAL = interval
    with DemoRunner(config_dir=pack, db_path=root / "db.sqlite", checkpoint_dir=root / "ckpt", max_episodes=max_episodes, level_name=LEVEL) as runner:
        runner.run()
        state = runner.env.vfs_random_state(); ep_runner = runner.current_episode
    return list(LOG), state, sorted(p.name for p in (root / "ckpt").glob("*.pt"))

A, stA, ckA = run("A", 5)
print(f"uninterrupted: {len(A)} steps, final state {stA}, ckpts {ckA}")
B, stB, ckB = run("B", 3, interval=2)   # saves at runner episodes 0 and 2 (+ final)
print(f"interrupted at 3 episodes: {len(B)} steps, final state {stB}, ckpts {ckB}")
C, stC, ckC = run("C", 5, fresh=False)  # resumes from the latest checkpoint in B's dir? no: same dir needed
# resume must read B's directory
import os
shutil.rmtree(HERE / "work_resume" / "C", ignore_errors=True); shutil.copytree(HERE / "work_resume" / "B", HERE / "work_resume" / "C")
C, stC, ckC = run("C", 5, fresh=False)
print(f"resumed to 5 episodes: {len(C)} steps, final state {stC}, ckpts {ckC}")
print("episode counters seen: A", sorted({e for e, *_ in A}), "B", sorted({e for e, *_ in B}), "C", sorted({e for e, *_ in C}))
# compare C's rows against A's rows with the same (episode, tick)
idxA = {(e, t): (g, a, gt) for e, t, g, a, gt in A}
mism = 0; cmp = 0; first = None
for e, t, g, a, gt in C:
    if (e, t) not in idxA: print("  C has (episode, tick) absent from A:", (e, t)); continue
    cmp += 1
    ok = torch.equal(g, idxA[(e, t)][0]) and torch.equal(a, idxA[(e, t)][1]) and torch.equal(gt, idxA[(e, t)][2])
    if not ok:
        mism += 1
        if first is None: first = (e, t, g.tolist(), idxA[(e, t)][0].tolist())
print(f"resumed vs uninterrupted at the same (episode, tick): {cmp} compared, {mism} mismatches; first={first}")
print("B's own rows equal A's (prefix):", all(torch.equal(g, idxA[(e, t)][0]) and torch.equal(gt, idxA[(e, t)][2]) for e, t, g, a, gt in B))
# same runner-episode index correspondence: does C's first episode equal A's episode at the same runner index?
eps_C = sorted({e for e, *_ in C}); eps_B = sorted({e for e, *_ in B})
print("B episodes", eps_B, "C episodes", eps_C, "(C should continue after B's last, with none repeated and none skipped)")
# mid-episode save path?
import inspect, re
src = inspect.getsource(DemoRunner)
print("save_checkpoint call sites (line offsets in DemoRunner):", [i for i, l in enumerate(src.splitlines()) if "self.save_checkpoint()" in l])
print("shutdown break inside the step loop:", bool(re.search(r"for step in range.*?should_shutdown.*?break", src, re.S)))
