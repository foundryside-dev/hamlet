"""R6: transition rules (social_residue) — pair broadcast axis, agent-shaped value into a global
target, and `reads` being required but never checked against the expression."""
from harness import *  # noqa


def rules_file(rules):
    return {"transition_rules.yaml": {"version": "1.0", "social_residue": rules}}


def rule(rid, reads, writes, phase="apply_social_residue_effects", condition=None):
    return {"id": rid, "kind": "social_residue", "phase": phase, "reads": reads, "condition": condition, "writes": writes}


def rwrite(var, expr, composition="additive_delta", condition=None):
    return {"variable_id": var, "expression": expr, "composition": composition, "condition": condition, "clamp": None, "effect": None}


def run(label, decls, rules, n=2, show=(), pre=None):
    print(f"--- {label} (num_agents={n})")
    try:
        pack = make_pack(f"r6_{label}", variables=lambda v: v["declarations"].extend(decls), extra_files=rules_file(rules))
        u = compile_pack(pack)
        print("   compile: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:400]}")
        return
    try:
        env = build_env(u, num_agents=n)
        if pre:
            pre(env)
        step(env, "WAIT")
        for name in show:
            print(f"   after 1 step: {name} = {[[round(x, 4) for x in r] if isinstance(r, list) else round(r, 4) for r in reg(env, name).tolist()] if reg(env, name).dim() else round(reg(env, name).item(), 4)}")
    except Exception as exc:  # noqa: BLE001
        print(f"   runtime: {type(exc).__name__}: {str(exc)[:400]}")


def set_energy(env):
    idx = env.meter_name_to_index["energy"]
    env.meters[:, idx] = torch.tensor([0.9, 0.5, 0.1][: env.num_agents])


@probe("R6 transition rules")
def main():
    trust = decl("trust", scope="pair", initial_value=0.0)
    # agent-shaped value into a pair target: which axis receives agent i's value?
    run("pair_agent_value", [trust], [rule("t", ["trust", "energy"], [rwrite("trust", "bar.energy")])], n=3,
        show=("trust",), pre=set_energy)
    # agent-shaped value into a GLOBAL target: compile green?
    g = decl("gsum", scope="global", initial_value=0.0)
    run("global_agent_value", [g], [rule("g", ["energy"], [rwrite("gsum", "bar.energy")])], n=3, show=("gsum",), pre=set_energy)
    # reads list that names nothing real / omits what the expression reads
    run("reads_lies", [g], [rule("r", ["no_such_variable"], [rwrite("gsum", "immutable_scale")])], n=2, show=("gsum",))
    # kind is a label only: same rule under the three kinds
    for kind in ("social_residue", "visibility_effect", "institutional_rule"):
        r = rule("k", ["gsum"], [rwrite("gsum", "1.0")])
        r["kind"] = kind
        run(f"kind_{kind}", [g], [r], n=2, show=("gsum",))


main()
