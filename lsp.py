#!/usr/bin/env python

import re
import sys
import operator
from fractions import Fraction

from os.path import join, dirname


class Atom(object):
    def __nonzero__(self):
        "Everything is truthy"
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


class Collection(object):
    def __nonzero__(self):
        "Even empty collections are truthy"
        return True

    __bool__ = __nonzero__

    def __call__(self, index):
        return self[index]


class List(list, Collection):
    start = '('
    stop = ')'

    def __repr__(self):
        return '(' + ' '.join(map(str, self)) + ')'


class Vector(list, Collection):
    start = '['
    stop = ']'

    def __repr__(self):
        return '[' + ' '.join(map(str, self)) + ']'


class Symbol(str):
    def __repr__(self):
        return self


class Env(dict):
    def __init__(self, ns, parent=None, macros=None):
        super(Env, self).__init__(ns)

        if parent is not None:
            macros = parent.macros
        elif macros is None:
            macros = {}

        self.parent = parent
        self.macros = macros

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

        env.macros[name] = self

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


def call_method(body, env):
    if len(body) < 2:
        raise SyntaxError("method call expects at least 2 parts, got: {0}" \
            .format(len(body)))

    obj = body[0]
    meth = body[1]
    args = body[2:]

    return getattr(obj, meth)(*args)


def plus(*nums):
    return sum(nums)


def minus(num, *rest):
    nums = (num,) + rest

    if len(nums) == 1:
        return -nums[0]

    return nums[0] - sum(nums[1:])


def multiply(*nums):
    return reduce(operator.mul, nums, initializer=1)


def divide(num1, num2, *rest):
    return reduce(operator.truediv, (num1, num2) + rest)


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


def lt(i1, i2, *rest):
    return reduce(operator.lt, (i1, i2) + rest, sentinel=False)


def le(i1, i2, *rest):
    return reduce(operator.le, (i1, i2) + rest, sentinel=False)


def gt(i1, i2, *rest):
    return reduce(operator.gt, (i1, i2) + rest, sentinel=False)


def ge(i1, i2, *rest):
    return reduce(operator.ge, (i1, i2) + rest, sentinel=False)


def not_eq(i1, i2, rest):
    return reduce(operator.ne, (i1, i2) + rest, sentinel=False)


def print_(i1, *rest):
    for i in (i1,) + rest:
        print i,

    return Nil()


def println(i1, *rest):
    for i in (i1,) + rest:
        print i,
    print

    return Nil()


def input(msg=''):
    return raw_input(msg)


def rest(coll):
    return List(coll[1:])


def cons(item, coll):
    return List([item] + coll)


def concat(coll1, coll2):
    return List(coll1 + coll2)


def slice_list(coll, start, end, step=1):
    return List(coll[start:end:step])


def is_empty(coll):
    return len(coll) == 0


def is_nil(item):
    return Boolean(isinstance(item, Nil))


def make_list(*items):
    return List(items)


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
    '.': call_method,
}

env = Env({
    # Numbers
    '+': plus,
    '-': minus,
    '*': multiply,
    '/': divide,
    '<': lt,
    '>': gt,
    '<=': le,
    '>=': ge,

    # Bool
    '=': operator.eq,
    'not': operator.not_,
    'not=': not_eq,

    # Core
    'apply': apply,
    'nil?': is_nil,

    # Lists
    'list': make_list,
    'rest': rest,
    'cons': cons,
    'concat': concat,
    'empty?': is_empty,
    'slice': slice_list,
    'len': len,

    # IO
    'print': print_,
    'println': println,
    'input': input,
    'exit': sys.exit,
}, macros=macros)
loc = env


def eval(sexp, env=env):
    if isinstance(sexp, List):
        if len(sexp) == 0:
            raise ValueError("Missing function expression")

        if isinstance(sexp[0], Symbol) and sexp[0] in env.macros:
            m = env.macros[sexp[0]]
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


def parse_coll(kind, tokens, quoting):
    exp = []

    while True:
        try:
            if tokens[0] == kind.stop:
                break
        except IndexError:
            raise SyntaxError("Expected '{0}'".format(kind.stop))

        exp.append(parse(tokens))

    tokens.pop(0)  # Remove ')'
    exp = kind(exp)

    return quote_wrap(exp, quoting)


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
        return parse_coll(List, tokens, quoting)
    elif tok == '[':
        return parse_coll(Vector, tokens, quoting)

    for i in [List.stop, Vector.stop]:
        if tok == i:
            raise SyntaxError("Unexpected '{0}'".format(i))

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


def init():
    # load prelude
    with open(join(dirname(__file__), 'prelude.lsp')) as f:
        lsp(f.read())
init()


def target(*args):
    "RPython target"
    return main, []


def main():
    if len(sys.argv) == 1:
        while True:
            try:
                print lsp(raw_input('> '))
            except Exception, e:
                print e
    elif len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            lsp(f.read())
    elif len(sys.argv) == 3:
        if sys.argv[1] == '-c':
            print lsp(sys.argv[2])
        else:
            print "Only -c supported so far"
    else:
        print "Wrong args"

if __name__ == '__main__':
    main()
