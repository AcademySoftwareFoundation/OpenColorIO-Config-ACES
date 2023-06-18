# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Reference Implementation Discovery & Classification
==============================================================

Defines various objects related to *aces-dev* reference implementation *CTL*
transforms discovery and classification:

-   :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.unclassify_ctl_transforms`
-   :func:`opencolorio_config_aces.filter_ctl_transforms`
-   :func:`opencolorio_config_aces.print_aces_taxonomy`
"""

import itertools
import logging

# TODO: Use "pathlib".
import os
import re
import subprocess
from collections.abc import Mapping
from collections import defaultdict

from opencolorio_config_aces.utilities import (
    attest,
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
    "URN_CTL",
    "SEPARATOR_URN_CTL",
    "SEPARATOR_ID_CTL",
    "EXTENSION_CTL",
    "NAMESPACE_CTL",
    "TRANSFORM_TYPES_CTL",
    "TRANSFORM_FAMILIES_CTL",
    "TRANSFORM_GENUS_DEFAULT_CTL",
    "TRANSFORM_FILTERERS_DEFAULT_CTL",
    "PATTERNS_DESCRIPTION_CTL",
    "patch_invalid_aces_transform_id",
    "ROOT_TRANSFORMS_CTL",
    "version_aces_dev",
    "ctl_transform_relative_path",
    "ACESTransformID",
    "CTLTransform",
    "CTLTransformPair",
    "find_ctl_transform_pairs",
    "discover_aces_ctl_transforms",
    "classify_aces_ctl_transforms",
    "unclassify_ctl_transforms",
    "filter_ctl_transforms",
    "print_aces_taxonomy",
]

logger = logging.getLogger(__name__)


URN_CTL = "urn:ampas:aces:transformId:v1.5"
"""
*ACES* Uniform Resource Name (*URN*).

URN_CTL : unicode
"""

SEPARATOR_URN_CTL = ":"
"""
*ACEStransformID* separator used to separate the *URN* and *ID* part of the
*ACEStransformID*.

SEPARATOR_URN_CTL : unicode
"""

SEPARATOR_ID_CTL = "."
"""
*ACEStransformID* separator used to tokenize the *ID* part of the
*ACEStransformID*.

urn:ampas:aces:transformId:v1.5:ODT.Academy.DCDM.a1.0.3
|-------------URN-------------|:|----------ID---------|

SEPARATOR_ID_CTL : unicode
"""

EXTENSION_CTL = ".ctl"
"""
*CTL* transform extension.

EXTENSION_CTL : unicode
"""

NAMESPACE_CTL = "Academy"
"""
*ACES* namespace for *A.M.P.A.S* official *CTL* transforms.

NAMESPACE_CTL : unicode
"""

TRANSFORM_TYPES_CTL = [
    "IDT",
    "LMT",
    "ODT",
    "RRT",
    "RRTODT",
    "InvRRT",
    "InvODT",
    "InvRRTODT",
    "ACESlib",
    "ACEScsc",
    "ACESutil",
]
"""
*ACES* *CTL* transform types.

TRANSFORM_TYPES_CTL : list
"""

TRANSFORM_FAMILIES_CTL = {
    "csc": "csc",
    "idt": "input_transform",
    "lib": "lib",
    "lmt": "lmt",
    "odt": "output_transform",
    "outputTransforms": "output_transform",
    "rrt": "rrt",
    "utilities": "utility",
}
"""
*ACES* *CTL* transform families mapping the *CTL* transform directories to
family names.

TRANSFORM_FAMILIES_CTL : dict
"""

TRANSFORM_GENUS_DEFAULT_CTL = "undefined"
"""
*ACES* *CTL* transform default genus, i.e. *undefined*.

TRANSFORM_GENUS_DEFAULT_CTL : unicode
"""


def _exclusion_filterer_ARRIIDT(ctl_transform):
    """
    Filter out the *Alexa* *ACES* *CTL* transform whose name does not contain:

    - 'Alexa-v3-raw-EI800'
    - 'ND1pt3'

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to filter

    Returns
    -------
    bool
        Whether to include or excluded given *ACES* *CTL* transform.
    """

    path = ctl_transform.path

    if "Alexa" not in path:
        return True

    if "Alexa-v3-logC" in path:
        return True

    return False


TRANSFORM_FILTERERS_DEFAULT_CTL = [
    _exclusion_filterer_ARRIIDT,
]
"""
Default list of *ACES* *CTL* transform filterers.

TRANSFORM_FILTERERS_DEFAULT_CTL : list
"""

PATTERNS_DESCRIPTION_CTL = {
    "============ CONSTANTS ============ //": "",
    "Written by .*_IDT_maker\\.py v.* on .*": "",
}
"""
*ACES* *CTL* transform description substitution patterns.

PATTERNS_DESCRIPTION_CTL : dict
"""


def patch_invalid_aces_transform_id(aces_transform_id):
    """
    Patchan invalid *ACEStransformID*, see the *Notes* section for relevant
    issues supported by this definition.

    Parameters
    ----------
    aces_transform_id : unicode
        Invalid *ACEStransformID* to patch.

    Returns
    -------
    unicode
        Patched *ACEStransformID*.

    Notes
    -----
    -   Fixed by https://github.com/scottdyer/aces-dev/\
commit/4b88ef35afc41e58ea52d9acde68af24e75b58c5
        - https://github.com/ampas/aces-dev/issues/118
        - https://github.com/ampas/aces-dev/pull/119
    """

    # Addressed with https://github.com/scottdyer/aces-dev/
    # commit/4b88ef35afc41e58ea52d9acde68af24e75b58c5
    if False:
        invalid_id = aces_transform_id
        if not aces_transform_id.startswith(URN_CTL):
            logger.warning('"%s" is missing "ACES" URN!', invalid_id)

            aces_transform_id = f"{URN_CTL}:{aces_transform_id}"

        if "Academy.P3D65_108nits_7.2nits_ST2084" in aces_transform_id:
            logger.warning(
                '"%s" has an invalid separator in "7.2nits"!', invalid_id
            )

            aces_transform_id = aces_transform_id.replace("7.2", "7")
        elif "P3D65_709limit_48nits" in aces_transform_id:
            logger.warning('"%s" is inconsistently named!', invalid_id)

            aces_transform_id = aces_transform_id.replace(
                "P3D65_709limit_48nits", "P3D65_Rec709limited_48nits"
            )
        elif "Rec2020_100nits.a1.1.0" in aces_transform_id:
            logger.warning('"%s" is incorrectly named!', invalid_id)

            aces_transform_id = aces_transform_id.replace(
                "Rec2020_100nits", "Rec2020_P3D65limited_100nits_dim"
            )
        elif "ACEScsc" in aces_transform_id:
            if "ACEScsc.Academy" not in aces_transform_id:
                logger.warning(
                    '"%s" is missing "Academy" namespace!', invalid_id
                )

                aces_transform_id = aces_transform_id.replace(
                    "ACEScsc", "ACEScsc.Academy"
                )

            if aces_transform_id.endswith("a1.v1"):
                logger.warning('"%s" version scheme is invalid!', invalid_id)

                aces_transform_id = aces_transform_id.replace(
                    "a1.v1", "a1.1.0"
                )

    return aces_transform_id


ROOT_TRANSFORMS_CTL = os.path.normpath(
    os.environ.get(
        "OPENCOLORIO_CONFIG_CTL__CTL_TRANSFORMS_ROOT",
        os.path.join(
            os.path.dirname(__file__), "../", "aces-dev", "transforms", "ctl"
        ),
    )
)
"""
*aces-dev* *CTL* transforms root directory, default to the version controlled
sub-module repository. It can be defined by setting the
`OPENCOLORIO_CONFIG_CTL__CTL_TRANSFORMS_ROOT` environment variable with
the local 'aces-dev/transforms/ctl' directory.

ROOT_TRANSFORMS_CTL : unicode
"""


def version_aces_dev():
    """
    Return the current *aces-dev* version, trying first with *git*, then by
    parsing the *CHANGELOG.md* file.

    Returns
    -------
    str
        *aces-dev* version.
    """

    try:  # pragma: no cover
        version = subprocess.check_output(
            ["git", "describe"],  # noqa: S603, S607
            cwd=ROOT_TRANSFORMS_CTL,
            stderr=subprocess.STDOUT,
        ).strip()
        return version.decode("utf-8")
    except Exception:  # pragma: no cover
        changelog_path = os.path.join(
            ROOT_TRANSFORMS_CTL, "..", "..", "CHANGELOG.md"
        )
        if os.path.exists(changelog_path):
            with open(changelog_path) as changelog_file:
                for line in changelog_file.readlines():
                    search = re.search(r"Version\s+(\d\.\d(\.\d)?)", line)
                    if search:
                        return search.group(1)
        else:
            return "Undefined"


def ctl_transform_relative_path(path, root_directory=ROOT_TRANSFORMS_CTL):
    """
    Return the relative path from given *ACES* *CTL* transform to the
    *aces-dev* *CTL* transforms root directory.

    Parameters
    ----------
    path : unicode
        *ACES* *CTL* transform absolute path.
    root_directory : unicode, optional
        *aces-dev* *CTL* transforms root directory.

    Returns
    -------
    unicode
         *ACES* *CTL* transform relative path.
    """

    return path.replace(f"{root_directory}{os.sep}", "")


class ACESTransformID:
    """
    Define the *ACES* *CTL* transform *ACEStransformID*: an object parsing and
    storing information about an *ACEStransformID* unicode string.

    Parameters
    ----------
    aces_transform_id : unicode
        *ACEStransformID*, e.g.
        *urn:ampas:aces:transformId:v1.5:ODT.Academy.DCDM.a1.0.3*.

    Attributes
    ----------
    aces_transform_id
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

    def __init__(self, aces_transform_id):
        self._aces_transform_id = aces_transform_id

        self._urn = None
        self._type = None
        self._namespace = None
        self._name = None
        self._major_version = None
        self._minor_version = None
        self._patch_version = None
        self._source = None
        self._target = None

        self._parse()

    @property
    def aces_transform_id(self):
        """
        Getter property for the *ACEStransformID*, e.g.
        *urn:ampas:aces:transformId:v1.5:ODT.Academy.DCDM.a1.0.3*.

        Returns
        -------
        unicode
            *ACEStransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._aces_transform_id

    @property
    def urn(self):
        """
        Getter property for the *ACEStransformID* Uniform Resource Name (*URN*),
        e.g. *urn:ampas:aces:transformId:v1.5*.

        Returns
        -------
        unicode
            *ACEStransformID* Uniform Resource Name (*URN*).

        Notes
        -----
        -   This property is read only.
        """

        return self._urn

    @property
    def type(self):  # noqa: A003
        """
        Getter property for the *ACEStransformID* type, e.g. *ODT*.

        Returns
        -------
        unicode
            *ACEStransformID* type.

        Notes
        -----
        -   This property is read only.
        """

        return self._type

    @property
    def namespace(self):
        """
        Getter property for the *ACEStransformID* namespace, e.g. *Academy*.

        Returns
        -------
        unicode
            *ACEStransformID* namespace.

        Notes
        -----
        -   This property is read only.
        """

        return self._namespace

    @property
    def name(self):
        """
        Getter property for the *ACEStransformID* name, e.g. *DCDM*.

        Returns
        -------
        unicode
            *ACEStransformID* name.

        Notes
        -----
        -   This property is read only.
        """

        return self._name

    @property
    def major_version(self):
        """
        Getter property for the *ACEStransformID* major version number, e.g.
        *a1*.

        Returns
        -------
        unicode
            *ACEStransformID* major version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._major_version

    @property
    def minor_version(self):
        """
        Getter property for the *ACEStransformID* minor version number, e.g.
        *0*.

        Returns
        -------
        unicode
            *ACEStransformID* minor version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._minor_version

    @property
    def patch_version(self):
        """
        Getterproperty for the *ACEStransformID* patch version number, e.g. *3*.

        Returns
        -------
        unicode
            *ACEStransformID* patch version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._patch_version

    @property
    def source(self):
        """
        Getter property for the *ACEStransformID* source colourspace.

        Returns
        -------
        unicode
            *ACEStransformID* source colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._source

    @property
    def target(self):
        """
        Getter property for the *ACEStransformID* target colourspace.

        Returns
        -------
        unicode
            *ACEStransformID* target colourspace.

        Notes
        -----
        -   This property is read only.
        """

        return self._target

    def __str__(self):
        """
        Return a formatted string representation of the *ACEStransformID*.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return f"{self.__class__.__name__}('{self._aces_transform_id}')"

    def __repr__(self):
        """
        Return an evaluable string representation of the *ACEStransformID*.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def _parse(self):
        """Parse the *ACEStransformID*."""

        if self._aces_transform_id is None:
            return

        aces_transform_id = patch_invalid_aces_transform_id(
            self._aces_transform_id
        )

        self._urn, components = aces_transform_id.rsplit(SEPARATOR_URN_CTL, 1)
        components = components.split(SEPARATOR_ID_CTL)
        self._type, components = components[0], components[1:]

        attest(
            self._urn == URN_CTL,
            f"{self._aces_transform_id} URN {self._urn} is invalid!",
        )

        attest(
            len(components) in (3, 4, 5),
            f'{self._aces_transform_id} is an invalid "ACEStransformID"!',
        )

        if len(components) == 3:
            (
                self._major_version,
                self._minor_version,
                self._patch_version,
            ) = components
        elif len(components) == 4:
            if self._type in ("ACESlib", "ACESutil"):
                (
                    self._name,
                    self._major_version,
                    self._minor_version,
                    self._patch_version,
                ) = components
            elif self._type == "IDT":
                (
                    self._namespace,
                    self._name,
                    self._major_version,
                    self._minor_version,
                ) = components
        else:
            (
                self._namespace,
                self._name,
                self._major_version,
                self._minor_version,
                self._patch_version,
            ) = components

        attest(
            self._type in TRANSFORM_TYPES_CTL,
            f"{self._aces_transform_id} type {self._type} is invalid!",
        )

        if self._name is not None:
            if self._type == "ACEScsc":
                source, target = self._name.split("_to_")

                if source == "ACES":
                    source = "ACES2065-1"

                if target == "ACES":
                    target = "ACES2065-1"

                self._source, self._target = source, target
            elif self._type in ("IDT", "LMT"):
                self._source, self._target = self._name, "ACES2065-1"
            elif self._type == "ODT":
                self._source, self._target = "OCES", self._name
            elif self._type == "InvODT":
                self._source, self._target = self._name, "OCES"
            elif self._type == "RRTODT":
                self._source, self._target = "ACES2065-1", self._name
            elif self._type == "InvRRTODT":
                self._source, self._target = self._name, "ACES2065-1"
        else:
            if self._type == "RRT":  # noqa: PLR5501
                self._source, self._target = "ACES2065-1", "OCES"
            elif self._type == "InvRRT":
                self._source, self._target = "OCES", "ACES2065-1"


class CTLTransform:
    """
    Define the *ACES* *CTL* transform class: an object storing information
    about an *ACES* *CTL* transform file.

    Parameters
    ----------
    path : unicode
        *ACES* *CTL* transform path.
    family : unicode, optional
        *ACES* *CTL* transform family, e.g. *output_transform*
    genus : unicode, optional
        *ACES* *CTL* transform genus, e.g. *dcdm*

    Attributes
    ----------
    path
    code
    aces_transform_id
    user_name
    description
    source
    target
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
        self._aces_transform_id = None
        self._user_name = None
        self._description = ""

        self._family = family
        self._genus = genus

        self._parse()

    @property
    def path(self):
        """
        Getter  property for the *ACES* *CTL* transform path.

        Returns
        -------
        unicode
            *ACES* *CTL* transform path.

        Notes
        -----
        -   This property is read only.
        """

        return self._path

    @property
    def code(self):
        """
        Getter  property for the *ACES* *CTL* transform code, i.e. the *ACES*
        *CTL* transform file content.

        Returns
        -------
        unicode
            *ACES* *CTL* transform code.

        Notes
        -----
        -   This property is read only.
        -   This property contains the entire file content, i.e. the code along
            with the comments.
        """

        return self._code

    @property
    def aces_transform_id(self):
        """
        Getter property for the *ACES* *CTL* transform *ACEStransformID*.

        Returns
        -------
        unicode
            *ACES* *CTL* transform *ACEStransformID*.

        Notes
        -----
        -   This property is read only.
        """

        return self._aces_transform_id

    @property
    def user_name(self):
        """
        Getter property for the *ACES* *CTL* transform *ACESuserName*.

        Returns
        -------
        unicode
            *ACES* *CTL* transform *ACESuserName*.

        Notes
        -----
        -   This property is read only.
        """

        return self._user_name

    @property
    def description(self):
        """
        Getter property for the *ACES* *CTL* transform description extracted
        from parsing the file content header.

        Returns
        -------
        unicode
            *ACES* *CTL* transform description.

        Notes
        -----
        -   This property is read only.
        """

        return self._description

    @property
    def family(self):
        """
        Getter property for the *ACES* *CTL* transform family, e.g.
        *output_transform*, a value in
        :attr:`opencolorio_config_aces.config.reference.\
TRANSFORM_FAMILIES_CTL` attribute dictionary.

        Returns
        -------
        unicode
            *ACES* *CTL* transform family.

        Notes
        -----
        -   This property is read only.
        """

        return self._family

    @property
    def genus(self):
        """
        Getter property for the *ACES* *CTL* transform genus, e.g. *dcdm*.

        Returns
        -------
        unicode
            *ACES* *CTL* transform genus.

        Notes
        -----
        -   This property is read only.
        """

        return self._genus

    def __getattr__(self, item):
        """
        Reimplement the :meth:`object.__getattr__` so that unsuccessful
        attribute lookup on :class:`opencolorio_config_aces.config.reference.\
CTLTransform` class are tried on the underlying
        :class:`opencolorio_config_aces.config.reference.ACESTransformID` class
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

        aces_transform_id = object.__getattribute__(self, "_aces_transform_id")

        return getattr(aces_transform_id, item)

    def __str__(self):
        """
        Return a formatted string representation of the *ACES* *CTL*
        transform.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"'{ctl_transform_relative_path(self._path)}')"
        )

    def __repr__(self):
        """
        Return an evaluable representation of the *ACES* *CTL* transform.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
        Return whether the *ACES* *CTL* transform is equal to given other
        object.

        Parameters
        ----------
        other : object
            Object to test whether it is equal to the *ACES* *CTL* transform.

        Returns
        -------
        bool
            Is given object equal to *ACES* *CTL* transform.
        """

        if not isinstance(other, CTLTransform):
            return False
        else:
            return self._path == other.path

    def __ne__(self, other):
        """
        Return whether the *ACES* *CTL* transform is not equal to given other
        object.

        Parameters
        ----------
        other : object
            Object to test whether it is not equal to the *ACES* *CTL*
            transform.

        Returns
        -------
        bool
            Is given object not equal to *ACES* *CTL* transform.
        """

        return not (self == other)

    def _parse(self):
        """Parse the *ACES* *CTL* transform."""

        with open(self._path) as ctl_file:
            self._code = ctl_file.read()

        lines = filter(None, (line.strip() for line in self._code.split("\n")))

        in_header = True
        for line in lines:
            search = re.search("<ACEStransformID>(.*)</ACEStransformID>", line)
            if search:
                self._aces_transform_id = ACESTransformID(search.group(1))
                continue

            search = re.search("<ACESuserName>(.*)</ACESuserName>", line)
            if search:
                self._user_name = search.group(1)
                continue

            if line.startswith("//"):
                line = line[2:].strip()

                for pattern, substitution in PATTERNS_DESCRIPTION_CTL.items():
                    line = re.sub(pattern, substitution, line)

                self._description += line
                self._description += "\n"
            else:
                in_header = False

            if not in_header:
                break

        self._description = self._description.strip()


class CTLTransformPair:
    """
    Define the *ACES* *CTL* transform pair class: an object storing a pair of
    :class:`opencolorio_config_aces.config.reference.CTLTransform` class
    instances representing forward and inverse transformation.

    Parameters
    ----------
    forward_transform : CTLTransform
        *ACES* *CTL* transform forward transform.
    inverse_transform : CTLTransform
        *ACES* *CTL* transform inverse transform.

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
        Getter property for the *ACES* *CTL* transform pair forward transform.

        Returns
        -------
        unicode
            *ACES* *CTL* transform pair forward transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._forward_transform

    @property
    def inverse_transform(self):
        """
        Getter property for the *ACES* *CTL* transform pair inverse transform.

        Returns
        -------
        unicode
            *ACES* *CTL* transform pair inverse transform.

        Notes
        -----
        -   This property is read only.
        """

        return self._inverse_transform

    def __str__(self):
        """
        Return a formatted string representation of the *ACES* *CTL*
        transform pair.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (
            f"{self.__class__.__name__}("
            f"{self._forward_transform!s}', "
            f"{self._inverse_transform!s}')"
        )

    def __repr__(self):
        """
        Return an evaluable string representation of the *ACES* *CTL*
        transform pair.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
        Return whether the *ACES* *CTL* transform pair is equal to given
        other object.

        Parameters
        ----------
        other : object
            Object to test whether it is equal to the *ACES* *CTL* transform
            pair.

        Returns
        -------
        bool
            Is given object equal to *ACES* *CTL* transform pair.
        """

        if not isinstance(other, CTLTransformPair):
            return False
        else:
            return (self._forward_transform == other._forward_transform) and (
                self._inverse_transform == other._inverse_transform
            )

    def __ne__(self, other):
        """
        Return whether the *ACES* *CTL* transform pair is not equal to given
        other object.

        Parameters
        ----------
        other : object
            Object to test whether it is not equal to the *ACES* *CTL*
            transform pair.

        Returns
        -------
        bool
            Is given object not equal to *ACES* *CTL* transform pair.
        """

        return not (self == other)


def find_ctl_transform_pairs(ctl_transforms):
    """
    Find the pairs in given list of *ACES* *CTL* transform paths.

    Parameters
    ----------
    ctl_transforms : array_like
        *ACES* *CTL* transform paths to find the pairs from.

    Returns
    -------
    dict
        .. math::

            \\{``basename_1'': \\{
            ``forward\\_transform'': ``forward\\_transform_1.ctl'',
            ``inverse\\_transform'': ``inverse\\_transform_1.ctl''\\},
            \\ldots, 'basename_n': \\{
            ``forward\\_transform'': ``forward\\_transform_n.ctl'',
            ``inverse\\_transform'': ``inverse\\_transform_n.ctl''\\}\\}
    """

    ctl_transform_pairs = defaultdict(dict)
    for ctl_transform in ctl_transforms:
        is_forward = True

        basename = os.path.splitext(os.path.basename(ctl_transform))[0]
        if basename.startswith("Inv"):
            basename = basename.replace("Inv", "")
            is_forward = False

        if re.search(".*_to_ACES$", basename):
            basename = basename.replace("_to_ACES", "")
            is_forward = False

        basename = basename.replace("ACES_to_", "")

        if is_forward:
            ctl_transform_pairs[basename]["forward_transform"] = ctl_transform
        else:
            ctl_transform_pairs[basename]["inverse_transform"] = ctl_transform

    return ctl_transform_pairs


def discover_aces_ctl_transforms(root_directory=ROOT_TRANSFORMS_CTL):
    """
    Discover the *ACES* *CTL* transform paths in given root directory: The
    given directory is traversed and the `*.ctl` files are collected.

    Parameters
    ----------
    root_directory : unicode
        Root directory to traverse to find the *ACES* *CTL* transforms.

    Returns
    -------
    dict
        .. math::

            \\{``directory_1'':
            \\left[``transform_a.ctl'', ``transform_b.ctl''\\right],\\\\
            \\ldots,\\\\
            ``directory_n'':
            \\left[``transform_c.ctl'', ``transform_d.ctl''\\right]\\}

    Examples
    --------
    >>> ctl_transforms = discover_aces_ctl_transforms()
    >>> key = sorted(ctl_transforms.keys())[0]
    >>> os.path.basename(key)
    'ACEScc'
    >>> sorted([os.path.basename(path) for path in ctl_transforms[key]])
    ['ACEScsc.Academy.ACES_to_ACEScc.ctl', \
'ACEScsc.Academy.ACEScc_to_ACES.ctl']
    """

    root_directory = os.path.normpath(os.path.expandvars(root_directory))

    ctl_transforms = defaultdict(list)
    for directory, _sub_directories, filenames in os.walk(root_directory):
        if not filenames:
            continue

        for filename in filenames:
            if not filename.lower().endswith(EXTENSION_CTL):
                continue

            ctl_transform = os.path.join(directory, filename)

            logger.debug(
                '"%s" CTL transform was found!',
                ctl_transform_relative_path(ctl_transform),
            )

            ctl_transforms[directory].append(ctl_transform)

    return ctl_transforms


def classify_aces_ctl_transforms(unclassified_ctl_transforms):
    """
    Classifie given *ACES* *CTL* transforms.

    Parameters
    ----------
    unclassified_ctl_transforms : dict
        Unclassified *ACES* *CTL* transforms as returned by
        :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
        definition.

    Returns
    -------
    dict
        .. math::

            \\{``family_1'': \\{``genus_1'': \\{\\}_{CTL_1},
            \\ldots,
            ``family_n'': \\{``genus_2'':\\{\\}_{CTL_2}\\}\\}

        where

        .. math::

            \\{\\}_{CTL_n}=\\{``basename_n'': CTLTransform_n,
            \\ldots,
            ``basename_{n + 1}'': CTLTransform_{n + 1}\\}

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> family = sorted(ctl_transforms.keys())[0]
    >>> str(family)
    'csc'
    >>> genera = sorted(ctl_transforms[family])
    >>> print(genera)
    ['ACEScc', 'ACEScct', 'ACEScg', 'ACESproxy', 'ADX', 'arri', 'canon', \
'panasonic', 'red', 'sony']
    >>> genus = genera[0]
    >>> sorted(ctl_transforms[family][genus].items())  # doctest: +ELLIPSIS
    [('ACEScsc.Academy.ACEScc', CTLTransformPair(\
CTLTransform('csc...ACEScc...ACEScsc.Academy.ACES_to_ACEScc.ctl')', \
CTLTransform('csc...ACEScc...ACEScsc.Academy.ACEScc_to_ACES.ctl')'))]
    """

    classified_ctl_transforms = defaultdict(lambda: defaultdict(dict))

    root_directory = paths_common_ancestor(
        *itertools.chain.from_iterable(unclassified_ctl_transforms.values())
    )
    for directory, ctl_transforms in unclassified_ctl_transforms.items():
        sub_directory = directory.replace(f"{root_directory}{os.sep}", "")
        family, *genus = (
            TRANSFORM_FAMILIES_CTL.get(part, part)
            for part in sub_directory.split(os.sep)
        )

        genus = TRANSFORM_GENUS_DEFAULT_CTL if not genus else "/".join(genus)

        for basename, pairs in find_ctl_transform_pairs(
            ctl_transforms
        ).items():
            if len(pairs) == 1:
                ctl_transform = CTLTransform(
                    list(pairs.values())[0], family, genus
                )

                logger.debug(
                    'Classifying "%s" under "%s".', ctl_transform, genus
                )

                classified_ctl_transforms[family][genus][
                    basename
                ] = ctl_transform

            elif len(pairs) == 2:
                forward_ctl_transform = CTLTransform(
                    pairs["forward_transform"], family, genus
                )
                inverse_ctl_transform = CTLTransform(
                    pairs["inverse_transform"], family, genus
                )

                ctl_transform = CTLTransformPair(
                    forward_ctl_transform, inverse_ctl_transform
                )

                logger.debug(
                    'Classifying "%s" under "%s".', ctl_transform, genus
                )

                classified_ctl_transforms[family][genus][
                    basename
                ] = ctl_transform

    return vivified_to_dict(classified_ctl_transforms)


def unclassify_ctl_transforms(classified_ctl_transforms):
    """
    Unclassifie given *ACES* *CTL* transforms.

    Parameters
    ----------
    classified_ctl_transforms : dict
        Classified *ACES* *CTL* transforms as returned by
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
        definition.

    Returns
    -------
    list
        .. math::

            \\left[CTLTransform_1, \\ldots, CTLTransform_n\\right]

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> sorted(  # doctest: +ELLIPSIS
    ...     unclassify_ctl_transforms(ctl_transforms), key=lambda x: x.path)[0]
    CTLTransform('csc...ACEScc...ACEScsc.Academy.ACES_to_ACEScc.ctl')
    """

    unclassified_ctl_transforms = []
    for genera in classified_ctl_transforms.values():
        for ctl_transforms in genera.values():
            for ctl_transform in ctl_transforms.values():
                if isinstance(ctl_transform, CTLTransform):
                    unclassified_ctl_transforms.append(ctl_transform)
                elif isinstance(ctl_transform, CTLTransformPair):
                    unclassified_ctl_transforms.append(
                        ctl_transform.forward_transform
                    )
                    unclassified_ctl_transforms.append(
                        ctl_transform.inverse_transform
                    )

    return unclassified_ctl_transforms


def filter_ctl_transforms(ctl_transforms, filterers=None):
    """
    Filter given *ACES* *CTL* transforms with given filterers.

    Parameters
    ----------
    ctl_transforms : dict or list
        *ACES* *CTL* transforms as returned by
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms` or
        :func:`opencolorio_config_aces.unclassify_aces_ctl_transforms`
        definitions.
    filterers : array_like, optional
        List of callables used to filter the *ACES* *CTL* transforms, each
        callable takes an *ACES* *CTL* transform as argument and returns
        whether to include or exclude the *ACES* *CTL* transform as a bool.

    Returns
    -------
    list
        .. math::

            \\left[CTLTransform_1, \\ldots, CTLTransform_n\\right]

    Warnings
    --------
    -   This definition will forcibly unclassify the given *ACES* *CTL*
        transforms and return a flattened list.

    Examples
    --------
    >>> ctl_transforms = classify_aces_ctl_transforms(
    ...     discover_aces_ctl_transforms())
    >>> sorted(  # doctest: +ELLIPSIS
    ...     filter_ctl_transforms(ctl_transforms, [lambda x: x.genus == 'p3']),
    ...     key=lambda x: x.path)[0]
    CTLTransform('odt...p3...InvODT.Academy.P3D60_48nits.ctl')
    """

    if filterers is None:
        filterers = TRANSFORM_FILTERERS_DEFAULT_CTL

    if isinstance(ctl_transforms, Mapping):
        ctl_transforms = unclassify_ctl_transforms(ctl_transforms)

    filtered_ctl_transforms = []
    for ctl_transform in ctl_transforms:
        included = True
        for filterer in filterers:
            included *= filterer(ctl_transform)

        if included:
            filtered_ctl_transforms.append(ctl_transform)

    return filtered_ctl_transforms


def print_aces_taxonomy():
    """
    Print *aces-dev* taxonomy:

    -   The *aces-dev* *CTL* transforms are discovered by traversing the
        directory defined by the :attr:`opencolorio_config_aces.config.\
reference.ROOT_TRANSFORMS_CTL` attribute using the
        :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
        definition.
    -   The *CTL* transforms are classified by *family* e.g.
        *output_transform*, and *genus* e.g. *dcdm* using the
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
        definition.
    -   The resulting data structure is printed.
    """

    classified_ctl_transforms = classify_aces_ctl_transforms(
        discover_aces_ctl_transforms()
    )

    for family, genera in classified_ctl_transforms.items():
        message_box(family, print_callable=logger.info)
        for genus, ctl_transforms in genera.items():
            logger.info("[ %s ]", genus)
            for name, ctl_transform in ctl_transforms.items():
                logger.info("\t( %s )", name)
                if isinstance(ctl_transform, CTLTransform):
                    logger.info(
                        '\t\t"%s" --> "%s"',
                        ctl_transform.source,
                        ctl_transform.target,
                    )
                elif isinstance(ctl_transform, CTLTransformPair):
                    logger.info(
                        '\t\t"%s" <--> "%s"',
                        ctl_transform.forward_transform.source,
                        ctl_transform.forward_transform.target,
                    )


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    logging.info('"aces-dev" version : %s', version_aces_dev())
    print_aces_taxonomy()
