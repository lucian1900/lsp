from fractions import Fraction


class Atom(object):
    def __nonzero__(self):
        "Everything is truthy"
        return True

    def __bool__(self):
        return self.__nonzero__()


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


def pairs(lst):
    it = iter(lst)
    while True:
        yield next(it), next(it)


class Map(dict, Collection):
    start = '{'
    stop = '}'

    def __init__(self, init=None):
        if init is None:
            init = []

        super(Map, self).__init__(pairs(init))

    def __repr__(self):
        parts = []

        for k, v in self.iteritems():
            parts.append("{0} {1}".format(k, v))

        return '{' + ', '.join(parts) + '}'


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
