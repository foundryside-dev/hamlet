"""R10: two exposed variables with the same declared parameters are refused, whatever writes them
and whatever brain reads them; the only escape is perturbing a behavioural parameter."""
from harness import *  # noqa

MM = {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True}


def attempt(label, decls, acts=None):
    print(f"--- {label}")
    try:
        u = compile_pack(make_pack(f"r10_{label}", variables=lambda v: v["declarations"].extend(decls), actions=acts))
        print("   compile: OK (witness brain: dueling — a flat net that reads by slot position)")
    except Exception as exc:  # noqa: BLE001
        print(f"   REFUSED {type(exc).__name__}: {str(exc)[:500]}")


def two_writers(a):
    for ca in a["custom_actions"]:
        if ca["name"] == "ADVANCE":
            ca["writes"] = [write("hunger", "0.1"), write("thirst", "0.3")]


@probe("R10 indistinguishability")
def main():
    # hunger and thirst: same range, same initial, different dynamics (different writes / expressions)
    attempt("two_meters_like_vars_different_writes",
            [decl("hunger", exposed=("agent",), normalization=MM), decl("thirst", exposed=("agent",), normalization=MM)], acts=two_writers)
    attempt("two_expressions_different_formulas",
            [decl("e1", exposed=("agent",), normalization=MM, expression="bar.energy"),
             decl("e2", exposed=("agent",), normalization=MM, expression="bar.health")])
    # the escape hatch the error message suggests: perturb a declared behavioural parameter
    attempt("perturbed_initial", [decl("hunger", exposed=("agent",), normalization=MM),
                                  decl("thirst", exposed=("agent",), normalization=MM, initial_value=0.001)], acts=two_writers)


main()
