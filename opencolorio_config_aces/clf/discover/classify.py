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

import itertools
import logging
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Mapping

from opencolorio_config_aces.utilities import (
    message_box,
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

URN_CLF = "urn:aswf:ocio:transformId:1.0"
"""
*CLF* Uniform Resource Name (*URN*).

URN_CLF : unicode
"""

SEPARATOR_VERSION_CLF = "."
"""
*CLFtransformID* separator used to tokenize the *VERSION* parts of the
*CLFtransformID*.

urn:aswf:ocio:transformId:1.0:OCIO:ACES:AP0_to_AP1-Gamma2pnt2:1.0
                         |---|                               |---|

SEPARATOR_ID_CLF : unicode
"""

SEPARATOR_ID_CLF = ":"
"""
*CLFtransformID* separator used to tokenize the *ID* part of the
*CLFtransformID*.

urn:aswf:ocio:transformId:1.0:OCIO:ACES:AP0_to_AP1-Gamma2pnt2:1.0
|-------------URN-----------|:|----------------ID---------------|

SEPARATOR_ID_CLF : unicode
"""

NAMESPACE_CLF = "OCIO"
"""
Namespace for the *OCIO* *CLF* transforms.

NAMESPACE_CLF : unicode
"""

TRANSFORM_TYPES_CLF = [
    "Utility",
]
"""
*CLF* transform types.

TRANSFORM_TYPES_CLF : list
"""

TRANSFORM_FAMILIES_CLF = {"utility": "Utility"}
"""
*CLF* transform families mapping the *CLF* transform directories to family
names.

TRANSFORM_FAMILIES_CLF : dict
"""

TRANSFORM_GENUS_DEFAULT_CLF = "undefined"
"""
*CLF* transform default genus, i.e. *undefined*.

TRANSFORM_GENUS_DEFAULT_CLF : unicode
"""

TRANSFORM_FILTERERS_DEFAULT_CLF = []
"""
Default list of *CLF* transform filterers.

TRANSFORM_FILTERERS_DEFAULT_CLF : list
"""

PATTERNS_DESCRIPTION_CLF = {}
"""
*CLF* transform description substitution patterns.

PATTERNS_DESCRIPTION_CLF : dict
"""

ROOT_TRANSFORMS_CLF = os.path.normpath(
    os.environ.get(
        "OPENCOLORIO_CONFIG_ACES__CLF_TRANSFORMS_ROOT",
        os.path.join(os.path.dirname(__file__), "..", "transforms", "ocio"),
    )
)
"""
*CLF* transforms root directory, default to the version controlled
sub-module repository. It can be defined by setting the
`OPENCOLORIO_CONFIG_ACES__CLF_TRANSFORMS_ROOT` environment variable with
the local 'transforms/clf' directory.

ROOT_TRANSFORMS_CLF : unicode
"""


def clf_transform_relative_path(path, root_directory=ROOT_TRANSFORMS_CLF):
    """
    Return the relative path from given *CLF* transform to the *CLF* transforms
    root directory.

    Parameters
    ----------
    path : unicode
        *CLF* transform absolute path.
    root_directory : unicode, optional
        *CLF* transforms root directory.

    Returns
    -------
    unicode
         *CLF* transform relative path.
    """

    return path.replace(f"{root_directory}{os.sep}", "")


class CLFTransformID:
    """
    Define the *CLF* transform *CLFtransformID*: an object parsing and storing
    information about a *CLFtransformID* unicode string.

    Parameters
    ----------
    clf_transform_id : unicode
        *CLFtransformID*, e.g.
        *urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_AP1-Gamma2pnt2.c1.v1*.

    Attributes
    ----------
    clf_transform_id
    urn
    type
    namespace
    name
    major_version_number
    minor_version_number
    patch_version_number
    source
    target

    Methods
    -------
    __str__
    __repr__
    """

    def __init__(self, clf_transform_id):
        self._clf_transform_id = clf_transform_id

        self._urn = None
        self._type = None
        self._namespace = None
        self._name = None
        self._major_version_number = None
        self._minor_version_number = None
        self._patch_version_number = None
        self._source = None
        self._target = None

        self._parse()

    @property
    def clf_transform_id(self):
        """
        Getter and setter property for the *CLFtransformID*, e.g.
        *urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_AP1-Gamma2pnt2.c1.v1*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._clf_transform_id

    @property
    def urn(self):
        """
        Getter and setter property for the *CLFtransformID* Uniform Resource
        Name (*URN*), e.g. *urn:aswf:ocio:transformId:v1.0*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* Uniform Resource Name (*URN*).

        Notes
        -----
        -   This property is read only.
        """

        return self._urn

    @property
    def type(self):
        """
        Getter and setter property for the *CLFtransformID* type, e.g. *ACES*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* type.

        Notes
        -----
        -   This property is read only.
        """

        return self._type

    @property
    def namespace(self):
        """
        Getter and setter property for the *CLFtransformID* namespace, e.g.
        *OCIO*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* namespace.

        Notes
        -----
        -   This property is read only.
        """

        return self._namespace

    @property
    def name(self):
        """
        Getter and setter property for the *CLFtransformID* name, e.g.
        *AP0_to_AP1-Gamma2pnt2*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* name.

        Notes
        -----
        -   This property is read only.
        """

        return self._name

    @property
    def major_version_number(self):
        """
        Getter and setter property for the *CLFtransformID* major version
        number, e.g. *c1*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* major version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._major_version_number

    @property
    def minor_version_number(self):
        """
        Getter and setter property for the *CLFtransformID* minor version
        number, e.g. *v1*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* minor version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._minor_version_number

    @property
    def patch_version_number(self):
        """
        Getter and setter property for the *CLFtransformID* patch version
        number.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* patch version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._patch_version_number

    @property
    def source(self):
        """
        Getter and setter property for the *CLFtransformID* source colourspace.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* source colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._source

    @property
    def target(self):
        """
        Getter and setter property for the *CLFtransformID* target colourspace.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLFtransformID* target colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._target

    def __str__(self):
        """
        Return a formatted string representation of the *CLFtransformID*.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return f"{self.__class__.__name__}(" f"'{self._clf_transform_id}')"

    def __repr__(self):
        """
        Return an evaluable string representation of the *CLFtransformID*.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def _parse(self):
        """Parse the *CLFtransformID*."""

        if self._clf_transform_id is None:
            return

        clf_transform_id = self._clf_transform_id

        assert clf_transform_id.startswith(
            URN_CLF
        ), f"{self._clf_transform_id} URN {self._urn} is invalid!"

        self._urn = clf_transform_id[: len(URN_CLF) + 1]
        components = clf_transform_id[len(URN_CLF) + 1 :]
        components = components.split(SEPARATOR_ID_CLF)

        assert (
            len(components) == 4
        ), f'{self._clf_transform_id} is an invalid "CLFtransformID"!'

        (self._namespace, self._type, self._name, version) = components

        assert (
            self._type in TRANSFORM_TYPES_CLF
        ), f"{self._clf_transform_id} type {self._type} is invalid!"

        if self._name is not None:
            self._source, self._target = self._name.split("_to_")

        assert version.count(SEPARATOR_VERSION_CLF) == 1, (
            f'{self._clf_transform_id} has an invalid "CLFtransformID" '
            f"version!"
        )

        (
            self._major_version_number,
            self._minor_version_number,
        ) = version.split(SEPARATOR_VERSION_CLF)


class CLFTransform:
    """
    Define the *CLF* transform class: an object storing information about a
    *CLF* transform file.

    Parameters
    ----------
    path : unicode
        *CLF* transform path.
    family : unicode, optional
        *CLF* transform family, e.g. *aces*
    genus : unicode, optional
        *CLF* transform genus, e.g. *undefined*

    Attributes
    ----------
    path
    code
    clf_transform_id
    user_name
    description
    input_descriptor
    output_descriptor
    family
    genus

    Methods
    -------
    __str__
    __repr__
    __eq__
    __ne__
    """

    def __init__(self, path, family=None, genus=None):
        self._path = os.path.abspath(os.path.normpath(path))

        self._code = None
        self._clf_transform_id = None
        self._user_name = None
        self._description = ""
        self._input_descriptor = ""
        self._output_descriptor = ""

        self._family = family
        self._genus = genus

        self._parse()

    @property
    def path(self):
        """
        Getter and setter property for the *CLF* transform path.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform path.

        Notes
        -----
        -   This property is read only.
        """

        return self._path

    @property
    def code(self):
        """
        Getter and setter property for the *CLF* transform code, i.e. the *CLF*
        transform file content.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform code.

        Notes
        -----
        -   This property is read only.
        -   This property contains the entire file content, i.e. the code along
            with the comments.
        """

        return self._code

    @property
    def clf_transform_id(self):
        """
        Getter and setter property for the *CLF* transform *CLFtransformID*.

        Parameters
        ----------
        value : CLFTransformID
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform *CLFtransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._clf_transform_id

    @property
    def user_name(self):
        """
        Getter and setter property for the *CLF* transform user name.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform user name.

        Notes
        -----
        -   This property is read only.
        """

        return self._user_name

    @property
    def description(self):
        """
        Getter and setter property for the *CLF* transform description
        extracted from parsing the file content header.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform description.

        Notes
        -----
        -   This property is read only.
        """

        return self._description

    @property
    def input_descriptor(self):
        """
        Getter and setter property for the *CLF* transform input descriptor
        extracted from parsing the file content header.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform input descriptor.

        Notes
        -----
        -   This property is read only.
        """

        return self._input_descriptor

    @property
    def output_descriptor(self):
        """
        Getter and setter property for the *CLF* transform output descriptor
        extracted from parsing the file content header.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform output descriptor.

        Notes
        -----
        -   This property is read only.
        """

        return self._output_descriptor

    @property
    def family(self):
        """
        Getter and setter property for the *CLF* transform family, e.g.
        *aces*, a value in
        :attr:`opencolorio_config_aces.clf.reference.\
TRANSFORM_FAMILIES_CLF` attribute dictionary.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform family.

        Notes
        -----
        -   This property is read only.
        """

        return self._family

    @property
    def genus(self):
        """
        Getter and setter property for the *CLF* transform genus, e.g.
        *undefined*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform genus.

        Notes
        -----
        -   This property is read only.
        """

        return self._genus

    def __getattr__(self, item):
        """
        Reimplement the :meth:`object.__getattr__` so that unsuccessful
        attribute lookup on :class:`opencolorio_config_aces.clf.reference.\
CLFTransform` class are tried on the underlying
        :class:`opencolorio_config_aces.clf.reference.CLFTransformID` class
        instance.

        Parameters
        ----------
        item : unicode
            Attribute to lookup the value of.

        Returns
        -------
        object
             Attribute value.
        """

        clf_transform_id = object.__getattribute__(self, "_clf_transform_id")

        return getattr(clf_transform_id, item)

    def __str__(self):
        """
        Return a formatted string representation of the *CLF* transform.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"'{clf_transform_relative_path(self._path)}')"
        )

    def __repr__(self):
        """
        Return an evaluable representation of the *CLF* transform.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
        Return whether the *CLF* transform is equal to given other object.

        Parameters
        ----------
        other : object
            Object to test whether it is equal to the *CLF* transform.

        Returns
        -------
        bool
            Is given object equal to *CLF* transform.
        """

        if not isinstance(other, CLFTransform):
            return False
        else:
            return self._path == other.path

    def __ne__(self, other):
        """
        Return whether the *CLF* transform is not equal to given other
        object.

        Parameters
        ----------
        other : object
            Object to test whether it is not equal to the *CLF* transform.

        Returns
        -------
        bool
            Is given object not equal to *CLF* transform.
        """

        return not (self == other)

    def _parse(self):
        """Parse the *CLF* transform."""

        tree = ET.parse(self._path)
        root = tree.getroot()

        self._clf_transform_id = CLFTransformID(root.attrib["id"])
        self._user_name = root.attrib["name"]

        description = next(iter(root.findall("./Description")), None)
        if description is not None:
            self._description = description.text

        input_descriptor = next(iter(root.findall("./InputDescriptor")), None)
        if input_descriptor is not None:
            self._input_descriptor = input_descriptor.text

        output_descriptor = next(
            iter(root.findall("./OutputDescriptor")), None
        )
        if output_descriptor is not None:
            self._output_descriptor = output_descriptor.text


class CLFTransformPair:
    """
    Define the *CLF* transform pair class: an object storing a pair of
    :class:`opencolorio_config_aces.clf.reference.CLFTransform` class instances
    representing forward and inverse transformation.

    Parameters
    ----------
    forward_transform : CLFTransform
        *CLF* transform forward transform.
    inverse_transform : CLFTransform
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

    def __init__(self, forward_transform, inverse_transform):
        self._forward_transform = forward_transform
        self._inverse_transform = inverse_transform

    @property
    def forward_transform(self):
        """
        Getter and setter property for the *CLF* transform pair forward
        transform.

        Parameters
        ----------
        value : CLFTransform
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform pair forward transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._forward_transform

    @property
    def inverse_transform(self):
        """
        Getter and setter property for the *CLF* transform pair inverse
        transform.

        Parameters
        ----------
        value : CLFTransform
            Attribute value.

        Returns
        -------
        unicode
            *CLF* transform pair inverse transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._inverse_transform

    def __str__(self):
        """
        Return a formatted string representation of the *CLF* transform pair.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"{str(self._forward_transform)}', "
            f"{str(self._inverse_transform)}')"
        )

    def __repr__(self):
        """
        Return an evaluable string representation of the *CLF* transform pair.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
        Return whether the *CLF* transform pair is equal to given other
        object.

        Parameters
        ----------
        other : object
            Object to test whether it is equal to the *CLF* transform pair.

        Returns
        -------
        bool
            Is given object equal to *CLF* transform pair.
        """

        if not isinstance(other, CLFTransformPair):
            return False
        else:
            (
                (self._forward_transform == other._forward_transform)
                and (self._inverse_transform == other._inverse_transform)
            )

    def __ne__(self, other):
        """
        Return whether the *CLF* transform pair is not equal to given other
        object.

        Parameters
        ----------
        other : object
            Object to test whether it is not equal to the *CLF* transform
            pair.

        Returns
        -------
        bool
            Is given object not equal to *CLF* transform pair.
        """

        return not (self == other)


def find_clf_transform_pairs(clf_transforms):
    """
    Find the pairs in given list of *CLF* transform paths.

    Parameters
    ----------
    clf_transforms : array_like
        *CLF* transform paths to find the pairs from.

    Returns
    -------
    dict
        .. math::

            \\{``basename_1'': \\{
            ``forward\\_transform'': ``forward\\_transform_1.clf'',
            ``inverse\\_transform'': ``inverse\\_transform_1.clf''\\},
            \\ldots, 'basename_n': \\{
            ``forward\\_transform'': ``forward\\_transform_n.clf'',
            ``inverse\\_transform'': ``inverse\\_transform_n.clf''\\}\\}
    """

    def stem(path):
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
            clf_transform_pairs[basename][
                "inverse_transform"
            ] = clf_transforms[1]

    return clf_transform_pairs


def discover_clf_transforms(root_directory=ROOT_TRANSFORMS_CLF):
    """
    Discover the *CLF* transform paths in given root directory: The given
    directory is traversed and the `*.clf` files are collected.

    Parameters
    ----------
    root_directory : unicode
        Root directory to traverse to find the *CLF* transforms.

    Returns
    -------
    dict
        .. math::

            \\{``directory_1'':
            \\left[``transform_a.clf'', ``transform_b.clf''\\right],\\\\
            \\ldots,\\\\
            ``directory_n'':
            \\left[``transform_c.clf'', ``transform_d.clf''\\right]\\}

    Examples
    --------
    >>> clf_transforms = discover_clf_transforms()
    >>> key = sorted(clf_transforms.keys())[0]
    >>> os.path.basename(key)
    'utility'
    >>> sorted([os.path.basename(path) for path in clf_transforms[key]])[:2]
    ['OCIO.Utility.AP0_to_AP1-Gamma2.2.clf', \
'OCIO.Utility.AP0_to_P3-D65-Linear.clf']
    """

    root_directory = os.path.normpath(os.path.expandvars(root_directory))

    clf_transforms = defaultdict(list)
    for directory, _sub_directories, filenames in os.walk(root_directory):
        if not filenames:
            continue

        for filename in filenames:
            if not filename.lower().endswith("clf"):
                continue

            clf_transform = os.path.join(directory, filename)

            logging.debug(
                f'"{clf_transform_relative_path(clf_transform)}" '
                f"CLF transform was found!"
            )

            clf_transforms[directory].append(clf_transform)

    return clf_transforms


def classify_clf_transforms(unclassified_clf_transforms):
    """
    Classifie given *CLF* transforms.

    Parameters
    ----------
    unclassified_clf_transforms : dict
        Unclassified *CLF* transforms as returned by
        :func:`opencolorio_config_aces.discover_clf_transforms` definition.

    Returns
    -------
    dict
        .. math::

            \\{``family_1'': \\{``genus_1'': \\{\\}_{CLF_1},
            \\ldots,
            ``family_n'': \\{``genus_2'':\\{\\}_{CLF_2}\\}\\}

        where

        .. math::

            \\{\\}_{CLF_n}=\\{``basename_n'': CLFTransform_n,
            \\ldots,
            ``basename_{n + 1}'': CLFTransform_{n + 1}\\}

    Examples
    --------
    >>> clf_transforms = classify_clf_transforms(
    ...     discover_clf_transforms())
    >>> family = sorted(clf_transforms.keys())[0]
    >>> str(family)
    'Utility'
    >>> genera = sorted(clf_transforms[family])
    >>> print(genera)
    ['undefined']
    >>> genus = genera[0]
    >>> sorted(clf_transforms[family][genus].items())[:2]  # doctest: +ELLIPSIS
    [('OCIO.Utility.AP0_to_AP1-Gamma2.2', \
CLFTransform('utility...OCIO.Utility.AP0_to_AP1-Gamma2.2.clf')), \
('OCIO.Utility.AP0_to_P3-D65-Linear', \
CLFTransform('utility...OCIO.Utility.AP0_to_P3-D65-Linear.clf'))]
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

        for basename, pairs in find_clf_transform_pairs(
            clf_transforms
        ).items():
            if len(pairs) == 1:
                clf_transform = CLFTransform(
                    list(pairs.values())[0], family, genus
                )

                logging.debug(
                    f'Classifying "{clf_transform}" under "{genus}".'
                )

                classified_clf_transforms[family][genus][
                    basename
                ] = clf_transform

            elif len(pairs) == 2:
                forward_clf_transform = CLFTransform(
                    pairs["forward_transform"], family, genus
                )
                inverse_clf_transform = CLFTransform(
                    pairs["inverse_transform"], family, genus
                )

                clf_transform = CLFTransformPair(
                    forward_clf_transform, inverse_clf_transform
                )

                logging.debug(
                    f'Classifying "{clf_transform}" under "{genus}".'
                )

                classified_clf_transforms[family][genus][
                    basename
                ] = clf_transform

    return vivified_to_dict(classified_clf_transforms)


def unclassify_clf_transforms(classified_clf_transforms):
    """
    Unclassifie given *CLF* transforms.

    Parameters
    ----------
    classified_clf_transforms : dict
        Classified *CLF* transforms as returned by
        :func:`opencolorio_config_aces.classify_clf_transforms` definition.

    Returns
    -------
    list
        .. math::

            \\left[CLFTransform_1, \\ldots, CLFTransform_n\\right]

    Examples
    --------
    >>> clf_transforms = classify_clf_transforms(
    ...     discover_clf_transforms())
    >>> sorted(  # doctest: +ELLIPSIS
    ...     unclassify_clf_transforms(clf_transforms), key=lambda x: x.path)[0]
    CLFTransform('utility...OCIO.Utility.AP0_to_AP1-Gamma2.2.clf')
    """

    unclassified_clf_transforms = []
    for genera in classified_clf_transforms.values():
        for clf_transforms in genera.values():
            for clf_transform in clf_transforms.values():
                if isinstance(clf_transform, CLFTransform):
                    unclassified_clf_transforms.append(clf_transform)
                elif isinstance(clf_transform, CLFTransformPair):
                    unclassified_clf_transforms.append(
                        clf_transform.forward_transform
                    )
                    unclassified_clf_transforms.append(
                        clf_transform.inverse_transform
                    )

    return unclassified_clf_transforms


def filter_clf_transforms(clf_transforms, filterers=None):
    """
    Filter given *CLF* transforms with given filterers.

    Parameters
    ----------
    clf_transforms : dict or list
        *CLF* transforms as returned by
        :func:`opencolorio_config_aces.classify_clf_transforms` or
        :func:`opencolorio_config_aces.unclassify_clf_transforms`
        definitions.
    filterers : array_like, optional
        List of callables used to filter the *CLF* transforms, each callable
        takes a *CLF* transform as argument and returns whether to include or
        exclude the *CLF* transform as a bool.

    Returns
    -------
    list
        .. math::

            \\left[CLFTransform_1, \\ldots, CLFTransform_n\\right]

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
    ...         [lambda x: x.family == 'Utility']),
    ...     key=lambda x: x.path)[0]
    CLFTransform('utility...OCIO.Utility.AP0_to_AP1-Gamma2.2.clf')
    """

    if filterers is None:
        filterers = TRANSFORM_FILTERERS_DEFAULT_CLF

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


def print_clf_taxonomy():
    """
    Print the *builtins* *CLF* taxonomy:

    -   The *CLF* transforms are discovered by traversing the directory defined
        by the :attr:`opencolorio_config_aces.clf.\
reference.ROOT_TRANSFORMS_CLF` attribute using the
        :func:`opencolorio_config_aces.discover_clf_transforms` definition.
    -   The *CLF* transforms are classified by *family* e.g. *aces*, and
        *genus* e.g. *undefined* using the
        :func:`opencolorio_config_aces.classify_clf_transforms` definition.
    -   The resulting data structure is printed.
    """

    classified_clf_transforms = classify_clf_transforms(
        discover_clf_transforms()
    )

    for family, genera in classified_clf_transforms.items():
        message_box(family, print_callable=logging.info)
        for genus, clf_transforms in genera.items():
            logging.info(f"[ {genus} ]")
            for name, clf_transform in clf_transforms.items():
                logging.info(f"\t( {name} )")
                if isinstance(clf_transform, CLFTransform):
                    logging.info(
                        f'\t\t"{clf_transform.source}"'
                        f" --> "
                        f'"{clf_transform.target}"'
                    )
                elif isinstance(clf_transform, CLFTransformPair):
                    logging.info(
                        f'\t\t"{clf_transform.forward_transform.source}"'
                        f" <--> "
                        f'"{clf_transform.forward_transform.target}"'
                    )


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    print_clf_taxonomy()
