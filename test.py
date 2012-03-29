from lsp import tokenize, read, eval, Symbol


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

def test_eval_func():
	assert eval([Symbol('+'), 1, 2]) == 3