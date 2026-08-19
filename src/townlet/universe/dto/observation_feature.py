"""The ONE closed vocabulary of compiled observation FEATURES (PDR-0045, WS-4 unit 4).

A compiled `ObservationField` carries exactly one of these, and it answers a different
question from `semantic_type`. The semantic type says which GROUP of the observation vector a
field belongs to (its slice, its layout order). The feature says WHO FILLS the field's source
variable each tick — the registry, or one of the engine's own encoders — and it is what the
runtime dispatches on. Before it existed the runtime answered that question by comparing
field NAMES to string literals (`if field.name == "obs_local_window"`, nine sync steps in
the observation encoder, the recurrent network's slice lookup, two demo sites sizing the
vision window, and a meter step that PARSED the meter's name back out of the field's name).
A name is a label the compiler chose; branching on it is the shape PDR-0045 forbids and the
shape unit 3 (PDR-0075) removed for `obs_vfs`. This module is the general fix that PDR named.

Members, and what fills them:

- `variable`               — an authored variable the registry owns (an `environment.yaml`
                             variable, or an exposed global/agent VFS profile variable). The
                             runtime never publishes into it; it READS it by declared scope.
- `grid_encoding`          — the substrate's global grid encoding. Engine-published.
- `local_window`           — the substrate's partial-vision window. Engine-published.
- `position`               — the substrate's position features. Engine-published.
- `velocity`               — the substrate's velocity features. Engine-published.
- `meter`                  — one meter's current value; `feature_ref` names the meter, so
                             nothing has to parse it out of the field's name. Engine-published.
- `affordance_at_position` — the one-hot affordance-under-agent block. Engine-published.
- `effects`                — the observable-effects block. Engine-published.
- `temporal`               — the day/night temporal-features block. Engine-published.
- `item_slots`             — the exposed item-profile variables of the item in each of the
                             agent's slots (PDR-0075). Engine-published.

Where this lives, on purpose: on the compiled DTO the runtime iterates, NOT on the VFS
observation-field mirror that feeds `observation_schema_hash`. The mirror is the field's
ABI — id, source variable, shape, normalization, semantic group, curriculum activity — and
none of that changes when the runtime learns which encoder fills the source. So the
discriminator moves no provenance hash and no stream, and the oracle harness is expected to
read the cut as invisible; that expectation is MEASURED at the cut (PDR-0056), not assumed.
"""

from __future__ import annotations

from typing import Final, Literal, get_args

ObservationFeature = Literal[
    "variable",
    "grid_encoding",
    "local_window",
    "position",
    "velocity",
    "meter",
    "affordance_at_position",
    "effects",
    "temporal",
    "item_slots",
]

OBSERVATION_FEATURES: Final[frozenset[str]] = frozenset(get_args(ObservationFeature))

# The one member the registry fills. Every other member is published by the engine each tick
# into an engine-written primitive variable the compiler mints for it (`build_vfs_variables`).
VARIABLE_FEATURE: Final[str] = "variable"

# The one member that names a referent: a `meter` field's `feature_ref` is the meter's name.
METER_FEATURE: Final[str] = "meter"


def require_observation_feature(value: object, *, where: str) -> str:
    """Return `value` if it is a vocabulary member; raise with the rule otherwise."""
    if not isinstance(value, str) or value not in OBSERVATION_FEATURES:
        raise ValueError(
            f"{where}: feature {value!r} is not in the closed vocabulary "
            f"{sorted(OBSERVATION_FEATURES)}. The set is defined once, in "
            "townlet.universe.dto.observation_feature; the runtime dispatches on it, so a new "
            "engine-published block is a new member here AND a new sync step, never a name to match."
        )
    return value


__all__ = [
    "METER_FEATURE",
    "OBSERVATION_FEATURES",
    "VARIABLE_FEATURE",
    "ObservationFeature",
    "require_observation_feature",
]
