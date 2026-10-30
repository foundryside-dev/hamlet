"""CLI entry point for the Universe compiler (python -m townlet.universe)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from collections.abc import Iterable, Mapping
from pathlib import Path

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import SlotBinding
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage

INSPECT_STAGE = "Inspect"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m townlet.universe",
        description="Utility commands for the UniverseCompiler (UAC CLI).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile a config pack and optionally cache the artifact.")
    compile_parser.add_argument("config_dir", help="Path to config pack (nested YAML declarations, with levels/<id> scope)")
    compile_parser.add_argument("--primary-level", required=True, help="Curriculum level to compile as the primary level.")
    compile_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache reads/writes (always rebuild).",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a compiled universe artifact (MessagePack file).",
    )
    inspect_parser.add_argument(
        "artifact", help="Path to a .compiled/universe-<level>.msgpack artifact, or a config directory (then --primary-level is required)"
    )
    inspect_parser.add_argument(
        "--primary-level",
        default=None,
        help="Level to inspect. Required when ARTIFACT is a config directory, because one artifact exists per level.",
    )
    inspect_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for inspection (default: table)",
    )

    validate_parser = subparsers.add_parser("validate", help="Run compilation without touching the cache (lint-style check).")
    validate_parser.add_argument("config_dir", help="Path to config directory to validate")
    validate_parser.add_argument("--primary-level", required=True, help="Curriculum level to validate as the primary level.")

    return parser


def _format_metadata_lines(metadata) -> list[str]:
    rows: list[tuple[str, str]] = [
        ("Universe", metadata.universe_name),
        ("Substrate", metadata.substrate_type),
        ("Meters", f"{metadata.meter_count}"),
        ("Affordances", f"{metadata.affordance_count}"),
        ("Actions", f"{metadata.action_count}"),
        ("Observation Dim", f"{metadata.observation_dim}"),
        ("Grid Cells", metadata.grid_cells if metadata.grid_cells is not None else "N/A"),
        ("Config Hash", metadata.config_hash[:16] if metadata.config_hash else ""),
        ("Compiled At", metadata.compiled_at),
    ]
    width = max(len(label) for label, _ in rows)
    return [f"  {label.ljust(width)} : {value}" for label, value in rows]


def _print_summary(metadata) -> None:
    print("Summary:")
    for line in _format_metadata_lines(metadata):
        print(line)


def _cmd_compile(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir).resolve()
    compiler = UniverseCompiler()
    start = time.perf_counter()
    compiled = compiler.compile(config_dir, primary_level=args.primary_level, use_cache=not args.no_cache)
    level = compiled.get_level(compiled.metadata.primary_level)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    _print_summary(compiled.metadata)
    print(f"  VFS Hash : {level.vfs_hash[:16]}")
    print(f"  Action Schema Hash : {level.action_schema_hash[:16]}")
    print(f"  Observation Schema Hash : {level.observation_schema_hash[:16]}")
    print(f"  Variable Schema Hash : {level.variable_schema_hash[:16]}")
    print(f"  Transition Graph Hash : {_format_transition_hash(level.transition_graph_hash)}")
    print(f"Compilation succeeded in {elapsed_ms:.1f} ms")

    if not args.no_cache:
        # compile() either reused a fingerprint-validated artifact or wrote a fresh
        # one; a failed write raises CompilationError, so this path always exists here.
        cache_path = config_dir / ".compiled" / f"universe-{args.primary_level}.msgpack"
        print(f"Cache artifact: {cache_path}")

    return 0


def _convert_for_json(value):
    if isinstance(value, Mapping):
        return {k: _convert_for_json(v) for k, v in dict(value).items()}
    if isinstance(value, list | tuple):
        return [_convert_for_json(v) for v in value]
    return value


def _metadata_to_dict(metadata) -> dict:
    payload = {}
    for field in dataclasses.fields(metadata):
        payload[field.name] = _convert_for_json(getattr(metadata, field.name))
    return payload


def _format_transition_hash(transition_graph_hash: str) -> str:
    if transition_graph_hash == "":
        return "<empty>"
    return transition_graph_hash[:16]


def _print_token_census(compiled: CompiledUniverse) -> None:
    """The per-type token census (token-obs spec §2: published in the artifact and here)."""
    level = compiled.get_level(compiled.metadata.primary_level)
    spec = level.token_spec
    compact_layout = spec.compact_layout()
    print("Token census:")
    for token_type in spec.types:
        type_layout = compact_layout.get_type(token_type.type_name)
        assert type_layout is not None
        print(
            f"  {token_type.type_name:<17}: {token_type.capacity:>4} slots x compact row "
            f"{type_layout.compact_row_width} (fixed network boundary {type_layout.fixed_row_width})"
        )
    print(f"  {'compact total':<17}: {spec.total_dims}")
    print(f"  {'fixed boundary':<17}: {spec.fixed_total_dims}")
    if level.token_type_schema_hash:
        print(f"  Token Type Schema Hash : {level.token_type_schema_hash[:16]}")
    if level.layout_hash:
        print(f"  Layout Hash : {level.layout_hash[:16]}")
    for advisory in level.token_advisories:
        print(f"  ADVISORY: {advisory}")


def _refusal(stage: str, code: ErrorCode, location: Path | str, message: str) -> CompilationError:
    """A CLI refusal in the compiler's own ``[CODE] file:line - message`` shape."""
    return CompilationError(stage, [CompilationMessage(code=code, message=message, location=f"{location}:1")])


def _token_layout_payload(compiled: CompiledUniverse) -> dict:
    """Where every token row lands in the flat view, and what fills it.

    ``token_rows`` joins ``row_layout()`` (compact transport offsets) and
    ``fixed_row_layout()`` (network-boundary offsets) with each slot's binding, so
    "where did my variable land" is answerable without Python.
    """
    spec = compiled.get_level(compiled.metadata.primary_level).token_spec
    compact_layout = spec.compact_layout()
    token_types = []
    bindings: list[SlotBinding] = []
    for token_type in spec.types:
        type_layout = compact_layout.get_type(token_type.type_name)
        assert type_layout is not None
        token_types.append(
            {
                "type_name": token_type.type_name,
                "capacity": token_type.capacity,
                "payload_features": list(token_type.payload_features),
                "compact_row_width": type_layout.compact_row_width,
                "fixed_row_width": token_type.fixed_row_width,
            }
        )
        bindings.extend(token_type.slot_bindings)
    compact_rows = spec.row_layout()
    fixed_rows = spec.fixed_row_layout()
    assert len(compact_rows) == len(fixed_rows) == len(bindings)
    token_rows = []
    for (type_name, slot_index, start, end), (_, _, fixed_start, fixed_end), binding in zip(
        compact_rows, fixed_rows, bindings, strict=True
    ):
        assert binding.slot_index == slot_index
        token_rows.append(
            {
                "type_name": type_name,
                "slot_index": slot_index,
                "filler_kind": binding.filler_kind,
                "filler_ref": binding.filler_ref,
                "scope": None if binding.scope is None else str(binding.scope),
                "start": start,
                "end": end,
                "fixed_start": fixed_start,
                "fixed_end": fixed_end,
            }
        )
    return {"token_types": token_types, "token_rows": token_rows}


def _freshness(compiled: CompiledUniverse, source_pack: Path | None, requested_level: str | None) -> dict:
    """Check the artifact against its source pack with the compile cache's own rule."""
    if source_pack is None:
        return {"status": "unknown", "source_pack": None, "reasons": ["artifact records no source pack"]}
    if not source_pack.is_dir():
        return {"status": "unknown", "source_pack": str(source_pack), "reasons": [f"source pack {source_pack} not found"]}
    reasons = UniverseCompiler().cache_staleness(compiled, source_pack)
    if requested_level is not None and compiled.metadata.primary_level != requested_level:
        reasons.append(f"artifact is for level '{compiled.metadata.primary_level}', not '{requested_level}'")
    return {"status": "stale" if reasons else "fresh", "source_pack": str(source_pack), "reasons": reasons}


def _cmd_inspect(args: argparse.Namespace) -> int:
    artifact_path = Path(args.artifact).resolve()
    source_pack: Path | None = None

    # A config directory resolves to its per-level artifact.
    if artifact_path.is_dir():
        if not args.primary_level:
            raise _refusal(
                INSPECT_STAGE,
                ErrorCode.CLI_PRIMARY_LEVEL_REQUIRED,
                artifact_path,
                "This is a config directory and holds one artifact per level; pass --primary-level to say which one to inspect.",
            )
        source_pack = artifact_path
        artifact_path = artifact_path / ".compiled" / f"universe-{args.primary_level}.msgpack"

    if not artifact_path.is_file():
        raise _refusal(
            INSPECT_STAGE,
            ErrorCode.ARTIFACT_NOT_FOUND,
            artifact_path,
            "Compiled artifact not found; run `python -m townlet.universe compile` first.",
        )

    try:
        compiled = CompiledUniverse.load_from_cache(artifact_path)
        recorded_pack = None if compiled.experiment_dir is None else Path(compiled.experiment_dir)
    except Exception as exc:
        # The same breadth as the compile cache read (_read_cache_artifact): any malformed
        # artifact — wrong schema, wrong types, not msgpack at all — is a coded refusal.
        raise _refusal(INSPECT_STAGE, ErrorCode.ARTIFACT_LOAD_REFUSED, artifact_path, f"{type(exc).__name__}: {exc}") from exc

    # Given a pack directory, freshness is checked against it; given an artifact file,
    # against the pack the artifact records (a copied pack's artifact still names its source).
    source_origin = "argument" if source_pack is not None else "recorded in artifact"
    if source_pack is None:
        source_pack = recorded_pack
    freshness = _freshness(compiled, source_pack, args.primary_level)
    freshness["source_pack_origin"] = source_origin
    checked = f"checked against {freshness['source_pack']} ({source_origin})"
    if freshness["status"] != "fresh":
        print(
            f"WARNING: artifact freshness is {freshness['status'].upper()}, {checked}: " + "; ".join(freshness["reasons"]),
            file=sys.stderr,
        )

    level = compiled.get_level(compiled.metadata.primary_level)
    if args.format == "json":
        payload = {
            "artifact": str(artifact_path),
            "freshness": freshness,
            "metadata": _metadata_to_dict(compiled.metadata),
            "vfs_hash": level.vfs_hash,
            "action_schema_hash": level.action_schema_hash,
            "observation_schema_hash": level.observation_schema_hash,
            "variable_schema_hash": level.variable_schema_hash,
            "transition_graph_hash": level.transition_graph_hash,
            "token_census": level.token_spec.census,
            "token_compact_total_dims": level.token_spec.total_dims,
            "token_fixed_boundary_total_dims": level.token_spec.fixed_total_dims,
            "token_type_schema_hash": level.token_type_schema_hash,
            "layout_hash": level.layout_hash,
            "token_advisories": list(level.token_advisories),
            **_token_layout_payload(compiled),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_summary(compiled.metadata)
        print(f"  VFS Hash : {level.vfs_hash[:16]}")
        print(f"  Action Schema Hash : {level.action_schema_hash[:16]}")
        print(f"  Observation Schema Hash : {level.observation_schema_hash[:16]}")
        print(f"  Variable Schema Hash : {level.variable_schema_hash[:16]}")
        print(f"  Transition Graph Hash : {_format_transition_hash(level.transition_graph_hash)}")
        _print_token_census(compiled)
        freshness_line = f"{freshness['status'].upper()}, {checked}"
        if freshness["reasons"]:
            freshness_line += " - " + "; ".join(freshness["reasons"])
        print(f"Freshness: {freshness_line}")
        print(f"Artifact path: {artifact_path}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir).resolve()
    compiler = UniverseCompiler()
    start = time.perf_counter()
    compiler.compile(config_dir, primary_level=args.primary_level, use_cache=False)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    print(f"Validation succeeded in {elapsed_ms:.1f} ms (no cache artifacts written)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    """Run one CLI command. Every refusal returns 1 with a diagnostic; none ends in a traceback."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    commands = {"compile": _cmd_compile, "inspect": _cmd_inspect, "validate": _cmd_validate}
    prefix = "" if args.command == "inspect" else "Compilation failed: "
    target = args.artifact if args.command == "inspect" else args.config_dir

    try:
        return commands[args.command](args)
    except CompilationError as exc:
        print(f"{prefix}{exc}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        # Last resort: a refusal raised below the CLI that does not yet carry its own
        # code still reaches the user in the compiler's diagnostic shape.
        refusal = _refusal(
            INSPECT_STAGE if args.command == "inspect" else "Compiler",
            ErrorCode.UNCLASSIFIED_REFUSAL,
            Path(target).resolve(),
            f"{type(exc).__name__}: {exc}",
        )
        print(f"{prefix}{refusal}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
