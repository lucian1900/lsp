from py.test import raises

from lsp import tokenize, read, eval, Symbol, List


def test_tokenize():
    assert tokenize("(1, 2)") == ['(', '1', '2', ')']


def test_read_atom():
    assert read(['1']) == 1


def test_read_list():
    assert read(['(', '1', '2', ')']) == [1, 2]


def test_read_func():
    assert read(['(', '+', '1', '2', ')']) == ['+', 1, 2]


def test_read_unmatched():
    pass


def test_eval_atom():
    assert eval(1) == 1


def test_eval_symbol():
    assert eval('+')

    with raises(RuntimeError):
        assert eval('missing')


def test_eval_func():
    with raises(TypeError):
        assert eval(List([1, 2]))

    assert eval(List([Symbol('+'), 1, 2])) == 3
