"""Expression parser using pyparsing."""

from pyparsing import (
    Literal,
    ParserElement,
    QuotedString,
    Regex,
    Word,
    alphanums,
    alphas,
    infixNotation,
    opAssoc,
    pyparsing_common,
)

from townlet.world.expression import (
    ASTNode,
    BinaryOp,
    Constant,
    OperatorType,
    PathAccess,
    Variable,
)

# Enable packrat parsing for performance
ParserElement.enablePackrat()


class ExpressionParser:
    """Parser for HAMLET Expression Language.

    Converts expression strings into AST nodes using pyparsing.

    Examples:
        >>> parser = ExpressionParser()
        >>> parser.parse("0.05")
        Constant(value=0.05)
        >>> parser.parse("a + b")
        BinaryOp(left=Variable("a"), op=ADD, right=Variable("b"))
    """

    def __init__(self):
        """Initialize parser with grammar rules."""
        self._build_grammar()

    def _build_grammar(self):
        """Build pyparsing grammar for expression language."""

        # Literals
        # Boolean literals (must come before identifiers)
        true_literal = Literal("true").setParseAction(lambda: Constant(value=True))
        false_literal = Literal("false").setParseAction(lambda: Constant(value=False))
        bool_literal = true_literal | false_literal

        # Numeric literals
        # CRITICAL FIX: Use strict float matching to prevent "42" from parsing as float
        # fnumber() aggressively matches integers, breaking type checking for array indices
        # This regex requires either a decimal point OR scientific notation: 0.5, -10.3, 1., 1.0e-5, 1e-3
        float_literal = Regex(r"[+-]?(\d+\.\d*([eE][+-]?\d+)?|\d+[eE][+-]?\d+)").setParseAction(
            lambda tokens: Constant(value=float(tokens[0]))
        )
        int_literal = pyparsing_common.signed_integer().setParseAction(lambda tokens: Constant(value=int(tokens[0])))
        # Try float first (so "0.5" isn't parsed as "0"), but strict regex prevents "42" matching
        numeric_literal = float_literal | int_literal

        # String literals (double or single quotes)
        string_literal = (QuotedString('"', escChar="\\") | QuotedString("'", escChar="\\")).setParseAction(
            lambda tokens: Constant(value=str(tokens[0]))
        )

        # Combine all constants
        constant = bool_literal | numeric_literal | string_literal

        # Variables (identifiers)
        # Must not match keywords (true, false, and, or, not, if, then, else)
        keywords = {"true", "false", "and", "or", "not", "if", "then", "else"}
        identifier = Word(alphas + "_", alphanums + "_")

        def make_variable(tokens):
            name = tokens[0]
            if name in keywords:
                # This shouldn't happen due to grammar ordering,
                # but guard against it
                raise ValueError(f"Cannot use keyword '{name}' as variable")
            return Variable(name=name)

        # Path access (dotted notation)
        # target.bar.energy → ["target", "bar", "energy"]
        def make_path_access(tokens):
            segments = [str(t) for t in tokens]
            if len(segments) == 1:
                # Single identifier is a Variable, not PathAccess
                return Variable(name=segments[0])
            return PathAccess(segments=segments)

        path_or_variable = identifier + (Literal(".").suppress() + identifier)[...].setParseAction(lambda tokens: tokens.asList())
        path_or_variable.setParseAction(make_path_access)

        # Primary expressions (atoms)
        primary = constant | path_or_variable

        # Helper to make binary ops
        def make_binop(tokens):
            """Convert infix tokens to BinaryOp AST nodes."""
            result = tokens[0][0]
            i = 1
            while i < len(tokens[0]):
                op_str = tokens[0][i]
                right = tokens[0][i + 1]

                # Map operator string to OperatorType
                op_map = {
                    "+": OperatorType.ADD,
                    "-": OperatorType.SUB,
                    "*": OperatorType.MUL,
                    "/": OperatorType.DIV,
                    "%": OperatorType.MOD,
                    "**": OperatorType.POW,
                    "==": OperatorType.EQ,
                    "!=": OperatorType.NEQ,
                    "<": OperatorType.LT,
                    ">": OperatorType.GT,
                    "<=": OperatorType.LTE,
                    ">=": OperatorType.GTE,
                    "and": OperatorType.AND,
                    "or": OperatorType.OR,
                }

                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown operator: {op_str}")

                result = BinaryOp(left=result, op=op_type, right=right)
                i += 2

            return result

        # Build expression with operator precedence
        expression_with_ops = infixNotation(
            primary,
            [
                # Level 6: Exponentiation (right-associative)
                (Literal("**"), 2, opAssoc.RIGHT, make_binop),
                # Level 5: Multiplication, Division, Modulo (left-associative)
                (Literal("*") | Literal("/") | Literal("%"), 2, opAssoc.LEFT, make_binop),
                # Level 4: Addition, Subtraction (left-associative)
                (Literal("+") | Literal("-"), 2, opAssoc.LEFT, make_binop),
                # Level 3: Comparisons (left-associative)
                (
                    Literal("==") | Literal("!=") | Literal("<=") | Literal(">=") | Literal("<") | Literal(">"),
                    2,
                    opAssoc.LEFT,
                    make_binop,
                ),
                # Level 2: Logical AND (left-associative)
                (Literal("and"), 2, opAssoc.LEFT, make_binop),
                # Level 1: Logical OR (left-associative)
                (Literal("or"), 2, opAssoc.LEFT, make_binop),
            ],
        )

        self.expression = expression_with_ops

    def parse(self, text: str) -> ASTNode:
        """Parse expression string into AST.

        Args:
            text: Expression string to parse

        Returns:
            AST node representing the expression

        Raises:
            ParseException: If text is not a valid expression
        """
        result = self.expression.parseString(text, parseAll=True)
        return result[0]
