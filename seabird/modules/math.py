import ast
import math  # pylint: disable=unused-import
import operator

from seabird.decorators import command
from seabird.plugin import Plugin


class MathError(Exception):
    pass


class MathPlugin(Plugin):
    # supported operators
    operators = {ast.Add: operator.add, ast.Sub: operator.sub,
                 ast.Mult: operator.mul, ast.Div: operator.truediv,
                 ast.Pow: operator.pow, ast.BitXor: operator.xor,
                 ast.USub: operator.neg, ast.Mod: operator.mod}

    constants = {'PI': math.pi, 'E': math.e}

    functions = {'pow': math.pow,
                 'log': math.log,
                 'sin': math.sin,
                 'cos': math.cos,
                 'tan': math.tan,
                 'asin': math.asin,
                 'acos': math.acos,
                 'atan': math.atan,
                 'deg': math.degrees,
                 'rad': math.radians,
                 'floor': math.floor,
                 'ceil': math.ceil,
                 'abs': math.fabs}

    @command
    def math(self, msg):
        """[expr]

        Run some simple calculations.
        """
        try:
            val = self.eval(msg.trailing)
            self.bot.mention_reply(msg, "{} = {}".format(msg.trailing, val))
        except (SyntaxError, MathError, TypeError) as exc:
            self.bot.mention_reply(msg, "Error: {}".format(exc))

    def eval(self, expr):
        return self._eval(ast.parse(expr, mode='eval').body)

    def _eval(self, node):
        if isinstance(node, ast.Num):
            # <number>
            return node.n
        elif isinstance(node, ast.BinOp):
            # <left> <operator> <right>
            oper = MathPlugin.operators.get(type(node.op))
            if oper is None:
                raise MathError('Weird error')

            return oper(self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            # <operator> <operand> e.g., -1
            oper = MathPlugin.operators.get(type(node.op))
            if oper is None:
                raise MathError('Weird error')

            return oper(self._eval(node.operand))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise MathError('Invalid function name')

            args = [self._eval(arg) for arg in node.args]

            func = MathPlugin.functions.get(node.func.id)
            if func is None:
                raise MathError('Function does not exist')

            return func(*args)
        elif isinstance(node, ast.Name):
            # <id>
            ret = MathPlugin.constants.get(node.id)
            if ret is None:
                raise MathError('Invalid constant')

            return ret
        else:
            raise TypeError(node)
