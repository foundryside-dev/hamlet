"""Expression parser using pyparsing."""

from pyparsing import (
    Forward,
    Literal,
    Optional,
    ParserElement,
    QuotedString,
    Regex,
    Suppress,
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
    FunctionCall,
    IfThenElse,
    OperatorType,
    PathAccess,
    UnaryOp,
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

        # Forward declaration for recursive grammar
        expression_ref = Forward()

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

        # Identifiers and keywords
        keywords = {"true", "false", "and", "or", "not", "if", "then", "else"}
        identifier = Word(alphas + "_", alphanums + "_")

        # Function calls (must come before variables to parse correctly)
        lparen = Suppress("(")
        rparen = Suppress(")")
        comma = Suppress(",")

        def make_function_call(tokens):
            func_name = tokens[0]
            args = list(tokens[1:]) if len(tokens) > 1 else []
            return FunctionCall(function_name=func_name, arguments=args)

        function_call = (identifier + lparen + Optional(expression_ref + (comma + expression_ref)[...]) + rparen).setParseAction(
            make_function_call
        )

        # Path access or variable
        def make_path_access(tokens):
            segments = [str(t) for t in tokens]
            if len(segments) == 1:
                name = segments[0]
                if name in keywords:
                    raise ValueError(f"Cannot use keyword '{name}' as variable")
                return Variable(name=name)
            return PathAccess(segments=segments)

        path_or_variable = (identifier + (Literal(".").suppress() + identifier)[...]).setParseAction(make_path_access)

        # If-Then-Else (ternary conditional)
        # if x > 0 then 1 else -1
        if_kw = Literal("if")
        then_kw = Literal("then")
        else_kw = Literal("else")

        def make_if_then_else(tokens):
            # tokens: [condition, true_branch, false_branch]
            return IfThenElse(condition=tokens[0], true_branch=tokens[1], false_branch=tokens[2])

        if_expression = (
            if_kw.suppress() + expression_ref + then_kw.suppress() + expression_ref + else_kw.suppress() + expression_ref
        ).setParseAction(make_if_then_else)

        # Primary expressions (order matters: try function_call before path)
        primary = constant | function_call | if_expression | path_or_variable

        # Unary operator helpers
        def make_unaryop(tokens):
            result = tokens[0][-1]
            for i in range(len(tokens[0]) - 2, -1, -1):
                op_str = tokens[0][i]
                op_map = {"-": OperatorType.SUB, "not": OperatorType.NOT}
                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown unary operator: {op_str}")
                result = UnaryOp(op=op_type, operand=result)
            return result

        # Binary operator helpers (LEFT-associative)
        def make_binop(tokens):
            """Convert infix tokens to BinaryOp (left-associative)."""
            result = tokens[0][0]
            i = 1
            while i < len(tokens[0]):
                op_str = tokens[0][i]
                right = tokens[0][i + 1]
                op_map = {
                    "+": OperatorType.ADD,
                    "-": OperatorType.SUB,
                    "*": OperatorType.MUL,
                    "/": OperatorType.DIV,
                    "%": OperatorType.MOD,
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

        # Binary operator helpers (RIGHT-associative)
        def make_right_binop(tokens):
            """Convert infix tokens to BinaryOp (right-associative).

            For a ** b ** c, parse as a ** (b ** c), not (a ** b) ** c.
            """
            items = tokens[0]
            # Build from right to left
            result = items[-1]  # Rightmost operand
            for i in range(len(items) - 2, -1, -2):
                op_str = items[i]
                left = items[i - 1]

                if op_str == "**":
                    op_type = OperatorType.POW
                else:
                    raise ValueError(f"Unknown right-assoc operator: {op_str}")

                result = BinaryOp(left=left, op=op_type, right=result)
            return result

        # Build expression with operator precedence
        expression_with_ops = infixNotation(
            primary,
            [
                (Literal("-") | Literal("not"), 1, opAssoc.RIGHT, make_unaryop),
                (Literal("**"), 2, opAssoc.RIGHT, make_right_binop),
                (Literal("*") | Literal("/") | Literal("%"), 2, opAssoc.LEFT, make_binop),
                (Literal("+") | Literal("-"), 2, opAssoc.LEFT, make_binop),
                (
                    Literal("==") | Literal("!=") | Literal("<=") | Literal(">=") | Literal("<") | Literal(">"),
                    2,
                    opAssoc.LEFT,
                    make_binop,
                ),
                (Literal("and"), 2, opAssoc.LEFT, make_binop),
                (Literal("or"), 2, opAssoc.LEFT, make_binop),
            ],
        )

        # Bind forward reference
        expression_ref <<= expression_with_ops
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
