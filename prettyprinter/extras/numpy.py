import ast
from distutils.version import LooseVersion
from math import ceil

from ..prettyprinter import (
    register_pretty,
    pretty_call_alt,
    pretty_bool,
    pretty_int,
    pretty_float
)


def pretty_ndarray(value, ctx):
    pass


def install():
    register_pretty("numpy.bool_")(pretty_bool)

    for name in [
        "uint8", "uint16", "uint32", "uint64",
        "int8", "int16", "int32", "int64",
    ]:
        register_pretty("numpy." + name)(pretty_int)

    for name in [
        "float16", "float32", "float64", "float128",
    ]:
        register_pretty("numpy." + name)(pretty_float)

    register_pretty("numpy.ndarray")(pretty_ndarray)
