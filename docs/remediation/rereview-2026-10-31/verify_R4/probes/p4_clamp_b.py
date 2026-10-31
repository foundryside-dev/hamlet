"""D3 follow-up: same-phase action write then rule read, with mood started below its max so the read is visible."""
import torch
from harness import *  # noqa
from harness import make_pack, write, rule, rwrite, try_compile, build_env, step, meter
L1 = "L1_full_observability"
def actions(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "REST": ca["writes"] = [write("bar.satiation", "5.0", phase="ingest_actions")]
for label, rules in [("control", []), ("rule same phase (ingest_actions)", [rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="ingest_actions")]),
                     ("rule later phase (apply_action_effects)", [rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_action_effects")]),
                     ("rule at apply_transition_rules", [rule("rd", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_transition_rules")])]:
    u, err = try_compile(make_pack("c3_" + str(abs(hash(label)) % 10**6), actions=actions, rules=rules)); env = build_env(u, 1)
    env.meters[:, env.meter_name_to_index["mood"]] = 0.5; env.meters[:, env.meter_name_to_index["satiation"]] = 0.3
    step(env, "REST"); print(f"  {label:42}: dmood={float(meter(env,'mood')[0]) - 0.5:+.5f} satiation={float(meter(env,'satiation')[0]):.4f}")
print("  (raw 5.3 -> +0.053; clamped 1.0 -> +0.010; phase-entry 0.3 -> +0.003; each minus mood passive 0.004)")
