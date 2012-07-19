#!/usr/bin/env python

import re
import sys
import operator
from functools import wraps


class Atom(object):
    pass


class Number(Atom, int):
    def __repr__(self):
        return str(self)


class String(Atom, str):
    def __repr__(self):
        return '"' + self + '"'


class List(list):
    def __repr__(self):
        return '(' + ' '.join(map(str, self)) + ')'


class Symbol(str):
    def __repr__(self):
        return self


class Quote(object):
    def __init__(self, payload):
        self.payload = payload


class Env(dict):
    def __init__(self, ns, parent=None):
        super(Env, self).__init__(ns)
        self.parent = parent

    def __getitem__(self, key):
        try:
            return super(Env, self).__getitem__(key)
        except KeyError, e:
            if self.parent:
                return self.parent[key]
            else:
                raise e


def if_macro(body, env):
    if eval(body[0], env):
        return eval(body[1], env)
    else:
        return eval(body[2], env)


def def_macro(body, env):
    if not isinstance(body[0], Symbol):
        raise SyntaxError("Expected symbol, got {0}".format(body[0]))

    name = body[0]
    val = eval(body[1], env)

    env[name] = eval(val, env)

    return val


class defmacro_macro(object):
    def __init__(self, body, env):
        self.env = env

        if not isinstance(body[0], Symbol):
            raise SyntaxError("Expected symbol, got {0}".format(body[0]))

        name = body[0]

        if not isinstance(body[1], List):
            raise SyntaxError("Expected argument list, got {0}".format(body[1]))

        self.args = body[1]
        self.body = body[2]

        macros[name] = self

    def __call__(self, args, env):
        if len(args) != len(self.args):
            raise SyntaxError("Expected {0} args, got {1}: {2}".format(
                len(self.args), len(args), args))

        return eval(eval(self.body,
                        Env(zip(self.args, args),
                            parent=self.env)),
                    env)


class fn_macro(object):
    def __init__(self, body, env):
        self.args = body[0]
        self.body = body[1:]
        self.env = env

    def __call__(self, *args):
        if len(args) != len(self.args):
            raise RuntimeError("Expected {0} args, got {1}: {2}".format(
                len(self.args), len(args), args))

        return eval(self.body[0],
                    Env(zip(self.args, args),
                        parent=self.env))

    def __repr__(self):
        return '<lsp.lambda object at {0}>'.format(hex(id(self)))


def quote_macro(body, env):
    if len(body) != 1:
        raise SyntaxError("quote expects 1 part")

    return body[0]


def quasiquote_macro(body, env):
    if len(body) != 1:
        raise SyntaxError("quasiquote expects 1 part")

    return eval(Quote(body[0], env))


def unquote_macro(body, env):
    if len(body) != 1:
        raise SyntaxError("unquote expects 1 part")

    return eval(body[0], env)


class arguments(object):
    def __init__(self, gte=0, eq=None):
        self.gte = gte
        self.eq = eq

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args):
            if self.eq is not None:
                if len(args) == self.eq:
                    raise RuntimeError(
                        "Expects exactly {0} arguments".format(self.eq))
            else:
                if len(args) < self.gte:
                    raise RuntimeError(
                        "Expects at least {0} arguments".format(self.gte))

            return func(*args)

        return wrapper


def plus(*args):
    return sum(args)


@arguments(1)
def minus(*args):
    if len(args) == 1:
        return -args[0]

    return args[0] - sum(args[1:])


def reduce(op, coll, initializer=None, sentinel=None):
    if initializer is None:
        acc = coll[0]
        coll = coll[1:]
    else:
        acc = initializer

    for i in coll:
        if acc == sentinel:
            return acc

        acc = op(acc, i)

    return acc


@arguments(2)
def lt(*args):
    return reduce(operator.lt, args, sentinel=False)


@arguments(2)
def lte(*args):
    return reduce(operator.lte, args, sentinel=False)


@arguments(2)
def gt(*args):
    return reduce(operator.gt, args, sentinel=False)


@arguments(2)
def gte(*args):
    return reduce(operator.gte, args, sentinel=False)


macros = {
    'if': if_macro,
    'fn': fn_macro,
    'def': def_macro,
    'quote': quote_macro,
    'defmacro': defmacro_macro,
}

env = Env({
    '+': plus,
    '-': minus,
    '=': operator.eq,
    '<': lt,
    '>': gt,
    '<=': lte,
    '>=': gte,
    'exit': sys.exit,
})
loc = env


def eval(sexp, env=env):
    if isinstance(sexp, List):
        if len(sexp) == 0:
            raise ValueError("Missing function expression")

        if isinstance(sexp[0], Symbol) and sexp[0] in macros:
            m = macros[sexp[0]]
            return m(sexp[1:], env)

        else:
            vals = [eval(i, env) for i in sexp]
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

    elif isinstance(sexp, Quote):
        return sexp.payload

    return sexp


def parse(tokens):
    if len(tokens) == 0:
        raise SyntaxError("Unexpected EOF")

    tok = tokens.pop(0)

    if tok == "'":
        tokens = ['quote'] + tokens + [')']
        tok = '('

    if tok == '(':
        exp = List()

        while True:
            try:
                if tokens[0] == ')':
                    break
            except IndexError:
                raise SyntaxError("Expected ')'")

            exp.append(parse(tokens))

        tokens.pop(0)  # Remove ')'

        return exp

    if tok == ')':
        raise SyntaxError("Unexpected ')'")

    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return String(tok)

    try:
        atom = Number(tok)
    except ValueError:
        return Symbol(tok)
    else:
        return atom  # int after all


def lex(source):
    '''Split by parens, consider commas whitespace
    Inspired by Peter Norvig's lis.py
    '''

    separators = {
        "(": " ( ",
        ")": " ) ",
        ",": " ",
        "'": " ' ",
        "`": " ` ",
        "~": " ~ ",
    }

    source = re.sub(r';.*(\n|$)', '\n', source)

    for sep, rep in separators.items():
        source = source.replace(sep, rep)

    return source.split()


def read(source):
    return parse(lex(source))


def lsp(source):
    return eval(parse(lex(source)))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        while True:
            try:
                print lsp(raw_input('> '))
            except Exception, e:
                print e
    elif len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            print lsp(f.parse())
    elif len(sys.argv) == 3:
        if sys.argv[1] == '-c':
            print lsp(sys.argv[2])
        else:
            print "Only -c supported so far"
    else:
        print "Wrong args"
