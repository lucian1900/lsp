from lsp.types import *


def if_(body, env):
    if eval(body[0], env):
        return eval(body[1], env)
    else:
        return eval(body[2], env)


def def_(body, env):
    name = body[0]
    if not isinstance(name, Symbol):
        raise SyntaxError("Expected symbol, got {0}".format(name))

    val = eval(body[1], env)
    env[name] = eval(val, env)

    return val


class fn(object):
    def __init__(self, body, env):
        first = body[0]

        # Optional name for self call
        if isinstance(first, Symbol):
            self.name = first
            body = body[1:]
            first = body[0]
        else:
            self.name = None

        if isinstance(first, List):
            self.args = first
        else:
            raise SyntaxError("Expected argument list, got: {0}".format(
                first))

        # Rest arguments
        if '&' in self.args:
            i = self.args.index('&')

            self.rest_arg = self.args[i + 1]
            if not isinstance(self.rest_arg, Symbol):
                raise SyntaxError("Expected symbol as rest argument, got: {0}" \
                    .format(self.rest_arg))

            self.args = self.args[:i]
        else:
            self.rest_arg = None

        self.body = body[1:]
        self.env = env

    def __call__(self, *args):
        if self.rest_arg is not None:
            if len(args) < len(self.args):
                raise RuntimeError("Expected at least {0} args, got {1}: {2}" \
                    .format(len(self.args), len(args), args))

        elif len(args) != len(self.args):
            raise RuntimeError("Expected {0} args, got {1}: {2}".format(
                len(self.args), len(args), args))

        loc = Env(zip(self.args, args), parent=self.env)

        if self.rest_arg is not None:
            loc[self.rest_arg] = List(args[len(self.args):])

        if self.name is not None:
            loc[self.name] = self

        return eval(self.body[0], loc)

    def __repr__(self):
        return '<lsp.lambda object at {0}>'.format(hex(id(self)))


class defmacro(object):
    def __init__(self, body, env):
        name = body[0]
        if not isinstance(name, Symbol):
            raise SyntaxError("Expected symbol, got {0}".format(name))

        args = body[1]
        if isinstance(args, List):
            self.args = args
        else:
            raise SyntaxError("Expected argument list, got: {0}".format(args))

        # Rest arguments
        if '&' in self.args:
            i = self.args.index('&')

            self.rest_arg = self.args[i + 1]
            if not isinstance(self.rest_arg, Symbol):
                raise SyntaxError("Expected symbol as rest argument, got: {0}" \
                    .format(self.rest_arg))

            self.args = List(self.args[:i])
        else:
            self.rest_arg = None

        self.body = body[2]
        self.env = env

        env.macros[name] = self

    def __call__(self, args, env):
        if self.rest_arg is not None:
            if len(args) < len(self.args):
                raise RuntimeError("Expected at least {0} args, got {1}: {2}" \
                    .format(len(self.args), len(args), args))

        elif len(args) != len(self.args):
            raise RuntimeError("Expected {0} args, got {1}: {2}".format(
                len(self.args), len(args), args))

        loc = Env(zip(self.args, args), parent=self.env)

        if self.rest_arg is not None:
            loc[self.rest_arg] = List(args[len(self.args):])

        return eval(eval(self.body, loc), env)


def quote(body, env):
    if len(body) != 1:
        raise SyntaxError("quote expects 1 part")

    return body[0]


def quasiquote(body, env):
    if len(body) != 1:
        raise SyntaxError("quasiquote expects 1 part")

    return eval_unquote(body[0], env)


def unquote(body, env):
    raise SyntaxError("unquote only valid in quasiquote")


def unquote_splicing(body, env):
    raise SyntaxError("unquote-splicing only valid in quasiquote")


def do(body, env):
    for i in body:
        result = eval(i, env)

    return result


def call_method(body, env):
    if len(body) < 2:
        raise SyntaxError("method call expects at least 2 parts, got: {0}" \
            .format(len(body)))

    obj = body[0]
    meth = body[1]
    args = body[2:]

    return getattr(obj, meth)(*args)


def eval(sexp, env):
    if isinstance(sexp, List):
        if len(sexp) == 0:
            raise ValueError("Missing function expression")

        if isinstance(sexp[0], Symbol) and sexp[0] in env.macros:
            m = env.macros[sexp[0]]
            return m(sexp[1:], env)

        else:
            vals = List(eval(i, env) for i in sexp)
            fun = vals[0]

            if not hasattr(fun, '__call__'):
                raise TypeError("Expected function, got: {0}".format(fun))

            return fun(*vals[1:])

    elif isinstance(sexp, Symbol):
        try:
            return env[sexp]
        except KeyError:
            raise RuntimeError("Unbound symbol: {0}".format(sexp))

    elif isinstance(sexp, Atom):
        return sexp

    return sexp


def eval_unquote(sexp, env):
    if isinstance(sexp, List):
        if len(sexp) == 2 and sexp[0] == Symbol('unquote'):
            return eval(sexp[1], env)
        else:
            l = []
            for i in sexp:
                if hasattr(i, '__len__') and len(i) == 2 \
                    and i[0] == Symbol('unquote-splicing'):
                    l.extend(eval(i[1], env))
                else:
                    l.append(eval_unquote(i, env))

            return List(l)

    return sexp


from lsp.env import top
