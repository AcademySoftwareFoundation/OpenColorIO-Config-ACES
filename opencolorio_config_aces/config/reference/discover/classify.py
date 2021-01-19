# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Reference Implementation Discovery & Classification
==============================================================

Defines various objects related to *aces-dev* reference implementation *CTL*
transforms discovery and classification:

-   :attr:`opencolorio_config_aces.config.reference.ACES_URN`
-   :attr:`opencolorio_config_aces.config.reference.ACES_NAMESPACE`
-   :attr:`opencolorio_config_aces.config.reference.ACES_TYPES`
-   :attr:`opencolorio_config_aces.config.reference.ACES_CTL_TRANSFORMS_ROOT`
-   :attr:`opencolorio_config_aces.config.reference.\
ACES_CTL_TRANSFORM_FAMILIES`
-   :class:`opencolorio_config_aces.config.reference.ACESTransformID`
-   :class:`opencolorio_config_aces.config.reference.CTLTransform`
-   :class:`opencolorio_config_aces.config.reference.CTLTransformPair`
-   :func:`opencolorio_config_aces.config.reference.discover.\
find_ctl_transform_pairs`
-   :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.unclassify_ctl_transforms`
-   :func:`opencolorio_config_aces.filter_ctl_transforms`
-   :func:`opencolorio_config_aces.print_aces_taxonomy`
"""

import itertools
import logging
import os
import re
from collections import Mapping, defaultdict

from opencolorio_config_aces.utilities import (
    message_box, paths_common_ancestor, vivified_to_dict)

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'ACES_URN', 'ACES_URN_SEPARATOR', 'ACES_ID_SEPARATOR', 'ACES_NAMESPACE',
    'ACES_TYPES', 'ACES_CTL_TRANSFORMS_ROOT', 'ACES_CTL_TRANSFORM_FAMILIES',
    'DEFAULT_ACES_CTL_TRANSFORM_GENUS', 'DEFAULT_ACES_CTL_TRANSFORM_FILTERERS',
    'DESCRIPTION_SUBSTITUTION_PATTERNS', 'patch_invalid_aces_transform_id',
    'ctl_transform_relative_path', 'ACESTransformID', 'CTLTransform',
    'CTLTransformPair', 'find_ctl_transform_pairs',
    'discover_aces_ctl_transforms', 'classify_aces_ctl_transforms',
    'unclassify_ctl_transforms', 'filter_ctl_transforms', 'print_aces_taxonomy'
]

ACES_URN = 'urn:ampas:aces:transformId:v1.5'
"""
*ACES* Uniform Resource Name (*URN*).

ACES_URN : unicode
"""

ACES_URN_SEPARATOR = ':'
"""
*ACEStransformID* separator used to separate the *URN* and *ID* part of the
*ACEStransformID*.

ACES_URN_SEPARATOR : unicode
"""

ACES_ID_SEPARATOR = '.'
"""
*ACEStransformID* separator used to tokenize the *ID* part of the
*ACEStransformID*.

urn:ampas:aces:transformId:v1.5:ODT.Academy.DCDM.a1.0.3
|-------------URN-------------|:|----------ID---------|

ACES_ID_SEPARATOR : unicode
"""

ACES_NAMESPACE = 'Academy'
"""
*ACES* namespace for *A.M.P.A.S* official *CTL* transforms.

ACES_NAMESPACE : unicode
"""

ACES_TYPES = [
    'IDT',
    'LMT',
    'ODT',
    'RRT',
    'RRTODT',
    'InvRRT',
    'InvODT',
    'InvRRTODT',
    'ACESlib',
    'ACEScsc',
    'ACESutil',
]
"""
*ACES* *CTL* transform types.

ACES_TYPES : list
"""

ACES_CTL_TRANSFORMS_ROOT = os.path.normpath(
    os.environ.get(
        'OPENCOLORIO_CONFIG_ACES__ACES_CTL_TRANSFORMS_ROOT',
        os.path.join(
            os.path.dirname(__file__), '../', 'aces-dev', 'transforms',
            'ctl')))
"""
*aces-dev* *CTL* transforms root directory, default to the version controlled
sub-module repository. It can be defined by setting the
`OPENCOLORIO_CONFIG_ACES__ACES_CTL_TRANSFORMS_ROOT` environment variable with
the local 'aces-dev/transforms/ctl' directory.

ACES_CTL_TRANSFORMS_ROOT : unicode
"""

ACES_CTL_TRANSFORM_FAMILIES = {
    'csc': 'csc',
    'idt': 'input_transform',
    'lib': 'lib',
    'lmt': 'lmt',
    'odt': 'output_transform',
    'outputTransforms': 'output_transform',
    'rrt': 'rrt',
    'utilities': 'utility'
}
"""
*ACES* *CTL* transform families mapping the *CTL* transform directories to
family names.

ACES_CTL_TRANSFORM_FAMILIES : dict
"""

DEFAULT_ACES_CTL_TRANSFORM_GENUS = 'undefined'
"""
*ACES* *CTL* transform default genus, i.e. *undefined*.

DEFAULT_ACES_CTL_TRANSFORM_GENUS : unicode
"""

DESCRIPTION_SUBSTITUTION_PATTERNS = {
    '============ CONSTANTS ============ //': '',
    'Written by .*_IDT_maker\\.py v.* on .*': ''
}
"""
*ACES* *CTL* transform description substitution patterns.

DESCRIPTION_SUBSTITUTION_PATTERNS : dict
"""


def _exclusion_filterer_ARRIIDT(ctl_transform):
    """
    A filterer excluding the *Alexa* *ACES* *CTL* transform whose name does not
    contain:

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

    if 'Alexa' not in path:
        return True

    if 'Alexa-v3-raw-EI800' in path and 'ND1pt3' not in path:
        return True

    return False


DEFAULT_ACES_CTL_TRANSFORM_FILTERERS = [
    _exclusion_filterer_ARRIIDT,
]
"""
Default list of *ACES* *CTL* transform filterers.

DEFAULT_ACES_CTL_TRANSFORM_FILTERERS : list
"""


def patch_invalid_aces_transform_id(aces_transform_id):
    """
    Patches an invalid *ACEStransformID*, see the *Notes* section for relevant
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
    - https://github.com/ampas/aces-dev/issues/118
    - https://github.com/ampas/aces-dev/pull/119
    """

    invalid_id = aces_transform_id
    if not aces_transform_id.startswith(ACES_URN):
        logging.warning(f'{invalid_id} is missing "ACES" URN!')

        aces_transform_id = f'{ACES_URN}:{aces_transform_id}'

    if 'Academy.P3D65_108nits_7.2nits_ST2084' in aces_transform_id:
        logging.warning(f'{invalid_id} has an invalid separator in "7.2nits"!')

        aces_transform_id = aces_transform_id.replace('7.2', '7')
    elif 'P3D65_709limit_48nits' in aces_transform_id:
        logging.warning(f'{invalid_id} is inconsistently named!')

        aces_transform_id = aces_transform_id.replace(
            'P3D65_709limit_48nits', 'P3D65_Rec709limited_48nits')
    elif 'Rec2020_100nits.a1.1.0' in aces_transform_id:
        logging.warning(f'{invalid_id} is incorrectly named!')

        aces_transform_id = aces_transform_id.replace(
            'Rec2020_100nits', 'Rec2020_P3D65limited_100nits_dim')
    elif 'ACEScsc' in aces_transform_id:
        if 'ACEScsc.Academy' not in aces_transform_id:
            logging.warning(f'{invalid_id} is missing "Academy" namespace!')

            aces_transform_id = aces_transform_id.replace(
                'ACEScsc', 'ACEScsc.Academy')

        if aces_transform_id.endswith('a1.v1'):
            logging.warning(f'{invalid_id} version scheme is invalid!')

            aces_transform_id = aces_transform_id.replace('a1.v1', 'a1.1.0')

    return aces_transform_id


def ctl_transform_relative_path(path, root_directory=ACES_CTL_TRANSFORMS_ROOT):
    """
    Helper definition returning the relative path from given *ACES* *CTL*
    transform to *aces-dev* *CTL* transforms root directory.

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

    return path.replace(f'{root_directory}{os.sep}', '')


class ACESTransformID:
    """
    Defines the *ACES* *CTL* transform *ACEStransformID*: an object parsing and
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

    def __init__(self, aces_transform_id):
        self._aces_transform_id = aces_transform_id

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
    def aces_transform_id(self):
        """
        Getter and setter property for the *ACEStransformID*, e.g.
        *urn:ampas:aces:transformId:v1.5:ODT.Academy.DCDM.a1.0.3*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACEStransformID* Uniform Resource
        Name (*URN*), e.g. *urn:ampas:aces:transformId:v1.5*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACEStransformID* type, e.g. *ODT*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACEStransformID* namespace, e.g.
        *Academy*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACEStransformID* name, e.g.
        *DCDM*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
    def major_version_number(self):
        """
        Getter and setter property for the *ACEStransformID* major version
        number, e.g. *a1*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *ACEStransformID* major version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._major_version_number

    @property
    def minor_version_number(self):
        """
        Getter and setter property for the *ACEStransformID* minor version
        number, e.g. *0*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *ACEStransformID* minor version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._minor_version_number

    @property
    def patch_version_number(self):
        """
        Getter and setter property for the *ACEStransformID* patch version
        number, e.g. *3*.

        Parameters
        ----------
        value : unicode
            Attribute value.

        Returns
        -------
        unicode
            *ACEStransformID* patch version number.

        Notes
        -----
        -   This property is read only.
        """

        return self._patch_version_number

    @property
    def source(self):
        """
        Getter and setter property for the *ACEStransformID* source
        colourspace.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACEStransformID* target
        colourspace.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Returns a formatted string representation of the *ACEStransformID*.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return f"{self.__class__.__name__}(" f"'{self._aces_transform_id}')"

    def __repr__(self):
        """
        Returns an evaluable string representation of the *ACEStransformID*.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def _parse(self):
        """
        Parses the *ACEStransformID*.
        """

        if self._aces_transform_id is None:
            return

        aces_transform_id = patch_invalid_aces_transform_id(
            self._aces_transform_id)

        self._urn, components = aces_transform_id.rsplit(ACES_URN_SEPARATOR, 1)
        components = components.split(ACES_ID_SEPARATOR)
        self._type, components = components[0], components[1:]

        assert self._urn == ACES_URN, (
            f'{self._aces_transform_id} URN {self._urn} is invalid!')

        assert len(components) in (3, 4, 5), (
            f'{self._aces_transform_id} is an invalid "ACEStransformID"!')

        if len(components) == 3:
            (self._major_version_number, self._minor_version_number,
             self._patch_version_number) = components
        elif len(components) == 4:
            if self._type in ('ACESlib', 'ACESutil'):
                (self._name, self._major_version_number,
                 self._minor_version_number,
                 self._patch_version_number) = components
            elif self._type == 'IDT':
                (self._namespace, self._name, self._major_version_number,
                 self._minor_version_number) = components
        else:
            (self._namespace, self._name, self._major_version_number,
             self._minor_version_number,
             self._patch_version_number) = components

        assert self._type in ACES_TYPES, (
            f'{self._aces_transform_id} type {self._type} is invalid!')

        if self._name is not None:
            if self._type == 'ACEScsc':
                source, target = self._name.split('_to_')

                if source == 'ACES':
                    source = 'ACES2065-1'

                if target == 'ACES':
                    target = 'ACES2065-1'

                self._source, self._target = source, target
            elif self._type in ('IDT', 'LMT'):
                self._source, self._target = self._name, 'ACES2065-1'
            elif self._type == 'ODT':
                self._source, self._target = 'OCES', self._name
            elif self._type == 'InvODT':
                self._source, self._target = self._name, 'OCES'
            elif self._type == 'RRTODT':
                self._source, self._target = 'ACES2065-1', self._name
            elif self._type == 'InvRRTODT':
                self._source, self._target = self._name, 'ACES2065-1'
        else:
            if self._type == 'RRT':
                self._source, self._target = 'ACES2065-1', 'OCES'
            elif self._type == 'InvRRT':
                self._source, self._target = 'OCES', 'ACES2065-1'


class CTLTransform:
    """
    Defines the *ACES* *CTL* transform class: an object storing information
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
        self._description = ''
        self._source = None
        self._target = None

        self._family = family
        self._genus = genus

        self._parse()

    @property
    def path(self):
        """
        Getter and setter property for the *ACES* *CTL* transform path.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform code, i.e.
        the *ACES* *CTL* transform file content.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform
        *ACEStransformID*.

        Parameters
        ----------
        value : ACESTransformID
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform
        *ACESuserName*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform description
        extracted from parsing the file content header.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform family, e.g.
        *output_transform*, a value in
        :attr:`opencolorio_config_aces.config.reference.\
ACES_CTL_TRANSFORM_FAMILIES` attribute dictionary.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform genus, e.g.
        *dcdm*.

        Parameters
        ----------
        value : unicode
            Attribute value.

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
        Reimplements the :meth:`object.__getattr__` so that unsuccessful
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

        aces_transform_id = object.__getattribute__(self, '_aces_transform_id')

        return getattr(aces_transform_id, item)

    def __str__(self):
        """
        Returns a formatted string representation of the *ACES* *CTL*
        transform.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (f"{self.__class__.__name__}("
                f"'{ctl_transform_relative_path(self._path)}')")

    def __repr__(self):
        """
        Returns an evaluable representation of the *ACES* *CTL* transform.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
         Returns whether the *ACES* *CTL* transform is equal to given other
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
         Returns whether the *ACES* *CTL* transform is not equal to given other
         object.

         Parameters
         ----------
         other : object
             Object to test whether it is not equal to the *ACES* *CTL*
             transform.

         Returns
         -------
         bool
             Is given object notequal to *ACES* *CTL* transform.
        """

        return not (self == other)

    def _parse(self):
        """
        Parses the *ACES* *CTL* transform.

        """

        with open(self._path) as ctl_file:
            self._code = ctl_file.read()

        lines = filter(None, (line.strip() for line in self._code.split('\n')))

        in_header = True
        for line in lines:
            search = re.search('<ACEStransformID>(.*)</ACEStransformID>', line)
            if search:
                self._aces_transform_id = ACESTransformID(search.group(1))
                continue

            search = re.search('<ACESuserName>(.*)</ACESuserName>', line)
            if search:
                self._user_name = search.group(1)
                continue

            if line.startswith('//'):
                line = line[2:].strip()

                for pattern, substitution in (
                        DESCRIPTION_SUBSTITUTION_PATTERNS.items()):
                    line = re.sub(pattern, substitution, line)

                self._description += line
                self._description += '\n'
            else:
                in_header = False

            if not in_header:
                break

        self._description = self._description.strip()


class CTLTransformPair:
    """
    Defines the *ACES* *CTL* transform pair class: an object storing a pair of
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
        Getter and setter property for the *ACES* *CTL* transform pair forward
        transform.

        Parameters
        ----------
        value : CTLTransform
            Attribute value.

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
        Getter and setter property for the *ACES* *CTL* transform pair inverse
        transform.

        Parameters
        ----------
        value : CTLTransform
            Attribute value.

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
        Returns a formatted string representation of the *ACES* *CTL*
        transform pair.

        Returns
        -------
        unicode
            Formatted string representation.
        """

        return (f"{self.__class__.__name__}("
                f"{str(self._forward_transform)}', "
                f"{str(self._forward_transform)}')")

    def __repr__(self):
        """
        Returns an evaluable string representation of the *ACES* *CTL*
        transform pair.

        Returns
        -------
        unicode
            Evaluable string representation.
        """

        return str(self)

    def __eq__(self, other):
        """
         Returns whether the *ACES* *CTL* transform pair is equal to given
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
            ((self._forward_transform == other._forward_transform)
             and (self._inverse_transform == other._inverse_transform))

    def __ne__(self, other):
        """
         Returns whether the *ACES* *CTL* transform pair is not equal to given
         other object.

         Parameters
         ----------
         other : object
             Object to test whether it is not equal to the *ACES* *CTL*
             transform pair.

         Returns
         -------
         bool
             Is given object notequal to *ACES* *CTL* transform pair.
        """

        return not (self == other)


def find_ctl_transform_pairs(ctl_transforms):
    """
    Finds the pairs in given list of *ACES* *CTL* transform paths.

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
        if basename.startswith('Inv'):
            basename = basename.replace('Inv', '')
            is_forward = False

        if re.search('.*_to_ACES$', basename):
            basename = basename.replace('_to_ACES', '')
            is_forward = False

        basename = basename.replace('ACES_to_', '')

        if is_forward:
            ctl_transform_pairs[basename]['forward_transform'] = ctl_transform
        else:
            ctl_transform_pairs[basename]['inverse_transform'] = ctl_transform

    return ctl_transform_pairs


def discover_aces_ctl_transforms(root_directory=ACES_CTL_TRANSFORMS_ROOT):
    """
    Discovers the *ACES* *CTL* transform paths in given root directory: The
    given directory is traversed and `*.ctl` files are collected.

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
            if not filename.lower().endswith('ctl'):
                continue

            ctl_transform = os.path.join(directory, filename)

            logging.debug(f'"{ctl_transform_relative_path(ctl_transform)}" '
                          f'CTL transform was found!')

            ctl_transforms[directory].append(ctl_transform)

    return ctl_transforms


def classify_aces_ctl_transforms(unclassified_ctl_transforms):
    """
    Classifies given *ACES* *CTL* transforms.

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
    [('ACEScsc.Academy.ACEScc', \
CTLTransformPair(\
CTLTransform('csc...ACEScc...ACEScsc.Academy.ACES_to_ACEScc.ctl')', \
CTLTransform('csc...ACEScc...ACEScsc.Academy.ACES_to_ACEScc.ctl')'))]
    """

    classified_ctl_transforms = defaultdict(lambda: defaultdict(dict))

    root_directory = paths_common_ancestor(
        *itertools.chain.from_iterable(unclassified_ctl_transforms.values()))
    for directory, ctl_transforms in unclassified_ctl_transforms.items():
        sub_directory = directory.replace(f'{root_directory}{os.sep}', '')
        family, *genus = [
            ACES_CTL_TRANSFORM_FAMILIES.get(part, part)
            for part in sub_directory.split(os.sep)
        ]

        genus = DEFAULT_ACES_CTL_TRANSFORM_GENUS if not genus else '/'.join(
            genus)

        for basename, pairs in find_ctl_transform_pairs(
                ctl_transforms).items():
            if len(pairs) == 1:
                ctl_transform = CTLTransform(
                    list(pairs.values())[0], family, genus)

                logging.debug(
                    f'Classifying "{ctl_transform}" under "{genus}".')

                classified_ctl_transforms[family][genus][basename] = (
                    ctl_transform)

            elif len(pairs) == 2:
                forward_ctl_transform = CTLTransform(
                    pairs['forward_transform'], family, genus)
                inverse_ctl_transform = CTLTransform(
                    pairs['inverse_transform'], family, genus)

                ctl_transform = CTLTransformPair(forward_ctl_transform,
                                                 inverse_ctl_transform)

                logging.debug(
                    f'Classifying "{ctl_transform}" under "{genus}".')

                classified_ctl_transforms[family][genus][basename] = (
                    ctl_transform)

    return vivified_to_dict(classified_ctl_transforms)


def unclassify_ctl_transforms(classified_ctl_transforms):
    """
    Unclassifies given *ACES* *CTL* transforms.

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
                        ctl_transform.forward_transform)
                    unclassified_ctl_transforms.append(
                        ctl_transform.inverse_transform)

    return unclassified_ctl_transforms


def filter_ctl_transforms(ctl_transforms, filterers=None):
    """
    Filters given *ACES* *CTL* transforms with given filterers.

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
        filterers = DEFAULT_ACES_CTL_TRANSFORM_FILTERERS

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
    Prints *aces-dev* taxonomy:

    -   The *aces-dev* *CTL* transforms are discovered by traversing the
        directory defined by the :attr:`opencolorio_config_aces.config.\
reference.ACES_CTL_TRANSFORMS_ROOT` attribute using the
        :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
        definition.
    -   The *CTL* transforms are classified by *family* e.g.
        *output_transform*, and *genus* e.g. *dcdm* using the
        :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
        definition.
    -   The resulting datastructure is printed.
    """

    classified_ctl_transforms = classify_aces_ctl_transforms(
        discover_aces_ctl_transforms())

    for family, genera in classified_ctl_transforms.items():
        message_box(family, print_callable=logging.info)
        for genus, ctl_transforms in genera.items():
            logging.info(f'[ {genus} ]')
            for name, ctl_transform in ctl_transforms.items():
                logging.info(f'\t( {name} )')
                if isinstance(ctl_transform, CTLTransform):
                    logging.info(f'\t\t"{ctl_transform.source}"'
                                 f' --> '
                                 f'"{ctl_transform.target}"')
                elif isinstance(ctl_transform, CTLTransformPair):
                    logging.info(
                        f'\t\t"{ctl_transform.forward_transform.source}"'
                        f' <--> '
                        f'"{ctl_transform.forward_transform.target}"')


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    print_aces_taxonomy()
