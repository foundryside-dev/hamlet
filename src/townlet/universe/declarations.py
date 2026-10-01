"""Content-addressed authoring declarations and their transport provenance."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.source_map import SourceMap, variable_location_key
from townlet.universe.stages import CompilationStage

Model = TypeVar("Model", bound=BaseModel)
PACK_FAMILIES = frozenset(
    {
        "experiment",
        "stratum",
        "environment",
        "actions",
        "brain",
        "items",
        "variables",
        "effects",
        "transition_rules",
        "action_labels",
        "presentation",
    }
)
LEVEL_FAMILIES = frozenset({"curriculum", "bars", "affordances", "drive", "training", "brain", "items_appearance"})
REQUIRED_PACK = ("experiment", "stratum", "environment", "actions", "brain", "variables")
REQUIRED_LEVEL = ("curriculum", "bars", "affordances", "drive", "training")
WRAPPED = frozenset(
    {"experiment", "stratum", "environment", "actions", "curriculum", "bars", "affordances", "drive", "training", "items", "variables"}
)
COLLECTION_FAMILIES = frozenset({"bars", "affordances", "items", "effects", "variables", "transition_rules"})
STRUCTURAL_HEADERS = frozenset(
    {"version", "evaluation_mode", "debug_logging", "max_items_in_world", "max_items_per_agent", "max_active_effects", "extents"}
)


class MarkedMapping(dict[Any, Any]):
    """A mapping carrying marks separately from its authored keys."""

    def __init__(self, line: int) -> None:
        super().__init__()
        self.line = line
        self.key_lines: dict[Any, int] = {}
        self.path: Path | None = None
        self.key_paths: dict[Any, Path] = {}


class DeclarationLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses duplicate keys before they disappear."""


def _construct_mapping(loader: DeclarationLoader, node: yaml.MappingNode) -> MarkedMapping:
    result = MarkedMapping(node.start_mark.line + 1)
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, (str, int)):
            raise ValueError(f"Declaration keys must be strings or integer identifiers (line {key_node.start_mark.line + 1})")
        if key in result:
            raise ValueError(f"Duplicate declaration key '{key}' at lines {result.key_lines[key]} and {key_node.start_mark.line + 1}")
        result.key_lines[key] = key_node.start_mark.line + 1
        result[key] = loader.construct_object(value_node, deep=True)
    return result


DeclarationLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def config_documents(experiment_dir: Path) -> tuple[Path, ...]:
    """Enumerate all YAML transports, excluding only compiler-owned cache files."""
    paths = [
        path
        for path in experiment_dir.rglob("*")
        if path.is_file() and path.suffix in {".yaml", ".yml"} and ".compiled" not in path.relative_to(experiment_dir).parts
    ]
    return tuple(
        sorted(paths, key=lambda path: (path.relative_to(experiment_dir).parts[0] == "levels", path.relative_to(experiment_dir).as_posix()))
    )


@dataclass(frozen=True)
class Declaration:
    family: str
    scope: str | None
    payload: MarkedMapping
    path: Path
    line: int

    @property
    def key(self) -> str:
        return f"levels/{self.scope}/{self.family}" if self.scope is not None else self.family

    @property
    def origin(self) -> str:
        return f"{self.path}:{self.line}"


class DeclarationStore:
    """One scoped declaration inventory, lowered into existing typed products."""

    def __init__(self, experiment_dir: Path) -> None:
        self.experiment_dir = experiment_dir
        self.declarations: dict[tuple[str | None, str], Declaration] = {}
        self.source_map = SourceMap()
        levels_dir = experiment_dir / "levels"
        if levels_dir.is_dir() and levels_dir.resolve().is_relative_to(experiment_dir):
            self.level_names = tuple(sorted(path.name for path in levels_dir.iterdir() if path.is_dir()))
        else:
            self.level_names = ()
        self.errors = CompilationErrorCollector(stage=CompilationStage.PARSE.label)

    @classmethod
    def discover(cls, experiment_dir: Path) -> DeclarationStore:
        store = cls(Path(experiment_dir).resolve())
        if store.experiment_dir.parent.name == "levels":
            store.errors.add(
                f"Cannot validate level directory directly. Validate its experiment root: {store.experiment_dir.parent.parent}",
                code=ErrorCode.SCOPING_LEVEL_DIRECTORY,
                location=f"{store.experiment_dir}:1",
            )
            store.errors.check_and_raise()
        for path in store.experiment_dir.rglob("*"):
            if ".compiled" not in path.relative_to(store.experiment_dir).parts and path.is_symlink():
                if not path.resolve().is_relative_to(store.experiment_dir):
                    store.errors.add(
                        "Declaration transport resolves outside the pack", code=ErrorCode.DECLARATION_SCOPE, location=f"{path}:1"
                    )
                elif path.is_dir():
                    store.errors.add(
                        "Directory symlinks cannot carry declarations; use ordinary transport subfolders",
                        code=ErrorCode.DECLARATION_SCOPE,
                        location=f"{path}:1",
                    )
                elif not path.exists() and path.suffix in {".yaml", ".yml"}:
                    store.errors.add("Declaration transport is a broken symlink", code=ErrorCode.DECLARATION_SCOPE, location=f"{path}:1")
        store.errors.check_and_raise()
        for path in config_documents(store.experiment_dir):
            if not path.resolve().is_relative_to(store.experiment_dir):
                store.errors.add("Declaration transport resolves outside the pack", code=ErrorCode.DECLARATION_SCOPE, location=f"{path}:1")
                continue
            relative = path.relative_to(store.experiment_dir)
            if relative.parts[0] == "levels" and len(relative.parts) >= 3:
                scope = relative.parts[1]
            else:
                scope = None
            try:
                documents = list(yaml.load_all(path.read_text(encoding="utf-8"), Loader=DeclarationLoader))
            except (yaml.YAMLError, ValueError) as exc:
                mark = getattr(exc, "problem_mark", None)
                if mark is not None:
                    line = mark.line + 1
                else:
                    line = 1
                store.errors.add(str(exc), code=ErrorCode.YAML_SYNTAX_ERROR, location=f"{path}:{line}")
                continue
            if not documents:
                documents = [None]
            for document in documents:
                store._bind_paths(document, path)
                store._consume(document, path, scope)
        store._require_families()
        store.errors.check_and_raise()
        return store

    @staticmethod
    def _bind_paths(value: Any, path: Path) -> None:
        if isinstance(value, MarkedMapping):
            value.path = path
            value.key_paths.update({key: path for key in value})
            for child in value.values():
                DeclarationStore._bind_paths(child, path)
        elif isinstance(value, list):
            for child in value:
                DeclarationStore._bind_paths(child, path)

    def _consume(self, document: Any, path: Path, scope: str | None) -> None:
        if isinstance(document, MarkedMapping):
            line = document.line
        else:
            line = 1
        if not isinstance(document, MarkedMapping) or not document:
            self.errors.add("Expected a nonempty declaration mapping", code=ErrorCode.DECLARATION_UNKNOWN, location=f"{path}:{line}")
            return
        if any(not isinstance(key, str) for key in document):
            self.errors.add("Declaration root keys must be strings", code=ErrorCode.DECLARATION_UNKNOWN, location=f"{path}:{line}")
            return
        bare = self._bare_family(document)
        if bare is not None:
            self._add(Declaration(bare, scope, document, path, line))
            return
        consumed: set[str] = set()
        for family in sorted(set(document) & WRAPPED):
            payload = document[family]
            if not isinstance(payload, MarkedMapping):
                self.errors.add(
                    f"{family} declaration must be a mapping", code=ErrorCode.LOAD_ERROR, location=f"{path}:{document.key_lines[family]}"
                )
                consumed.add(family)
                continue
            if family == "training":
                payload = self._copy_mapping(payload)
                payload["run_metadata"] = document.get("run_metadata")
                payload["recording"] = document.get("recording")
                consumed.update(set(document) & {"run_metadata", "recording"})
            self._add(Declaration(family, scope, payload, path, document.key_lines[family]))
            consumed.add(family)
        unknown = set(document) - consumed
        if unknown:
            first_key = min(unknown, key=lambda key: document.key_lines[key])
            origins = ", ".join(f"{key} at {path}:{document.key_lines[key]}" for key in sorted(unknown))
            self.errors.add(
                f"Unknown declaration fields: {sorted(unknown)}; {origins}",
                code=ErrorCode.DECLARATION_UNKNOWN,
                location=f"{path}:{document.key_lines[first_key]}",
            )

    @staticmethod
    def _bare_family(document: MarkedMapping) -> str | None:
        signatures = {
            "brain": {"architecture", "optimizer"},
            "effects": {"effect_definitions"},
            "transition_rules": {"social_residue"},
            "action_labels": {"custom"},
        }
        matches = [family for family, fields in signatures.items() if fields <= set(document)]
        if "items" in document and isinstance(document["items"], list):
            matches.append("items_appearance")
        if "meters" in document and isinstance(document["meters"], dict) and "affordances" in document:
            matches.append("presentation")
        return matches[0] if len(matches) == 1 else None

    def _add(self, declaration: Declaration) -> None:
        if declaration.scope is None:
            allowed = PACK_FAMILIES
        else:
            allowed = LEVEL_FAMILIES
        if declaration.family not in allowed:
            counterparts = [entry.origin for entry in self.declarations.values() if entry.family == declaration.family]
            if counterparts:
                related = f"; related declarations: {', '.join(counterparts)}"
            else:
                related = ""
            self.errors.add(
                f"{declaration.family} declaration is not allowed at {'pack' if declaration.scope is None else 'level'} scope{related}",
                code=ErrorCode.DECLARATION_SCOPE,
                location=declaration.origin,
            )
            return
        key = (declaration.scope, declaration.family)
        self._validate_entity_duplicates(declaration.payload, declaration)
        previous = self.declarations.get(key)
        if previous is None:
            self.declarations[key] = declaration
        elif declaration.family in COLLECTION_FAMILIES:
            payload = self._merge(previous.payload, declaration.payload, previous, declaration, ())
            self.declarations[key] = Declaration(previous.family, previous.scope, payload, previous.path, previous.line)
        else:
            self.errors.add(
                f"Duplicate {declaration.family} declaration; first declared at {previous.origin}",
                code=ErrorCode.DECLARATION_COLLISION,
                location=declaration.origin,
            )
            return
        self._record_sources(self.declarations[key])

    @staticmethod
    def _copy_mapping(mapping: MarkedMapping) -> MarkedMapping:
        result = MarkedMapping(mapping.line)
        result.update(mapping)
        result.key_lines.update(mapping.key_lines)
        result.path = mapping.path
        result.key_paths.update(mapping.key_paths)
        return result

    def _merge(
        self, left: MarkedMapping, right: MarkedMapping, previous: Declaration, incoming: Declaration, field_path: tuple[str, ...]
    ) -> MarkedMapping:
        merged = self._copy_mapping(left)
        for key, value in right.items():
            if key not in merged:
                merged[key] = value
                key_path, key_line = self._key_origin(right, key, incoming)
                merged.key_lines[key] = key_line
                merged.key_paths[key] = key_path
                continue
            current = merged[key]
            if not field_path and key in STRUCTURAL_HEADERS:
                if current != value:
                    self._field_collision(key, field_path, left, right, previous, incoming)
            elif isinstance(current, MarkedMapping) and isinstance(value, MarkedMapping):
                merged[key] = self._merge(current, value, previous, incoming, (*field_path, key))
            elif incoming.family == "variables" and key == "item_profiles" and isinstance(current, list) and isinstance(value, list):
                if all(isinstance(profile, str) for profile in [*current, *value]) and set(current) & set(value):
                    self._field_collision(key, field_path, left, right, previous, incoming)
                merged[key] = [*current, *value]
            elif isinstance(current, list) and isinstance(value, list) and self._is_named_collection(key, current, value):
                seen = {self._entry_key(entry): entry for entry in current}
                for entry in value:
                    identity = self._entry_key(entry)
                    if identity in seen:
                        prior = self._node_origin(seen[identity], previous)
                        self.errors.add(
                            f"Duplicate {incoming.family} identifier '{self._entry_id(entry)}'; first declared at {prior}",
                            code=ErrorCode.DECLARATION_COLLISION,
                            location=self._node_origin(entry, incoming),
                        )
                    seen[identity] = entry
                merged[key] = [*current, *value]
            else:
                self._field_collision(key, field_path, left, right, previous, incoming)
        return merged

    def _field_collision(
        self, key: str, field_path: tuple[str, ...], left: MarkedMapping, right: MarkedMapping, previous: Declaration, incoming: Declaration
    ) -> None:
        prior_path, prior_line = self._key_origin(left, key, previous)
        incoming_path, incoming_line = self._key_origin(right, key, incoming)
        prior = f"{prior_path}:{prior_line}"
        self.errors.add(
            f"Duplicate/conflicting {incoming.family} field '{'.'.join((*field_path, str(key)))}'; first declared at {prior}",
            code=ErrorCode.DECLARATION_COLLISION,
            location=f"{incoming_path}:{incoming_line}",
        )

    @staticmethod
    def _key_origin(mapping: MarkedMapping, key: Any, declaration: Declaration) -> tuple[Path, int]:
        if key in mapping.key_paths:
            path = mapping.key_paths[key]
        elif mapping.path is not None:
            path = mapping.path
        else:
            path = declaration.path
        if key in mapping.key_lines:
            line = mapping.key_lines[key]
        else:
            line = mapping.line
        return path, line

    @staticmethod
    def _node_origin(value: Any, declaration: Declaration) -> str:
        if isinstance(value, MarkedMapping):
            if value.path is not None:
                return f"{value.path}:{value.line}"
            return f"{declaration.path}:{value.line}"
        return declaration.origin

    def _validate_entity_duplicates(self, value: Any, declaration: Declaration) -> None:
        if isinstance(value, MarkedMapping):
            for key, child in value.items():
                if declaration.family == "variables" and key == "item_profiles" and isinstance(child, list):
                    for profile in child:
                        if not isinstance(profile, str):
                            self.errors.add(
                                "variables.item_profiles must contain string identifiers",
                                code=ErrorCode.LOAD_ERROR,
                                location=self._node_origin(profile, declaration),
                            )
                if isinstance(child, list) and self._is_named_collection(key, child, []):
                    seen: dict[tuple[str | None, str] | None, Any] = {}
                    for entry in child:
                        identity = self._entry_key(entry)
                        if identity in seen:
                            prior = self._node_origin(seen[identity], declaration)
                            self.errors.add(
                                f"Duplicate {declaration.family} identifier '{self._entry_id(entry)}'; first declared at {prior}",
                                code=ErrorCode.DECLARATION_COLLISION,
                                location=self._node_origin(entry, declaration),
                            )
                        seen[identity] = entry
                self._validate_entity_duplicates(child, declaration)
        elif isinstance(value, list):
            for child in value:
                self._validate_entity_duplicates(child, declaration)

    @classmethod
    def _entry_key(cls, entry: Any) -> tuple[str | None, str] | None:
        """Compare canonical identity components without flattening item profiles."""
        identity = cls._entry_id(entry)
        if identity is None:
            return None
        if entry.get("scope") == "item" and isinstance(entry.get("profile"), str) and isinstance(entry.get("id"), str):
            return entry["profile"], entry["id"]
        return None, identity

    @staticmethod
    def _entry_id(entry: Any) -> str | None:
        if not isinstance(entry, dict):
            return None
        if isinstance(entry.get("source"), str) and isinstance(entry.get("target"), str):
            return f"{entry['source']}->{entry['target']}"
        if entry.get("scope") == "item" and isinstance(entry.get("profile"), str) and isinstance(entry.get("id"), str):
            return f"{entry['profile']}:{entry['id']}"
        for field in ("id", "name", "profile_name"):
            identity = entry.get(field)
            if isinstance(identity, str) and identity:
                return identity
        return None

    @classmethod
    def _is_named_collection(cls, key: str, left: list[Any], right: list[Any]) -> bool:
        return key in {
            "meters",
            "affordances",
            "cascades",
            "item_types",
            "effect_definitions",
            "declarations",
            "variables",
            "item_profiles",
            "social_residue",
        } and all(cls._entry_id(entry) is not None for entry in [*left, *right])

    def _record_sources(self, declaration: Declaration) -> None:
        self.source_map.record(declaration.key, declaration.path, declaration.line)

        def walk(value: Any, segments: tuple[str, ...], namespace: str) -> None:
            if isinstance(value, MarkedMapping):
                if value.path is not None:
                    path = value.path
                else:
                    path = declaration.path
                if segments:
                    self.source_map.record(f"{declaration.key}:{'.'.join(segments)}", path, value.line)
                identity = self._entry_id(value)
                if identity is not None:
                    if declaration.family == "variables" and isinstance(value.get("id"), str):
                        if value.get("scope") == "item":
                            profile = value.get("profile")
                        else:
                            profile = None
                        location_key = variable_location_key(profile, value["id"])
                    elif namespace:
                        qualified = f"{namespace}:{identity}"
                        location_key = f"{declaration.key}:{qualified}"
                    else:
                        location_key = f"{declaration.key}:{identity}"
                    self.source_map.record(location_key, path, value.line)
                for key, child in value.items():
                    child_segments = (*segments, str(key))
                    key_path, key_line = self._key_origin(value, key, declaration)
                    self.source_map.record(f"{declaration.key}:{'.'.join(child_segments)}", key_path, key_line)
                    walk(child, child_segments, namespace)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if segments:
                        indexed = (*segments[:-1], f"{segments[-1]}[{index}]")
                    else:
                        indexed = (f"[{index}]",)
                    walk(child, indexed, namespace)

        walk(declaration.payload, (), "")

    def _require_families(self) -> None:
        if not self.level_names:
            self.errors.add(
                "No curriculum level declarations found", code=ErrorCode.NO_CURRICULUM_LEVELS, location=f"{self.experiment_dir}:1"
            )
        for scope, families in [(None, REQUIRED_PACK), *((level, REQUIRED_LEVEL) for level in self.level_names)]:
            for family in families:
                if (scope, family) not in self.declarations:
                    if scope is None:
                        directory = self.experiment_dir
                    else:
                        directory = self.experiment_dir / "levels" / scope
                    self.errors.add(f"Missing required {family} declaration", code=ErrorCode.DECLARATION_MISSING, location=f"{directory}:1")

    def get(self, family: str, scope: str | None) -> Declaration | None:
        return self.declarations.get((scope, family))

    def parse(self, family: str, scope: str | None, model: type[Model], wrapped: bool) -> Model | None:
        declaration = self.declarations.get((scope, family))
        if declaration is None:
            return None
        payload: dict[str, Any] = declaration.payload
        if wrapped:
            payload = {family: payload}
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            for issue in exc.errors(include_url=False):
                segments = list(issue["loc"])
                if wrapped and segments and segments[0] == family:
                    segments.pop(0)
                key = ""
                for segment in segments:
                    key += f"[{segment}]" if isinstance(segment, int) else f"{'.' if key else ''}{segment}"
                if key:
                    display_key = key
                else:
                    display_key = family
                self.errors.add(
                    f"Invalid {family} declaration ({display_key}): {issue['msg']}",
                    code=ErrorCode.LOAD_ERROR if scope is None else ErrorCode.LEVEL_LOAD_ERROR,
                    location=self.source_map.lookup(f"{declaration.key}:{key}") or declaration.origin,
                )
            return None

    def resolve_clock_references(self) -> None:
        profiles = self.declarations.get((None, "variables"))
        if profiles is None:
            return
        from townlet.config.variables_config import VariableDeclaration, VariablesConfig
        from townlet.vfs.schema import VariableScope

        profile_config = self.parse("variables", None, VariablesConfig, False)
        if profile_config is None:
            self.errors.check_and_raise()
            return
        clocks: dict[str, VariableDeclaration] = {}
        global_variables: dict[str, VariableDeclaration] = {}
        authored_periods: dict[str, Any] = {}
        for variable, raw_variable in zip(profile_config.declarations, profiles.payload["declarations"], strict=True):
            if variable.scope != VariableScope.GLOBAL:
                continue
            identifier = variable.id
            global_variables[identifier] = variable
            if variable.expression is None or variable.normalization is None:
                continue
            if (
                variable.semantic_type == "temporal"
                and variable.expression.strip() == "tick"
                and variable.normalization.kind == "cyclical_sin_cos"
            ):
                clocks[identifier] = variable
                authored_periods[identifier] = raw_variable["normalization"]["period"]
        for level in self.level_names:
            declaration = self.declarations.get((level, "curriculum"))
            if declaration is None:
                continue
            day_length = declaration.payload.get("day_length")
            origin = self.source_map.lookup(f"{declaration.key}:day_length")
            if origin is None:
                origin = declaration.origin
            if isinstance(day_length, dict):
                clock_reference = day_length.get("period_of")
                if isinstance(clock_reference, str):
                    clock_variable = clocks.get(clock_reference)
                else:
                    clock_variable = None
                if set(day_length) != {"period_of"} or clock_variable is None:
                    message = "day_length.period_of must identify a declared global temporal ambient-tick cyclical variable"
                    if isinstance(clock_reference, str) and clock_reference in global_variables:
                        target = self.source_map.lookup(variable_location_key(None, clock_reference))
                        if target is not None:
                            message += f"; target declared at {target}"
                    self.errors.add(
                        message,
                        code=ErrorCode.CLOCK_REFERENCE,
                        location=origin,
                    )
                    continue
                assert clock_variable.normalization is not None
                assert isinstance(clock_reference, str)
                period = authored_periods[clock_reference]
                if (
                    clock_variable.type != "scalar"
                    or not isinstance(period, (int, float))
                    or isinstance(period, bool)
                    or not math.isfinite(period)
                    or period <= 0
                    or int(period) != period
                ):
                    target = self.source_map.lookup(variable_location_key(None, clock_reference))
                    if target is None:
                        target = profiles.origin
                    self.errors.add(
                        f"Clock period must be a finite positive integer; target declared at {target}",
                        code=ErrorCode.CLOCK_REFERENCE,
                        location=origin,
                    )
                    continue
                declaration.payload["day_length"] = int(period)
            elif day_length is not None and clocks:
                targets = [self.source_map.lookup(variable_location_key(None, identity)) or profiles.origin for identity in clocks]
                self.errors.add(
                    f"Duplicated clock period: use day_length.period_of to link its authority; clock declaration(s): {', '.join(targets)}",
                    code=ErrorCode.CLOCK_REFERENCE,
                    location=origin,
                )
        self.errors.check_and_raise()
