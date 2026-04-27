from .doctypes import (  # noqa
    AlwaysBreak,
    Concat,
    Contextual,
    Doc,
    FlatChoice,
    Fill,
    Group,
    Nest,
    Annotated,
    NIL,
    LINE,
    SOFTLINE,
    HARDLINE,
)
from .utils import intersperse  # noqa


def validate_doc(doc):
    pass


def group(doc):
    pass


def concat(docs):
    pass


def annotate(annotation, doc):
    pass


def contextual(fn):
    pass


def align(doc):
    def evaluator(indent, column, page_width, ribbon_width):
        pass
    pass


def hang(i, doc):
    pass


def nest(i, doc):
    pass


def fill(docs):
    pass


def always_break(doc):
    pass


def flat_choice(when_broken, when_flat):
    pass
