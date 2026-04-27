
class SDoc(object):
    pass


class SLine(SDoc):
    __slots__ = ('indent', )

    def __init__(self, indent):
        pass

    def __repr__(self):
        pass


class SAnnotationPush(SDoc):
    __slots__ = ('value', )

    def __init__(self, value):
        pass

    def __repr__(self):
        pass


class SAnnotationPop(SDoc):
    __slots__ = ('value', )

    def __init__(self, value):
        pass

    def __repr__(self):
        pass
