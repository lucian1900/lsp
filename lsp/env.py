import sys
import pdb
import operator
from functools import partial

from lsp.forms import *
from lsp.builtins import *


top = Env({
    # Numbers
    '+': plus,
    '-': minus,
    '*': multiply,
    '/': divide,
    '<': lt,
    '>': gt,
    '<=': le,
    '>=': ge,

    # Bool
    '=': operator.eq,
    'not': operator.not_,
    'not=': not_eq,

    # Core
    'apply': apply,
    'nil?': is_nil,

    # Lists
    'list': make_list,
    'cons': cons,
    'concat': concat,
    'empty?': is_empty,
    'slice': slice_list,
    'len': len,

    # IO
    'print': print_,
    'println': println,
    'input': input,
    'exit': sys.exit,

    'debugger': pdb.set_trace,
}, macros={
    # Special forms
    'if': if_,
    'fn': fn,
    'def': def_,
    'quote': quote,
    'quasiquote': quasiquote,
    'unquote': unquote,
    'unquote-splicing': unquote_splicing,
    'defmacro': defmacro,
    'do': do,
    '.': call_method,
})

# TODO use current env, not top
top['eval'] = partial(eval, env=top)
