def parse(s):

	return result

def tokenize(s):
	'''
	>>> tokenize("(1, 2)")
	['(', '1', '2', ')']
	'''

	tokens = {
		'(': ' ( ',
		')': ' ) ',
		',': ' ',
	}

	for tok, rep in tokens.items():
		s = s.replace(tok, rep)

	return s.split()

if __name__ == '__main__':
	import doctest
	doctest.testmod()