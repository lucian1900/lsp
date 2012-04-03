class Symbol(str): pass
class List(list): pass
class Atom(object): pass
class Number(Atom, int): pass
class String(Atom, str): pass


def plus(*args):
    return sum(args)

funs = {
    '+': plus,
}


def eval(sexp):
    if isinstance(sexp, List):
        if len(sexp) == 0:
            raise ValueError("Missing function expression")

        vals = [eval(i) for i in sexp]
        fun = vals[0]
        return fun(*vals[1:])

    elif isinstance(sexp, Symbol):
        return funs[sexp]

    elif isinstance(sexp, Atom):
        return sexp

    return sexp


def read(tokens):
    try:
        tok = tokens[0]
        tokens = tokens[1:]
    except IndexError:
        raise SyntaxError("Unexpected EOF")

    if tok == '(':
        try:
            end = tokens.index(')')
        except ValueError:
            raise SyntaxError("Expected ')'")

        in_toks = tokens[:end]

        exp = List()
        while in_toks:
            exp.append(read(in_toks))
            in_toks.pop(0)

        return exp

    try:
        atom = Number(tok)
    except ValueError:
        return Symbol(tok)
    else:
        return atom  # int after all


def tokenize(source):
    '''Split by parens, consider commas whitespace
    Inspired by Peter Norvig's lis.py
    '''

    tokens = {
        '(': ' ( ',
        ')': ' ) ',
        ',': ' ',
    }

    for tok, rep in tokens.items():
        source = source.replace(tok, rep)

    return source.split()
