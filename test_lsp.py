from fractions import Fraction

from py.test import raises

from lsp import lex, parse, read, eval, Symbol, List, Nil, lsp, Env, env


def test_lex():
    assert lex("(1, 2)") == ['(', '1', '2', ')']


def test_lex_comment():
    assert lex("1; foo\n2") == lex("1\n2")
    assert lex('; 1') == lex('')
    assert lex(';') == lex('')


def test_lex_unquotes():
    assert lex("~x") == ['~', 'x']
    assert lex("~@x") == ['~@', 'x']


def test_read_atom():
    assert parse(['1']) == 1
    assert parse(['1/3']) == Fraction(1, 3)
    assert parse(['true'])
    assert parse(['nil']) == Nil()


def test_bool():
    assert parse(['true']) == True
    assert parse(['true']) == parse(['true'])

    assert not parse(['false'])
    assert parse(['false']) == False


def test_parse_list():
    assert parse(['(', '1', '2', ')']) == [1, 2]

    assert parse(['(', '1', '(', '2', '3', ')', ')']) == [1, [2, 3]]
    assert parse(['(', '(', '1', '2', ')', '3', ')']) == [[1, 2], 3]
    assert parse(['(', '1', '(', '2', ')', '3', ')']) == [1, [2], 3]
    assert parse(['(', '(', '1', ')', '(', '2', ')', ')']) == [[1], [2]]


def test_parse_unmatched():
    with raises(SyntaxError):
        assert parse(['('])


def test_read_func():
    assert read('(+ 1 2)') == ['+', 1, 2]
    assert read('(fn (x) (+ x 1))') == ['fn', ['x'], ['+', 'x', 1]]


def test_repr():
    assert str(read('1')) == '1'
    assert str(read('"hello"')) == '"hello"'
    assert str(read('(1 2 3)')) == '(1 2 3)'


def test_read_quote():
    assert read("'x") == read('(quote x)')

    assert read("'(1 2)") == read("(quote (1 2))")
    assert read("'((1 2))") == read("(quote ((1 2)))")
    assert read("'((1 2) (3 4))") == read("(quote ((1 2) (3 4)))")

    assert read("(= '1 '(2 3))") == read("(= (quote 1) (quote (2 3)))")
    assert read("(= '(1 2) '3)") == read("(= (quote (1 2)) (quote 3))")


def test_eval_atom():
    assert eval(1) == 1


def test_eval_symbol():
    assert eval('+')

    with raises(RuntimeError):
        assert eval(List([Symbol('foo')]))


def test_eval_func():
    with raises(TypeError):
        assert eval(List([1, 2]))

    assert eval(List([Symbol('+'), 1, 2])) == 3


def test_if():
    assert lsp('(if 1 2 3)') == 2
    assert lsp('(if 0 2 3)') == 2
    assert lsp('(if true 2 3)') == 2
    assert lsp('(if false 2 3)') == 3
    assert lsp('(if nil 2 3)') == 3


def test_def():
    lsp('(def a 1)')
    assert lsp('a') == 1


def test_env():
    glob = Env({'x': 1})
    loc = Env({'y': 2}, parent=glob)

    assert glob['x'] == 1
    assert loc['y'] == 2
    assert loc['x'] == 1


def test_fn():
    assert lsp('((fn () 1))') == 1
    assert lsp('((fn (x) x) 1)') == 1
    assert lsp('((fn (x) (+ x 1)) 1)') == 2


def test_defn():
    lsp('(def f (fn () 1))')
    assert lsp('(f)') == 1


def test_quote():
    assert lsp('(quote (+))') == ['+']
    assert lsp("'(+)") == ['+']

    assert lsp('(quote (1 2))') == [1, 2]
    assert lsp("'(1 2)") == [1, 2]

    assert lsp("'((1 2))") == [[1, 2]]
    assert lsp("'((1 2) (1 2))") == [[1, 2], [1, 2]]


def test_quasiquote():
    assert lsp("`(+ 1 2)") == lsp("'(+ 1 2)")

    loc = Env({'x': 2}, parent=env)
    assert lsp("(eval `(+ 1 ~x))", env=loc) == 3

    loc = Env({'x': [3, 4]}, parent=env)
    assert lsp("`(+ 1 2 ~@x)", env=loc) == read("(+ 1 2 3 4)")


def test_defmacro():
    lsp('(defmacro foo (x) x)')
    assert lsp('(foo 1)') == lsp('1')

    lsp('(defmacro foo (x) (quote x))')
    with raises(RuntimeError):
        assert lsp('(foo (+ 1 2))') == lsp('(quote (+ 1 2))')

    lsp('(defmacro foo (x) `(+ 1 ~x))')
    assert lsp('(foo 2)') == 3

    lsp('(defmacro foo (x) `(+ 1 ~@x))')
    assert lsp('(foo (2 3))') == 6


def test_plus():
    assert lsp('(+)') == 0
    assert lsp('(+ 1)') == 1
    assert lsp('(+ 1 2 3)') == 6


def test_minus():
    with raises(TypeError):
        assert lsp('(-)')

    assert lsp('(- 1)') == -1
    assert lsp('(- 1 2)') == -1


def test_multiply():
    assert lsp('(*)') == 1
    assert lsp('(* 2)') == 2
    assert lsp('(* 1 2 3)') == 6


def test_divide():
    assert lsp('(/ 10 5)') == 2
    assert lsp('(/ 10 5 3)') == lsp('(/ (/ 10 5) 3)')
    assert lsp('(/ 5 1/2)')


def test_eq():
    assert lsp('(= 1 1)') == True
    assert lsp('(= 1 2)') == False
    assert lsp("(= (quote (1 2)) (quote (3 4)))") == False
    assert lsp("(= '(1 2) '(1 2))") == True
    assert lsp("(= '(1 2) '(3 4))") == False


def test_lt():
    with raises(TypeError):
        lsp('(<)')
        lsp('(< 1)')
        lsp('(<=)')
        lsp('(<= 1)')

    assert lsp('(< 1 2)') == True
    assert lsp('(< 2 1)') == False
    assert lsp('(< 2 2)') == False

    assert lsp('(<= 1 2)') == True
    assert lsp('(<= 2 1)') == False
    assert lsp('(<= 2 2)') == True


def test_gt():
    with raises(TypeError):
        lsp('(>)')
        lsp('(> 1)')
        lsp('(>=)')
        lsp('(>= 1)')

    assert lsp('(> 1 2)') == False
    assert lsp('(> 2 1)') == True
    assert lsp('(> 2 2)') == False

    assert lsp('(>= 1 2)') == False
    assert lsp('(>= 2 1)') == True
    assert lsp('(>= 2 2)') == True


def test_fact():
    fact = '''
(fn fact (x)
  (if (<= x 1)
    1
    (* x (fact (- x 1)))))
'''
    assert lsp('({0} 5)'.format(fact)) == 120
