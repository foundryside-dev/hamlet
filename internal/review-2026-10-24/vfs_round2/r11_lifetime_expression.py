"""R11: (a) an action write that reads an expression variable of lifetime `tick` sees the reset literal,
not 'the value computed at the end of the previous tick' (variables.md); (b) an action write / rule
whose target is an expression variable compiles and is silently overwritten by evaluation."""
from harness import *  # noqa


@probe("R11a tick-lifetime expression read by an action-write condition")
def a():
    def vars_(v):
        v["declarations"] += [
            decl("rich", lifetime="tick", type="bool", initial_value=False, expression="bar.money > 0.1"),
            decl("rich_ep", lifetime="episode", type="bool", initial_value=False, expression="bar.money > 0.1"),
            decl("hits_tick_lifetime", initial_value=0.0),
            decl("hits_episode_lifetime", initial_value=0.0),
        ]

    def acts(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "ADVANCE":
                ca["writes"] = [write("hits_tick_lifetime", "1.0", condition="rich"),
                                write("hits_episode_lifetime", "1.0", condition="rich_ep")]

    u = compile_pack(make_pack("r11a", variables=vars_, actions=acts))
    env = build_env(u, num_agents=1)
    for k in range(3):
        step(env, "ADVANCE")
        print(f"step{k+1}: money={env.meters[0, env.meter_name_to_index['money']].item():.2f} rich(after eval)={reg(env,'rich').tolist()} "
              f"hits via tick-lifetime cond={reg(env,'hits_tick_lifetime').tolist()} via episode-lifetime cond={reg(env,'hits_episode_lifetime').tolist()}")


@probe("R11b action write / transition rule targeting an expression variable")
def b():
    def vars_(v):
        v["declarations"] += [decl("derived", initial_value=0.0, expression="public_state * 2.0")]

    def acts(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "ADVANCE":
                ca["writes"].append(write("derived", "100.0", composition="overwrite"))

    rules = {"transition_rules.yaml": {"version": "1.0", "social_residue": [
        {"id": "boost", "kind": "social_residue", "phase": "apply_social_residue_effects", "reads": ["derived"], "condition": None,
         "writes": [{"variable_id": "derived", "expression": "derived + 50.0", "composition": "overwrite", "condition": None,
                     "clamp": None, "effect": None}]}]}}
    u = compile_pack(make_pack("r11b", variables=vars_, actions=acts, extra_files=rules))
    print("compile: OK (no refusal for writes to an expression-owned variable)")
    env = build_env(u, num_agents=1)
    step(env, "ADVANCE")
    print(f"after ADVANCE: public_state={reg(env,'public_state').tolist()} derived={reg(env,'derived').tolist()} "
          f"(action wrote 100, rule wrote derived+50; both discarded)")


a()
b()
