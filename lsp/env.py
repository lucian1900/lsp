import sys
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
    'rest': rest,
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
}, macros={
    'if': if_macro,
    'fn': fn_macro,
    'def': def_macro,
    'quote': quote_macro,
    'quasiquote': quasiquote_macro,
    'unquote': unquote_macro,
    'unquote-splicing': unquote_splicing_macro,
    'defmacro': defmacro_macro,
    'do': do_macro,
    '.': call_method,
})

# TODO use current env, not top
top['eval'] = partial(eval, env=top)
