# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Common Utilities
================

Defines common utilities objects that don't fall in any specific category.
"""

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
    'first_item', 'common_ancestor', 'paths_common_ancestor', 'vivification',
    'vivified_to_dict', 'message_box'
]


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
