from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.references import is_identifier
p = ExpressionParser()
for s in ["true_count", "truex", "falsey", "false_alarm", "notable", "nothing", "not_x", "iffy", "if_open", "thenx", "elsewhere",
          "orbit", "order", "android", "and_x", "True", "TRUE", "abs", "min", "x + notable", "notable + 1", "1.0 + true_count", "orbit * 2",
          "a or orbit", "a and android", "where(notable, 1.0, 0.0)", "_x", "x_", "X1", "__", "nullref", "tick"]:
    try:
        r = p.parse(s)
        print(f"{s!r:30} is_identifier={is_identifier(s.split()[0]) if ' ' not in s else '-'} -> {r!r}"[:200])
    except Exception as e:
        print(f"{s!r:30} -> ERROR {type(e).__name__}: {str(e)[:100]}")
