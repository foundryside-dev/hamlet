import sys, logging; logging.disable(logging.CRITICAL)
from pathlib import Path
import torch
from townlet.universe.compiler import UniverseCompiler
u = UniverseCompiler().compile(Path(sys.argv[1]), primary_level="L0_smoke", use_cache=False)
env = u.create_environment(num_agents=2, level_name="L0_smoke", device="cpu"); env.reset()
im = env.item_manager
print(sys.argv[1].split('/')[-1], "item_manager:", type(im).__name__ if im else None, "active:", (lambda x: len(x() if callable(x) else x))(im.live_items) if im else "-", "appearance_on_level:", u.get_level("L0_smoke").items_appearance is not None)
