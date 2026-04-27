from contextlib import contextmanager

from .ipython import OriginalRepresentationPrinter
from ..utils import (
    compose,
    identity,
)
from ..prettyprinter import (
    register_pretty,
    pretty_python_value,
)
from ..doc import (
    HARDLINE,
    concat,
    contextual,
    flat_choice,
    group,
    nest
)


def implements_repr_pretty(instance):
    pass


class NoopStream:
    def write(self, value):
        pass


class CompatRepresentationPrinter(OriginalRepresentationPrinter):
    def __init__(self, *args, **kwargs):
        pass

    def text(self, obj):
        pass

    def breakable(self, sep=' '):
        pass

    def begin_group(self, indent=0, open=''):
        def wrapper(doc):
            pass
        pass

    def end_group(self, dedent=0, close=''):
        pass

    @contextmanager
    def indent(self, indent):
        pass

    def pretty(self, obj):
        pass


def wrap_repr_pretty(fn):
    def wrapped(value, ctx):
        def evaluator(indent, column, page_width, ribbon_width):
            pass
        pass
    pass


def pretty_repr_pretty(value, ctx):
    pass


def install():
    pass
