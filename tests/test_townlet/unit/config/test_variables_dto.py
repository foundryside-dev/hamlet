import pytest
from pydantic import ValidationError

from townlet.config.variables_config import VariableDeclaration, VariablesConfig


def variable(**changes):
    return {
        "id": "state",
        "scope": "agent",
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "initial_value": 0.0,
        **changes,
    }


def test_same_variable_contract_for_all_storage_scopes():
    for scope in ["global", "agent", "agent_private", "pair", "group", "affordance", "zone", "message"]:
        assert VariableDeclaration.model_validate(variable(scope=scope)).scope == scope


def test_initialization_is_explicit_even_for_derived_values():
    payload = variable(scope="global", expression="tick")
    payload.pop("initial_value")
    with pytest.raises(ValidationError, match="initial"):
        VariableDeclaration.model_validate(payload)


def test_reference_null_is_a_declared_unbound_value():
    declaration = VariableDeclaration.model_validate(variable(type="agent_ref", initial_value=None))
    assert declaration.initial_value is None
    payload = variable(type="agent_ref")
    payload.pop("initial_value")
    with pytest.raises(ValidationError, match="initial"):
        VariableDeclaration.model_validate(payload)


@pytest.mark.parametrize("field,value", [("name", "state")])
def test_removed_aliases_refuse(field, value):
    with pytest.raises(ValidationError, match="Extra inputs"):
        VariableDeclaration.model_validate(variable(**{field: value}))


@pytest.mark.parametrize("kind", ["float", "int", "vector"])
def test_public_type_has_one_spelling(kind):
    with pytest.raises(ValidationError):
        VariableDeclaration.model_validate(variable(type=kind))


@pytest.mark.parametrize("scope", ["agent_private", "pair", "group", "affordance", "zone", "message"])
def test_unimplemented_expression_scopes_refuse(scope):
    with pytest.raises(ValidationError, match="expression"):
        VariableDeclaration.model_validate(variable(scope=scope, expression="tick"))


def test_item_group_and_runtime_limits_are_explicit():
    accepted = VariableDeclaration.model_validate(variable(scope="item", profile="food"))
    assert accepted.profile == "food"
    for changes in [{"profile": None}, {"lifetime": "persistent"}, {"expression": "tick"}, {"type": "vec2f", "initial_value": [0.0, 0.0]}]:
        with pytest.raises(ValidationError):
            VariableDeclaration.model_validate(variable(**{"scope": "item", "profile": "food", **changes}))


def test_normalization_is_consumed_exactly_at_exposure():
    with pytest.raises(ValidationError, match="normalization"):
        VariableDeclaration.model_validate(variable(exposed_to=["agent"]))
    with pytest.raises(ValidationError, match="normalization"):
        VariableDeclaration.model_validate(variable(normalization={"kind": "minmax", "min": 0, "max": 1, "clip": True}))
    VariableDeclaration.model_validate(variable(exposed_to=["agent"], normalization={"kind": "minmax", "min": 0, "max": 1, "clip": True}))


def test_empty_item_profile_remains_a_real_binding_target():
    config = VariablesConfig.model_validate(
        {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": [],
        }
    )
    assert config.item_profiles == ["default_item"]


@pytest.mark.parametrize(
    "mode,params",
    [
        ("random_normal", {"mean": 0.0, "std": -1.0}),
        ("random_normal", {"mean": float("nan"), "std": 1.0}),
        ("random_uniform", {"low": 2.0, "high": 1.0}),
        ("random_uniform", {"low": 0.0, "high": float("inf")}),
    ],
)
def test_random_initializer_parameters_refuse_before_allocation(mode, params):
    payload = variable(type="tensor1d", shape=[2], initial_value_mode=mode, initial_value_params=params)
    payload.pop("initial_value")
    with pytest.raises(ValidationError, match="initializer"):
        VariableDeclaration.model_validate(payload)


def test_item_reference_null_initializes_actual_arena_as_unbound(tmp_path):
    import shutil

    import yaml

    from townlet.universe.compiled import CompiledUniverse
    from townlet.universe.compiler import UniverseCompiler

    directory = tmp_path / "pack"
    shutil.copytree("configs/test/items_smoke", directory)
    path = directory / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"].append(variable(id="claimant", scope="item", profile="food", type="agent_ref", initial_value=None))
    path.write_text(yaml.safe_dump(payload))
    compiled = UniverseCompiler().compile(directory, primary_level="L0_smoke", use_cache=False)
    for universe in (compiled, CompiledUniverse.from_dict(compiled.to_dict())):
        env = universe.create_environment(num_agents=1, level_name="L0_smoke", device="cpu")
        env.reset()
        item = env.item_manager.spawn_item(item_type="apple", position=(0, 0), current_tick=0)
        assert item is not None
        assert env.vfs_registry.read_item("food", "claimant", item.vfs_index) == -1


@pytest.mark.parametrize(
    "declarations",
    [
        [variable(scope="global", type="agent_ref", initial_value=None)],
        [variable(scope="global", type="tensor1d", shape=[2], initial_value_mode="ones")],
    ],
)
def test_eager_unsupported_initialization_refuses_before_execution(declarations):
    for declaration in declarations:
        if "initial_value_mode" in declaration:
            declaration.pop("initial_value")
    with pytest.raises(ValidationError, match="eager"):
        VariablesConfig.model_validate(
            dict(version="1.0", evaluation_mode="eager", debug_logging=False, extents={}, item_profiles=[], declarations=declarations)
        )


@pytest.mark.parametrize(
    "dtype,initial,extra", [("bool", True, {}), ("agent_ref", 0, {}), ("vec2i", [0, 0], {}), ("vecNi", [0], {"dims": 1})]
)
def test_registry_exposure_refuses_non_float_storage_before_construction(dtype, initial, extra):
    with pytest.raises(ValidationError, match="float32"):
        VariableDeclaration.model_validate(
            variable(type=dtype, initial_value=initial, exposed_to=["agent"], normalization={"kind": "none"}, **extra)
        )


@pytest.mark.parametrize(
    "dtype,width,extra", [("vec2f", 2, {}), ("vec3f", 3, {}), ("vecNf", 1, {"dims": 1}), ("message_token", 1, {"dims": 1})]
)
def test_float_vector_exposure_preserves_actual_declared_element_axes(tmp_path, dtype, width, extra):
    import shutil

    import yaml

    from townlet.universe.compiler import UniverseCompiler
    from townlet.vfs.schema import variable_element_shape

    directory = tmp_path / "pack"
    shutil.copytree("configs/simple", directory)
    path = directory / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"] = [
        variable(
            type=dtype,
            initial_value=[0.0] * width,
            exposed_to=["agent"],
            normalization={"kind": "minmax", "min": 0, "max": 1, "clip": True},
            **extra,
        )
    ]
    path.write_text(yaml.safe_dump(payload))
    compiled = UniverseCompiler().compile(directory, primary_level="L0_simple", use_cache=False)
    descriptor = next(v for v in compiled.get_level("L0_simple").vfs_variables if v.id == "state")
    assert variable_element_shape(descriptor) == (width,)
    env = compiled.create_environment(num_agents=2, level_name="L0_simple", device="cpu")
    env.reset()
    assert env.vfs_registry.get("state", reader="engine").shape == (2, width)


@pytest.mark.parametrize("field", ["readable_by", "writable_by"])
def test_static_access_fields_are_required(field):
    payload = variable()
    payload.pop(field)
    with pytest.raises(ValidationError, match=field):
        VariableDeclaration.model_validate(payload)


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"readable_by": ["engine", "engine"]}, "duplicate readers"),
        ({"writable_by": ["engine", "engine"]}, "duplicate writers"),
        ({"readable_by": ["agent"]}, "engine read"),
        ({"readable_by": ["social_model"]}, "readable_by"),
        ({"writable_by": ["agent"]}, "writable_by"),
        ({"writable_by": ["vtc"]}, "writable_by"),
        ({"readable_by": ["engine"], "exposed_to": ["agent"], "normalization": {"kind": "none"}}, "exposure requires read"),
    ],
)
def test_static_access_invalid_policies_refuse(changes, reason):
    with pytest.raises(ValidationError, match=reason):
        VariableDeclaration.model_validate(variable(**changes))


def test_static_access_supports_hidden_immutable_literal():
    declaration = VariableDeclaration.model_validate(variable(readable_by=["engine"], writable_by=[]))
    assert declaration.readable_by == ["engine"]
    assert declaration.writable_by == []


def test_runtime_definition_supports_same_closed_policy():
    from townlet.vfs.schema import VariableDef

    declaration = VariableDef(
        id="literal", scope="global", type="scalar", lifetime="persistent", readable_by=["engine"], writable_by=[], default=3.0
    )
    assert declaration.writable_by == []
    with pytest.raises(ValidationError, match="engine read"):
        VariableDef(id="literal", scope="global", type="scalar", lifetime="persistent", readable_by=["agent"], writable_by=[], default=3.0)
