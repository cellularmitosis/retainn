"""Python 2 and 3 compatibility."""

import sys


def isnumeric(s):
    try:
        # Python 2
        if isinstance(s, unicode):
            u = s
        else:
            u = unicode(s, "utf-8")
    except NameError:
        # Python 3
        if isinstance(s, str):
            u = s
        else:
            u = s.decode("utf-8")
    return u.isnumeric()


def is_int(x):
    """`isinstance(x, int)` but portable across Python 2 and 3."""
    if sys.version_info[0] == 2:
        # Python 2
        return isinstance(x, (int, long))
    else:
        # Python 3
        return isinstance(x, int)


def is_str(x):
    if sys.version_info[0] == 2:
        # Python 2
        return isinstance(x, str)
    else:
        # Python 3
        return isinstance(x, (str, bytes))
