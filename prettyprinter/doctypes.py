def normalize_doc(doc):
    pass


class Doc:
    """The base class for all Docs, except for plain ``str`` s which
    are unboxed.

    A Doc is a tree structure that represents the set of all possible
    layouts of the contents. The layout algorithm processes the tree,
    narrowing down the set of layouts based on input parameters like
    total and ribbon width to produce a stream of SDocs (simple Docs)
    that represent a single layout.
    """
    __slots__ = ()

    def normalize(self):
        pass


class Annotated(Doc):
    __slots__ = ('doc', 'annotation')

    def __init__(self, doc, annotation):
        pass

    def __repr__(self):
        pass

    def normalize(self):
        pass


class Nil(Doc):
    def __repr__(self):
        pass


NIL = Nil()


class Concat(Doc):
    __slots__ = ('docs', )

    def __init__(self, docs):
        pass

    def normalize(self):
        pass

    def __repr__(self):
        pass


class Nest(Doc):
    __slots__ = ('indent', 'doc')

    def __init__(self, indent, doc):
        pass

    def normalize(self):
        pass

    def __repr__(self):
        pass


class FlatChoice(Doc):
    __slots__ = (
        '_when_broken',
        '_when_flat',
        'normalize_on_access',
        '_broken_normalized',
        '_flat_normalized',
    )

    def __init__(self, when_broken, when_flat, normalize_on_access=False):
        pass

    def normalize(self):
        pass

    @property
    def when_broken(self):
        pass

    @property
    def when_flat(self):
        pass

    def __repr__(self):
        pass


class Contextual(Doc):
    __slots__ = ('fn', )

    def __init__(self, fn):
        pass

    def __repr__(self):
        pass


class HardLine(Doc):
    def __repr__(self):
        pass


HARDLINE = HardLine()
LINE = FlatChoice(HARDLINE, ' ')
SOFTLINE = FlatChoice(HARDLINE, NIL)


class Group(Doc):
    __slots__ = ('doc', )

    def __init__(self, doc):
        pass

    def normalize(self):
        pass

    def __repr__(self):
        pass


class AlwaysBreak(Doc):
    __slots__ = ('doc', )

    def __init__(self, doc):
        pass

    def normalize(self):
        pass

    def __repr__(self):
        pass


class Fill(Doc):
    __slots__ = ('docs', )

    def __init__(self, docs):
        pass

    def normalize(self):
        pass

    def __repr__(self):
        pass
