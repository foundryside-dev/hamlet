"""The finite static access contract shared by authoring and runtime products."""

from collections.abc import Sequence


def validate_static_access(
    variable_id: str,
    readable_by: Sequence[str],
    writable_by: Sequence[str],
    exposed_to: Sequence[str],
) -> None:
    """Refuse invalid roles and contradictions, including mutated source DTOs."""
    for field_name, roles in (("readable_by", readable_by), ("writable_by", writable_by), ("exposed_to", exposed_to)):
        if not isinstance(roles, Sequence) or isinstance(roles, str | bytes):
            raise ValueError(f"Variable '{variable_id}' {field_name} requires an explicit role sequence")
    if any(role not in ("engine", "agent") for role in readable_by):
        raise ValueError(f"Variable '{variable_id}' readable_by admits engine and agent only")
    if any(role != "engine" for role in writable_by):
        raise ValueError(f"Variable '{variable_id}' writable_by admits engine or an empty policy only")
    if any(role != "agent" for role in exposed_to):
        raise ValueError(f"Variable '{variable_id}' exposed_to admits agent only")
    if len(set(readable_by)) != len(readable_by):
        raise ValueError(f"Variable '{variable_id}' has duplicate readers")
    if len(set(writable_by)) != len(writable_by):
        raise ValueError(f"Variable '{variable_id}' has duplicate writers")
    if len(set(exposed_to)) != len(exposed_to):
        raise ValueError(f"Variable '{variable_id}' has duplicate exposure roles")
    if "engine" not in readable_by:
        raise ValueError(f"Variable '{variable_id}' requires engine read access")
    if not set(exposed_to).issubset(readable_by):
        raise ValueError(f"Variable '{variable_id}' exposure requires read access")
