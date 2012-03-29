class Symbol(str): pass
class List(list): pass

def eval(sexp):
	try:
		if len(sexp) == 0:
			raise ValueError("Missing function expression")
	except:

	
	return sexp

def read(tokens):
	'''Lisp reader

	>>> read(['1'])
	1

	>>> read(['(', '1', '2', ')'])
	[1, 2]

	>>> read(['(', '+', '1', '2', ')'])
	['+', 1, 2]
	'''

	try:
		tok = tokens[0]
		tokens = tokens[1:]
	except IndexError:
		raise SyntaxError("Unexpected EOF")

	if tok == '(':
		import pdb; pdb.set_trace()
		try:
			end = tokens.index(')')
		except ValueError:
			raise SyntaxError("Expected ')'")

		in_toks = tokens[:end]

		exp = List()
		while in_toks: # depends on mutation inside parse(). nasty
			exp.append(read(in_toks))
			exp.pop(0)

		return exp

	try:
		atom = int(tok)
	except ValueError:
		return Symbol(tok)
	else:
		return atom # int after all

def tokenize(source):
	'''Split by parens, consider commas whitespace
	Inspired by Peter Norvig's lis.py

	>>> tokenize("(1, 2)")
	['(', '1', '2', ')']
	'''

	tokens = {
		'(': ' ( ',
		')': ' ) ',
		',': ' ',
	}

	for tok, rep in tokens.items():
		source = source.replace(tok, rep)

	return source.split()

if __name__ == '__main__':
	import doctest
	doctest.testmod()