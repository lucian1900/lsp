#!/usr/bin/env python

import re
import sys
import operator
from functools import wraps
from fractions import Fraction


class Atom(object):
    def __nonzero__(self):
        return True

    __bool__ = __nonzero__


class Integral(Atom, int):
    def __repr__(self):
        return str(self)


class Rational(Atom, Fraction):
    pass


class Boolean(Atom):
    def __init__(self, value='false'):
        if value == 'true':
            self.value = True
        elif value == 'false':
            self.value = False
        else:
            raise ValueError('Invalid boolean literal: {0}'.format(value))

    def __repr__(self):
        return repr(self.value).lower()

    def __nonzero__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, bool):
            return bool(self) == other
        elif isinstance(other, Boolean):
            return self.value == other.value
        else:
            return False


class Nil(Atom):
    def __init__(self, value='nil'):
        if value != 'nil':
            raise ValueError('Invalid nil literal: {0}'.format(value))

    def __nonzero__(self):
        return False

    def __repr__(self):
        return 'nil'

    def __eq__(self, other):
        if isinstance(other, Nil):
            return True
        else:
            return False


class String(Atom, str):
    def __repr__(self):
        return '"' + self + '"'


class List(list):
    def __repr__(self):
        return '(' + ' '.join(map(str, self)) + ')'


class Symbol(str):
    def __repr__(self):
        return self


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
        first = body[0]
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

        self.body = body[1:]
        self.env = env

    def __call__(self, *args):
        if len(args) != len(self.args):
            raise RuntimeError("Expected {0} args, got {1}: {2}".format(
                len(self.args), len(args), args))

        loc = Env(zip(self.args, args), parent=self.env)
        if self.name is not None:
            loc[self.name] = self

        return eval(self.body[0], loc)

    def __repr__(self):
        return '<lsp.lambda object at {0}>'.format(hex(id(self)))


def quote_macro(body, env):
    if len(body) != 1:
        raise SyntaxError("quote expects 1 part")

    return body[0]


def quasiquote_macro(body, env):
    if len(body) != 1:
        raise SyntaxError("quasiquote expects 1 part")

    return eval_unquote(body[0], env)


def unquote_macro(body, env):
    raise SyntaxError("unquote only valid in quasiquote")


def unquote_splicing_macro(body, env):
    raise SyntaxError("unquote-splicing only valid in quasiquote")


def do_macro(body, env):
    for i in body:
        result = eval(i, env)

    return result


class arguments(object):
    def __init__(self, ge=0, eq=None):
        self.gte = ge
        self.eq = eq

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args):
            if self.eq is not None:
                if len(args) == self.eq:
                    raise TypeError(
                        "Expects exactly {0} arguments".format(self.eq))
            else:
                if len(args) < self.gte:
                    raise TypeError(
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


def multiply(*args):
    return reduce(operator.mul, args, initializer=1)


@arguments(2)
def divide(*args):
    return reduce(operator.truediv, args)


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
def le(*args):
    return reduce(operator.le, args, sentinel=False)


@arguments(2)
def gt(*args):
    return reduce(operator.gt, args, sentinel=False)


@arguments(2)
def ge(*args):
    return reduce(operator.ge, args, sentinel=False)


macros = {
    'if': if_macro,
    'fn': fn_macro,
    'def': def_macro,
    'quote': quote_macro,
    'quasiquote': quasiquote_macro,
    'unquote': unquote_macro,
    'unquote-splicing': unquote_splicing_macro,
    'defmacro': defmacro_macro,
    'do': do_macro,
}

env = Env({
    '+': plus,
    '-': minus,
    '*': multiply,
    '/': divide,
    '=': operator.eq,
    '<': lt,
    '>': gt,
    '<=': le,
    '>=': ge,
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

    return sexp

env['eval'] = eval


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


def quote_wrap(exp, quoting):
    "Wrap expression in a quote if necessary"

    if quoting is not None:
        return List([Symbol(quoting), exp])
    else:
        return exp


def parse(tokens):
    if len(tokens) == 0:
        raise SyntaxError("Unexpected EOF")

    tok = tokens.pop(0)

    if tok == "'":
        quoting = 'quote'
        tok = tokens.pop(0)
    elif tok == "`":
        quoting = 'quasiquote'
        tok = tokens.pop(0)
    elif tok == "~":
        quoting = "unquote"
        tok = tokens.pop(0)
    elif tok == "~@":
        quoting = "unquote-splicing"
        tok = tokens.pop(0)
    else:
        quoting = None

    # Lists
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

        return quote_wrap(exp, quoting)

    if tok == ')':
        raise SyntaxError("Unexpected ')'")

    # Strings
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return quote_wrap(String(tok), quoting)

    # Atoms
    for t in [Integral, Rational, Boolean, Nil, Symbol]:
        try:
            exp = t(tok)
        except ValueError:
            pass
        else:
            return quote_wrap(exp, quoting)


def lex(source):
    '''Split by parens, quotes and other reader tokens
    Inspired by Peter Norvig's lis.py
    '''

    separators = {
        # commas are whitespace
        r",": " ",
        r"\(": " ( ",
        r"\)": " ) ",
        r"'": " ' ",
        r"`": " ` ",
        # match only if next char isn't @, lookahead so it isn't consumed
        r"~(?=[^@])": " ~ ",
        r"~@": " ~@ ",
    }

    # Remove comments
    source = re.sub(r';.*(\n|$)', '\n', source)

    for sep, rep in separators.items():
        source = re.sub(sep, rep, source)

    return source.split()


def read(source):
    return parse(lex(source))


def lsp(source, env=env):
    return eval(parse(lex('(do {0})'.format(source))), env=env)

# load prelude
with open('prelude.lsp') as f:
    lsp(f.read())


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
