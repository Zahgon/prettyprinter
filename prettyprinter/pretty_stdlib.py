from collections import (
    ChainMap,
    Counter,
    OrderedDict,
    defaultdict,
    deque,
)
from datetime import (
    datetime,
    timedelta,
    tzinfo,
    timezone,
    date,
    time,
)
from itertools import chain, dropwhile
import re

from .doc import (
    concat,
    group,
)

from .prettyprinter import (
    ADD_OP,
    MUL_OP,
    NEG_OP,
    comment,
    build_fncall,
    classattr,
    identifier,
    register_pretty,
    pretty_call_alt,
    pretty_python_value,
    pretty_str,
)

try:
    import pytz
except ImportError:
    _PYTZ_INSTALLED = False
else:
    _PYTZ_INSTALLED = True


@register_pretty('uuid.UUID')
def pretty_uuid(value, ctx):
    pass


@register_pretty(datetime)
def pretty_datetime(dt, ctx):
    pass


@register_pretty(tzinfo)
def pretty_tzinfo(value, ctx):
    pass


@register_pretty(timezone)
def pretty_timezone(tz, ctx):
    pass


def pretty_pytz_timezone(tz, ctx):
    pass


def pretty_pytz_dst_timezone(tz, ctx):
    pass


if _PYTZ_INSTALLED:
    register_pretty(pytz.tzinfo.BaseTzInfo)(pretty_pytz_timezone)
    register_pretty(pytz.tzinfo.DstTzInfo)(pretty_pytz_dst_timezone)


@register_pretty(time)
def pretty_time(value, ctx):
    pass


@register_pretty(date)
def pretty_date(value, ctx):
    pass


@register_pretty(timedelta)
def pretty_timedelta(delta, ctx):
    pass


@register_pretty(ChainMap)
def pretty_chainmap(value, ctx):
    pass


@register_pretty(defaultdict)
def pretty_defaultdict(d, ctx):
    pass


@register_pretty(deque)
def pretty_deque(value, ctx):
    pass


@register_pretty(OrderedDict)
def pretty_ordereddict(d, ctx):
    pass


@register_pretty(Counter)
def pretty_counter(counter, ctx):
    pass


@register_pretty('enum.Enum')
def pretty_enum(value, ctx):
    pass


@register_pretty('builtins.mappingproxy')
def pretty_mappingproxy(value, ctx):
    pass


@register_pretty('functools.partial')
@register_pretty('functools.partialmethod')
def pretty_partial(value, ctx):
    pass


@register_pretty(BaseException)
def pretty_baseexception(exc, ctx):
    pass


@register_pretty('_ast.AST')
def pretty_nodes(value, ctx):
    pass


pathstr_split_pattern = re.compile("(/+)")


@register_pretty('pathlib.PurePath')
def pretty_path(value, ctx):
    pass
