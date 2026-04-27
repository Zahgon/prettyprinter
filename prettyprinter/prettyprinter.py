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
        assert isinstance(value, str)
        self.value = value

    def __repr__(self):
        return 'ValueComment({})'.format(repr(self.value))


class _CommentedValue:
    def __init__(self, value, comment):
        self.value = value
        self.comment = comment


class _TrailingCommentedValue:
    def __init__(self, value, comment):
        self.value = value
        self.comment = comment


def comment_value(value, comment_text):
    """Annotates a Python value with a comment text.

    prettyprinter will inspect and strip the annotation
    during the layout process, and handle rendering the comment
    next to the value in the output.

    It is highly unlikely you need to call this function. Use
    ``comment`` instead, which works in almost all cases.
    """
    return _CommentedValue(value, comment_text)


def comment_doc(doc, comment_text):
    """Annotates a Doc with a comment; used by the layout algorithm.

    You don't need to call this unless you're doing something low-level
    with Docs; use ``comment`` instead.

    ``prettyprinter`` will make sure the parent (or top-level) handler
    will render the comment in a proper way. E.g. if ``doc``
    represents an element in a list, then the ``list`` pretty
    printer will handle where to place the comment.
    """
    return annotate(CommentAnnotation(comment_text), doc)


def comment(value, comment_text):
    """Annotates a value or a Doc with a comment.

    When printed by prettyprinter, the comment will be
    rendered next to the value or Doc.
    """
    if isinstance(value, Doc):
        return comment_doc(value, comment_text)
    return comment_value(value, comment_text)


def trailing_comment(value, comment_text):
    """Annotates a value with a comment text, so that
    the comment will be rendered "trailing", e.g. in place
    of the last element in a list, set or tuple, or after
    the last argument in a function.

    This will force the rendering of ``value`` to be broken
    to multiple lines as Python does not have inline comments.

    >>> trailing_comment(['value'], '...and more')
    [
        'value',
        # ...and more
    ]
    """
    return _TrailingCommentedValue(value, comment_text)


def unwrap_comments(value):
    comment = None
    trailing_comment = None

    while isinstance(value, (_CommentedValue, _TrailingCommentedValue)):
        if isinstance(value, _CommentedValue):
            comment = value.comment
            value = value.value
        elif isinstance(value, _TrailingCommentedValue):
            trailing_comment = value.comment
            value = value.value

    return (value, comment, trailing_comment)


def is_commented(value):
    return (
        isinstance(value, Annotated) and
        isinstance(value.annotation, CommentAnnotation)
    )


def builtin_identifier(s):
    return annotate(Token.NAME_BUILTIN, s)


def identifier(s):
    return annotate(Token.NAME_FUNCTION, s)


def keyword_arg(s):
    return annotate(Token.NAME_VARIABLE, s)


def general_identifier(s):
    if callable(s):
        module, qualname = s.__module__, s.__qualname__
        if module is None and hasattr(s, '__self__'):
            # Builtin methods on builtin types.
            module = type(s.__self__).__module__

        if module in IMPLICIT_MODULES:
            if module == 'builtins':
                return builtin_identifier(qualname)
            return identifier(qualname)
        return identifier('{}.{}'.format(module, qualname))
    return identifier(s)


def classattr(cls, attrname):
    return concat([
        general_identifier(cls),
        identifier('.{}'.format(attrname))
    ])


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
        self.indent = indent
        self.depth_left = depth_left
        self.multiline_strategy = multiline_strategy
        self.max_seq_len = max_seq_len
        self.sort_dict_keys = sort_dict_keys

        if visited is None:
            visited = set()
        self.visited = visited

        self.user_ctx = user_ctx or {}

    def _replace(self, **kwargs):
        passed_keys = set(kwargs.keys())
        fieldnames = type(self).__slots__
        assert passed_keys.issubset(set(fieldnames))
        return PrettyContext(
            **{
                k: (
                    kwargs[k]
                    if k in passed_keys
                    else getattr(self, k)
                )
                for k in fieldnames
            }
        )

    def use_multiline_strategy(self, strategy):
        return self._replace(multiline_strategy=strategy)

    def assoc(self, key, value):
        """
        Return a modified PrettyContext with ``key`` set to ``value``
        """
        pass

    def set(self, key, value):
        pass

    def get(self, key, default=None):
        return self.user_ctx.get(key, default)

    def nested_call(self):
        return self._replace(depth_left=self.depth_left - 1)

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
    return type.__module__ + '.' + type.__qualname__


_PREDICATE_REGISTRY = []


def _repr_pretty(value, ctx):
    pass


_BASE_DISPATCH = partial(_run_pretty, _repr_pretty)

pretty_dispatch = singledispatch(_BASE_DISPATCH)


def pretty_python_value(value, ctx):
    comment = None
    trailing_comment = None

    value, comment, trailing_comment = unwrap_comments(value)

    is_registered(
        type(value),
        check_superclasses=True,
        check_deferred=True,
        register_deferred=True
    )

    if trailing_comment:
        doc = pretty_dispatch(
            value,
            ctx,
            trailing_comment=trailing_comment
        )
    else:
        doc = pretty_dispatch(
            value,
            ctx
        )

    if comment:
        return comment_doc(
            doc,
            comment
        )
    return doc


def register_pretty(type=None, predicate=None):
    """Returns a decorator that registers the decorated function
    as the pretty printer for instances of ``type``.

    :param type: the type to register the pretty printer for, or a ``str``
                 to indicate the module and name, e.g.: ``'collections.Counter'``.
    :param predicate: a predicate function that takes one argument
                      and returns a boolean indicating if the value
                      should be handled by the registered pretty printer.

    Only one of ``type`` and ``predicate`` may be supplied. That means
    that ``predicate`` will be run on unregistered types only.

    The decorated function must accept exactly two positional arguments:

    - ``value`` to pretty print, and
    - ``ctx``, a context value.

    Here's an example of the pretty printer for OrderedDict:

    .. code:: python

        from collections import OrderedDict
        from prettyprinter import register_pretty, pretty_call

        @register_pretty(OrderedDict)
        def pretty_orderreddict(value, ctx):
            return pretty_call(ctx, OrderedDict, list(value.items()))
    """

    if type is None and predicate is None:
        raise ValueError(
            "You must provide either the 'type' or 'predicate' argument."
        )

    if type is not None and predicate is not None:
        raise ValueError(
            "You must provide either the 'type' or 'predicate' argument,"
            "but not both"
        )

    if predicate is not None:
        if not callable(predicate):
            raise ValueError(
                "Expected a callable for 'predicate', got {}".format(
                    repr(predicate)
                )
            )

    def decorator(fn):
        pass
    return decorator


def is_registered(
    type,
    *,
    check_superclasses=False,
    check_deferred=True,
    register_deferred=True
):
    if not check_deferred and register_deferred:
        raise ValueError(
            'register_deferred may not be True when check_deferred is False'
        )

    if type in pretty_dispatch.registry:
        return True

    if check_deferred:
        # Check deferred printers for the type exactly.
        deferred_key = get_deferred_key(type)
        if deferred_key in _DEFERRED_DISPATCH_BY_NAME:
            if register_deferred:
                deferred_dispatch = _DEFERRED_DISPATCH_BY_NAME.pop(
                    deferred_key
                )
                register_pretty(type)(deferred_dispatch)
            return True

    if not check_superclasses:
        return False

    if check_deferred:
        # Check deferred printers for supertypes.
        for supertype in type.__mro__[1:]:
            deferred_key = get_deferred_key(supertype)
            if deferred_key in _DEFERRED_DISPATCH_BY_NAME:
                if register_deferred:
                    deferred_dispatch = _DEFERRED_DISPATCH_BY_NAME.pop(
                        deferred_key
                    )
                    register_pretty(supertype)(deferred_dispatch)
                return True
    return pretty_dispatch.dispatch(type) is not _BASE_DISPATCH


def bracket(ctx, left, child, right):
    pass


def commentdoc(text):
    """Returns a Doc representing a comment `text`. `text` is
    treated as words, and any whitespace may be used to break
    the comment to multiple lines."""
    if not text:
        raise ValueError(
            'Expected non-empty comment str, got {}'.format(repr(text))
        )

    commentlines = []
    for line in text.splitlines():
        alternating_words_ws = list(filter(None, WHITESPACE_PATTERN_TEXT.split(line)))
        starts_with_whitespace = bool(
            WHITESPACE_PATTERN_TEXT.match(alternating_words_ws[0])
        )

        if starts_with_whitespace:
            prefix = alternating_words_ws[0]
            alternating_words_ws = alternating_words_ws[1:]
        else:
            prefix = NIL

        if len(alternating_words_ws) % 2 == 0:
            # The last part must be whitespace.
            alternating_words_ws = alternating_words_ws[:-1]

        for idx, tup in enumerate(zip(alternating_words_ws, cycle([False, True]))):
            part, is_ws = tup
            if is_ws:
                alternating_words_ws[idx] = flat_choice(
                    when_flat=part,
                    when_broken=always_break(
                        concat([
                            HARDLINE,
                            '# ',
                        ])
                    )
                )

        commentlines.append(
            concat([
                '# ',
                prefix,
                fill(alternating_words_ws)
            ])
        )

    outer = identity

    if len(commentlines) > 1:
        outer = always_break

    return annotate(
        Token.COMMENT_SINGLE,
        outer(concat(intersperse(HARDLINE, commentlines)))
    )


def sequence_of_docs(ctx, left, docs, right, dangle=False, force_break=False):
    pass


def pretty_call(ctx, fn, *args, **kwargs):
    """Returns a Doc that represents a function call to :keyword:`fn` with
    the remaining positional and keyword arguments.

    You can only use this function on Python 3.6+. On Python 3.5, the order
    of keyword arguments is not maintained, and you have to use
    :func:`~prettyprinter.pretty_call_alt`.

    Given an arbitrary context ``ctx``,::

        pretty_call(ctx, sorted, [7, 4, 5], reverse=True)

    Will result in output::

        sorted([7, 4, 5], reverse=True)

    The layout algorithm will automatically break the call to multiple
    lines if needed::

        sorted(
            [7, 4, 5],
            reverse=True
        )

    ``pretty_call`` automatically handles syntax highlighting.

    :param ctx: a context value
    :type ctx: prettyprinter.prettyprinter.PrettyContext
    :param fn: a callable
    :param args: positional arguments to render to the call
    :param kwargs: keyword arguments to render to the call
    :returns: :class:`~prettyprinter.doc.Doc`
    """
    return pretty_call_alt(ctx, fn, args, kwargs)


def pretty_call_alt(ctx, fn, args=(), kwargs=()):
    """Returns a Doc that represents a function call to :keyword:`fn` with
    the ``args`` and ``kwargs``.

    Given an arbitrary context ``ctx``,::

        pretty_call_alt(ctx, sorted, args=([7, 4, 5], ), kwargs=[('reverse', True)])

    Will result in output::

        sorted([7, 4, 5], reverse=True)

    The layout algorithm will automatically break the call to multiple
    lines if needed::

        sorted(
            [7, 4, 5],
            reverse=True
        )

    ``pretty_call_alt`` automatically handles syntax highlighting.

    :param ctx: a context value
    :type ctx: prettyprinter.prettyprinter.PrettyContext
    :param fn: a callable
    :param args: a ``tuple`` of positional arguments to render to the call
    :param kwargs: keyword arguments to render to the call. Either an instance
                   of ``OrderedDict``, or an iterable of two-tuples, where the
                   first element is a `str` (key), and the second is the Python
                   value for that keyword argument.
    :returns: :class:`~prettyprinter.doc.Doc`
    """

    fndoc = general_identifier(fn)

    if ctx.depth_left <= 0:
        return concat([fndoc, LPAREN, ELLIPSIS, RPAREN])

    if not kwargs and len(args) == 1:
        sole_arg = args[0]
        unwrapped_sole_arg, _comment, _trailing_comment = unwrap_comments(args[0])
        if type(unwrapped_sole_arg) in (list, dict, tuple):
            return build_fncall(
                ctx,
                fndoc,
                argdocs=[pretty_python_value(sole_arg, ctx)],
                hug_sole_arg=True,
            )

    nested_ctx = (
        ctx
        .nested_call()
        .use_multiline_strategy(MULTILINE_STRATEGY_HANG)
    )

    if not DICT_KEY_ORDER_SUPPORTED and isinstance(kwargs, dict):
        warnings.warn(
            "A dict was passed to pretty_call_alt to represent kwargs, "
            "but Python 3.5 doesn't maintain key order for dicts. The order "
            "of keyword arguments will be undefined in the output. "
            "To fix this, pass a list of two-tuples or an instance of "
            "OrderedDict instead.",
            UserWarning
        )

    kwargitems = (
        kwargs.items()
        if isinstance(kwargs, (OrderedDict, dict))
        else kwargs
    )

    return build_fncall(
        ctx,
        fndoc,
        argdocs=(
            pretty_python_value(arg, nested_ctx)
            for arg in args
        ),
        kwargdocs=(
            (kwarg, pretty_python_value(v, nested_ctx))
            for kwarg, v in kwargitems
        ),
    )


def build_fncall(
    ctx,
    fndoc,
    argdocs=(),
    kwargdocs=(),
    hug_sole_arg=False,
    trailing_comment=None,
):
    """Builds a doc that looks like a function call,
    from docs that represent the function, arguments
    and keyword arguments.

    If ``hug_sole_arg`` is True, and the represented
    functional call is done with a single non-keyword
    argument, the function call parentheses will hug
    the sole argument doc without newlines and indentation
    in break mode. This makes a difference in calls
    like this::

        > hug_sole_arg = False
        frozenset(
            [
                1,
                2,
                3,
                4,
                5
            ]
        )
        > hug_sole_arg = True
        frozenset([
            1,
            2,
            3,
            4,
            5,
        ])

    If ``trailing_comment`` is provided, the text is
    rendered as a comment after the last argument and
    before the closing parenthesis. This will force
    the function call to be broken to multiple lines.
    """
    if callable(fndoc):
        fndoc = general_identifier(fndoc)

    has_comment = bool(trailing_comment)

    argdocs = list(argdocs)
    kwargdocs = list(kwargdocs)

    kwargdocs = [
        # Propagate any comments to the kwarg doc.
        (
            comment_doc(
                concat([
                    keyword_arg(binding),
                    ASSIGN_OP,
                    doc.doc
                ]),
                doc.annotation.value
            )
            if is_commented(doc)
            else concat([
                keyword_arg(binding),
                ASSIGN_OP,
                doc
            ])
        )
        for binding, doc in kwargdocs
    ]

    if not (argdocs or kwargdocs):
        return concat([
            fndoc,
            LPAREN,
            RPAREN,
        ])

    if (
        hug_sole_arg and
        not kwargdocs and
        len(argdocs) == 1 and
        not is_commented(argdocs[0])
    ):
        return group(
            concat([
                fndoc,
                LPAREN,
                argdocs[0],
                RPAREN
            ])
        )

    allarg_docs = [*argdocs, *kwargdocs]

    if trailing_comment:
        allarg_docs.append(commentdoc(trailing_comment))

    parts = []

    for idx, doc in enumerate(allarg_docs):
        last = idx == len(allarg_docs) - 1

        if is_commented(doc):
            has_comment = True
            comment_str = doc.annotation.value
            doc = doc.doc
        else:
            comment_str = None

        part = concat([doc, NIL if last else COMMA])

        if comment_str:
            part = group(
                flat_choice(
                    when_flat=concat([
                        part,
                        '  ',
                        commentdoc(comment_str)
                    ]),
                    when_broken=concat([
                        commentdoc(comment_str),
                        HARDLINE,
                        part,
                    ]),
                )
            )

        if not last:
            part = concat([part, HARDLINE if has_comment else LINE])

        parts.append(part)

    outer = (
        always_break
        if has_comment
        else group
    )

    return outer(
        concat([
            fndoc,
            LPAREN,
            nest(
                ctx.indent,
                concat([
                    SOFTLINE,
                    concat(parts),
                ])
            ),
            SOFTLINE,
            RPAREN
        ])
    )


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
    expr_node = ast.parse(repr(value), mode='eval')
    call_node = expr_node.body
    return tuple(
        keyword_node.arg
        for keyword_node in call_node.keywords
    )


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
        self.value = value

    def sortable_value(self):
        pass

    def __lt__(self, other):
        try:
            return self.value < other.value
        except TypeError:
            return self.sortable_value() < other.sortable_value()


@register_pretty(dict)
def pretty_dict(d, ctx, trailing_comment=None):
    pass


INF_FLOAT = float('inf')
NEG_INF_FLOAT = float('-inf')


@register_pretty(float)
def pretty_float(value, ctx):
    constructor = type(value)

    if ctx.depth_left == 0:
        return pretty_call_alt(ctx, constructor, args=(..., ))

    if value == INF_FLOAT:
        return pretty_call_alt(ctx, constructor, args=('inf', ))
    elif value == NEG_INF_FLOAT:
        return pretty_call_alt(ctx, constructor, args=('-inf', ))
    elif math.isnan(value):
        return pretty_call_alt(ctx, constructor, args=('nan', ))

    doc = annotate(Token.NUMBER_FLOAT, repr(value))
    if constructor is float:
        return doc

    return build_fncall(ctx, general_identifier(constructor), argdocs=(doc, ))


@register_pretty(int)
def pretty_int(value, ctx):
    constructor = type(value)
    if ctx.depth_left == 0:
        return pretty_call_alt(ctx, constructor, args=(..., ))

    doc = annotate(Token.NUMBER_INT, repr(value))
    if constructor is int:
        return doc

    return build_fncall(ctx, general_identifier(constructor), argdocs=(doc, ))


@register_pretty(type(...))
def pretty_ellipsis(value, ctx):
    pass


@register_pretty(bool)
def pretty_bool(value, ctx):
    constructor = type(value)

    doc = annotate(Token.KEYWORD_CONSTANT, 'True' if value else 'False')
    if constructor is bool:
        return doc
    return build_fncall(
        ctx,
        general_identifier(constructor),
        argdocs=(doc, )
    )


NONE_DOC = annotate(Token.KEYWORD_CONSTANT, 'None')


@register_pretty(type(None))
def pretty_none(value, ctx):
    pass


SINGLE_QUOTE_TEXT = "'"
SINGLE_QUOTE_BYTES = b"'"

DOUBLE_QUOTE_TEXT = '"'
DOUBLE_QUOTE_BYTES = b'"'


def determine_quote_strategy(s):
    if isinstance(s, str):
        single_quote = SINGLE_QUOTE_TEXT
        double_quote = DOUBLE_QUOTE_TEXT
    else:
        single_quote = SINGLE_QUOTE_BYTES
        double_quote = DOUBLE_QUOTE_BYTES

    contains_single = single_quote in s
    contains_double = double_quote in s

    if not contains_single:
        return SINGLE_QUOTE_TEXT

    if not contains_double:
        return DOUBLE_QUOTE_TEXT

    assert contains_single and contains_double

    single_count = s.count(single_quote)
    double_count = s.count(double_quote)

    if single_count <= double_count:
        return SINGLE_QUOTE_TEXT

    return DOUBLE_QUOTE_TEXT


def escape_str_for_quote(use_quote, s):
    escaped_with_quotes = repr(s)
    repr_used_quote = escaped_with_quotes[-1]

    # string may have a prefix
    first_quote_at_index = escaped_with_quotes.find(repr_used_quote)
    repr_escaped = escaped_with_quotes[first_quote_at_index + 1:-1]

    if repr_used_quote == use_quote:
        # repr produced the quotes we wanted -
        # escaping is correct.
        return repr_escaped

    # repr produced different quotes, which escapes
    # alternate quotes.
    if use_quote == SINGLE_QUOTE_TEXT:
        # repr used double quotes
        return (
            repr_escaped
            .replace('\\"', DOUBLE_QUOTE_TEXT)
            .replace(SINGLE_QUOTE_TEXT, "\\'")
        )
    else:
        # repr used single quotes
        return (
            repr_escaped
            .replace("\\'", SINGLE_QUOTE_TEXT)
            .replace(DOUBLE_QUOTE_TEXT, '\\"')
        )


STR_LITERAL_ESCAPES = re.compile(
    r'''((?:\\[\\abfnrtv"'])|'''
    r'(?:\\N\{.*?\})|'
    r'(?:\\u[a-fA-F0-9]{4})|'
    r'(?:\\U[a-fA-F0-9]{8})|'
    r'(?:\\x[a-fA-F0-9]{2})|'
    r'(?:\\[0-7]{1,3}))'
)


def highlight_escapes(s):
    if not s:
        return NIL

    matches = STR_LITERAL_ESCAPES.split(s)

    starts_with_match = bool(STR_LITERAL_ESCAPES.match(matches[0]))

    docs = []
    for part, is_escaped in zip(
        matches,
        cycle([starts_with_match, not starts_with_match])
    ):
        if not part:
            continue

        docs.append(
            annotate(
                (
                    Token.STRING_ESCAPE
                    if is_escaped
                    else Token.LITERAL_STRING
                ),
                part
            )
        )

    return concat(docs)


def pretty_single_line_str(s, indent, use_quote=None):
    prefix = (
        annotate(Token.STRING_AFFIX, 'b')
        if isinstance(s, bytes)
        else ''
    )

    if use_quote is None:
        use_quote = determine_quote_strategy(s)

    escaped = escape_str_for_quote(use_quote, s)
    escapes_highlighted = highlight_escapes(escaped)

    return concat([
        prefix,
        annotate(
            Token.LITERAL_STRING,
            concat([
                use_quote,
                escapes_highlighted,
                use_quote
            ])
        )
    ])


def split_at(idx, sequence):
    return (sequence[:idx], sequence[idx:])


def escaped_len(s, use_quote):
    return len(escape_str_for_quote(use_quote, s))


def str_to_lines(max_len, use_quote, s, pattern=None):
    assert max_len > 0, "max_len must be positive"
    if len(s) <= max_len:
        if s:
            yield s
        return

    if pattern is None:

        if isinstance(s, str):
            whitespace_pattern = WHITESPACE_PATTERN_TEXT
            nonword_pattern = NONWORD_PATTERN_TEXT
        else:
            assert isinstance(s, bytes)
            whitespace_pattern = WHITESPACE_PATTERN_BYTES
            nonword_pattern = NONWORD_PATTERN_BYTES

        alternating_words_ws = whitespace_pattern.split(s)
        pattern = whitespace_pattern

        if len(alternating_words_ws) <= 1:
            # no whitespace: try splitting with nonword pattern.
            alternating_words_ws = nonword_pattern.split(s)
            pattern = nonword_pattern

    else:
        alternating_words_ws = pattern.split(s)

    if isinstance(s, str):
        empty = ''
    else:
        assert isinstance(s, bytes)
        empty = b''

    starts_with_whitespace = bool(pattern.match(alternating_words_ws[0]))

    # List[Tuple[str, bool]]
    # The boolean associated with each part indicates if it is a
    # whitespce/non-word part or not.
    tagged_alternating = iter(
        zip(
            alternating_words_ws,
            cycle([starts_with_whitespace, not starts_with_whitespace])
        )
    )

    next_part = None
    next_is_whitespace = None

    curr_line_parts = []
    curr_line_len = 0

    while True:
        if not next_part:
            try:
                next_part, next_is_whitespace = next(tagged_alternating)
            except StopIteration:
                break

            if not next_part:
                continue

        # We think of the current line as including next_part,
        # but as an optimization we don't append to curr_line_parts,
        # as we often would have to pop it back out.
        next_escaped_len = escaped_len(next_part, use_quote)
        curr_line_len += next_escaped_len

        if curr_line_len == max_len:
            if not next_is_whitespace and len(curr_line_parts) > 1:
                yield empty.join(curr_line_parts)
                curr_line_parts = []
                curr_line_len = 0
                # Leave next_part and next_is_whitespace as is
                # to be processed on next iteration
            else:
                yield empty.join(chain(curr_line_parts, [next_part]))
                curr_line_parts = []
                curr_line_len = 0
                next_part = None
                next_is_whitespace = None
        elif curr_line_len > max_len:
            if not next_is_whitespace and curr_line_parts:
                yield empty.join(curr_line_parts)
                curr_line_parts = []
                curr_line_len = 0
                # Leave next_part and next_is_whitespace as is
                # to be processed on next iteration
                continue

            remaining_len = max_len - (curr_line_len - next_escaped_len)
            this_line_part, next_line_part = split_at(max(remaining_len, 0), next_part)
            if this_line_part:
                curr_line_parts.append(this_line_part)

            if curr_line_parts:
                yield empty.join(curr_line_parts)

            curr_line_parts = []
            curr_line_len = 0

            if next_line_part:
                next_part = next_line_part
            else:
                next_part = None
        else:
            curr_line_parts.append(next_part)
            next_part = None
            next_is_whitespace = None

    if curr_line_parts:
        yield empty.join(curr_line_parts)


@register_pretty(str)
@register_pretty(bytes)
def pretty_str(s, ctx, split_pattern=None):
    # Subclasses of str/bytes
    # will be printed as StrSubclass('the actual string')
    constructor = type(s)
    is_native_type = constructor in (str, bytes)

    if ctx.depth_left == 0:
        return pretty_call_alt(ctx, constructor, args=(..., ))

    multiline_strategy = ctx.multiline_strategy
    prettyprinter_indent = ctx.indent

    def evaluator(indent, column, page_width, ribbon_width):
        pass

    return contextual(evaluator)


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
    if depth is None:
        depth = float('inf')

    doc = pretty_python_value(
        value,
        ctx=PrettyContext(
            indent=indent,
            depth_left=depth,
            visited=set(),
            max_seq_len=max_seq_len,
            sort_dict_keys=sort_dict_keys
        )
    )

    if is_commented(doc):
        doc = group(
            flat_choice(
                when_flat=concat([
                    doc,
                    '  ',
                    commentdoc(doc.annotation.value),
                ]),
                when_broken=concat([
                    commentdoc(doc.annotation.value),
                    HARDLINE,
                    doc
                ])
            )
        )

    ribbon_frac = min(1.0, ribbon_width / width)

    return layout_smart(doc, width=width, ribbon_frac=ribbon_frac)
