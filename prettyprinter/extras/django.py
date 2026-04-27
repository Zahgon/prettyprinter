from enum import Enum, unique

from django.db.models.fields import NOT_PROVIDED
from django.db.models import Model, ForeignKey
from django.db.models.query import QuerySet

from ..prettyprinter import (
    MULTILINE_STRATEGY_HANG,
    build_fncall,
    pretty_call_alt,
    pretty_python_value,
    register_pretty,
    comment_doc,
    trailing_comment
)

from ..utils import find


QUERYSET_OUTPUT_SIZE = 20


@unique
class ModelVerbosity(Enum):
    UNSET = 1
    MINIMAL = 2
    SHORT = 3
    FULL = 4


def inc(value):
    pass


class dec(object):
    __slots__ = ('value', )

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        assert isinstance(other, dec)
        return self.value > other.value

    def __gt__(self, other):
        assert isinstance(other, dec)
        return self.value < other.value

    def __eq__(self, other):
        assert isinstance(other, dec)
        return self.value == other.value

    def __le__(self, other):
        assert isinstance(other, dec)
        return self.value >= other.value

    def __ge__(self, other):
        assert isinstance(other, dec)
        return self.value <= other.value

    __hash__ = None


def field_sort_key(field):
    pass


def pretty_base_model(instance, ctx):
    pass


def pretty_queryset(queryset, ctx):
    pass


def install():
    register_pretty(Model)(pretty_base_model)
    register_pretty(QuerySet)(pretty_queryset)
