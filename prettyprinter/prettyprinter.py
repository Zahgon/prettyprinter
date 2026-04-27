import inspect
import math
import re
import sys
import warnings
import ast
from collections import OrderedDict
from functools import singledispatch, partial
from itertools import chain, cycle
from traceback import format_exception
from types import (
    FunctionType,
    BuiltinFunctionType,
    ModuleType,
    SimpleNamespace,
)
from weakref import WeakKeyDictionary

from .doc import (
    always_break,
    annotate,
    concat,
    contextual,
    flat_choice,
    fill,
    group,
    nest,
    NIL,
    LINE,
    SOFTLINE,
    HARDLINE
)
from .doctypes import (
    Annotated,
    Doc
)

from .layout import layout_smart
from .syntax import Token
from .utils import identity, intersperse, take

PY_VERSION_INFO = sys.version_info
DICT_KEY_ORDER_SUPPORTED = PY_VERSION_INFO >= (3, 6)

UNSET_SENTINEL = object()

COMMA = annotate(Token.PUNCTUATION, ',')
COLON = annotate(Token.PUNCTUATION, ':')
ELLIPSIS = annotate(Token.PUNCTUATION, '...')

LPAREN = annotate(Token.PUNCTUATION, '(')
RPAREN = annotate(Token.PUNCTUATION, ')')

LBRACKET = annotate(Token.PUNCTUATION, '[')
RBRACKET = annotate(Token.PUNCTUATION, ']')

LBRACE = annotate(Token.PUNCTUATION, '{')
RBRACE = annotate(Token.PUNCTUATION, '}')

NEG_OP = annotate(Token.OPERATOR, '-')
MUL_OP = annotate(Token.OPERATOR, '*')
ADD_OP = annotate(Token.OPERATOR, '+')
ASSIGN_OP = annotate(Token.OPERATOR, '=')

WHITESPACE_PATTERN_TEXT = re.compile(r'(\s+)')
WHITESPACE_PATTERN_BYTES = re.compile(rb'(\s+)')

NONWORD_PATTERN_TEXT = re.compile(r'(\W+)')
NONWORD_PATTERN_BYTES = re.compile(rb'(\W+)')


# For dict keys
"""
(
    'aaaaaaaaaa'
    'aaaaaa'
)
"""
MULTILINE_STRATEGY_PARENS = 'MULTILINE_STRATEGY_PARENS'

# For dict values
"""
    'aaaaaaaaaa'
    'aaaaa'
"""
MULTILINE_STRATEGY_INDENTED = 'MULTILINE_STRATEGY_INDENTED'

# For sequence elements
"""
'aaaaaaaaa'
    'aaaaaa'
"""
MULTILINE_STRATEGY_HANG = 'MULTILINE_STRATEGY_HANG'

# For top level strs
"""
'aaaaaaaaa'
'aaaaaa'
"""
MULTILINE_STRATEGY_PLAIN = 'MULTILINE_STRATEGY_PLAIN'


IMPLICIT_MODULES = {
    '__main__',
    'builtins',
}


class CommentAnnotation:
    def __init__(self, value):
        pass

    def __repr__(self):
        pass


class _CommentedValue:
    def __init__(self, value, comment):
        pass


class _TrailingCommentedValue:
    def __init__(self, value, comment):
        pass


def comment_value(value, comment_text):
    pass


def comment_doc(doc, comment_text):
    pass


def comment(value, comment_text):
    pass


def trailing_comment(value, comment_text):
    pass


def unwrap_comments(value):
    pass


def is_commented(value):
    pass


def builtin_identifier(s):
    pass


def identifier(s):
    pass


def keyword_arg(s):
    pass


def general_identifier(s):
    pass


def classattr(cls, attrname):
    pass


class PrettyContext:
    """
    An immutable object used to track context during construction of
    layout primitives. An instance of PrettyContext is passed to every
    pretty printer definition.

    As a performance optimization, the ``visited`` set is implemented
    as mutable.
    """
    __slots__ = (
        'indent',
        'depth_left',
        'visited',
        'multiline_strategy',
        'max_seq_len',
        'sort_dict_keys',
        'user_ctx'
    )

    def __init__(
        self,
        indent,
        depth_left,
        visited=None,
        multiline_strategy=MULTILINE_STRATEGY_PLAIN,
        max_seq_len=1000,
        sort_dict_keys=False,
        user_ctx=None
    ):
        pass

    def _replace(self, **kwargs):
        pass

    def use_multiline_strategy(self, strategy):
        pass

    def assoc(self, key, value):
        pass

    def set(self, key, value):
        pass

    def get(self, key, default=None):
        pass

    def nested_call(self):
        pass

    def start_visit(self, value):
        pass

    def end_visit(self, value):
        pass

    def is_visited(self, value):
        pass


def _warn_about_bad_printer(pretty_fn, value, exc):
    pass


def _run_pretty(pretty_fn, value, ctx, trailing_comment=None):
    pass


_DEFERRED_DISPATCH_BY_NAME = {}


def get_deferred_key(type):
    pass


_PREDICATE_REGISTRY = []


def _repr_pretty(value, ctx):
    pass


_BASE_DISPATCH = partial(_run_pretty, _repr_pretty)

pretty_dispatch = singledispatch(_BASE_DISPATCH)


def pretty_python_value(value, ctx):
    pass


def register_pretty(type=None, predicate=None):
    def decorator(fn):
        pass
    pass


def is_registered(
    type,
    *,
    check_superclasses=False,
    check_deferred=True,
    register_deferred=True
):
    pass


def bracket(ctx, left, child, right):
    pass


def commentdoc(text):
    pass


def sequence_of_docs(ctx, left, docs, right, dangle=False, force_break=False):
    pass


def pretty_call(ctx, fn, *args, **kwargs):
    pass


def pretty_call_alt(ctx, fn, args=(), kwargs=()):
    pass


def build_fncall(
    ctx,
    fndoc,
    argdocs=(),
    kwargdocs=(),
    hug_sole_arg=False,
    trailing_comment=None,
):
    pass


@register_pretty(type)
def pretty_type(_type, ctx):
    pass


@register_pretty(FunctionType)
def pretty_function(fn, ctx):
    pass


@register_pretty(BuiltinFunctionType)  # Also includes bound methods.
def pretty_builtin_function(fn, ctx):
    pass


namedtuple_clsattrs = (
    '__slots__',
    '_make',
    '_replace',
    '_asdict'
)

c_namedtuple_identify_by_clsattrs = (
    'n_fields',
    'n_sequence_fields',
    'n_unnamed_fields'
)


def _is_namedtuple(value):
    pass


def _is_cnamedtuple(value):
    pass


def pretty_namedtuple(value, ctx, trailing_comment=None):
    pass


# Given a cnamedtuple value, returns a tuple
# of fieldnames. Each fieldname at ith index of
# the tuple corresponds to the ith element in the cnamedtuple.
def resolve_cnamedtuple_fieldnames(value):
    # The cnamedtuple repr returns a non-evaluable representation
    # of the value. It has the keyword arguments for each element
    # of the named tuple in the correct order. You can see the
    # source here:
    # https://github.com/python/cpython/blob/53b9e1a1c1d86187ad6fbee492b697ef8be74205/Objects/structseq.c#L168-L241
    # As long as the repr is implemented like that, we can count
    # on this function to work.
    pass


# Keys: classes/constructors
# Values: a tuple of fieldnames is resolving them was successful.
#         Otherwise, an exception that was raised when attempting
#         to resolve the fieldnames.
_cnamedtuple_fieldnames_by_class = WeakKeyDictionary()


# Examples of cnamedtuples:
# - return value of time.strptime()
# - return value of os.uname()
def pretty_cnamedtuple(value, ctx, trailing_comment=None):
    pass


@register_pretty(SimpleNamespace)
def pretty_simplenamespace(value, ctx, trailing_comment=None):
    pass


@register_pretty(tuple)
@register_pretty(list)
@register_pretty(set)
def pretty_bracketable_iterable(value, ctx, trailing_comment=None):
    pass


@register_pretty(frozenset)
def pretty_frozenset(value, ctx):
    pass


class _AlwaysSortable(object):
    __slots__ = ('value', )

    def __init__(self, value):
        pass

    def sortable_value(self):
        pass

    def __lt__(self, other):
        pass


@register_pretty(dict)
def pretty_dict(d, ctx, trailing_comment=None):
    pass


INF_FLOAT = float('inf')
NEG_INF_FLOAT = float('-inf')


@register_pretty(float)
def pretty_float(value, ctx):
    pass


@register_pretty(int)
def pretty_int(value, ctx):
    pass


@register_pretty(type(...))
def pretty_ellipsis(value, ctx):
    pass


@register_pretty(bool)
def pretty_bool(value, ctx):
    pass


NONE_DOC = annotate(Token.KEYWORD_CONSTANT, 'None')


@register_pretty(type(None))
def pretty_none(value, ctx):
    pass


SINGLE_QUOTE_TEXT = "'"
SINGLE_QUOTE_BYTES = b"'"

DOUBLE_QUOTE_TEXT = '"'
DOUBLE_QUOTE_BYTES = b'"'


def determine_quote_strategy(s):
    pass


def escape_str_for_quote(use_quote, s):
    pass


STR_LITERAL_ESCAPES = re.compile(
    r'''((?:\\[\\abfnrtv"'])|'''
    r'(?:\\N\{.*?\})|'
    r'(?:\\u[a-fA-F0-9]{4})|'
    r'(?:\\U[a-fA-F0-9]{8})|'
    r'(?:\\x[a-fA-F0-9]{2})|'
    r'(?:\\[0-7]{1,3}))'
)


def highlight_escapes(s):
    pass


def pretty_single_line_str(s, indent, use_quote=None):
    pass


def split_at(idx, sequence):
    pass


def escaped_len(s, use_quote):
    pass


def str_to_lines(max_len, use_quote, s, pattern=None):
    pass


@register_pretty(str)
@register_pretty(bytes)
def pretty_str(s, ctx, split_pattern=None):
    # Subclasses of str/bytes
    # will be printed as StrSubclass('the actual string')
    def evaluator(indent, column, page_width, ribbon_width):
        pass
    pass


def _pretty_recursion(value):
    pass


def python_to_sdocs(
    value,
    indent,
    width,
    depth,
    ribbon_width,
    max_seq_len,
    sort_dict_keys
):
    pass
