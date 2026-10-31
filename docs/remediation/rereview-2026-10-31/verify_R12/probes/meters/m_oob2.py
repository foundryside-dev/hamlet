"""D3 follow-up: rule at apply_threshold_cascades overshoots; a later rule at apply_transition_rules reads it."""
import sys
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/meters")
for label, clamp in [("no clamp", None), ("rule clamp [0,1]", [0.0, 1.0])]:
    p = make_pack("oob2", rules=[rule("over", [rwrite("bar.satiation", "-5.0", clamp=clamp)], phase="apply_threshold_cascades"),
                                 rule("reader", [rwrite("bar.mood", "bar.satiation * 0.01")], phase="apply_transition_rules")])
    u, err = try_compile(p); env = build_env(u, 1); m0 = float(meter(env, "mood")[0])
    step(env, "WAIT")
    print(f"{label:18} satiation={float(meter(env,'satiation')[0]):.4f} dmood={float(meter(env,'mood')[0])-m0:+.5f}")
