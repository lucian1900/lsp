#!/usr/bin/env python

import os
import sys
from subprocess import call

from lsp import read

from pycparser import c_ast, CParser
from pycparser.c_generator import CGenerator

c_tmpl = '''
int main() {
    return 0;
}
'''

def gen_c(src, filename):
    parser = CParser()
    ast = parser.parse(c_tmpl, filename + '.c')

    main = ast.ext[0].body
    ret = main.block_items[0]

    ret.expr = c_ast.BinaryOp(
        src[0],
        c_ast.Constant('int', src[1]),
        c_ast.Constant('int', src[2])
    )

    gen = CGenerator()
    return gen.visit(ast)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            src = f.read()

        ast = read(src)

        c_name, _ = os.path.splitext(sys.argv[1])
        c_src = gen_c(ast, c_name)

        with open(c_name + '.c', 'w') as f:
            f.write(c_src)

        out = call(['cc', '-o', c_name, c_name + '.c'])
        if out != 0:
            print "Failed compilation: ", out
    else:
        print "Wrong args"
