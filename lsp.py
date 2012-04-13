#!/usr/bin/env python

import re
import sys


class Symbol(str): pass
class List(list): pass
class Atom(object): pass
class Number(Atom, int): pass
class String(Atom, str): pass


class Env(dict):
    def __init__(self, ns, parent=None):
        super(Env, self).__init__(ns)
        self.parent = None

    def __getitem__(self, key):
        try:
            return super(Env, self).__getitem__(key)
        except KeyError, e:
            if self.parent:
                return self.parent[key]
            else:
                raise e


def if_macro(body):
    if eval(body[0]):
        return eval(body[1])
    else:
        return eval(body[2])


def def_macro(body):
    name = body[0]
    val = eval(body[1])

    env[name] = eval(val)

    return val


class fn_macro(object):
    def __init__(self, body):
        self.args = body[0]
        self.body = body[1:]

    def __call__(self, *args):
        if len(args) != len(self.args):
            raise RuntimeError("Wrong number of args")

        ns = Env(zip(self.args, args), parent=env)

        return eval(self.body[0], ns)


def plus(*args):
    return sum(args)


def minus(*args):
    if len(args) == 0:
        raise RuntimeError('expects at least 1 arguments')

    elif len(args) == 1:
        return -args[0]

    return args[0] - sum(args[1:])


macros = {
    'if': if_macro,
    'fn': fn_macro,
    'def': def_macro,
    'quote': '',
}

env = Env({
    '+': plus,
    '-': minus,
    'exit': sys.exit,
})


def eval(sexp, env=env):
    if isinstance(sexp, List):
        if len(sexp) == 0:
            raise ValueError("Missing function expression")

        if isinstance(sexp[0], Symbol) and sexp[0] in macros:
            m = macros[sexp[0]]
            return m(sexp[1:])

        else:
            vals = [eval(i) for i in sexp]
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


def parse(tokens):
    if len(tokens) == 0:
        raise SyntaxError("Unexpected EOF")

    tok = tokens.pop(0)
    if tok == '(':
        exp = List()

        try:
            while tokens[0] != ')':
                exp.append(parse(tokens))
        except IndexError:
            raise SyntaxError("Expected ')'")

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
        '(': ' ( ',
        ')': ' ) ',
        ',': ' ',
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
