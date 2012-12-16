import re

from lsp.types import *


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

    # Lists and Vectors
    if tok == '(':
        return parse_coll(List, tokens, quoting)
    elif tok == '[':
        return parse_coll(Vector, tokens, quoting)
    elif tok == '{':
        return parse_coll(Map, tokens, quoting)

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
        r"\[": " [ ",
        r"\]": " ] ",
        r"\{": " { ",
        r"\}": " } ",
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
