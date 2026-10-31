"""Build a command-pipeline compiler from a canonical spelling schema, for unit tests.

Production builds its namespace with ``Namespace.of_registry`` from the compiled roster;
a unit test states the few names it needs as ``{spelling: type}`` in canonical spelling
(``x`` a registry variable, ``bar.m`` a meter, ``item.x`` state of the one test item profile). ``scopes`` names
the declared scope of a bare variable (agent when omitted).
"""

from __future__ import annotations

from collections.abc import Mapping

from townlet.effects.compiler import CommandCompiler
from townlet.vfs.namespace import ANY_ITEM, EFFECT_LOCALS, EFFECT_PIPELINE, INTERACTION_PIPELINE, CommandSymbols, Namespace, ReadContext
from townlet.vfs.schema import VariableScope
from townlet.world.expression.references import ReferenceKind, parse_reference

TEST_PROFILE = "test"
"""The one item profile a test schema's ``item.<x>`` keys declare."""


def namespace_from_schema(schema: Mapping[str, str], scopes: Mapping[str, str] | None = None) -> Namespace:
    variables: list[tuple[str, VariableScope | str, str]] = []
    meters: list[str] = []
    items: dict[str, str] = {}
    for spelling, value_type in schema.items():
        reference = parse_reference(spelling)
        if reference is None:
            raise ValueError(f"test schema key '{spelling}' is not a canonical spelling")
        declared = "scalar" if value_type == "float" else value_type
        if reference.kind == ReferenceKind.METER:
            meters.append(reference.name)
        elif reference.kind == ReferenceKind.ITEM:
            items[reference.name] = declared
        elif reference.name not in EFFECT_LOCALS:
            variables.append((reference.name, (scopes or {}).get(reference.name, "agent"), declared))
    return Namespace(variables=variables, meters=meters, item_profiles={TEST_PROFILE: items})


def command_symbols(schema: Mapping[str, str], scopes: Mapping[str, str] | None = None) -> CommandSymbols:
    return CommandSymbols(namespace=namespace_from_schema(schema, scopes), expressions={}, time_enabled=True)


def command_compiler(
    schema: Mapping[str, str],
    *,
    item: bool = False,
    effect: bool = True,
    time_enabled: bool = True,
    scopes: Mapping[str, str] | None = None,
) -> CommandCompiler:
    context: ReadContext = (EFFECT_PIPELINE if effect else INTERACTION_PIPELINE).with_item(ANY_ITEM if item else None)
    return CommandCompiler(namespace_from_schema(schema, scopes), context=context, time_enabled=time_enabled, expressions={})
