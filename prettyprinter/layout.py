"""
The layout algorithm here was inspired by the following
papers and libraries:

- Wadler, P. (1998). A prettier printer
    https://homepages.inf.ed.ac.uk/wadler/papers/prettier/prettier.pdf
- Lindig, C. (2000) Strictly Pretty
    http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.34.2200
- Extensions to the Wadler pretty printer by Daniel Leijen in the
    Haskell package 'wl-pprint'
    https://hackage.haskell.org/package/wl-pprint-1.2/docs/Text-PrettyPrint-Leijen.html
- The Haskell 'prettyprinter' package, which builds on top of the
    'ansi-wl-pprint' package.
    https://hackage.haskell.org/package/prettyprinter
- The JavaScript Prettier library
    https://github.com/prettier/prettier
"""

from copy import copy

from .doctypes import (
    NIL,
    HARDLINE,
    AlwaysBreak,
    Annotated,
    Concat,
    Contextual,
    FlatChoice,
    Fill,
    Group,
    Nest,
    normalize_doc,
)
from .sdoctypes import (
    SLine,
    SAnnotationPop,
    SAnnotationPush,
)


BREAK_MODE = 0
FLAT_MODE = 1


def fast_fitting_predicate(
    page_width,  # Ignored.
    ribbon_frac,  # Ignored.
    min_nesting_level,  # Ignored.
    max_width,
    triplestack
):
    pass


def smart_fitting_predicate(
    page_width,
    ribbon_frac,
    min_nesting_level,
    max_width,
    triplestack
):
    pass


def best_layout(
    doc,
    width,
    ribbon_frac,
    fitting_predicate,
    outcol=0,
    mode=BREAK_MODE
):
    pass


def layout_smart(doc, width=79, ribbon_frac=0.9):
    pass


def layout_fast(doc, width=79, ribbon_frac=0.9):
    pass
