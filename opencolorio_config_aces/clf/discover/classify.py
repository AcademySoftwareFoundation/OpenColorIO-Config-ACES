# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
CLF Transforms Discovery & Classification
=========================================

Defines various objects related to *Common LUT Format* (CLF) transforms
discovery and classification:

-   :func:`opencolorio_config_aces.discover_clf_transforms`
-   :func:`opencolorio_config_aces.classify_clf_transforms`
-   :func:`opencolorio_config_aces.unclassify_clf_transforms`
-   :func:`opencolorio_config_aces.filter_clf_transforms`
-   :func:`opencolorio_config_aces.print_clf_taxonomy`
"""

from __future__ import annotations

import itertools
import logging
import os
import xml.etree.ElementTree
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from opencolorio_config_aces.config.reference.discover.classify import (
    ACESTransformID,
)
from opencolorio_config_aces.utilities import (
    attest,
    message_box,
    optional,
    paths_common_ancestor,
    vivified_to_dict,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "URN_CLF",
    "SEPARATOR_VERSION_CLF",
    "SEPARATOR_ID_CLF",
    "EXTENSION_CLF",
    "NAMESPACE_CLF",
    "TRANSFORM_TYPES_CLF",
    "TRANSFORM_FAMILIES_CLF",
    "TRANSFORM_GENUS_DEFAULT_CLF",
    "TRANSFORM_FILTERERS_DEFAULT_CLF",
    "PATTERNS_DESCRIPTION_CLF",
    "ROOT_TRANSFORMS_CLF",
    "clf_transform_relative_path",
    "CLFTransformID",
    "CLFTransform",
    "CLFTransformPair",
    "find_clf_transform_pairs",
    "discover_clf_transforms",
    "classify_clf_transforms",
    "unclassify_clf_transforms",
    "filter_clf_transforms",
    "print_clf_taxonomy",
]

LOGGER = logging.getLogger(__name__)

URN_CLF: str = "urn:aswf:ocio:transformId:1.0"
"""
*CLF* Uniform Resource Name (*URN*).
"""

SEPARATOR_VERSION_CLF: str = "."
"""
*CLFtransformID* separator used to tokenize the *VERSION* parts of the
*CLFtransformID*.

urn:aswf:ocio:transformId:1.0:OCIO:ACES:AP0_to_AP1-Gamma2pnt2:1.0
                         |---|                               |---|
"""

SEPARATOR_ID_CLF: str = ":"
"""
*CLFtransformID* separator used to tokenize the *ID* part of the
*CLFtransformID*.

urn:aswf:ocio:transformId:1.0:OCIO:ACES:AP0_to_AP1-Gamma2pnt2:1.0
|-------------URN-----------|:|----------------ID---------------|
"""

EXTENSION_CLF: str = ".clf"
"""
*CLF* transform extension.
"""

NAMESPACE_CLF: str = "OCIO"
"""
Namespace for the *OCIO* *CLF* transforms.
"""

TRANSFORM_TYPES_CLF: list = ["", "Input", "Utility"]
"""
*CLF* transform types.
"""

TRANSFORM_FAMILIES_CLF: dict = {"input": "Input", "utility": "Utility"}
"""
*CLF* transform families mapping the *CLF* transform directories to family
names.
"""

TRANSFORM_GENUS_DEFAULT_CLF: str = "undefined"
"""
*CLF* transform default genus, i.e., *undefined*.
"""

TRANSFORM_FILTERERS_DEFAULT_CLF: list = []
"""
Default list of *CLF* transform filterers.
"""

PATTERNS_DESCRIPTION_CLF: dict = {}
"""
*CLF* transform description substitution patterns.
"""

ROOT_TRANSFORMS_CLF: str = os.path.normpath(
    os.environ.get(
        "OPENCOLORIO_CONFIG_ACES__CLF_TRANSFORMS_ROOT",
        os.path.join(os.path.dirname(__file__), "..", "transforms"),
    )
)
"""
*CLF* transforms root directory, default to the version controlled
sub-module repository. It can be defined by setting the
`OPENCOLORIO_CONFIG_ACES__CLF_TRANSFORMS_ROOT` environment variable with
the local 'transforms/clf' directory.
"""


def clf_transform_relative_path(
    path: str, root_directory: str = ROOT_TRANSFORMS_CLF
) -> str:
    """
    Return the relative path from given *CLF* transform to the *CLF* transforms
    root directory.

    Parameters
    ----------
    path
        *CLF* transform absolute path.
    root_directory
        *CLF* transforms root directory.

    Returns
    -------
    :class:`str`
         *CLF* transform relative path.
    """

    return path.replace(f"{root_directory}{os.sep}", "")


class CLFTransformID:
    """
    Define the *CLF* transform *CLFtransformID*: an object parsing and storing
    information about a *CLFtransformID* unicode string.

    Parameters
    ----------
    clf_transform_id
        *CLFtransformID*, e.g.,
        *urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_AP1-Gamma2pnt2.c1.v1*.

    Attributes
    ----------
    clf_transform_id
    urn
    type
    namespace
    name
    major_version
    minor_version
    patch_version
    source
    target

    Methods
    -------
    __str__
    __repr__
    """

    def __init__(self, clf_transform_id: str) -> None:
        self._clf_transform_id: str = clf_transform_id

        self._urn: str | None = None
        self._type: str | None = None
        self._namespace: str | None = None
        self._name: str | None = None
        self._major_version: str | None = None
        self._minor_version: str | None = None
        self._patch_version: str | None = None
        self._source: str | None = None
        self._target: str | None = None

        self._parse()

    @property
    def clf_transform_id(self) -> str | None:
        """
        Getter property for the *CLFtransformID*, e.g.,
        *urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_AP1-Gamma2pnt2.c1.v1*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._clf_transform_id

    @property
    def urn(self) -> str | None:
        """
        Getter property for the *CLFtransformID* Uniform Resource Name (*URN*),
        e.g., *urn:aswf:ocio:transformId:v1.0*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* Uniform Resource Name (*URN*).

        Notes
        -----
        -   This property is read only.
        """

        return self._urn

    @property
    def type(self) -> str | None:
        """
        Getter property for the *CLFtransformID* type, e.g., *ACES*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* type.

        Notes
        -----
        -   This property is read only.
        """

        return self._type

    @property
    def namespace(self) -> str | None:
        """
        Getter property for the *CLFtransformID* namespace, e.g., *OCIO*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* namespace.

        Notes
        -----
        -   This property is read only.
        """

        return self._namespace

    @property
    def name(self) -> str | None:
        """
        Getter property for the *CLFtransformID* name, e.g.,
        *AP0_to_AP1-Gamma2pnt2*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* name.

        Notes
        -----
        -   This property is read only.
        """

        return self._name

    @property
    def major_version(self) -> str | None:
        """
        Getter property for the *CLFtransformID* major version number, e.g., *c1*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* major version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._major_version

    @property
    def minor_version(self) -> str | None:
        """
        Getter property for the *CLFtransformID* minor version number, e.g., *v1*.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* minor version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._minor_version

    @property
    def patch_version(self) -> str | None:
        """
        Getter property for the *CLFtransformID* patch version number.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* patch version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._patch_version

    @property
    def source(self) -> str | None:
        """
        Getter property for the *CLFtransformID* source colourspace.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* source colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._source

    @property
    def target(self) -> str | None:
        """
        Getter property for the *CLFtransformID* target colourspace.

        Returns
        -------
        :class:`str` or None
            *CLFtransformID* target colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._target

    def __str__(self) -> str:
        """
        Return a formatted string representation of the *CLFtransformID*.

        Returns
        -------
        :class:`str`
            Formatted string representation.
        """

        return f"{self.__class__.__name__}('{self._clf_transform_id}')"

    def __repr__(self) -> str:
        """
        Return an evaluable string representation of the *CLFtransformID*.

        Returns
        -------
        :class:`str`
            Evaluable string representation.
        """

        return str(self)

    def _parse(self) -> None:
        """Parse the *CLFtransformID*."""

        if self._clf_transform_id is None:
            return

        clf_transform_id = self._clf_transform_id

        attest(
            clf_transform_id.startswith(URN_CLF),
            f"{self._clf_transform_id} URN {self._urn} is invalid!",
        )

        self._urn = clf_transform_id[: len(URN_CLF) + 1]
        components = clf_transform_id[len(URN_CLF) + 1 :]
        components = components.split(SEPARATOR_ID_CLF)

        attest(
            (len(components) == 4),
            f'{self._clf_transform_id} is an invalid "CLFtransformID"!',
        )

        self._namespace, self._type, self._name, version = components

        attest(
            (self._type in TRANSFORM_TYPES_CLF),
            f"{self._clf_transform_id} type {self._type} is invalid!",
        )

        if self._name is not None:
            self._source, self._target = self._name.split("_to_")

        attest(
            version.count(SEPARATOR_VERSION_CLF) == 1,
            f'{self._clf_transform_id} has an invalid "CLFtransformID" version!',
        )

        (
            self._major_version,
            self._minor_version,
        ) = version.split(SEPARATOR_VERSION_CLF)


class CLFTransform:
    """
    Define the *CLF* transform class: an object storing information about a
    *CLF* transform file.

    Parameters
    ----------
    path
        *CLF* transform path.
    family
        *CLF* transform family, e.g., *aces*
    genus
        *CLF* transform genus, e.g., *undefined*
    siblings
        *CLF* transform siblings, e.g., inverse transform.

    Attributes
    ----------
    path
    code
    clf_transform_id
    user_name
    description
    input_descriptor
    output_descriptor
    information
    family
    genus

    Methods
    -------
    __str__
    __repr__
    __eq__
    __ne__
    """

    def __init__(
        self,
        path: str,
        family: str | None = None,
        genus: str | None = None,
        siblings: Sequence | None = None,
    ) -> None:
        siblings = optional(siblings, [])

        self._path: str = os.path.abspath(os.path.normpath(path))

        self._code: str | None = None
        self._clf_transform_id: CLFTransformID | None = None
        self._user_name: str | None = None
        self._description: str | None = ""
        self._input_descriptor: str | None = ""
        self._output_descriptor: str | None = ""
        self._information: dict = {}

        self._family: str | None = family
        self._genus: str | None = genus
        self._siblings: Sequence | None = siblings

        self._parse()

    @property
    def path(self) -> str | None:
        """
        Getter property for the *CLF* transform path.

        Returns
        -------
        :class:`str` or None
            *CLF* transform path.

        Notes
        -----
        -   This property is read only.
        """

        return self._path

    @property
    def code(self) -> str | None:
        """
        Getter property for the *CLF* transform code, i.e., the *CLF* transform
        file content.

        Returns
        -------
        :class:`str` or None
            *CLF* transform code.

        Notes
        -----
        -   This property is read only.
        -   This property contains the entire file content, i.e., the code along
            with the comments.
        """

        return self._code

    @property
    def clf_transform_id(self) -> CLFTransformID | None:
        """
        Getter property for the *CLF* transform *CLFtransformID*.

        Returns
        -------
        :class:`CLFTransformID`
            *CLF* transform *CLFtransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._clf_transform_id

    @property
    def user_name(self) -> str | None:
        """
        Getter property for the *CLF* transform user name.

        Returns
        -------
        :class:`str` or None
            *CLF* transform user name.

        Notes
        -----
        -   This property is read only.
        """

        return self._user_name

    @property
    def description(self) -> str | None:
        """
        Getter property for the *CLF* transform description extracted from
        parsing the file content header.

        Returns
        -------
        :class:`str` or None
            *CLF* transform description.

        Notes
        -----
        -   This property is read only.
        """

        return self._description

    @property
    def input_descriptor(self) -> str | None:
        """
        Getter property for the *CLF* transform input descriptor extracted from
        parsing the file content header.

        Returns
        -------
        :class:`str` or None
            *CLF* transform input descriptor.

        Notes
        -----
        -   This property is read only.
        """

        return self._input_descriptor

    @property
    def output_descriptor(self) -> str | None:
        """
        Getter property for the *CLF* transform output descriptor extracted
        from parsing the file content header.

        Returns
        -------
        :class:`str` or None
            *CLF* transform output descriptor.

        Notes
        -----
        -   This property is read only.
        """

        return self._output_descriptor

    @property
    def information(self) -> dict:
        """
        Getter property for the *CLF* transform information extracted from
        parsing the file content header.

        Returns
        -------
        :class:`dict`
            *CLF* transform information.

        Notes
        -----
        -   This property is read only.
        """

        return self._information

    @property
    def family(self) -> str | None:
        """
        Getter property for the *CLF* transform family, e.g., *aces*, a value in
        :attr:`opencolorio_config_aces.clf.reference.\
TRANSFORM_FAMILIES_CLF` attribute dictionary.

        Returns
        -------
        :class:`str` or None
            *CLF* transform family.

        Notes
        -----
        -   This property is read only.
        """

        return self._family

    @property
    def genus(self) -> str | None:
        """
        Getter property for the *CLF* transform genus, e.g., *undefined*.

        Returns
        -------
        :class:`str` or None
            *CLF* transform genus.

        Notes
        -----
        -   This property is read only.
        """

        return self._genus

    @property
    def siblings(self) -> Sequence | None:
        """
        Getter property for the *CLF* transform siblings, e.g., inverse
        transform.

        Returns
        -------
        :class:`Sequence` or None
            *CLF* transform siblings.

        Notes
        -----
        -   This property is read only.
        """

        return self._siblings

    def __getattr__(self, item: str) -> Any:
        """
        Reimplement the :meth:`object.__getattr__` so that unsuccessful
        attribute lookup on :class:`opencolorio_config_aces.clf.reference.\
CLFTransform` class are tried on the underlying
        :class:`opencolorio_config_aces.clf.reference.CLFTransformID` class
        instance.

        Parameters
        ----------
        item
            Attribute to lookup the value of.

        Returns
        -------
        :class:`object`
             Attribute value.
        """

        clf_transform_id = object.__getattribute__(self, "_clf_transform_id")

        return getattr(clf_transform_id, item)

    def __str__(self) -> str:
        """
        Return a formatted string representation of the *CLF* transform.

        Returns
        -------
        :class:`str`
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"'{clf_transform_relative_path(self._path)}')"
        )

    def __repr__(self) -> str:
        """
        Return an evaluable representation of the *CLF* transform.

        Returns
        -------
        :class:`str`
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other: Any) -> bool:
        """
        Return whether the *CLF* transform is equal to given other object.

        Parameters
        ----------
        other
            Object to test whether it is equal to the *CLF* transform.

        Returns
        -------
        :class:`bool`
            Is given object equal to *CLF* transform.
        """

        if not isinstance(other, CLFTransform):
            return False
        else:
            return self._path == other.path

    def __ne__(self, other: Any) -> bool:
        """
        Return whether the *CLF* transform is not equal to given other
        object.

        Parameters
        ----------
        other
            Object to test whether it is not equal to the *CLF* transform.

        Returns
        -------
        :class:`bool`
            Is given object not equal to *CLF* transform.
        """

        return not (self == other)

    def _parse(self) -> None:
        """Parse the *CLF* transform."""

        tree = xml.etree.ElementTree.parse(self._path)  # noqa: S314
        root = tree.getroot()

        self._clf_transform_id = CLFTransformID(root.attrib["id"])
        self._user_name = root.attrib["name"]

        description = next(iter(root.findall("./Description")), None)
        if description is not None:
            self._description = description.text

        input_descriptor = next(iter(root.findall("./InputDescriptor")), None)
        if input_descriptor is not None:
            self._input_descriptor = input_descriptor.text

        output_descriptor = next(iter(root.findall("./OutputDescriptor")), None)
        if output_descriptor is not None:
            self._output_descriptor = output_descriptor.text

        information = next(iter(root.findall("./Info")), None)
        if information is not None:
            aces_transform_id = next(
                iter(information.findall("./ACEStransformID")), None
            )
            if aces_transform_id is not None:
                self._information["ACEStransformID"] = ACESTransformID(
                    aces_transform_id.text
                )

            builtin_transform = next(
                iter(information.findall("./BuiltinTransform")), None
            )
            if builtin_transform is not None:
                self._information["BuiltinTransform"] = builtin_transform.text


class CLFTransformPair:
    """
    Define the *CLF* transform pair class: an object storing a pair of
    :class:`opencolorio_config_aces.clf.reference.CLFTransform` class instances
    representing forward and inverse transformation.

    Parameters
    ----------
    forward_transform
        *CLF* transform forward transform.
    inverse_transform
        *CLF* transform inverse transform.

    Attributes
    ----------
    forward_transform
    inverse_transform

    Methods
    -------
    __str__
    __repr__
    __eq__
    __ne__
    """

    def __init__(
        self, forward_transform: CLFTransform, inverse_transform: CLFTransform
    ) -> None:
        self._forward_transform = forward_transform
        self._inverse_transform = inverse_transform

    @property
    def forward_transform(self) -> CLFTransform:
        """
        Getter property for the *CLF* transform pair forward transform.

        Returns
        -------
        :class:`CLFTransform`
            *CLF* transform pair forward transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._forward_transform

    @property
    def inverse_transform(self) -> CLFTransform:
        """
        Getter property for the *CLF* transform pair inverse transform.

        Returns
        -------
        :class:`CLFTransform`
            *CLF* transform pair inverse transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._inverse_transform

    def __str__(self) -> str:
        """
        Return a formatted string representation of the *CLF* transform pair.

        Returns
        -------
        :class:`str`
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"{self._forward_transform!s}', "
            f"{self._inverse_transform!s}')"
        )

    def __repr__(self) -> str:
        """
        Return an evaluable string representation of the *CLF* transform pair.

        Returns
        -------
        :class:`str`
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other: Any) -> bool:
        """
        Return whether the *CLF* transform pair is equal to given other
        object.

        Parameters
        ----------
        other
            Object to test whether it is equal to the *CLF* transform pair.

        Returns
        -------
        :class:`bool`
            Is given object equal to *CLF* transform pair.
        """

        if not isinstance(other, CLFTransformPair):
            return False
        else:
            return (self._forward_transform == other._forward_transform) and (
                self._inverse_transform == other._inverse_transform
            )

    def __ne__(self, other: Any) -> bool:
        """
        Return whether the *CLF* transform pair is not equal to given other
        object.

        Parameters
        ----------
        other
            Object to test whether it is not equal to the *CLF* transform
            pair.

        Returns
        -------
        :class:`bool`
            Is given object not equal to *CLF* transform pair.
        """

        return not (self == other)


def find_clf_transform_pairs(
    clf_transforms: Sequence[str],
) -> defaultdict[str, dict[str, list[str]]]:
    """
    Find the pairs in given list of *CLF* transform paths.

    Parameters
    ----------
    clf_transforms
        *CLF* transform paths to find the pairs from.

    Returns
    -------
    :class:`defaultdict`
        Pairs of *CLF* transform paths.
    """

    def stem(path: str) -> str:
        """Return the stem of given path."""

        return os.path.splitext(os.path.basename(path))[0]

    # NOTE: We are currently relying on the ordered "CLF" transform basenames
    # to define which transform is the forward transform.
    paths = defaultdict(list)
    for clf_transform in sorted(clf_transforms, key=stem):
        forward_path = tuple(stem(clf_transform).split("_to_", 1))
        inverse_path = tuple(reversed(forward_path))
        if inverse_path in paths:
            paths[inverse_path].append(clf_transform)
        else:
            paths[forward_path].append(clf_transform)

    clf_transform_pairs = defaultdict(dict)
    for clf_transforms in paths.values():
        basename = stem(clf_transforms[0])
        clf_transform_pairs[basename]["forward_transform"] = clf_transforms[0]
        if len(clf_transforms) > 1:
            clf_transform_pairs[basename]["inverse_transform"] = clf_transforms[1]
            clf_transform_pairs[basename]["forward_transform"].siblings.append(
                clf_transform_pairs[basename]["inverse_transform"]
            )
            clf_transform_pairs[basename]["inverse_transform"].siblings.append(
                clf_transform_pairs[basename]["forward_transform"]
            )

    return clf_transform_pairs


def discover_clf_transforms(
    root_directory: str = ROOT_TRANSFORMS_CLF,
) -> defaultdict[str, list[str]]:
    """
    Discover the *CLF* transform paths in given root directory: The given
    directory is traversed and the `*.clf` files are collected.

    Parameters
    ----------
    root_directory
        Root directory to traverse to find the *CLF* transforms.

    Returns
    -------
    :class:`defaultdict`
        Discovered *CLF* transform paths.

    Examples
    --------
    >>> clf_transforms = discover_clf_transforms()
    >>> key = sorted(clf_transforms.keys())[0]
    >>> os.path.basename(key)
    'input'
    >>> sorted([os.path.basename(path) for path in clf_transforms[key]])[:2]
    ['Apple.Input.Apple_Log-Curve.clf', \
'Apple.Input.Apple_Log_to_ACES2065-1.clf']
    """

    root_directory = os.path.normpath(os.path.expandvars(root_directory))

    clf_transforms = defaultdict(list)
    for directory, _sub_directories, filenames in os.walk(root_directory):
        if not filenames:
            continue

        for filename in filenames:
            if not filename.lower().endswith(EXTENSION_CLF):
                continue

            clf_transform = os.path.join(directory, filename)

            LOGGER.debug(
                '"%s" CLF transform was found!',
                clf_transform_relative_path(clf_transform),
            )

            clf_transforms[directory].append(clf_transform)

    return clf_transforms


TypeClassifiedCLFTransforms = dict[
    str, dict[str, dict[str, CLFTransform | CLFTransformPair]]
]


def classify_clf_transforms(
    unclassified_clf_transforms: defaultdict[str, list[str]],
) -> TypeClassifiedCLFTransforms:
    """
    Classify given *CLF* transforms.

    Parameters
    ----------
    unclassified_clf_transforms
        Unclassified *CLF* transforms as returned by
        :func:`opencolorio_config_aces.discover_clf_transforms` definition.

    Returns
    -------
    :class:`dict`
        Classified *CLF* transforms.

    Examples
    --------
    >>> clf_transforms = classify_clf_transforms(
    ...     discover_clf_transforms())
    >>> family = sorted(clf_transforms.keys())[0]
    >>> str(family)
    'apple'
    >>> genera = sorted(clf_transforms[family])
    >>> print(genera)
    ['Input']
    >>> genus = genera[0]
    >>> sorted(clf_transforms[family][genus].items())[:2]  # doctest: +ELLIPSIS
    [('Apple.Input.Apple_Log-Curve', \
CLFTransform(\
'apple...input...Apple.Input.Apple_Log-Curve.clf')), \
('Apple.Input.Apple_Log_to_ACES2065-1', \
CLFTransform(\
'apple...input...Apple.Input.Apple_Log_to_ACES2065-1.clf'))]
    """

    classified_clf_transforms = defaultdict(lambda: defaultdict(dict))

    root_directory = paths_common_ancestor(
        *itertools.chain.from_iterable(unclassified_clf_transforms.values())
    )
    for directory, clf_transforms in unclassified_clf_transforms.items():
        if directory == root_directory:
            sub_directory = os.path.basename(root_directory)
        else:
            sub_directory = directory.replace(f"{root_directory}{os.sep}", "")

        family, *genus = (
            TRANSFORM_FAMILIES_CLF.get(part, part)
            for part in sub_directory.split(os.sep)
        )

        genus = TRANSFORM_GENUS_DEFAULT_CLF if not genus else "/".join(genus)

        for basename, pairs in find_clf_transform_pairs(clf_transforms).items():
            if len(pairs) == 1:
                clf_transform = CLFTransform(
                    cast(str, next(iter(pairs.values()))),
                    family,
                    genus,
                )

                LOGGER.debug('Classifying "%s" under "%s".', clf_transform, genus)

                classified_clf_transforms[family][genus][basename] = clf_transform

            elif len(pairs) == 2:
                forward_clf_transform = CLFTransform(
                    cast(str, pairs["forward_transform"]), family, genus
                )
                inverse_clf_transform = CLFTransform(
                    cast(str, pairs["inverse_transform"]), family, genus
                )

                clf_transform = CLFTransformPair(
                    forward_clf_transform, inverse_clf_transform
                )

                LOGGER.debug('Classifying "%s" under "%s".', clf_transform, genus)

                classified_clf_transforms[family][genus][basename] = clf_transform

    return vivified_to_dict(classified_clf_transforms)


TypeUnclassifiedCLFTransforms = list[CLFTransform]


def unclassify_clf_transforms(
    classified_clf_transforms: TypeClassifiedCLFTransforms,
) -> TypeUnclassifiedCLFTransforms:
    """
    Unclassify given *CLF* transforms.

    Parameters
    ----------
    classified_clf_transforms
        Classified *CLF* transforms as returned by
        :func:`opencolorio_config_aces.classify_clf_transforms` definition.

    Returns
    -------
    :class:`list`
        Unclassified *CLF* transforms.

    Examples
    --------
    >>> clf_transforms = classify_clf_transforms(
    ...     discover_clf_transforms())
    >>> sorted(  # doctest: +ELLIPSIS
    ...     unclassify_clf_transforms(clf_transforms), key=lambda x: x.path)[0]
    CLFTransform('apple...input...Apple.Input.Apple_Log-Curve.clf')
    """

    unclassified_clf_transforms = []
    for genera in classified_clf_transforms.values():
        for clf_transforms in genera.values():
            for clf_transform in clf_transforms.values():
                if isinstance(clf_transform, CLFTransform):
                    unclassified_clf_transforms.append(clf_transform)
                elif isinstance(clf_transform, CLFTransformPair):
                    unclassified_clf_transforms.append(clf_transform.forward_transform)
                    unclassified_clf_transforms.append(clf_transform.inverse_transform)

    return unclassified_clf_transforms


def filter_clf_transforms(
    clf_transforms: TypeClassifiedCLFTransforms | TypeUnclassifiedCLFTransforms,
    filterers: Sequence[Callable] | None = None,
) -> list[CLFTransform]:
    """
    Filter given *CLF* transforms with given filterers.

    Parameters
    ----------
    clf_transforms
        *CLF* transforms as returned by
        :func:`opencolorio_config_aces.classify_clf_transforms` or
        :func:`opencolorio_config_aces.unclassify_clf_transforms`
        definitions.
    filterers
        List of callables used to filter the *CLF* transforms, each callable
        takes a *CLF* transform as argument and returns whether to include or
        exclude the *CLF* transform as a bool.

    Returns
    -------
    :class:`list`
        Filtered *CLF* transforms.

    Warnings
    --------
    -   This definition will forcibly unclassify the given *CLF* transforms and
        return a flattened list.

    Examples
    --------
    >>> clf_transforms = classify_clf_transforms(
    ...     discover_clf_transforms())
    >>> sorted(  # doctest: +ELLIPSIS
    ...     filter_clf_transforms(
    ...         clf_transforms,
    ...         [lambda x: x.family == 'blackmagic']),
    ...     key=lambda x: x.path)[0]
    CLFTransform(\
'blackmagic...input...BlackmagicDesign.Input.BMDFilm_Gen5_Log-Curve.clf')
    """

    filterers = optional(filterers, TRANSFORM_FILTERERS_DEFAULT_CLF)

    if isinstance(clf_transforms, Mapping):
        clf_transforms = unclassify_clf_transforms(clf_transforms)

    filtered_clf_transforms = []
    for clf_transform in clf_transforms:
        included = True
        for filterer in filterers:
            included *= filterer(clf_transform)

        if included:
            filtered_clf_transforms.append(clf_transform)

    return filtered_clf_transforms


def print_clf_taxonomy() -> None:
    """
    Print the *builtins* *CLF* taxonomy:

    -   The *CLF* transforms are discovered by traversing the directory defined
        by the :attr:`opencolorio_config_aces.clf.\
reference.ROOT_TRANSFORMS_CLF` attribute using the
        :func:`opencolorio_config_aces.discover_clf_transforms` definition.
    -   The *CLF* transforms are classified by *family* e.g., *aces*, and
        *genus* e.g., *undefined* using the
        :func:`opencolorio_config_aces.classify_clf_transforms` definition.
    -   The resulting data structure is printed.
    """

    classified_clf_transforms = classify_clf_transforms(discover_clf_transforms())

    for family, genera in classified_clf_transforms.items():
        message_box(family, print_callable=LOGGER.info)
        for genus, clf_transforms in genera.items():
            LOGGER.info("[ %s ]", genus)
            for name, clf_transform in clf_transforms.items():
                LOGGER.info("\t( %s )", name)
                if isinstance(clf_transform, CLFTransform):
                    LOGGER.info(
                        '\t\t"%s" --> "%s"',
                        clf_transform.source,
                        clf_transform.target,
                    )
                    if clf_transform.clf_transform_id is not None:
                        LOGGER.info(
                            '\t\tCLFtransformID : "%s"',
                            clf_transform.clf_transform_id.clf_transform_id,
                        )
                elif isinstance(clf_transform, CLFTransformPair):
                    LOGGER.info(
                        '\t\t"%s" <--> "%s"',
                        clf_transform.forward_transform.source,
                        clf_transform.forward_transform.target,
                    )
                    if clf_transform.forward_transform.clf_transform_id is not None:
                        LOGGER.info(
                            '\t\tACEStransformID : "%s"',
                            clf_transform.forward_transform.clf_transform_id.clf_transform_id,
                        )
                    if clf_transform.inverse_transform.clf_transform_id is not None:
                        LOGGER.info(
                            '\t\tACEStransformID : "%s"',
                            clf_transform.inverse_transform.clf_transform_id.clf_transform_id,
                        )


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    print_clf_taxonomy()
