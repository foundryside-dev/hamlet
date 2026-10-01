"""Selected write intent survives no-op composition and excludes inactive rules."""

import pytest
import torch

from tests.test_townlet.unit.vfs.test_vtc_action_writes import _action, _write
from townlet.vfs.vtc import compile_vtc_action_writes, compile_vtc_social_residue_rules


@pytest.mark.parametrize("composition,expression", [("overwrite", "state"), ("additive_delta", "0"), ("claim_if_free", "7")])
def test_same_value_or_failed_claim_is_still_an_attempt(composition, expression):
    action = _action(
        action_id=2,
        name="ATTEMPT",
        writes=[_write(variable_id="state", expression=expression, condition=None, composition=composition, clamp=None)],
    )
    result = compile_vtc_action_writes([action]).apply(
        actions=torch.tensor([2]),
        vfs_state={"state": torch.tensor([5.0])},
        bars_state={},
        active_mask=torch.tensor([True]),
        device=torch.device("cpu"),
    )
    assert result.attempted_targets == frozenset({"state"})
    assert torch.equal(result.values["state"], torch.tensor([5.0]))


@pytest.mark.parametrize("action,active,condition", [(0, True, None), (2, False, None), (2, True, "false")])
def test_unselected_action_write_has_no_intent(action, active, condition):
    config = _action(
        action_id=2,
        name="ATTEMPT",
        writes=[_write(variable_id="state", expression="7", condition=condition, composition="overwrite", clamp=None)],
    )
    result = compile_vtc_action_writes([config]).apply(
        actions=torch.tensor([action]),
        vfs_state={"state": torch.tensor([5.0])},
        bars_state={},
        active_mask=torch.tensor([active]),
        device=torch.device("cpu"),
    )
    assert result.attempted_targets == frozenset()
    assert torch.equal(result.values["state"], torch.tensor([5.0]))


@pytest.mark.parametrize("active,condition,attempted", [(True, None, True), (False, None, False), (True, "false", False)])
def test_scalar_social_write_respects_active_selection(active, condition, attempted):
    program = compile_vtc_social_residue_rules(
        [
            dict(
                id="global",
                kind="social_residue",
                phase="apply_social_residue_effects",
                reads=["state"],
                condition=condition,
                writes=[dict(variable_id="state", expression="state", composition="overwrite")],
            )
        ]
    )
    result = program.apply(vfs_state={"state": torch.tensor(5.0)}, active_mask=torch.tensor([active]), device=torch.device("cpu"))
    assert result.attempted_targets == (frozenset({"state"}) if attempted else frozenset())
    assert torch.equal(result.values["state"], torch.tensor(5.0))
