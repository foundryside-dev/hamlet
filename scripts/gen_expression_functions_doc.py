#!/usr/bin/env python3
"""Render the expression-function reference in ``docs/config-schemas/expressions.md`` from the registry.

The table between the ``BEGIN GENERATED`` / ``END GENERATED`` markers is the
``FUNCTION_SPECS`` registry (``src/townlet/world/expression/functions.py``) rendered one
row per function, grouped by family. The registry is the only authority on which
functions exist and what they return; this script keeps the document from drifting
away from it.

    uv run python scripts/gen_expression_functions_doc.py          # rewrite the block
    uv run python scripts/gen_expression_functions_doc.py --check  # exit 1 when it is stale

``tests/test_townlet/unit/world/expression/test_expression_functions_doc.py`` runs the
check so a registry change without a regenerated document fails CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from townlet.world.expression.functions import FAMILY_ORDER, FUNCTION_SPECS, FunctionSpec

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "config-schemas" / "expressions.md"
BEGIN_MARKER = "<!-- BEGIN GENERATED: expression-functions (scripts/gen_expression_functions_doc.py) -->"
END_MARKER = "<!-- END GENERATED: expression-functions -->"

FAMILY_NOTES: dict[str, str] = {
    "Math": "Element-wise over numeric scalars.",
    "Statistics": "Reduced across the *arguments*, never across agents: `mean(bar.energy, bar.health)` is each agent's own mean.",
    "Logic and masks": "Boolean combination and masked selection; `gather`/`scatter` index rows of a per-agent value.",
    "Sampling": (
        "`uniform` and `normal_dist` draw once per row of the context they run in, each row from its own world's stream "
        "(S1): per world in a global expression or on a global rule target, per agent in an agent expression, an action "
        "write or on an agent target (the arguments are numbers). A literal-only call still draws once per row, "
        "never once for the batch. They run wherever the runtime carries a world stream: global and agent variable "
        "expressions, action writes, transition rules, effect and interaction pipelines; an item spawn predicate "
        "carries none and refuses. A random expression variable is stored, never inlined into a write (the write "
        "reads the draw the observation showed); see [variables.md](variables.md#random-draws). Noise fields are "
        "deterministic in their inputs."
    ),
    "Temporal": (
        "History operators (`lag`, `delta`, `moving_average`, `ema`, `rate_of_change`, `rising_edge`, `falling_edge`) "
        "run only in global and agent variable expressions. Their first argument names a variable, `tick` or "
        "`bar.<meter>`; window, depth and alpha are literals. Each reads the history of committed values, one per "
        "tick, which is episode-scoped and seeded with the value the argument held when the episode began. See "
        "[variables.md](variables.md#history-operators). `time_in_window` measures a 24-tick day."
    ),
    "Spatial": (
        "Vector variables only (`vec2i`, `vec3i`, `vec2f`, `vec3f`, `vecNi`, `vecNf`); the distance between two scalars is `abs(a - b)`. "
        "Both vectors must share a width: `vec2*` against `vec3*` is refused at compile time; a `vecN*` or `tensor2d` width is only "
        "known at run time, and a mismatch there raises an error naming the function. Int and float vectors mix freely and are "
        "measured in float. A scalar- or bool-returning vector function (`distance`, `manhattan_distance`, `within_radius`, "
        "`nearest`, `gather`) runs in every context, a variable expression included: its result has its arguments' row axis, "
        "and that is how a declared vector variable is read into a scalar or bool expression variable. A vector-returning "
        "function (`normalize`, `scatter`, `one_hot`, `direction_to_affordance`) fits no scalar or bool target."
    ),
    "Affordance": (
        "Read the agent and affordance positions the engine threads into the context: one value per agent, so in a variable "
        "expression they belong to an `agent`-scope variable (a global expression has no agent axis and refuses, naming "
        "`scope: agent`). The environment lays out affordances and positions before the instant-0 evaluation at `reset()`, so "
        '`distance_to_affordance("EAT")` is live in the first observation. Served in global and agent variable expressions '
        "and in effect pipelines; a transition write or rule and a spawn predicate are handed no positions and refuse, naming "
        "the expression-variable route (declare the distance as an agent expression variable and read it by name)."
    ),
}


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_table(specs: dict[str, FunctionSpec]) -> str:
    """Render the registry as Markdown, grouped by ``FAMILY_ORDER``."""
    unknown_families = {spec.family for spec in specs.values()} - set(FAMILY_ORDER)
    if unknown_families:
        raise ValueError(f"FUNCTION_SPECS names families outside FAMILY_ORDER: {sorted(unknown_families)}")
    missing_notes = set(FAMILY_ORDER) - set(FAMILY_NOTES)
    if missing_notes:
        raise ValueError(f"FAMILY_NOTES lacks an entry for: {sorted(missing_notes)}")

    lines: list[str] = [
        f"{len(specs)} functions are registered. A scalar-typed result (`int`, `float`, `bool`) keeps the batch axis of its",
        "per-agent inputs; a vector-typed result (`vec2f`, `vec3f`, `vecNf`) keeps it in front of the vector axis. No function",
        "collapses the batch axis. A literal has no batch axis, so a result built only from literals is unbatched:",
        "`one_hot(2, 3)` is `[3]`, `one_hot(bar.slot, 3)` is `[batch, 3]` — except a random draw, which is one per row of",
        "its context even with literal arguments. The **Needs** column is the context a call needs; a consumer admits a",
        "call by it alone (every function whose needs the consumer's runtime does not carry refuses at compile, naming",
        "the consumer), and the VFS shape proof derives a call's row axis from the registry's shape rule, never from a",
        "hand-kept list: a position function is one row per agent, a draw is one per row of its context, every other",
        "function joins its arguments' axes.",
        "",
    ]
    for family in FAMILY_ORDER:
        members = sorted((spec for spec in specs.values() if spec.family == family), key=lambda spec: spec.name)
        if not members:
            continue
        lines.append(f"### {family}")
        lines.append("")
        lines.append(FAMILY_NOTES[family])
        lines.append("")
        lines.append("| Function | Returns | What it computes | Needs |")
        lines.append("|---|---|---|---|")
        for spec in members:
            needs = "; ".join(spec.requires) if spec.requires else "—"
            lines.append(f"| `{_cell(spec.signature)}` | {_cell(spec.returns)} | {_cell(spec.summary)} | {_cell(needs)} |")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def splice(document: str, table: str) -> str:
    """Replace the generated block in ``document`` with ``table``."""
    begin = document.find(BEGIN_MARKER)
    end = document.find(END_MARKER)
    if begin < 0 or end < 0 or end < begin:
        raise ValueError(f"{DOC_PATH} lacks the generated-block markers {BEGIN_MARKER!r} / {END_MARKER!r}")
    head = document[: begin + len(BEGIN_MARKER)]
    tail = document[end:]
    return f"{head}\n{table}{tail}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 instead of writing when the document is stale")
    args = parser.parse_args(argv)

    current = DOC_PATH.read_text(encoding="utf-8")
    rendered = splice(current, render_table(FUNCTION_SPECS))
    if rendered == current:
        print(f"{DOC_PATH.relative_to(REPO_ROOT)} is current ({len(FUNCTION_SPECS)} functions)")
        return 0
    if args.check:
        print(f"{DOC_PATH.relative_to(REPO_ROOT)} is stale; run scripts/gen_expression_functions_doc.py", file=sys.stderr)
        return 1
    DOC_PATH.write_text(rendered, encoding="utf-8")
    print(f"rewrote the generated block in {DOC_PATH.relative_to(REPO_ROOT)} ({len(FUNCTION_SPECS)} functions)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
