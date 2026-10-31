import torch
from townlet.config.stratum_config import SubstrateConfig
from townlet.substrate.factory import SubstrateFactory
for desc, cfg in [("gridnd with 2 dims", {"type": "gridnd", "gridnd": {"dimension_sizes": [3, 3], "boundary": "clamp", "distance_metric": "manhattan", "topology": "hypercube"}}),
                  ("continuous with 5 dims", {"type": "continuous", "continuous": {"dimensions": 5, "bounds": [[0, 1]]*5, "boundary": "clamp", "movement_delta": 0.1, "interaction_radius": 0.2, "distance_metric": "euclidean", "action_discretization": {"num_directions": 8, "num_magnitudes": 3}}}),
                  ("continuousnd with 2 dims", {"type": "continuousnd", "continuous": {"dimensions": 2, "bounds": [[0, 1]]*2, "boundary": "clamp", "movement_delta": 0.1, "interaction_radius": 0.2, "distance_metric": "euclidean", "action_discretization": {"num_directions": 8, "num_magnitudes": 3}}}),
                  ("grid width 1", {"type": "grid", "grid": {"topology": "square", "width": 1, "height": 1, "boundary": "bounce", "distance_metric": "manhattan", "diagonals": False}})]:
    try:
        c = SubstrateConfig(**cfg); print(f"{desc}: DTO accepts;", end=" ")
        SubstrateFactory.build(c, torch.device("cpu")); print("factory builds")
    except Exception as e:
        print("refused ->", type(e).__name__, str(e).splitlines()[0][:120])
