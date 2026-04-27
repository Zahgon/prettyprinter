from collections import OrderedDict
from dataclasses import (
    fields,
    MISSING,
)

from prettyprinter.prettyprinter import pretty_call, register_pretty


def is_instance_of_dataclass(value):
    pass


def pretty_dataclass_instance(value, ctx):
    pass


def install():
    register_pretty(predicate=is_instance_of_dataclass)(pretty_dataclass_instance)
