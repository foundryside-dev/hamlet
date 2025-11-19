"""Expression parser using pyparsing."""
from pyparsing import (
    Literal,
    Word,
    alphas,
    alphanums,
    QuotedString,
    pyparsing_common,
    ParserElement,
    Regex,
)
from townlet.world.expression import (
    ASTNode,
    Constant,
    Variable,
    PathAccess,
    BinaryOp,
    UnaryOp,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
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
        int_literal = pyparsing_common.signed_integer().setParseAction(
            lambda tokens: Constant(value=int(tokens[0]))
        )
        # Try float first (so "0.5" isn't parsed as "0"), but strict regex prevents "42" matching
        numeric_literal = float_literal | int_literal

        # String literals (double or single quotes)
        string_literal = (
            QuotedString('"', escChar="\\")
            | QuotedString("'", escChar="\\")
        ).setParseAction(lambda tokens: Constant(value=str(tokens[0])))

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

        variable = identifier.copy().setParseAction(make_variable)

        # Primary expressions (atoms)
        primary = constant | variable

        # For now, expression is primary
        # We'll add operators in subsequent steps
        self.expression = primary

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
