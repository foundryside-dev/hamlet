"""Write-path dtype/shape traps: vector targets, clamp on bool/ref, bool composition, sample into bool/ref,
expression var with writable_by [], rule at evaluate_terminal_conditions, meter-name collision, composition clamp w/o clamp."""
from common import *  # noqa
import sys
import torch


@probe("W1 action write / rule into a vecNf / tensor1d agent target (type admits float; shape proof says 'agent')")
def w1():
    decls = [decl("vec", type="vecNf", dims=3, initial_value=[0.0, 0.0, 0.0]), decl("t1", type="tensor1d", shape=[2], initial_value=[0.0, 0.0]),
             decl("av", initial_value=2.0)]
    for label, expr in [("literal", "1.0"), ("agent scalar av", "av"), ("bar.energy", "bar.energy")]:
        u = try_compile(f"action write vec <- {label}", lambda: compile_sea(f"w1a_{label[:3]}", decls=decls, writes=[write("vec", expr, composition="overwrite")]))
        if u is not None:
            env = build_env(u, num_agents=3)
            try_run("  step ADVANCE", lambda: (step(env, "ADVANCE"), reg(env, "vec").tolist())[1])
        u = try_compile(f"rule vec <- {label}", lambda: compile_sea(f"w1r_{label[:3]}", decls=decls, rules=[rule("r", [rwrite("vec", expr, composition="overwrite")])]))
        if u is not None:
            env = build_env(u, num_agents=3)
            try_run("  step WAIT", lambda: (step(env, "WAIT"), reg(env, "vec").tolist())[1])
    # N == dims coincidence
    u = try_compile("rule t1 <- av at N == 2 == shape", lambda: compile_sea("w1n", decls=decls, rules=[rule("r", [rwrite("t1", "av", composition="overwrite")])]))
    if u is not None:
        for n in (2, 3):
            env = build_env(u, num_agents=n)
            setreg(env, "av", [float(i + 1) for i in range(n)])
            try_run(f"  N={n} step WAIT t1", lambda: (step(env, "WAIT"), reg(env, "t1").tolist())[1])
    # reading a vector in a write expression
    try_compile("action write av <- vec[0]", lambda: compile_sea("w1v", decls=decls, writes=[write("av", "vec[0]", composition="overwrite")]))
    try_compile("action write av <- vec", lambda: compile_sea("w1v2", decls=decls, writes=[write("av", "vec", composition="overwrite")]))


@probe("W2 clamp on a bool / reference target; bool compositions")
def w2():
    decls = [decl("flag", type="bool", initial_value=False), decl("aref", type="agent_ref", initial_value=None)]
    u = try_compile("action write flag <- true clamp [0,1]", lambda: compile_sea("w2a", decls=decls, writes=[write("flag", "true", composition="overwrite", clamp=[0.0, 1.0])]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step ADVANCE flag", lambda: (step(env, "ADVANCE"), reg(env, "flag").tolist())[1])
    u = try_compile("action write aref <- -1 overwrite clamp [0,10]", lambda: compile_sea("w2b", decls=decls, writes=[write("aref", "-1", composition="overwrite", clamp=[0.0, 10.0])]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step ADVANCE aref", lambda: (step(env, "ADVANCE"), reg(env, "aref").tolist())[1])
    u = try_compile("action write aref <- agent_id overwrite clamp [0,0.5]", lambda: compile_sea("w2c", decls=decls, writes=[write("aref", "agent_id", composition="overwrite", clamp=[0.0, 0.5])]))
    if u is not None:
        env = build_env(u, num_agents=3)
        try_run("  step ADVANCE aref", lambda: (step(env, "ADVANCE"), reg(env, "aref").tolist())[1])
    for comp in ("additive_delta", "multiplicative_modifier", "min", "max"):
        u = try_compile(f"action write flag <- true {comp}", lambda: compile_sea(f"w2_{comp[:3]}", decls=decls, writes=[write("flag", "true", composition=comp)]))
        if u is not None:
            env = build_env(u, num_agents=2)
            try_run("  step ADVANCE x2 flag", lambda: (step(env, "ADVANCE"), step(env, "ADVANCE"), reg(env, "flag").tolist())[2])
    u = try_compile("rule flag <- true clamp [0,1]", lambda: compile_sea("w2r", decls=decls, rules=[rule("r", [rwrite("flag", "true", composition="overwrite", clamp=[0.0, 1.0])])]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step WAIT flag", lambda: (step(env, "WAIT"), reg(env, "flag").tolist())[1])


@probe("W3 effect `sample` into a bool / reference target; effect modify int literal into scalar")
def w3():
    decls = [decl("flag", type="bool", initial_value=False), decl("aref", type="agent_ref", initial_value=None), decl("sv", initial_value=0.0)]
    for label, target in [("bool", "flag"), ("agent_ref", "aref"), ("scalar", "sv")]:
        u = try_compile(f"effect sample uniform store_in {label}", lambda: compile_sea(f"w3_{label[:4]}", decls=decls, effects=[effect("e1", [
            {"sample": "uniform", "params": {"min": 0.2, "max": 0.9}, "store_in": target}])]))
        if u is not None:
            env = build_env(u, num_agents=2)
            spawn(env, "e1", 1)
            try_run(f"  step WAIT {target}", lambda: (step(env, "WAIT"), reg(env, target).tolist())[1])
    try_compile("effect modify sv value 1 (int literal)", lambda: compile_sea("w3i", decls=decls, effects=[effect("e1", [{"modify": "sv", "value": "1"}])]))
    try_compile("effect modify flag value bar.energy (float into bool)", lambda: compile_sea("w3f", decls=decls, effects=[effect("e1", [{"modify": "flag", "value": "bar.energy"}])]))
    try_compile("effect modify aref value 0.6", lambda: compile_sea("w3r", decls=decls, effects=[effect("e1", [{"modify": "aref", "value": "0.6"}])]))
    u = try_compile("effect modify aref value 0 (int)", lambda: compile_sea("w3r0", decls=decls, effects=[effect("e1", [{"modify": "aref", "value": "0"}])]))
    if u is not None:
        env = build_env(u, num_agents=3)
        spawn(env, "e1", 2)
        try_run("  step WAIT aref (world 2 effect writes 0 = world 0's agent)", lambda: (step(env, "WAIT"), reg(env, "aref").tolist())[1])


@probe("W4 expression variable with writable_by [] ; expression var exposed; static engine-only read by exposed expression")
def w4():
    decls = [decl("ex", writable=(), initial_value=0.0, expression="public_state * 2.0")]
    u = try_compile("expression var writable_by []", lambda: compile_sea("w4a", decls=decls))
    if u is not None:
        try_run("  build_env (reset evaluates)", lambda: (build_env(u, num_agents=2), "ok")[1])
    decls = [decl("ex2", exposed=("agent",), normalization={"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True},
                  initial_value=0.0, expression="hidden_score * immutable_scale")]
    u = try_compile("exposed expression over engine-only hidden_score & immutable_scale", lambda: compile_sea("w4b", decls=decls))
    if u is not None:
        env = build_env(u, num_agents=2)
        obs = env._get_observations()
        from harness import ve_rows
        print("   obs variable_element rows:", ve_rows(env, obs, agent=0))
        print("   hidden_score*immutable_scale =", (reg(env, "hidden_score") * reg(env, "immutable_scale")).tolist(), "(engine-only values, readable in the token as ex2)")


@probe("W5 rule scheduled at evaluate_terminal_conditions / clamp_and_validate vs expression evaluation order")
def w5():
    decls = [decl("g", scope="global", initial_value=0.0), decl("g2", scope="global", initial_value=0.0, expression="g * 2.0")]
    for ph in ("apply_transition_rules", "clamp_and_validate", "evaluate_terminal_conditions", "ingest_actions", "apply_passive_depletion"):
        u = try_compile(f"rule g += 1 at {ph}", lambda: compile_sea(f"w5_{ph[:8]}", decls=decls, rules=[rule("r", [rwrite("g", "1.0")], phase=ph)]))
        if u is None:
            continue
        env = build_env(u, num_agents=2)
        out = []
        for _ in range(3):
            step(env, "WAIT")
            out.append((reg(env, "g")[0].item(), reg(env, "g2")[0].item()))
        print(f"   {ph}: (g, g2) per step = {out}")
    # action write at a non-action phase
    try_compile("action write at apply_transition_rules", lambda: compile_sea("w5a", decls=decls[:1], writes=[write("public_state", "1.0", phase="apply_transition_rules")]))
    try_compile("action write at evaluate_terminal_conditions", lambda: compile_sea("w5b", decls=decls[:1], writes=[write("public_state", "1.0", phase="evaluate_terminal_conditions")]))
    try_compile("rule at unknown phase", lambda: compile_sea("w5c", decls=decls[:1], rules=[rule("r", [rwrite("g", "1.0")], phase="compute_rewards")]))


@probe("W6 variable named like a meter; composition clamp with clamp null; condition non-bool; claim_if_free from a custom action")
def w6():
    try_compile("variable id 'energy' (meter name)", lambda: compile_sea("w6a", decls=[decl("energy", initial_value=0.0)]))
    u = try_compile("composition clamp with clamp: null", lambda: compile_sea("w6b", writes=[write("public_state", "5.0", composition="clamp", clamp=None)]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step ADVANCE public_state", lambda: (step(env, "ADVANCE"), reg(env, "public_state").tolist())[1])
    try_compile("condition float (bar.energy)", lambda: compile_sea("w6c", writes=[write("public_state", "1.0", condition="bar.energy")]))
    try_compile("rule condition int (agent_id)", lambda: compile_sea("w6d", rules=[rule("r", [rwrite("public_state", "1.0")], condition="agent_id")]))
    decls = [decl("occ", scope="affordance", type="agent_ref", initial_value=None)]
    try_compile("custom action claim_if_free on affordance agent_ref", lambda: compile_sea("w6e", decls=decls, writes=[write("occ", "agent_id", composition="claim_if_free", phase="resolve_affordance_access_and_occupancy")]))
    # int widening in a write; where(c,1,0) into scalar
    u = try_compile("action write public_state <- where(bar.energy > 0.5, 1, 0)", lambda: compile_sea("w6f", writes=[write("public_state", "where(bar.energy > 0.5, 1, 0)", composition="overwrite")]))
    if u is not None:
        env = build_env(u, num_agents=2)
        try_run("  step ADVANCE", lambda: (step(env, "ADVANCE"), reg(env, "public_state").tolist(), reg(env, "public_state").dtype)[1:])
    # division by zero in an exposed expression
    decls = [decl("zero", scope="global", initial_value=0.0), decl("inv", exposed=("agent",), normalization={"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}, initial_value=0.0, expression="public_state / zero")]
    u = try_compile("exposed expression public_state / zero", lambda: compile_sea("w6g", decls=decls))
    if u is not None:
        try_run("  build_env (reset publishes)", lambda: (build_env(u, num_agents=2), "ok")[1])


if __name__ == "__main__":
    which = sys.argv[1:] or ["w1", "w2", "w3", "w4", "w5", "w6"]
    for name in which:
        globals()[name]()
