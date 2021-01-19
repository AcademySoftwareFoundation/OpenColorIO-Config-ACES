# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Common Utilities
================

Defines common utilities objects that don't fall in any specific category.
"""

import functools
import os
from collections import defaultdict
from itertools import chain
from textwrap import TextWrapper

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'DocstringDict', 'first_item', 'common_ancestor', 'paths_common_ancestor',
    'vivification', 'vivified_to_dict', 'message_box', 'is_networkx_installed',
    'is_opencolorio_installed', 'REQUIREMENTS_TO_CALLABLE', 'required',
    'is_string', 'is_iterable'
]


class DocstringDict(dict):
    """
    A :class:`dict` sub-class that allows settings a docstring to :class:`dict`
    instances.
    """

    pass


def first_item(iterable, default=None):
    """
    Returns the first item of given iterable.

    Parameters
    ----------
    iterable : iterable
        Iterable
    default : object
         Default value if the iterable is empty.
    Returns
    -------
    object
        First iterable item.
    """

    if not iterable:
        return default

    for item in iterable:
        return item


def common_ancestor(*args):
    """
    Returns the common ancestor of given iterables.

    Other Parameters
    ----------------
    \\*args : list, optional
        Iterables to retrieve the common ancestor from.

    Returns
    -------
    iterable
        Common ancestor.

    Examples
    --------
    >>> common_ancestor(('1', '2', '3'), ('1', '2', '0'), ('1', '2', '3', '4'))
    ('1', '2')
    >>> common_ancestor('azerty', 'azetty', 'azello')
    'aze'
    """

    array = list(map(set, zip(*args)))
    divergence = list(filter(lambda i: len(i) > 1, array))

    if divergence:
        ancestor = first_item(args)[:array.index(first_item(divergence))]
    else:
        ancestor = min(args)

    return ancestor


def paths_common_ancestor(*args):
    """
    Returns the common ancestor path from given paths.

    Parameters
    ----------
    \\*args : list, optional
        Paths to retrieve common ancestor from.

    Returns
    -------
    unicode
        Common path ancestor.

    Examples
    --------
    >>> paths_common_ancestor(  # doctest: +SKIP
    ...     '/Users/JohnDoe/Documents', '/Users/JohnDoe/Documents/Test.txt')
    '/Users/JohnDoe/Documents'
    """

    path_ancestor = os.sep.join(
        common_ancestor(*[path.split(os.sep) for path in args]))

    return path_ancestor


def vivification():
    """
    Implements supports for vivification of the underlying dict like
    data-structure, magical!

    Returns
    -------
    defaultdict

    Examples
    --------
    >>> vivified = vivification()
    >>> vivified['my']['attribute'] = 1
    >>> vivified['my']  # doctest: +SKIP
    defaultdict(<function vivification at 0x...>, {u'attribute': 1})
    >>> vivified['my']['attribute']
    1
    """

    return defaultdict(vivification)


def vivified_to_dict(vivified):
    """
    Converts given vivified data-structure to dictionary.

    Parameters
    ----------
    vivified : defaultdict
        Vivified data-structure.

    Returns
    -------
    dict

    Examples
    --------
    >>> vivified = vivification()
    >>> vivified['my']['attribute'] = 1
    >>> vivified_to_dict(vivified)  # doctest: +SKIP
    {u'my': {u'attribute': 1}}
    """

    if isinstance(vivified, defaultdict):
        vivified = {
            key: vivified_to_dict(value)
            for key, value in vivified.items()
        }
    return vivified


def message_box(message, width=79, padding=3, print_callable=print):
    """
    Prints a message inside a box.

    Parameters
    ----------
    message : unicode
        Message to print.
    width : int, optional
        Message box width.
    padding : unicode, optional
        Padding on each sides of the message.
    print_callable : callable, optional
        Callable used to print the message box.

    Returns
    -------
    bool
        Definition success.

    Examples
    --------
    >>> message = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, '
    ...     'sed do eiusmod tempor incididunt ut labore et dolore magna '
    ...     'aliqua.')
    >>> message_box(message, width=75)
    ===========================================================================
    *                                                                         *
    *   Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do       *
    *   eiusmod tempor incididunt ut labore et dolore magna aliqua.           *
    *                                                                         *
    ===========================================================================
    True
    >>> message_box(message, width=60)
    ============================================================
    *                                                          *
    *   Lorem ipsum dolor sit amet, consectetur adipiscing     *
    *   elit, sed do eiusmod tempor incididunt ut labore et    *
    *   dolore magna aliqua.                                   *
    *                                                          *
    ============================================================
    True
    >>> message_box(message, width=75, padding=16)
    ===========================================================================
    *                                                                         *
    *                Lorem ipsum dolor sit amet, consectetur                  *
    *                adipiscing elit, sed do eiusmod tempor                   *
    *                incididunt ut labore et dolore magna                     *
    *                aliqua.                                                  *
    *                                                                         *
    ===========================================================================
    True
    """

    ideal_width = width - padding * 2 - 2

    def inner(text):
        """
        Formats and pads inner text for the message box.
        """

        return '*{0}{1}{2}{0}*'.format(
            ' ' * padding, text, (' ' * (width - len(text) - padding * 2 - 2)))

    print_callable('=' * width)
    print_callable(inner(''))

    wrapper = TextWrapper(
        width=ideal_width, break_long_words=False, replace_whitespace=False)

    lines = [wrapper.wrap(line) for line in message.split("\n")]
    lines = [' ' if len(line) == 0 else line for line in lines]
    for line in chain(*lines):
        print_callable(inner(line.expandtabs()))

    print_callable(inner(''))
    print_callable('=' * width)

    return True


def is_networkx_installed(raise_exception=False):
    """
    Returns if *NetworkX* is installed and available.

    Parameters
    ----------
    raise_exception : bool
        Raise exception if *NetworkX* is unavailable.

    Returns
    -------
    bool
        Is *NetworkX* installed.

    Raises
    ------
    ImportError
        If *NetworkX* is not installed.
    """

    try:  # pragma: no cover
        # pylint: disable=W0612
        import networkx  # noqa

        return True
    except ImportError as error:  # pragma: no cover
        if raise_exception:
            raise ImportError(('"NetworkX" related API features '
                               'are not available: "{0}".').format(error))
        return False


def is_opencolorio_installed(raise_exception=False):
    """
    Returns if *OpenColorIO* is installed and available.

    Parameters
    ----------
    raise_exception : bool
        Raise exception if *OpenColorIO* is unavailable.

    Returns
    -------
    bool
        Is *OpenColorIO* installed.

    Raises
    ------
    ImportError
        If *OpenColorIO* is not installed.
    """

    try:  # pragma: no cover
        import PyOpenColorIO  # noqa

        return True
    except ImportError as error:  # pragma: no cover
        if raise_exception:
            raise ImportError(('"OpenColorIO" related API features '
                               'are not available: "{0}".').format(error))
        return False


REQUIREMENTS_TO_CALLABLE = DocstringDict({
    'NetworkX':
    is_networkx_installed,
    'OpenColorIO':
    is_opencolorio_installed,
})
REQUIREMENTS_TO_CALLABLE.__doc__ = """
Mapping of requirements to their respective callables.

_REQUIREMENTS_TO_CALLABLE : CaseInsensitiveMapping
    **{'NetworkX', 'OpenImageIO'}**
"""


def required(*requirements):
    """
    A decorator checking if various requirements are satisfied.

    Other Parameters
    ----------------
    \\*requirements : list, optional
        Requirements to check whether they are satisfied.

    Returns
    -------
    object
    """

    def wrapper(function):
        """
        Wrapper for given function.
        """

        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            """
            Wrapped function.
            """

            for requirement in requirements:
                REQUIREMENTS_TO_CALLABLE[requirement](raise_exception=True)

            return function(*args, **kwargs)

        return wrapped

    return wrapper


def is_string(a):
    """
    Returns if given :math:`a` variable is a *string* like variable.

    Parameters
    ----------
    a : object
        Data to test.

    Returns
    -------
    bool
        Is :math:`a` variable a *string* like variable.

    Examples
    --------
    >>> is_string("I'm a string!")
    True
    >>> is_string(["I'm a string!"])
    False
    """

    return True if isinstance(a, str) else False


def is_iterable(a):
    """
    Returns if given :math:`a` variable is iterable.

    Parameters
    ----------
    a : object
        Variable to check the iterability.

    Returns
    -------
    bool
        :math:`a` variable iterability.

    Examples
    --------
    >>> is_iterable([1, 2, 3])
    True
    >>> is_iterable(1)
    False
    """

    return is_string(a) or (True if getattr(a, '__iter__', False) else False)
