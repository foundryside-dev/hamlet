"""Independent packet-A ENV currentness assertions; no native-owner proof."""

import gc
import weakref
from types import MappingProxyType

import pytest

from tests.test_townlet.regressions.bac.test_prepared_world_currentness import (
    compiled as compiled,
)
from tests.test_townlet.regressions.bac.test_prepared_world_currentness import (
    prepare,
    receiver,
    snapshot,
)


@pytest.mark.parametrize(
    "field", ["_world_role_owners", "_exploration_runtime", "_claim_vector_step", "_world_authority", "_manual_session"]
)
def test_issuance_pins_survive_scope_reacquisition(compiled, monkeypatch, field):
    env, roster, _ = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    with env.retain_parent_custody() as scope:
        scope.validate_prepared_restore(prepared=prepared)
    replacement = MappingProxyType(dict(env._world_role_owners)) if field == "_world_role_owners" else object()
    with monkeypatch.context() as patch:
        patch.setattr(env, field, replacement, raising=False)
        # This scope pins the replacement itself. Refusal must therefore come
        # from the issuance-time seal, not merely this scope's current pins.
        with env.retain_parent_custody() as scope:
            with pytest.raises(ValueError, match="receiving identity"):
                scope.validate_prepared_restore(prepared=prepared)
    with env.retain_parent_custody() as scope:
        assert scope.validate_prepared_restore(prepared=prepared) is None


@pytest.mark.parametrize("field", ["_owner", "_env"])
def test_authority_internal_identity_remains_pinned(compiled, monkeypatch, field):
    env, roster, authority = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    with monkeypatch.context() as patch:
        patch.setattr(authority, field, object())
        with env.retain_parent_custody() as scope:
            with pytest.raises(ValueError, match="receiving identity"):
                scope.validate_prepared_restore(prepared=prepared)
    with env.retain_parent_custody() as scope:
        scope.validate_prepared_restore(prepared=prepared)


def test_record_revocation_is_exact_and_terminal_input_refuses_all(compiled, monkeypatch):
    env, roster, _ = receiver(compiled)
    state = snapshot(env, roster, "INITIAL")
    first, second = prepare(env, roster, state), prepare(env, roster, state)
    # These injections test only A's predicate inputs. They do not stand in
    # for C's actual abort/publication classification or terminal ingress.
    env._world_restore_revoked.add(first)
    with env.retain_parent_custody() as scope:
        with pytest.raises(ValueError, match="current issuer seal"):
            scope.validate_prepared_restore(prepared=first)
        scope.validate_prepared_restore(prepared=second)
        with monkeypatch.context() as patch:
            patch.setattr(env, "_world_restore_terminal", True)
            with pytest.raises(ValueError, match="current issuer seal"):
                scope.validate_prepared_restore(prepared=second)
        scope.validate_prepared_restore(prepared=second)
    assert env._world_phase == "fresh-bound"
    assert env._world_generation == env._world_revision == 0
    assert set(env._world_restore_revoked) == {first}


def test_nested_opaque_preparation_graph_has_no_weak_key_value_cycle(compiled):
    env, roster, _ = receiver(compiled)
    older = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    state = snapshot(env, roster, "COMPLETED")
    state["last_closed_episode"]["completion_content"]["opaque"] = older
    newer = prepare(env, roster, state)
    old_ref, new_ref = weakref.ref(older), weakref.ref(newer)
    old_key, new_key = id(older), id(newer)
    del state, older
    gc.collect()
    assert old_ref() is not None, "a live outer preparation legitimately owns its opaque child"
    with env.retain_parent_custody() as scope:
        scope.validate_prepared_restore(prepared=newer)
    del newer
    gc.collect()
    assert new_ref() is None
    assert old_ref() is None
    assert old_key not in env._world_records and new_key not in env._world_records
    assert len(env._env_custody._restore_seals) == 0
