import operator
from itertools import islice

from lsp.types import *


def plus(*nums):
    return sum(nums)


def minus(num, *rest):
    nums = (num,) + rest

    if len(nums) == 1:
        return -nums[0]

    return nums[0] - sum(nums[1:])


def multiply(*nums):
    return reduce(operator.mul, nums, initializer=1)


def divide(num1, num2, *rest):
    return reduce(operator.truediv, (num1, num2) + rest)


def reduce(op, coll, initializer=None, sentinel=None):
    if initializer is None:
        acc = coll[0]
        coll = coll[1:]
    else:
        acc = initializer

    for i in coll:
        if acc == sentinel:
            return acc

        acc = op(acc, i)

    return acc


def lt(i1, i2, *rest):
    return reduce(operator.lt, (i1, i2) + rest, sentinel=False)


def le(i1, i2, *rest):
    return reduce(operator.le, (i1, i2) + rest, sentinel=False)


def gt(i1, i2, *rest):
    return reduce(operator.gt, (i1, i2) + rest, sentinel=False)


def ge(i1, i2, *rest):
    return reduce(operator.ge, (i1, i2) + rest, sentinel=False)


def not_eq(i1, i2, rest):
    return reduce(operator.ne, (i1, i2) + rest, sentinel=False)


def print_(i1, *rest):
    for i in (i1,) + rest:
        print i,

    return Nil()


def println(i1, *rest):
    for i in (i1,) + rest:
        print i,
    print

    return Nil()


def input(msg=''):
    return raw_input(msg)


def cons(item, coll):
    return List([item] + coll)


def concat(coll1, coll2):
    return List(coll1 + coll2)


def slice_list(coll, start, end, step=1):
    return List(islice(coll, start, end, step))


def is_empty(coll):
    return len(coll) == 0


def is_nil(item):
    return Boolean(isinstance(item, Nil))


def make_list(*items):
    return List(items)
