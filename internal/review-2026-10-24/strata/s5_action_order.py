"""H5/H6/H7: composed ordering vs the [-2]/[-1] contract; family WAIT split; action_discretization dead."""
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
from townlet.substrate.factory import SubstrateFactory
import torch
for pack, level in [("configs/default_curriculum", "L1_full_observability"), ("configs/test/gridnd_4d_pack", "L0_test"),
                    ("configs/test/action_space/continuous1d", None), ("configs/aspatial_test", "L0"), ("configs/trial_k_cold", "L0_cold")]:
    if level is None:
        import yaml; level = sorted(p.name for p in (Path(pack) / "levels").iterdir())[0]
    u = UniverseCompiler().compile(Path(pack), primary_level=level)
    acts = u.get_level(level).runtime_action_space.actions
    print(f"{pack}: n={len(acts)} substrate_count={u.get_level(level).runtime_action_space.substrate_action_count}")
    print("   order:", [f"{a.id}:{a.name}({a.source[0]})" for a in acts])
    print("   [-2] =", acts[-2].name, " [-1] =", acts[-1].name)
    sub = SubstrateFactory.build(u.stratum.stratum.substrate, torch.device("cpu"))
    print("   substrate default names:", [a.name for a in sub.get_default_actions()])
