"""Resolve a launch directory once through the compiler's declaration authority."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from townlet.config.effective_run import EffectiveRunConfig
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.stages import CompilationStage


@dataclass(frozen=True)
class ResolvedLaunch:
    """A selected compiled level, its existing effective view and declaration origins."""

    root: Path
    level_name: str
    compiled: CompiledUniverse
    effective: EffectiveRunConfig
    declaration_origins: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "declaration_origins", MappingProxyType(dict(self.declaration_origins)))


def _located_error(code: ErrorCode, message: str, path: Path) -> CompilationError:
    return CompilationError(
        CompilationStage.PREFLIGHT.label,
        [CompilationMessage(code=code, message=message, location=f"{path}:1")],
    )


def resolve_launch(path: Path, *, level_name: str | None) -> ResolvedLaunch:
    """Resolve a pack or its direct ``levels/<name>`` directory without filename inference.

    A direct-level input selects that level. A pack input requires an explicit
    selection unless it declares exactly one level. Discovery and compilation
    retain authority over declarations, sidecars, complete brains and overrides.
    """
    entry = Path(path).resolve()
    if not entry.is_dir():
        raise _located_error(ErrorCode.CONFIG_PATH_INVALID, f"Launch input must be a pack or direct-level directory: {entry}", entry)

    direct_level: str | None
    if entry.parent.name == "levels":
        direct_level = entry.name
        root = entry.parent.parent
    else:
        direct_level = None
        root = entry
    declarations = DeclarationStore.discover(root)
    available = declarations.level_names
    levels_path = root / "levels"

    if level_name is not None and level_name not in available:
        raise _located_error(
            ErrorCode.PRIMARY_LEVEL_UNKNOWN,
            f"Primary level '{level_name}' not found. Available: {list(available)}",
            levels_path,
        )
    if direct_level is not None:
        if direct_level not in available:
            raise _located_error(
                ErrorCode.PRIMARY_LEVEL_UNKNOWN,
                f"Direct-level input '{direct_level}' is not declared. Available: {list(available)}",
                entry,
            )
        if level_name is not None and level_name != direct_level:
            raise _located_error(
                ErrorCode.DECLARATION_SCOPE,
                f"Direct-level input selects '{direct_level}', conflicting with explicit level '{level_name}'.",
                entry,
            )
        selected = direct_level
    elif level_name is not None:
        selected = level_name
    elif len(available) == 1:
        selected = available[0]
    elif not available:
        raise _located_error(ErrorCode.DECLARATION_MISSING, "Launch pack declares no curriculum levels.", levels_path)
    else:
        raise _located_error(
            ErrorCode.DECLARATION_SCOPE,
            f"Launch pack declares multiple levels; level_name is required. Available: {list(available)}",
            levels_path,
        )

    compiled = UniverseCompiler().compile(root, primary_level=selected, use_cache=True)
    return ResolvedLaunch(
        root=root,
        level_name=selected,
        compiled=compiled,
        effective=compiled.effective_run,
        declaration_origins={declaration.key: declaration.origin for declaration in declarations.declarations.values()},
    )
