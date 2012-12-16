import sys
from os.path import join, dirname

from lsp.parser import read
from lsp.forms import eval
from lsp.env import top


def lsp(source, env=top):
    return eval(read('(do {0})'.format(source)), env=env)

def _init():
    # load prelude
    with open(join(dirname(__file__), 'prelude.lsp')) as f:
        lsp(f.read())
_init()
del _init


def main():
    if len(sys.argv) == 1:
        while True:
            try:
                print lsp(raw_input('> '))
            except Exception, e:
                print e
    elif len(sys.argv) == 2:
        with open(sys.argv[1]) as f:
            lsp(f.read())
    elif len(sys.argv) == 3:
        if sys.argv[1] == '-c':
            print lsp(sys.argv[2])
        else:
            print "Only -c supported so far"
    else:
        print "Wrong args"

