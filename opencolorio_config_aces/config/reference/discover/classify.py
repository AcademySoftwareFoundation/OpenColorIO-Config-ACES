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
-   :func:`opencolorio_config_aces.generate_amf_components`
"""

import itertools
import json
import logging
import os  # TODO: Use "pathlib".
import re
import subprocess
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from semver import Version

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
    "generate_amf_components",
]

LOGGER = logging.getLogger(__name__)

URN_CTL = "urn:ampas:aces:transformId:v2.0"
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

urn:ampas:aces:transformId:v2.0:CSC.Academy.ACES_to_ACEScc.a2.v1
|-------------URN-------------|:|--------------ID--------------|

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
    "CSC",
    "Lib",
    "Look",
    "InvLook",
    "Output",
    "InvOutput",
]
"""
*ACES* *CTL* transform types.

TRANSFORM_TYPES_CTL : list
"""

TRANSFORM_FAMILIES_CTL = {
    "aces-core": "lib",
    "aces-input-and-colorspaces": "csc",
    "aces-look": "look",
    "aces-output": "output",
}
"""
*ACES* *CTL* transform families mapping the *CTL* transform directories to
family names.

TRANSFORM_FAMILIES_CTL : dict
"""

TRANSFORM_GENUS_DEFAULT_CTL = "undefined"
"""
*ACES* *CTL* transform default genus, i.e., *undefined*.

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

PATH_AMF_COMPONENTS_FILE = (
    Path(__file__).parents[0] / "resources" / "ACES_AMF_Components.json"
)

"""
Path to the *ACES* *AMF* components file.

PATH_AMF_COMPONENTS_FILE : unicode
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
    """

    if True:
        invalid_id = aces_transform_id

        if "transformID" in invalid_id:
            LOGGER.critical(
                '"%s" urn is incorrect, "transformID" should be "transformId"!',
                invalid_id,
            )

            aces_transform_id = invalid_id.replace("transformID", "transformId")

        if "LogCv3" in invalid_id:
            LOGGER.critical(
                '"%s" urn is incorrect, "LogCv3" should be "LogC3"!',
                invalid_id,
            )

            aces_transform_id = invalid_id.replace("LogCv3", "LogC3")

        if "LogCv4" in invalid_id:
            LOGGER.critical(
                '"%s" urn is incorrect, "LogCv4" should be "LogC4"!',
                invalid_id,
            )

            aces_transform_id = invalid_id.replace("LogCv4", "LogC4")

    return aces_transform_id


ROOT_TRANSFORMS_CTL = os.path.normpath(
    os.environ.get(
        "OPENCOLORIO_CONFIG_CTL__CTL_TRANSFORMS_ROOT",
        os.path.join(os.path.dirname(__file__), "../", "aces-system"),
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
    :class:`semver.Version`
        *aces-dev* version.
    """

    try:  # pragma: no cover
        version = subprocess.check_output(
            ["git", "describe"],  # noqa: S603, S607
            cwd=ROOT_TRANSFORMS_CTL,
            stderr=subprocess.STDOUT,
        ).strip()

        version = version.decode("utf-8")

        return Version.parse(
            re.search(r"v(\d\.\d(\.\d)?)", version).group(1),
            optional_minor_and_patch=True,
        )
    except Exception:  # pragma: no cover
        changelog_path = os.path.join(ROOT_TRANSFORMS_CTL, "..", "..", "CHANGELOG.md")
        if os.path.exists(changelog_path):
            with open(changelog_path) as changelog_file:
                for line in changelog_file.readlines():
                    search = re.search(r"Version\s+(\d\.\d(\.\d)?)", line)
                    if search:
                        return Version.parse(search.group(1))

        return Version(0)


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
        *ACEStransformID*, e.g.,
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
        Getter property for the *ACEStransformID*, e.g.,
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
        e.g., *urn:ampas:aces:transformId:v1.5*.

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
    def type(self):
        """
        Getter property for the *ACEStransformID* type, e.g., *ODT*.

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
        Getter property for the *ACEStransformID* namespace, e.g., *Academy*.

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
        Getter property for the *ACEStransformID* name, e.g., *DCDM*.

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
        Getter property for the *ACEStransformID* major version number, e.g.,
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
        Getter property for the *ACEStransformID* minor version number, e.g.,
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
        Getterproperty for the *ACEStransformID* patch version number, e.g., *3*.

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

        aces_transform_id = patch_invalid_aces_transform_id(self._aces_transform_id)

        self._urn, components = aces_transform_id.rsplit(SEPARATOR_URN_CTL, 1)

        components = components.split(SEPARATOR_ID_CTL)
        self._type, components = components[0], components[1:]

        attest(
            self._urn == URN_CTL,
            f"{self._aces_transform_id} URN {self._urn} is invalid!",
        )

        attest(
            len(components) == 4,
            f'{self._aces_transform_id} is an invalid "ACEStransformID"!',
        )

        (
            self._namespace,
            self._name,
            self._major_version,
            self._minor_version,
        ) = components

        attest(
            self._type in TRANSFORM_TYPES_CTL,
            f"{self._aces_transform_id} type {self._type} is invalid!",
        )

        if self._name is not None:
            if self._type == "CSC":
                if "Unity" in self._name:
                    source, target = "ACES", "ACES"
                else:
                    source, target = self._name.split("_to_")

                if source == "ACES":
                    source = "ACES2065-1"

                if target == "ACES":
                    target = "ACES2065-1"

                self._source, self._target = source, target
            elif self._type in ("Look", "InvLook"):
                self._source, self._target = "ACES2065-1", "ACES2065-1"
            elif self._type == "Output":
                self._source, self._target = "ACES2065-1", self._name
            elif self._type == "InvOutput":
                self._source, self._target = self._name, "ACES2065-1"


class CTLTransform:
    """
    Define the *ACES* *CTL* transform class: an object storing information
    about an *ACES* *CTL* transform file.

    Parameters
    ----------
    path : unicode
        *ACES* *CTL* transform path.
    family : unicode, optional
        *ACES* *CTL* transform family, e.g., *output_transform*.
    genus : unicode, optional
        *ACES* *CTL* transform genus, e.g., *dcdm*.
    siblings : array_like, optional
        *ACES* *CTL* transform siblings, e.g., inverse transform.

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

    def __init__(self, path, family=None, genus=None, siblings=None):
        siblings = optional(siblings, [])

        self._path = os.path.abspath(os.path.normpath(path))

        self._code = None
        self._aces_transform_id = None
        self._user_name = None
        self._description = ""

        self._family = family
        self._genus = genus
        self._siblings = siblings

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
        Getter  property for the *ACES* *CTL* transform code, i.e., the *ACES*
        *CTL* transform file content.

        Returns
        -------
        unicode
            *ACES* *CTL* transform code.

        Notes
        -----
        -   This property is read only.
        -   This property contains the entire file content, i.e., the code along
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
        Getter property for the *ACES* *CTL* transform family, e.g.,
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
        Getter property for the *ACES* *CTL* transform genus, e.g., *dcdm*.

        Returns
        -------
        unicode
            *ACES* *CTL* transform genus.

        Notes
        -----
        -   This property is read only.
        """

        return self._genus

    @property
    def siblings(self):
        """
        Getter property for the *ACES* *CTL* transform siblings, e.g., inverse
        transform.

        Returns
        -------
        unicode
            *ACES* *CTL* transform siblings.

        Notes
        -----
        -   This property is read only.
        """

        return self._siblings

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

        LOGGER.info('Parsing "%s" CTL transform...', self._path)

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
                line = line[2:].strip()  # noqa: PLW2901

                for pattern, substitution in PATTERNS_DESCRIPTION_CTL.items():
                    line = re.sub(pattern, substitution, line)  # noqa: PLW2901

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

        LOGGER.debug(
            'Is "%s" CTL transform is forward? "%s"', ctl_transform, is_forward
        )

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
    'lib'
    >>> sorted([os.path.basename(path) for path in ctl_transforms[key]])
    ['Lib.Academy.ColorSpaces.ctl', 'Lib.Academy.DisplayEncoding.ctl', \
'Lib.Academy.OutputTransform.ctl', 'Lib.Academy.Tonescale.ctl', \
'Lib.Academy.Utilities.ctl']
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

            LOGGER.debug(
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
    ['ACEScc', 'ACEScct', 'ACEScg', 'ACESproxy', 'ADX', 'apple', 'arri', \
'blackmagic_design', 'canon', 'dji', 'panasonic', 'red', 'sony', 'unity']
    >>> genus = genera[0]
    >>> sorted(ctl_transforms[family][genus].items())  # doctest: +ELLIPSIS
    [('CSC.Academy.ACEScc', CTLTransformPair(CTLTransform(\
'aces-input-and-colorspaces...ACEScc...CSC.Academy.ACES_to_ACEScc.ctl')', \
CTLTransform('aces-input-and-colorspaces...ACEScc...CSC.Academy.ACEScc_to_ACES.ctl')'))]
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

        for basename, pairs in find_ctl_transform_pairs(ctl_transforms).items():
            if len(pairs) == 1:
                ctl_transform = CTLTransform(next(iter(pairs.values())), family, genus)

                LOGGER.debug('Classifying "%s" under "%s".', ctl_transform, genus)

                classified_ctl_transforms[family][genus][basename] = ctl_transform

            elif len(pairs) == 2:
                forward_ctl_transform = CTLTransform(
                    pairs["forward_transform"], family, genus
                )
                inverse_ctl_transform = CTLTransform(
                    pairs["inverse_transform"], family, genus
                )

                forward_ctl_transform.siblings.append(inverse_ctl_transform)
                inverse_ctl_transform.siblings.append(forward_ctl_transform)

                ctl_transform = CTLTransformPair(
                    forward_ctl_transform, inverse_ctl_transform
                )

                LOGGER.debug('Classifying "%s" under "%s".', ctl_transform, genus)

                classified_ctl_transforms[family][genus][basename] = ctl_transform

    return vivified_to_dict(classified_ctl_transforms)


def unclassify_ctl_transforms(classified_ctl_transforms):
    """
    Unclassify given *ACES* *CTL* transforms.

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
    CTLTransform('aces-core...lib...Lib.Academy.ColorSpaces.ctl')
    """

    unclassified_ctl_transforms = []
    for genera in classified_ctl_transforms.values():
        for ctl_transforms in genera.values():
            for ctl_transform in ctl_transforms.values():
                if isinstance(ctl_transform, CTLTransform):
                    unclassified_ctl_transforms.append(ctl_transform)
                elif isinstance(ctl_transform, CTLTransformPair):
                    unclassified_ctl_transforms.append(ctl_transform.forward_transform)
                    unclassified_ctl_transforms.append(ctl_transform.inverse_transform)

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
    ...     filter_ctl_transforms(ctl_transforms, [lambda x: x.genus == "d65/p3"]),
    ...     key=lambda x: x.path)[0]
    CTLTransform('aces-output...d65...p3...InvOutput.Academy.\
P3-D65_1000nit_in_P3-D65_ST2084.ctl')
    """

    filterers = optional(filterers, TRANSFORM_FILTERERS_DEFAULT_CTL)

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
    -   The *CTL* transforms are classified by *family* e.g.,
        *output_transform*, and *genus* e.g., *dcdm* using the
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
        definition.
    -   The resulting data structure is printed.
    """

    classified_ctl_transforms = classify_aces_ctl_transforms(
        discover_aces_ctl_transforms()
    )

    for family, genera in classified_ctl_transforms.items():
        message_box(family, print_callable=LOGGER.info)
        for genus, ctl_transforms in genera.items():
            LOGGER.info("[ %s ]", genus)
            for name, ctl_transform in ctl_transforms.items():
                LOGGER.info("\t( %s )", name)
                if isinstance(ctl_transform, CTLTransform):
                    LOGGER.info(
                        '\t\tACEStransformID : "%s"',
                        ctl_transform.aces_transform_id.aces_transform_id,
                    )
                    LOGGER.info(
                        '\t\t\t"%s" --> "%s"',
                        ctl_transform.source,
                        ctl_transform.target,
                    )
                elif isinstance(ctl_transform, CTLTransformPair):
                    LOGGER.info(
                        '\t\tACEStransformID : "%s"',
                        ctl_transform.forward_transform.aces_transform_id.aces_transform_id,
                    )
                    LOGGER.info(
                        '\t\t\t"%s" --> "%s"',
                        ctl_transform.forward_transform.source,
                        ctl_transform.forward_transform.target,
                    )
                    LOGGER.info(
                        '\t\tACEStransformID : "%s"',
                        ctl_transform.inverse_transform.aces_transform_id.aces_transform_id,
                    )
                    LOGGER.info(
                        '\t\t\t"%s" --> "%s"',
                        ctl_transform.inverse_transform.source,
                        ctl_transform.inverse_transform.target,
                    )


def generate_amf_components(ctl_transforms, raise_exception=False):
    """
    Generate the *ACES* *AMF* components from given *ACES* *CTL* transforms.

    Parameters
    ----------
    ctl_transforms : dict or list
        *ACES* *CTL* transforms as returned by
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms` or
        :func:`opencolorio_config_aces.unclassify_aces_ctl_transforms`
        definitions.
    raise_exception : bool, optional
        Whether to raise an exception if an *ACES* *ACEStransformID* is
        missing.

    Returns
    -------
    dict
        *ACES* *AMF* components.
    """

    amf_components = defaultdict(list)

    with open(PATH_AMF_COMPONENTS_FILE) as json_file:
        content = json_file.readlines()
        content = json.loads(
            "\n".join([line for line in content if not line.strip().startswith("//")])
        )

        attest(content["header"]["schema_version"].split(".")[0] == "1")

        amf_components_implicit = content["amf_components"]

    if isinstance(ctl_transforms, Mapping):
        ctl_transforms = unclassify_ctl_transforms(ctl_transforms)

    # Checking that the explicit "ACEStransformID" do exist.
    for aces_transform_id, relations in amf_components_implicit.items():
        explicit_aces_transform_ids = [aces_transform_id]
        explicit_aces_transform_ids.extend(relations)

        for explicit_aces_transform_id in explicit_aces_transform_ids:
            filtered_ctl_transforms = filter_ctl_transforms(
                ctl_transforms,
                [
                    lambda x, y=explicit_aces_transform_id: (
                        x.aces_transform_id.aces_transform_id == y
                    )
                ],
            )

            ctl_transform = next(iter(filtered_ctl_transforms), None)

            if ctl_transform is None:
                exception_message = (
                    f'"aces-dev" has no transform with '
                    f'"{explicit_aces_transform_id}" "ACEStransformID!'
                )

                if raise_exception:
                    attest(False, exception_message)
                else:
                    LOGGER.critical(exception_message)

    for ctl_transform in ctl_transforms:
        aces_transform_id = ctl_transform.aces_transform_id.aces_transform_id

        for siblings in [
            ctl_transform.siblings
            for ctl_transform in filter_ctl_transforms(
                ctl_transforms,
                [
                    lambda x, y=aces_transform_id: (
                        x.aces_transform_id.aces_transform_id == y
                    )
                ],
            )
        ]:
            for sibling in siblings:
                amf_components[aces_transform_id].append(
                    sibling.aces_transform_id.aces_transform_id
                )

    # Extending with explicit relations.
    for aces_transform_id, relations in amf_components_implicit.items():
        amf_components[aces_transform_id].extend(relations)

    # Generating the permutations.
    for aces_transform_id, relations in amf_components.copy().items():
        for relation in relations:
            amf_components[relation] = sorted(
                {*relations, *amf_components[relation], aces_transform_id} - {relation}
            )

    return dict(amf_components)


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    logging.info('"aces-dev" version : %s', version_aces_dev())
    print_aces_taxonomy()
