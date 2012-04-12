from py.test import raises

from lsp import lex, parse, read, eval, Symbol, List, lsp


def test_lex():
    assert lex("(1, 2)") == ['(', '1', '2', ')']


def test_lex_comment():
    assert lex("1; foo\n2") == lex("1\n2")
    assert lex('; 1') == lex('')
    assert lex(';') == lex('')


def test_read_atom():
    assert parse(['1']) == 1


def test_read_list():
    assert parse(['(', '1', '2', ')']) == [1, 2]

    assert parse(['(', '1', '(', '2', '3', ')', ')']) == [1, [2, 3]]
    assert parse(['(', '(', '1', '2', ')', '3', ')']) == [[1, 2], 3]
    assert parse(['(', '1', '(', '2', ')', '3', ')']) == [1, [2], 3]


def test_read_unmatched():
    with raises(SyntaxError):
        assert parse(['('])


def test_read_func():
    assert read('(+ 1 2)') == ['+', 1, 2]
    assert read('(fn (x) (+ x 1))') == ['fn', ['x'], ['+', 'x', 1]]


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
    assert lsp('(if 0 2 3)') == 3


def test_def():
    assert lsp('(def a 1) \n a') == 1


def test_fn():
    assert lsp('((fn () 1))') == 1
    assert lsp('((fn (x) x) 1)') == 1
    assert lsp('((fn (x) (+ x 1)) 1)') == 2


def test_defn():
    assert lsp('(def f (fn () 1)) \n (f)') == 1
