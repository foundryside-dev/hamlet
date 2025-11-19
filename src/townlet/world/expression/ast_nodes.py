"""Abstract Syntax Tree node types for HAMLET Expression Language."""

import enum


class OperatorType(enum.Enum):
    """Supported binary and unary operators.

    Notes:
        - POW uses ** (Python syntax) not ^ (mathematical notation)
        - Logical operators use Python keywords (and/or/not)
    """

    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    POW = "**"  # Python syntax for power

    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"

    # Comparison
    EQ = "=="
    NEQ = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
