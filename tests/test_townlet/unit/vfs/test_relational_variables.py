"""Tests for canonical L5 relational VFS variables."""

import torch

from townlet.vfs import VariableRegistry, canonical_l5_relational_variables


def test_canonical_l5_relational_variables_match_spec_metadata() -> None:
    variables = canonical_l5_relational_variables()

    assert [variable.id for variable in variables] == ["trust", "obligation", "public_reputation", "norm_legitimacy"]

    by_id = {variable.id: variable for variable in variables}
    assert by_id["trust"].scope == "pair"
    assert by_id["trust"].default == 0.5
    assert by_id["trust"].normalization is not None
    assert by_id["trust"].normalization.kind == "minmax"
    assert by_id["trust"].normalization.min == 0.0
    assert by_id["trust"].normalization.max == 1.0

    assert by_id["obligation"].scope == "pair"
    assert by_id["obligation"].default == 0.0
    assert by_id["public_reputation"].scope == "agent"
    assert by_id["public_reputation"].readable_by == ["agent", "other_agents", "social_model", "engine"]
    assert by_id["norm_legitimacy"].scope == "group"
    assert by_id["norm_legitimacy"].readable_by == ["engine", "social_model"]

    for variable in variables:
        assert variable.type == "scalar"
        assert variable.lifetime == "episode"
        assert variable.writable_by == ["vtc"]


def test_canonical_l5_relational_variables_initialize_expected_registry_shapes() -> None:
    registry = VariableRegistry(
        variables=list(canonical_l5_relational_variables()),
        num_agents=3,
        num_groups=2,
        device=torch.device("cpu"),
    )

    assert registry.get("trust", reader="engine").shape == torch.Size([3, 3])
    assert torch.all(registry.get("trust", reader="engine") == 0.5)
    assert registry.get("obligation", reader="engine").shape == torch.Size([3, 3])
    assert torch.all(registry.get("obligation", reader="engine") == 0.0)
    assert registry.get("public_reputation", reader="engine").shape == torch.Size([3])
    assert torch.all(registry.get("public_reputation", reader="engine") == 0.5)
    assert registry.get("norm_legitimacy", reader="engine").shape == torch.Size([2])
    assert torch.all(registry.get("norm_legitimacy", reader="engine") == 0.5)
