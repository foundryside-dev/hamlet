"""Out-of-bounds meter mid-tick: does an early-phase rule's out-of-bounds value drive cascades before clamp_and_validate?"""
import sys
sys.path.insert(0, "/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/probes/orig/authoring/probes")
from harness import *  # noqa
import harness
harness.PACKS = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/work/meters")
import torch
for label, w in [("overwrite 0.0", rwrite("bar.satiation", "0.0", composition="overwrite")),
                 ("additive -5.0 (escapes to -4)", rwrite("bar.satiation", "-5.0")),
                 ("additive -5.0 with rule clamp [0,1]", rwrite("bar.satiation", "-5.0", clamp=[0.0, 1.0]))]:
    for ph in ["ingest_actions", "apply_passive_depletion"]:
        p = make_pack("oob", rules=[rule("r", [w], phase=ph)])
        u, err = try_compile(p)
        env = build_env(u, 1)
        h0 = float(meter(env, "health")[0]); e0 = float(meter(env, "energy")[0])
        step(env, "WAIT")
        print(f"{label:38} @{ph:24} satiation={float(meter(env,'satiation')[0]):.4f} dhealth={float(meter(env,'health')[0])-h0:+.4f} denergy={float(meter(env,'energy')[0])-e0:+.4f}")
