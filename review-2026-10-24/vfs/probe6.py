"""Probe 6: apply_modulations — requested by nobody in step()?"""
import torch
from harness import *  # noqa: F403

@probe("A. action write and social_residue rule at apply_modulations")
def probe_a():
    p = make_pack("phase_apply_modulations_write", actions=lambda a: next(x for x in a["custom_actions"] if x["name"] == "ADVANCE").__setitem__("writes", [write("public_state", "1.0", phase="apply_modulations")]))
    try:
        u = compile_pack(p); env = build_env(u, 2); step(env, "ADVANCE"); step(env, "ADVANCE")
        print("   action write @apply_modulations: compile OK, 2x ADVANCE ->", reg(env, "public_state").tolist())
    except Exception as e:
        print("   action write @apply_modulations:", type(e).__name__, str(e)[:200])
    rules = {"version": "1.0", "social_residue": [{"id": "inc", "kind": "institutional_rule", "phase": "apply_modulations", "reads": ["public_state"], "condition": None,
             "writes": [{"variable_id": "public_state", "expression": "public_state + 1.0", "composition": "overwrite", "condition": None, "clamp": None, "effect": None, "scope": "agent"}]}]}
    p = make_pack("phase_apply_modulations_rule", extra_files={"transition_rules.yaml": rules})
    try:
        u = compile_pack(p); env = build_env(u, 2); step(env, "WAIT"); step(env, "WAIT")
        print("   residue rule @apply_modulations: compile OK, 2 steps ->", reg(env, "public_state").tolist())
    except Exception as e:
        print("   residue rule @apply_modulations:", type(e).__name__, str(e)[:200])

if __name__ == "__main__":
    probe_a()
