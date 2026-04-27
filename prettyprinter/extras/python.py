import builtins
import sys
from io import StringIO

from prettyprinter import cpprint
from prettyprinter.utils import get_terminal_width


def install():
    try:
        get_ipython
    except NameError:
        pass
    else:
        raise ValueError(
            "Don't install the default Python shell integration "
            "if you're using IPython, use the IPython integration with "
            "prettyprinter.install_extras(include=['ipython'])."
        )

    def prettyprinter_displayhook(value):
        pass

    sys.displayhook = prettyprinter_displayhook
