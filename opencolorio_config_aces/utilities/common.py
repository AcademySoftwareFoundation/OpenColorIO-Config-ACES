# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Common Utilities
================

Defines common utilities objects that don't fall in any specific category.
"""

from __future__ import annotations

import datetime
import functools
import logging
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from itertools import chain
from pathlib import Path
from pprint import PrettyPrinter
from textwrap import TextWrapper
from typing import Any, TypeVar

import requests

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "ROOT_BUILD_DEFAULT",
    "DocstringDict",
    "first_item",
    "common_ancestor",
    "paths_common_ancestor",
    "vivification",
    "vivified_to_dict",
    "message_box",
    "is_colour_installed",
    "is_jsonpickle_installed",
    "is_networkx_installed",
    "REQUIREMENTS_TO_CALLABLE",
    "required",
    "is_string",
    "is_iterable",
    "git_describe",
    "matrix_3x3_to_4x4",
    "multi_replace",
    "validate_method",
    "google_sheet_title",
    "slugify",
    "attest",
    "timestamp",
    "as_bool",
    "optional",
    "filter_any",
    "filter_all",
]

LOGGER = logging.getLogger(__name__)


# Monkey-patching the "PrettyPrinter" mapping to handle the "TypeError"
# exception raised with "instancemethod": https://bugs.python.org/issue33395
class _dispatch(dict[Any, Any]):
    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self.__get__(key, default)
        except Exception as error:  # noqa: F841, S110
            pass


PrettyPrinter._dispatch = _dispatch()

ROOT_BUILD_DEFAULT: Path = (Path(__file__) / ".." / ".." / ".." / "build").resolve()
"""
Default build root directory.

ROOT_BUILD_DEFAULT : str
"""


class DocstringDict(dict[str, Any]):
    """
    A :class:`dict` sub-class that allows settings a docstring to :class:`dict`
    instances.
    """


def first_item(iterable: Iterable[Any], default: Any = None) -> Any:
    """
    Return the first item of given iterable.

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

    return None


def common_ancestor(*args: Any) -> Any:
    """
    Return the common ancestor of given iterables.

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
        ancestor = first_item(args)[: array.index(first_item(divergence))]
    else:
        ancestor = min(args)

    return ancestor


def paths_common_ancestor(*args: str) -> str:
    """
    Return the common ancestor path from given paths.

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

    path_ancestor = os.sep.join(common_ancestor(*[path.split(os.sep) for path in args]))

    return path_ancestor


def vivification() -> defaultdict[Any, Any]:
    """
    Implement supports for vivification of the underlying dict like
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


def vivified_to_dict(
    vivified: defaultdict[Any, Any] | dict[Any, Any],
) -> dict[Any, Any]:
    """
    Convert given vivified data-structure to dictionary.

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
        vivified = {key: vivified_to_dict(value) for key, value in vivified.items()}
    return vivified


def message_box(
    message: str,
    width: int = 79,
    padding: int = 3,
    print_callable: Callable[[str], None] = print,
) -> bool:
    """
    Print a message inside a box.

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

    def inner(text: str) -> str:
        """Format and pads inner text for the message box."""

        return "*{0}{1}{2}{0}*".format(
            " " * padding, text, (" " * (width - len(text) - padding * 2 - 2))
        )

    print_callable("=" * width)
    print_callable(inner(""))

    wrapper = TextWrapper(
        width=ideal_width, break_long_words=False, replace_whitespace=False
    )

    lines = [wrapper.wrap(line) for line in message.split("\n")]
    lines = [" " if len(line) == 0 else line for line in lines]
    for line in chain(*lines):
        print_callable(inner(line.expandtabs()))

    print_callable(inner(""))
    print_callable("=" * width)

    return True


def is_colour_installed(raise_exception: bool = False) -> bool:
    """
    Return if *Colour* is installed and available.

    Parameters
    ----------
    raise_exception : bool
        Raise exception if *Colour* is unavailable.

    Returns
    -------
    bool
        Is *Colour* installed.

    Raises
    ------
    ImportError
        If *Colour* is not installed.
    """

    try:  # pragma: no cover
        import colour  # noqa: F401

        return True
    except ImportError as error:  # pragma: no cover
        if raise_exception:
            raise ImportError(
                f'"Colour" related API features are not available: "{error}".'
            ) from error
        return False


def is_jsonpickle_installed(raise_exception: bool = False) -> bool:
    """
    Return if *jsonpickle* is installed and available.

    Parameters
    ----------
    raise_exception : bool
        Raise exception if *jsonpickle* is unavailable.

    Returns
    -------
    bool
        Is *jsonpickle* installed.

    Raises
    ------
    ImportError
        If *jsonpickle* is not installed.
    """

    try:  # pragma: no cover
        import jsonpickle  # noqa: F401

        return True
    except ImportError as error:  # pragma: no cover
        if raise_exception:
            raise ImportError(
                f'"jsonpickle" related API features, '
                f'e.g., serialization, are not available: "{error}".'
            ) from error
        return False


def is_networkx_installed(raise_exception: bool = False) -> bool:
    """
    Return if *NetworkX* is installed and available.

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
        import networkx as nx  # noqa: F401

        return True
    except ImportError as error:  # pragma: no cover
        if raise_exception:
            raise ImportError(
                f'"NetworkX" related API features are not available: "{error}".'
            ) from error
        return False


REQUIREMENTS_TO_CALLABLE: DocstringDict = DocstringDict(
    {
        "Colour": is_colour_installed,
        "jsonpickle": is_jsonpickle_installed,
        "NetworkX": is_networkx_installed,
    }
)
REQUIREMENTS_TO_CALLABLE.__doc__ = """
Mapping of requirements to their respective callables.

_REQUIREMENTS_TO_CALLABLE : CaseInsensitiveMapping
    **{'Colour', 'jsonpickle', 'NetworkX', 'OpenImageIO'}**
"""


def required(*requirements: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorate a function to check whether various ancillary package requirements
    are satisfied.

    Other Parameters
    ----------------
    \\*requirements : list, optional
        Requirements to check whether they are satisfied.

    Returns
    -------
    object
    """

    def wrapper(function: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap given function wrapper."""

        @functools.wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            """Wrap given function."""

            for requirement in requirements:
                REQUIREMENTS_TO_CALLABLE[requirement](raise_exception=True)

            return function(*args, **kwargs)

        return wrapped

    return wrapper


def is_string(a: Any) -> bool:
    """
    Return if given :math:`a` variable is a *string* like variable.

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

    return isinstance(a, str)


def is_iterable(a: Any) -> bool:
    """
    Return if given :math:`a` variable is iterable.

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

    return is_string(a) or (bool(getattr(a, "__iter__", False)))


def git_describe() -> str:
    """
    Describe the current *OpenColorIO Configuration for ACES* *git* version.

    Returns
    -------
    >>> git_describe()  # doctest: +SKIP
    '0.1.0'
    """

    import opencolorio_config_aces

    try:  # pragma: no cover
        version = subprocess.check_output(
            ["git", "describe"],  # noqa: S603, S607
            cwd=opencolorio_config_aces.__path__[0],
            stderr=subprocess.STDOUT,
        ).strip()
        version = version.decode("utf-8")
    except Exception:  # pragma: no cover
        version = opencolorio_config_aces.__version__

    return version


# TODO: Numpy currently comes via "Colour", we might want that to be an
# explicit dependency in the future.
@required("Colour")
def matrix_3x3_to_4x4(M: Any) -> list[float]:
    """
    Convert given 3x3 matrix :math:`M` to a raveled 4x4 matrix.

    Parameters
    ----------
    M : array_like
        3x3 matrix :math:`M` to convert.

    Returns
    -------
    list
        Raveled 4x4 matrix.
    """

    import numpy as np

    M_I = np.identity(4)
    M_I[:3, :3] = M

    return np.ravel(M_I).tolist()


def multi_replace(name: str, patterns: dict[str, str]) -> str:
    """
    Update given name by applying in succession the given patterns and
    substitutions.

    Parameters
    ----------
    name : unicode
        Name to update.
    patterns : dict
        Dictionary of regular expression patterns and substitution to apply
        onto the name.

    Returns
    -------
    unicode
        Updated name.

    Examples
    --------
    >>> multi_replace(
    ...     'Canon Luke Skywalker was weak and powerless.',
    ...     {'Canon': 'Legends', 'weak': 'strong', '\\w+less': 'powerful'})
    'Legends Luke Skywalker was strong and powerful.'
    """

    for pattern, substitution in patterns.items():
        name = re.sub(pattern, substitution, name)

    return name


def validate_method(
    method: str,
    valid_methods: list[str],
    message: str = '"{0}" method is invalid, it must be one of {1}!',
) -> str:
    """
    Validate whether given method exists in the given valid methods and
    returns the method lower cased.

    Parameters
    ----------
    method : str
        Method to validate.
    valid_methods : Union[Sequence, Mapping]
        Valid methods.
    message : str
        Message for the exception.

    Returns
    -------
    :class:`str`
        Method lower cased.

    Raises
    ------
    :class:`ValueError`
         If the method does not exist.

    Examples
    --------
    >>> validate_method('Valid', ['Valid', 'Yes', 'Ok'])
    'valid'
    """

    valid_methods = [str(valid_method) for valid_method in valid_methods]

    method_lower = method.lower()
    if method_lower not in [valid_method.lower() for valid_method in valid_methods]:
        raise ValueError(message.format(method, valid_methods))

    return method_lower


def google_sheet_title(url: str) -> str:
    """
    Return the title from given *Google Sheet* url.

    Parameters
    ----------
    url : str
        *Google Sheet* url to return the title of.

    Returns
    -------
    :class:`str`
        *Google Sheet* title.

    Examples
    --------
    >>> url = (
    ...     "https://docs.google.com/spreadsheets/d/"
    ...     "1z3xsy3sF0I-8AN_tkMOEjHlAs13ba7VAVhrE8v4WIyo/"
    ...     "export?format=csv&gid=273921464"
    ... )
    >>> google_sheet_title(url)  # doctest: +SKIP
    'OpenColorIO-Config-ACES "Reference" Transforms - v...'
    """

    class Parser(HTMLParser):
        def __init__(self) -> None:
            HTMLParser.__init__(self)
            self.in_title: list[str] = []
            self.title: str | None = None

        def handle_starttag(
            self,
            tag: str,
            attrs: list[tuple[str, str | None]],  # noqa: ARG002
        ) -> None:
            if tag == "title":
                self.in_title.append(tag)

        def handle_endtag(self, tag: str) -> None:
            if tag == "title":
                self.in_title.pop()

        def handle_data(self, data: str) -> None:
            if self.in_title:
                self.title = data

    if "export" in url:
        url = url.split("export")[0]

    parser = Parser()
    parser.feed(requests.get(url, timeout=60).text)

    if parser.title is None:
        raise ValueError(f"Could not extract title from URL: {url}")

    return parser.title.rsplit("-", 1)[0].strip()


def slugify(object_: Any, allow_unicode: bool = False) -> str:
    """
    Generate a *SEO* friendly and human-readable slug from given object.

    Convert to ASCII if ``allow_unicode`` is *False*. Convert spaces or
    repeated dashes to single dashes. Remove characters that aren't
    alphanumerics, underscores, or hyphens. Convert to lowercase. Also strip
    leading and trailing whitespace, dashes, and underscores.

    Parameters
    ----------
    object_ : object
        Object to convert to a slug.
    allow_unicode : bool
        Whether to allow unicode characters in the generated slug.

    Returns
    -------
    :class:`str`
        Generated slug.

    References
    ----------
    -   https://github.com/django/django/blob/\
0dd29209091280ccf34e07c9468746c396b7778e/django/utils/text.py#L400

    Examples
    --------
    >>> slugify(
    ...     " Jack & Jill like numbers 1,2,3 and 4 and silly characters ?%.$!/"
    ... )
    'jack-jill-like-numbers-123-and-4-and-silly-characters'
    """

    value = str(object_)

    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

    value = re.sub(r"[^\w\s-]", "", value.lower())

    return re.sub(r"[-\s]+", "-", value).strip("-_")


def attest(condition: bool, message: str = "") -> None:
    """
    Provide the `assert` statement functionality without being disabled by
    optimised Python execution.

    Parameters
    ----------
    condition : bool
        Condition to attest/assert.
    message : str
        Message to display when the assertion fails.
    """

    if not condition:
        raise AssertionError(message)


def timestamp() -> str:
    """
    Return a timestamp description.

    Returns
    -------
    :class:`str`
    """

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d at %H:%M")
    timestamp = (
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} on the {now}.'
    )

    return timestamp


def as_bool(a: str) -> bool:
    """
    Convert given string to bool.

    The following string values evaluate to *True*: "1", "On", and "True".

    Parameters
    ----------
    a
        String to convert to bool.

    Returns
    -------
    :class:`bool`
        Whether the given string is *True*.

    Examples
    --------
    >>> as_bool("1")
    True
    >>> as_bool("On")
    True
    >>> as_bool("True")
    True
    >>> as_bool("0")
    False
    >>> as_bool("Off")
    False
    >>> as_bool("False")
    False
    """

    return a.lower() in ["1", "on", "true"]


T = TypeVar("T")


def optional(value: T | None, default: T) -> T:
    """
    Handle optional argument value by providing a default value.

    Parameters
    ----------
    value
        Optional argument value.
    default
        Default argument value if ``value`` is *None*.

    Returns
    -------
    T
        Argument value.

    Examples
    --------
    >>> optional("Foo", "Bar")
    'Foo'
    >>> optional(None, "Bar")
    'Bar'
    """

    if value is None:
        return default
    else:
        return value


def filter_any(
    array: list[dict[str, Any]], filterers: list[Callable[[dict[str, Any]], bool]]
) -> list[dict[str, Any]]:
    """
    Filter array elements that pass any of the provided filter functions.

    This function applies multiple filter functions to each element in the array
    and returns elements that satisfy at least one filter condition (OR logic).

    Parameters
    ----------
    array : list[dict[str, Any]]
        The list of dictionaries to filter.
    filterers : list[Callable[[dict[str, Any]], bool]]
        A list of callable filter functions. Each function should accept a
        dictionary and return True if the element passes the filter condition,
        False otherwise.

    Returns
    -------
    list[dict[str, Any]]
        A new list containing only the elements that pass at least one of the
        filter conditions.

    Examples
    --------
    >>> transforms = [
    ...     {'name': 'ACEScc', 'type': 'CSC', 'family': 'aces'},
    ...     {'name': 'ACEScg', 'type': 'CSC', 'family': 'aces'},
    ...     {'name': 'sRGB', 'type': 'Output', 'family': 'display'},
    ... ]
    >>> is_csc = lambda x: x['type'] == 'CSC'
    >>> is_output = lambda x: x['type'] == 'Output'
    >>> filter_any(transforms, [is_csc, is_output])
    [{'name': 'ACEScc', 'type': 'CSC', 'family': 'aces'}, \
{'name': 'ACEScg', 'type': 'CSC', 'family': 'aces'}, \
{'name': 'sRGB', 'type': 'Output', 'family': 'display'}]
    """

    filtered = [a for a in array if any(filterer(a) for filterer in filterers)]

    return filtered


def filter_all(
    array: list[dict[str, Any]], filterers: list[Callable[[dict[str, Any]], bool]]
) -> list[dict[str, Any]]:
    """
    Filter array elements that pass all of the provided filter functions.

    This function applies multiple filter functions to each element in the array
    and returns only elements that satisfy every filter condition (AND logic).

    Parameters
    ----------
    array : list[dict[str, Any]]
        The list of dictionaries to filter.
    filterers : list[Callable[[dict[str, Any]], bool]]
        A list of callable filter functions. Each function should accept a
        dictionary and return True if the element passes the filter condition,
        False otherwise.

    Returns
    -------
    list[dict[str, Any]]
        A new list containing only the elements that pass all of the filter
        conditions.

    Examples
    --------
    >>> transforms = [
    ...     {'name': 'ACEScc', 'type': 'CSC', 'family': 'aces'},
    ...     {'name': 'Rec709', 'type': 'Output', 'family': 'display'},
    ...     {'name': 'sRGB', 'type': 'Output', 'family': 'display'},
    ... ]
    >>> is_output = lambda x: x['type'] == 'Output'
    >>> is_display = lambda x: x['family'] == 'display'
    >>> filter_all(transforms, [is_output, is_display])
    [{'name': 'Rec709', 'type': 'Output', 'family': 'display'}, \
{'name': 'sRGB', 'type': 'Output', 'family': 'display'}]
    """

    filtered = [a for a in array if all(filterer(a) for filterer in filterers)]

    return filtered
