from attr import Factory, NOTHING
from prettyprinter.prettyprinter import pretty_call_alt, register_pretty


def is_instance_of_attrs_class(value):
    pass


def pretty_attrs(value, ctx):
    pass


def install():
    register_pretty(predicate=is_instance_of_attrs_class)(pretty_attrs)
