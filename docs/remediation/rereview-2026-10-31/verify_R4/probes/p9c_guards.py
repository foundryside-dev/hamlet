"""Engine-defect guards at f3a6d115 (R3 area 3a re-verified): programs run without draws, shape mismatches."""
import torch
from harness import *  # noqa
from harness import make_pack, decl, write, rule, rwrite, try_compile, build_env, step, reg, short
from townlet.determinism import seed_all
from townlet.vfs.random_draws import VFSRandomness, DrawStream
print("townlet at", __import__("townlet").__file__)
def variables(v): v["declarations"].extend([decl("g", scope="global", initial_value=0.0, expression="uniform()"), decl("t", initial_value=0.0), decl("gt", scope="global", initial_value=0.0)])
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("t", "uniform()", composition="overwrite")]
u, err = try_compile(make_pack("guards", variables=variables, actions=actions, rules=[rule("r", [rwrite("gt", "uniform()", composition="overwrite")])]))
seed_all(1); env = build_env(u, 3); s0 = torch.get_rng_state().clone()
def attempt(label, fn):
    try:
        fn(); print(f"  {label}: NO ERROR")
    except Exception as ex:
        print(f"  {label}: {type(ex).__name__}: {short(str(ex), 160)}")
    print("    global rng consumed:", not torch.equal(s0, torch.get_rng_state()))
aw = env.vtc_action_write_program if hasattr(env, "vtc_action_write_program") else None
names = [a for a in dir(env) if "program" in a or "runner" in a]; print("  env programs:", names)
prog_aw = getattr(env, "vtc_action_write_program", None) or getattr(env.vtc_transition_runner.schedule, "action_write_program", None)
prog_tr = getattr(env.vtc_transition_runner.schedule, "transition_rule_program", None)
print("  programs found:", type(prog_aw).__name__ if prog_aw else None, type(prog_tr).__name__ if prog_tr else None)
vfs = {k: env.vfs_registry.get(k, reader="engine") for k in env.vfs_registry.variables}
if prog_aw:
    attempt("action writes with draws=None", lambda: prog_aw.apply(actions=torch.zeros(3, dtype=torch.long), vfs_state=vfs, bars_state=env._current_bar_state(), active_mask=torch.ones(3, dtype=torch.bool), device=torch.device("cpu"), draws=None))
    attempt("action writes with draws for 2 worlds, 3 agents", lambda: prog_aw.apply(actions=torch.zeros(3, dtype=torch.long), vfs_state=vfs, bars_state=env._current_bar_state(), active_mask=torch.ones(3, dtype=torch.bool), device=torch.device("cpu"), draws=env.vfs_randomness.instant(tick=0, worlds=2, device=torch.device("cpu"))))
if prog_tr:
    attempt("transition rules with draws=None", lambda: prog_tr.apply(vfs_state=vfs, active_mask=torch.ones(3, dtype=torch.bool), device=torch.device("cpu"), draws=None, bars_state=env._current_bar_state()))
attempt("global profile evaluated with draws=None", lambda: env.vfs_evaluator.evaluate(u.compiled_vfs_profiles.global_profile if hasattr(u.compiled_vfs_profiles, "global_profile") else u.compiled_vfs_profiles, {}, vfs, {}, device=torch.device("cpu")))
ins = VFSRandomness(1).instant(tick=0, worlds=2, device=torch.device("cpu"))
attempt("DrawStream shape (3,) for 2 worlds", lambda: ins.stream("s", (3,)))
attempt("DrawStream empty shape", lambda: ins.stream("s", ()))
attempt("draw with like of shape (5,) in a (2,) context", lambda: ins.stream("s", (2,)).uniform("uniform", torch.zeros(5)))
attempt("draw with like (2,14) in a (2,) context (arg carries axes: admitted)", lambda: print("     ->", tuple(ins.stream("s", (2,)).uniform("uniform", torch.zeros(2, 14)).shape)))
attempt("draw with like (14,) in a (2,14) context", lambda: ins.stream("s", (2, 14)).uniform("uniform", torch.zeros(14)))
