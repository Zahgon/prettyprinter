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
        self._prettyprinter_ctx = kwargs.pop('prettyprinter_ctx')
        super().__init__(*args, **kwargs)

        # self.output should be assigned by the superclass
        assert isinstance(self.output, NoopStream)

        self._pending_wrapper = identity
        self._docparts = []

    def text(self, obj):
        super().text(obj)

        self._docparts.append(obj)

    def breakable(self, sep=' '):
        pass

    def begin_group(self, indent=0, open=''):
        pass

    def end_group(self, dedent=0, close=''):
        pass

    @contextmanager
    def indent(self, indent):
        """with statement support for indenting/dedenting."""
        pass

    def pretty(self, obj):
        pass


def wrap_repr_pretty(fn):
    pass


def pretty_repr_pretty(value, ctx):
    pass


def install():
    register_pretty(predicate=implements_repr_pretty)(pretty_repr_pretty)
