# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Reference Config Generator
=====================================

Defines various objects related to the generation of the *aces-dev* reference
*OpenColorIO* config:

-   :func:`opencolorio_config_aces.generate_config_aces`
"""

import csv
import logging
import re
from collections import defaultdict
from datetime import datetime
from enum import Flag, auto
from pathlib import Path

from opencolorio_config_aces.config.generation import (
    ConfigData, colorspace_factory, generate_config, look_factory,
    view_transform_factory)
from opencolorio_config_aces.config.reference import (
    classify_aces_ctl_transforms, discover_aces_ctl_transforms,
    unclassify_ctl_transforms)
from opencolorio_config_aces.utilities import git_describe, required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'ACES_CONFIG_REFERENCE_MAPPING_FILE_PATH',
    'ACES_CONFIG_REFERENCE_COLORSPACE',
    'ACES_CONFIG_OUTPUT_ENCODING_COLORSPACE',
    'ACES_CONFIG_COLORSPACE_NAME_SEPARATOR',
    'ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR',
    'ACES_CONFIG_BUILTIN_TRANSFORM_NAME_SEPARATOR',
    'ACES_CONFIG_DISPLAY_FAMILY', 'COLORSPACE_NAME_SUBSTITUTION_PATTERNS',
    'LOOK_NAME_SUBSTITUTION_PATTERNS',
    'TRANSFORM_FAMILY_SUBSTITUTION_PATTERNS',
    'VIEW_TRANSFORM_NAME_SUBSTITUTION_PATTERNS',
    'DISPLAY_NAME_SUBSTITUTION_PATTERNS', 'ColorspaceDescriptionStyle',
    'beautify_name', 'beautify_colorspace_name', 'beautify_look_name',
    'beautify_transform_family', 'beautify_view_transform_name',
    'beautify_display_name', 'ctl_transform_to_colorspace_name',
    'ctl_transform_to_look_name', 'ctl_transform_to_transform_family',
    'ctl_transform_to_description', 'ctl_transform_to_colorspace',
    'ctl_transform_to_look', 'create_builtin_transform',
    'style_to_view_transform', 'style_to_display_colorspace',
    'generate_config_aces'
]

ACES_CONFIG_REFERENCE_MAPPING_FILE_PATH = (
    Path(__file__).parents[0] / 'resources' /
    'OpenColorIO-ACES-Config Transforms - Reference Config - Mapping.csv')
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

CONFIG_MAPPING_FILE_PATH : unicode
"""

ACES_CONFIG_REFERENCE_COLORSPACE = 'ACES2065-1'
"""
*OpenColorIO* config reference colorspace.

ACES_CONFIG_REFERENCE_COLORSPACE : unicode
"""

ACES_CONFIG_OUTPUT_ENCODING_COLORSPACE = 'OCES'
"""
*OpenColorIO* config output encoding colorspace.

ACES_CONFIG_OUTPUT_ENCODING_COLORSPACE : unicode
"""

ACES_CONFIG_COLORSPACE_NAME_SEPARATOR = ' - '
"""
*OpenColorIO* config colorspace name separator.

ACES_CONFIG_COLORSPACE_NAME_SEPARATOR : unicode
"""

ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR = '/'
"""
*OpenColorIO* config colorspace family separator.

ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR : unicode
"""

ACES_CONFIG_BUILTIN_TRANSFORM_NAME_SEPARATOR = '_to_'
"""
*OpenColorIO* config *BuiltinTransform* name separator.

ACES_CONFIG_BUILTIN_TRANSFORM_NAME_SEPARATOR : unicode
"""

ACES_CONFIG_DISPLAY_FAMILY = 'Display'
"""
*OpenColorIO* config display family.

ACES_CONFIG_DISPLAY_FAMILY : unicode
"""

COLORSPACE_NAME_SUBSTITUTION_PATTERNS = {
    'ACES_0_1_1': 'ACES 0.1.1',
    'ACES_0_2_2': 'ACES 0.2.2',
    'ACES_0_7_1': 'ACES 0.7.1',
    '_7nits': '',
    '_15nits': '',
    '_': ' ',
    '-raw': '',
    '-': ' ',
    '\\b(\\w+)limited\\b': '(\\1 Limited)',
    '\\b(\\d+)nits\\b': '(\\1 nits)',
    'RGBmonitor': 'sRGB',
    'Rec709': 'Rec. 709',
    'Rec2020': 'Rec. 2020',
}
"""
*OpenColorIO* colorspace name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

COLORSPACE_NAME_SUBSTITUTION_PATTERNS : dict
"""

COLORSPACE_NAME_SUBSTITUTION_PATTERNS.update({
    # Input transforms also use the "family" name and thus need beautifying.
    (f'{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}Alexa'
     f'{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}v\\d+'
     f'{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}.*'):
    '',
    f'{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}':
    ACES_CONFIG_COLORSPACE_NAME_SEPARATOR,
})

LOOK_NAME_SUBSTITUTION_PATTERNS = {
    # TODO: Implement support for callable patterns.
    # The following one should be a dedicated definition/callable.
    'BlueLightArtifactFix': 'Blue Light Artifact Fix'
}
"""
*OpenColorIO* look name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

LOOK_NAME_SUBSTITUTION_PATTERNS : dict
"""

TRANSFORM_FAMILY_SUBSTITUTION_PATTERNS = {
    '\\\\': ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR,
    'vendorSupplied[/\\\\]': '',
    'arri': 'ARRI',
    'alexa': 'Alexa',
    'canon': 'Canon',
    'panasonic': 'Panasonic',
    'red': 'RED',
    'sony': 'Sony',
}
"""
*OpenColorIO* transform family substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

TRANSFORM_FAMILY_SUBSTITUTION_PATTERNS : dict
"""

VIEW_TRANSFORM_NAME_SUBSTITUTION_PATTERNS = {
    '7.2nit': '&',
    '15nit': '&',
    'lim': ' lim',
    'nit': ' nits',
    'sim': ' sim on',
    'CINEMA': 'Cinema',
    'VIDEO': 'Video',
    'REC1886': 'Rec.1886',
    'REC709': 'Rec.709',
    'REC2020': 'Rec.2020',
    '-': ' ',
}
"""
*OpenColorIO* view transform name substitution patterns.

VIEW_TRANSFORM_NAME_SUBSTITUTION_PATTERNS : dict
"""

DISPLAY_NAME_SUBSTITUTION_PATTERNS = {
    'G2.6-': '',
    '-BFD': '',
    'REC.1886': 'Rec.1886',
    'REC.709': 'Rec.709 Video',
    'REC.2020': 'Rec.2020 Video',
    'REC.2100': 'Rec.2100',
    '-Rec.': ' / Rec.',
    '-1000nit': '',
    # Legacy Substitutions
    'dcdm': 'DCDM',
    'p3': 'P3',
    'rec709': 'Rec. 709',
    'rec2020': 'Rec. 2020',
}
"""
*OpenColorIO* display name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

DISPLAY_NAME_SUBSTITUTION_PATTERNS : dict
"""


class ColorspaceDescriptionStyle(Flag):
    """
    Enum storing the various *OpenColorIO* colorspace description styles.
    """

    NONE = auto()
    ACES = auto()
    OPENCOLORIO = auto()
    SHORT = auto()
    LONG = auto()
    SHORT_UNION = ACES | OPENCOLORIO | SHORT
    LONG_UNION = ACES | OPENCOLORIO | LONG


def beautify_name(name, patterns):
    """
    Beautifies given name by applying in succession the given patterns.

    Parameters
    ----------
    name : unicode
        Name to beautify.
    patterns : dict
        Dictionary of regular expression patterns and substitution to apply
        onto the name.

    Returns
    -------
    unicode
        Beautified name.

    Examples
    --------
    >>> beautify_name(
    ...     'Rec709_100nits_dim',
    ...     COLORSPACE_NAME_SUBSTITUTION_PATTERNS)
    'Rec. 709 (100 nits) dim'
    """

    for pattern, substitution in patterns.items():
        name = re.sub(pattern, substitution, name)

    return name.strip()


def beautify_colorspace_name(name):
    """
    Beautifies given *OpenColorIO* colorspace name by applying in succession
    the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* colorspace name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* colorspace name.

    Examples
    --------
    >>> beautify_colorspace_name('Rec709_100nits_dim')
    'Rec. 709 (100 nits) dim'
    """

    return beautify_name(name, COLORSPACE_NAME_SUBSTITUTION_PATTERNS)


def beautify_look_name(name):
    """
    Beautifies given *OpenColorIO* look name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* look name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* look name.

    Examples
    --------
    >>> beautify_look_name('BlueLightArtifactFix')
    'Blue Light Artifact Fix'
    """

    return beautify_name(name, LOOK_NAME_SUBSTITUTION_PATTERNS)


def beautify_transform_family(name):
    """
    Beautifies given *OpenColorIO* colorspace family by applying in succession
    the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* colorspace family to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* colorspace family.

    Examples
    --------
    >>> beautify_transform_family('vendorSupplied/arri/alexa/v3/EI800')
    'ARRI/Alexa/v3/EI800'
    """

    return beautify_name(name, TRANSFORM_FAMILY_SUBSTITUTION_PATTERNS)


def beautify_view_transform_name(name):
    """
    Beautifies given *OpenColorIO* view transform name by applying in
    succession the relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* view transform name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* view transform name.

    Examples
    --------
    >>> beautify_view_transform_name(
    ...     'ACES-OUTPUT - ACES2065-1_to_CIE-XYZ-D65 - SDR-CINEMA_1.0')
    'Output - SDR Cinema - ACES 1.0'
    """

    basename, version = name.split(ACES_CONFIG_COLORSPACE_NAME_SEPARATOR)[
        -1].split('_')

    tokens = basename.split('-')
    family, genus = (['-'.join(tokens[:2]), '-'.join(tokens[2:])]
                     if len(tokens) > 2 else [basename, None])

    family = beautify_name(family, VIEW_TRANSFORM_NAME_SUBSTITUTION_PATTERNS)

    genus = (beautify_name(genus, VIEW_TRANSFORM_NAME_SUBSTITUTION_PATTERNS)
             if genus is not None else genus)

    return (f'Output - {family} ({genus}) - ACES {version}'
            if genus is not None else f'Output - {family} - ACES {version}')


def beautify_display_name(name):
    """
    Beautifies given *OpenColorIO* display name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* display name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* display name.

    Examples
    --------
    >>> beautify_display_name('DISPLAY - CIE-XYZ-D65_to_sRGB')
    'Display - sRGB'
    >>> beautify_display_name('rec709')
    'Display - Rec. 709'
    """

    basename = name.split(ACES_CONFIG_BUILTIN_TRANSFORM_NAME_SEPARATOR)[-1]

    name = beautify_name(basename, DISPLAY_NAME_SUBSTITUTION_PATTERNS)

    return f'Display - {name}'


def ctl_transform_to_colorspace_name(ctl_transform):
    """
    Generates the *OpenColorIO* colorspace name for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* colorspace name
        for.

    Returns
    -------
    unicode
        *OpenColorIO* colorspace name.
    """

    if ctl_transform.source in (ACES_CONFIG_REFERENCE_COLORSPACE,
                                ACES_CONFIG_OUTPUT_ENCODING_COLORSPACE):
        name = ctl_transform.target
    else:
        name = ctl_transform.source

    return beautify_colorspace_name(name)


def ctl_transform_to_look_name(ctl_transform):
    """
    Generates the *OpenColorIO* look name for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* look name for.

    Returns
    -------
    unicode
        *OpenColorIO* look name.
    """

    if ctl_transform.source in (ACES_CONFIG_REFERENCE_COLORSPACE,
                                ACES_CONFIG_OUTPUT_ENCODING_COLORSPACE):
        name = ctl_transform.target
    else:
        name = ctl_transform.source

    return beautify_look_name(name)


def ctl_transform_to_transform_family(ctl_transform, analytical=True):
    """
    Generates the *OpenColorIO* transform family for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* transform family
        for.
    analytical : bool, optional
        Whether to generate the *OpenColorIO* transform family that
        analytically matches the given *ACES* *CTL* transform, i.e. true to
        the *aces-dev* reference but not necessarily user friendly.

    Returns
    -------
    unicode
        *OpenColorIO* transform family.
    """

    if analytical:
        if (ctl_transform.family == 'csc'
                and ctl_transform.namespace == 'Academy'):
            family = 'CSC'
        elif ctl_transform.family == 'input_transform':
            family = (f'Input{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}'
                      f'{ctl_transform.genus}')
        elif ctl_transform.family == 'output_transform':
            family = 'Output'
        elif ctl_transform.family == 'lmt':
            family = 'LMT'
    else:
        if (ctl_transform.family == 'csc'
                and ctl_transform.namespace == 'Academy'):
            if re.match('ACES|ADX', ctl_transform.name):
                family = 'ACES'
            else:
                family = (f'Input{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}'
                          f'{ctl_transform.genus}')
        elif ctl_transform.family == 'input_transform':
            family = (f'Input{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}'
                      f'{ctl_transform.genus}')
        elif ctl_transform.family == 'output_transform':
            family = 'Output'
        elif ctl_transform.family == 'lmt':
            family = 'LMT'

    return beautify_transform_family(family)


@required('OpenColorIO')
def ctl_transform_to_description(
        ctl_transform,
        describe=ColorspaceDescriptionStyle.LONG_UNION,
        factory=colorspace_factory,
        **kwargs):
    """
    Generates the *OpenColorIO* colorspace or look description for given
    *ACES* *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* colorspace for.
    describe : bool, optional
        Whether to use the full *ACES* *CTL* transform description or just the
        first line.
    factory : callable, optional
        Factory used to adjust the code paths because of slight difference
        of signature between the *OpenColorIO* colorspace and look.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    unicode
        *OpenColorIO* colorspace or look description.
    """

    import PyOpenColorIO as ocio

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (ColorspaceDescriptionStyle.OPENCOLORIO,
                        ColorspaceDescriptionStyle.SHORT_UNION,
                        ColorspaceDescriptionStyle.LONG_UNION):

            forward, inverse = ([
                'to_reference',
                'from_reference',
            ] if factory is colorspace_factory else [
                'forward_transform',
                'inverse_transform',
            ])
            transforms = [
                transform for transform in (kwargs.get(forward),
                                            kwargs.get(inverse))
                if transform is not None
            ]
            transform = next(iter(transforms), None)
            if isinstance(transform, ocio.BuiltinTransform):
                description.append(transform.getDescription())

        if describe in (ColorspaceDescriptionStyle.ACES,
                        ColorspaceDescriptionStyle.ACES
                        | ColorspaceDescriptionStyle.SHORT,
                        ColorspaceDescriptionStyle.SHORT_UNION,
                        ColorspaceDescriptionStyle.LONG_UNION):
            if len(description) > 0:
                description.append('')

            aces_transform_id = (
                ctl_transform.aces_transform_id.aces_transform_id)

            if describe in (ColorspaceDescriptionStyle.ACES,
                            ColorspaceDescriptionStyle.ACES
                            | ColorspaceDescriptionStyle.SHORT,
                            ColorspaceDescriptionStyle.SHORT_UNION):
                description.append(f'ACEStransformID: {aces_transform_id}')
            else:
                description.append('CTL Transform')
                description.append(f'{"=" * len(description[-1])}\n')

                description.append(f'{ctl_transform.description}\n')
                description.append(f'ACEStransformID: {aces_transform_id}')

        description = '\n'.join(description)

    return description


def ctl_transform_to_colorspace(ctl_transform,
                                describe=ColorspaceDescriptionStyle.LONG_UNION,
                                analytical=True,
                                **kwargs):
    """
    Generates the *OpenColorIO* colorspace for given *ACES* *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* colorspace for.
    describe : bool, optional
        Whether to use the full *ACES* *CTL* transform description or just the
        first line.
    analytical : bool, optional
        Whether to generate the *OpenColorIO* transform family that
        analytically matches the given *ACES* *CTL* transform, i.e. true to
        the *aces-dev* reference but not necessarily user friendly.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    ColorSpace
        *OpenColorIO* colorspace.
    """

    name = ctl_transform_to_colorspace_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)

    description = ctl_transform_to_description(ctl_transform, describe,
                                               colorspace_factory, **kwargs)

    settings = {
        'name': (f'{beautify_colorspace_name(family)}'
                 f'{ACES_CONFIG_COLORSPACE_NAME_SEPARATOR}'
                 f'{name}'),
        'family':
        family,
        'description':
        description,
    }
    settings.update(kwargs)

    colorspace = colorspace_factory(**settings)

    return colorspace


def ctl_transform_to_look(ctl_transform,
                          describe=ColorspaceDescriptionStyle.LONG_UNION,
                          analytical=True,
                          **kwargs):
    """
    Generates the *OpenColorIO* look for given *ACES* *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* look for.
    describe : bool, optional
        Whether to use the full *ACES* *CTL* transform description or just the
        first line.
    analytical : bool, optional
        Whether to generate the *OpenColorIO* transform family that
        analytically matches the given *ACES* *CTL* transform, i.e. true to
        the *aces-dev* reference but not necessarily user friendly.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.look_factory` definition.

    Returns
    -------
    ColorSpace
        *OpenColorIO* look.
    """

    name = ctl_transform_to_look_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)

    description = ctl_transform_to_description(ctl_transform, describe,
                                               look_factory, **kwargs)

    settings = {
        'name': (f'{beautify_colorspace_name(family)}'
                 f'{ACES_CONFIG_COLORSPACE_NAME_SEPARATOR}'
                 f'{name}'),
        'description':
        description,
    }
    settings.update(kwargs)

    look = look_factory(**settings)

    return look


@required('OpenColorIO')
def create_builtin_transform(style):
    """
    Creates an *OpenColorIO* builtin transform for given style.

    If the style does not exist, a placeholder transform is used in place
    of the builtin transform.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style

    Returns
    -------
    BuiltinTransform
        *OpenColorIO* builtin transform for given style.
    """

    import PyOpenColorIO as ocio

    builtin_transform = ocio.BuiltinTransform()

    try:
        builtin_transform.setStyle(style)
    except ocio.Exception:
        logging.warning(f'{style} style is not defined, '
                        f'using a placeholder "FileTransform" instead!')
        builtin_transform = ocio.FileTransform()
        builtin_transform.setSrc(style)

    return builtin_transform


@required('OpenColorIO')
def style_to_view_transform(style,
                            ctl_transforms,
                            describe=ColorspaceDescriptionStyle.LONG_UNION):
    """
    Creates an *OpenColorIO* view transform for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style
    ctl_transforms : array_like
        Array of :class:`opencolorio_config_aces.config.reference.CTLTransform`
        class instances corresponding to the given style.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.

    Returns
    -------
    ViewTransform
        *OpenColorIO* view transform for given style.
    """

    import PyOpenColorIO as ocio

    name = beautify_view_transform_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (ColorspaceDescriptionStyle.OPENCOLORIO,
                        ColorspaceDescriptionStyle.SHORT_UNION,
                        ColorspaceDescriptionStyle.LONG_UNION):
            description.append(builtin_transform.getDescription())

        if describe in (ColorspaceDescriptionStyle.ACES,
                        ColorspaceDescriptionStyle.ACES
                        | ColorspaceDescriptionStyle.SHORT,
                        ColorspaceDescriptionStyle.SHORT_UNION,
                        ColorspaceDescriptionStyle.LONG_UNION):
            aces_transform_ids, aces_descriptions = zip(
                *[(ctl_transform.aces_transform_id.aces_transform_id,
                   ctl_transform.description)
                  for ctl_transform in ctl_transforms])

            if len(description) > 0:
                description.append('')

            if describe in (ColorspaceDescriptionStyle.ACES
                            | ColorspaceDescriptionStyle.SHORT,
                            ColorspaceDescriptionStyle.SHORT_UNION):
                description.extend([
                    f'ACEStransformID: {aces_transform_id}'
                    for aces_transform_id in aces_transform_ids
                ])
            else:
                description.append(
                    f'CTL Transform'
                    f'{"s" if len(aces_transform_ids) >= 2 else ""}')
                description.append(f'{"=" * len(description[-1])}\n')

                description.append(f'\n{"-" * 80}\n\n'.join([
                    (f'{aces_descriptions[i]}\n\n'
                     f'ACEStransformID: {aces_transform_id}\n')
                    for i, aces_transform_id in enumerate(aces_transform_ids)
                ]))

        description = '\n'.join(description)

    view_transform = view_transform_factory(
        name, from_reference=builtin_transform, description=description)

    return view_transform


@required('OpenColorIO')
def style_to_display_colorspace(
        style, describe=ColorspaceDescriptionStyle.OPENCOLORIO, **kwargs):
    """
    Creates an *OpenColorIO* display colorspace for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    ColorSpace
        *OpenColorIO* display colorspace for given style.
    """

    import PyOpenColorIO as ocio

    kwargs.setdefault('family', ACES_CONFIG_DISPLAY_FAMILY)

    name = beautify_display_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (ColorspaceDescriptionStyle.OPENCOLORIO,
                        ColorspaceDescriptionStyle.SHORT_UNION,
                        ColorspaceDescriptionStyle.LONG_UNION):
            description.append(builtin_transform.getDescription())

        description = '\n'.join(description)

    settings = {
        'name': name,
        'family': ACES_CONFIG_DISPLAY_FAMILY,
        'description': description,
        'from_reference': builtin_transform,
        'reference_space': ocio.REFERENCE_SPACE_DISPLAY,
    }
    settings.update(kwargs)

    colorspace = colorspace_factory(**settings)

    return colorspace


@required('OpenColorIO')
def generate_config_aces(
        config_name=None,
        validate=True,
        describe=ColorspaceDescriptionStyle.SHORT_UNION,
        config_mapping_file_path=ACES_CONFIG_REFERENCE_MAPPING_FILE_PATH,
        analytical=True,
        additional_data=False):
    """
    Generates the *aces-dev* reference implementation *OpenColorIO* Config
    using the *Mapping* method.

    The Config generation is constrained by a *CSV* file exported from the
    *Reference Config - Mapping* sheet from a
    `Google Sheets file <https://docs.google.com/spreadsheets/d/\
    1SXPt-USy3HlV2G2qAvh9zit6ZCINDOlfKT07yXJdWLg>`__. The *Google Sheets* file
    was originally authored using the output of the *aces-dev* conversion graph
    to support the discussions of the *OpenColorIO* *Working Group* on the
    design of the  *aces-dev* reference implementation *OpenColorIO* Config.
    The resulting mapping is the outcome of those discussions and leverages the
    new *OpenColorIO 2* display architecture while factoring many transforms.

    Parameters
    ----------
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    validate : bool, optional
        Whether to validate the config.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    config_mapping_file_path : unicode, optional
        Path to the *CSV* mapping file used by the *Mapping* method.
    analytical : bool, optional
        Whether to generate *OpenColorIO* transform families that analytically
        match the given *ACES* *CTL* transform, i.e. true to the *aces-dev*
        reference but not necessarily user friendly.
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config,
        :class:`opencolorio_config_aces.ConfigData` class instance and dict of
        *OpenColorIO* colorspaces and
        :class:`opencolorio_config_aces.config.reference.CTLTransform` class
        instances.
    """

    import PyOpenColorIO as ocio

    ctl_transforms = unclassify_ctl_transforms(
        classify_aces_ctl_transforms(discover_aces_ctl_transforms()))

    builtin_transforms = [
        builtin for builtin in ocio.BuiltinTransformRegistry()
    ]

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=',',
            fieldnames=[
                'ordering',
                'aces_transform_id',
                'builtin_transform_style',
                'linked_display_colorspace_style',
                'interface',
                'encoding',
                'categories',
            ])

        # Skipping the first header line.
        next(dict_reader)

        for transform_data in dict_reader:
            # Checking whether the "BuiltinTransform" style exists.
            style = transform_data['builtin_transform_style']
            if style:
                assert (style in builtin_transforms), (
                    f'"{style}" "BuiltinTransform" style does not '
                    f'exist!')

            # Checking whether the linked "DisplayColorspace"
            # "BuiltinTransform" style exists.
            style = transform_data['linked_display_colorspace_style']
            if style:
                assert (style in builtin_transforms), (
                    f'"{style}" "BuiltinTransform" style does not '
                    f'exist!')

            # Finding the "CTLTransform" class instance that matches given
            # "ACEStransformID", if it does not exist, there is a critical
            # mismatch in the mapping with *aces-dev*.
            aces_transform_id = transform_data['aces_transform_id']
            filtered_ctl_transforms = [
                ctl_transform for ctl_transform in ctl_transforms
                if ctl_transform.aces_transform_id.aces_transform_id ==
                aces_transform_id
            ]

            ctl_transform = next(iter(filtered_ctl_transforms), None)

            assert ctl_transform is not None, (
                f'"aces-dev" has no transform with "{aces_transform_id}" '
                f'ACEStransformID, please cross-check the '
                f'"{config_mapping_file_path}" config mapping file and '
                f'the "aces-dev" "CTL" transforms!')

            transform_data['ctl_transform'] = ctl_transform

            config_mapping[transform_data['builtin_transform_style']].append(
                transform_data)

    colorspaces = []
    looks = []
    displays, display_names = [], []
    view_transforms, view_transform_names = [], []
    shared_views = []

    aces_family_prefix = 'CSC' if analytical else 'ACES'

    scene_reference_colorspace = colorspace_factory(
        f'{aces_family_prefix} - {ACES_CONFIG_REFERENCE_COLORSPACE}',
        'ACES',
        description=(
            'The "Academy Color Encoding System" reference colorspace.'),
        encoding='scene-linear')

    display_reference_colorspace = colorspace_factory(
        'CIE-XYZ-D65',
        description='The "CIE XYZ (D65)" display connection colorspace.',
        reference_space=ocio.REFERENCE_SPACE_DISPLAY)

    raw_colorspace = colorspace_factory(
        'Utility - Raw',
        'Utility',
        description='The utility "Raw" colorspace.',
        is_data=True)

    colorspaces += [
        scene_reference_colorspace,
        display_reference_colorspace,
        raw_colorspace,
    ]

    for style, transforms_data in config_mapping.items():
        if transforms_data[0]['interface'] == 'ViewTransform':
            view_transform = style_to_view_transform(style, [
                transform_data['ctl_transform']
                for transform_data in transforms_data
            ], describe)
            view_transforms.append(view_transform)
            view_transform_name = view_transform.getName()
            view_transform_names.append(view_transform_name)

            for transform_data in transforms_data:
                display_style = transform_data[
                    'linked_display_colorspace_style']

                display = style_to_display_colorspace(
                    display_style,
                    encoding=transform_data.get('encoding'),
                    categories=transform_data.get('categories'))
                display_name = display.getName()

                if display_name not in display_names:
                    displays.append(display)
                    display_names.append(display_name)

                shared_views.append({
                    'display': display_name,
                    'view': view_transform_name,
                    'view_transform': view_transform_name,
                })
        else:
            for transform_data in transforms_data:
                ctl_transform = transform_data['ctl_transform']

                if transform_data['interface'] == 'Look':
                    look = ctl_transform_to_look(
                        ctl_transform,
                        describe,
                        analytical=analytical,
                        forward_transform=create_builtin_transform(style),
                        process_space=scene_reference_colorspace.getName(),
                    )

                    looks.append(look)
                else:
                    colorspace = ctl_transform_to_colorspace(
                        ctl_transform,
                        describe,
                        analytical=analytical,
                        to_reference=create_builtin_transform(style),
                        encoding=transform_data.get('encoding'),
                        categories=transform_data.get('categories'))

                    colorspaces.append(colorspace)

    untonemapped_view_transform = view_transform_factory(
        'Un-tone-mapped',
        from_reference=ocio.BuiltinTransform(
            'UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD'),
    )
    untonemapped_view_transform_name = untonemapped_view_transform.getName()
    for display in display_names:
        shared_views.append({
            'display': display,
            'view': untonemapped_view_transform_name,
            'view_transform': untonemapped_view_transform_name,
        })

    data = ConfigData(
        description=(
            f'The "Academy Color Encoding System" (ACES) "Reference Config".'
            f'\n\n'
            f'This "OpenColorIO" config is a strict and quasi-analytical '
            f'implementation of "aces-dev" and is designed as a reference for '
            f'software developers. It is not a replacement for the previous '
            f'"ACES" configs nor the "ACES Studio Config".'
            f'\n\n'
            f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
            f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.'),
        roles={
            ocio.ROLE_COLOR_TIMING: f'{aces_family_prefix} - ACEScct',
            ocio.ROLE_COMPOSITING_LOG: f'{aces_family_prefix} - ACEScct',
            ocio.ROLE_DATA: 'Utility - Raw',
            ocio.ROLE_DEFAULT: scene_reference_colorspace.getName(),
            ocio.ROLE_INTERCHANGE_DISPLAY:
            display_reference_colorspace.getName(),
            ocio.ROLE_INTERCHANGE_SCENE: scene_reference_colorspace.getName(),
            ocio.ROLE_REFERENCE: scene_reference_colorspace.getName(),
            ocio.ROLE_RENDERING: f'{aces_family_prefix} - ACEScg',
            ocio.ROLE_SCENE_LINEAR: f'{aces_family_prefix} - ACEScg',
        },
        colorspaces=colorspaces + displays,
        looks=looks,
        view_transforms=view_transforms + [untonemapped_view_transform],
        shared_views=shared_views,
        views=shared_views + [{
            'display': display,
            'view': 'Raw',
            'colorspace': 'Utility - Raw'
        } for display in display_names],
        active_displays=display_names,
        active_views=view_transform_names + ['Raw'],
        file_rules=[{
            'name': 'Default',
            'colorspace': scene_reference_colorspace.getName()
        }],
        inactive_colorspaces=['CIE-XYZ-D65'],
        default_view_transform=untonemapped_view_transform.getName(),
        profile_version=2)

    config = generate_config(data, config_name, validate)

    if additional_data:
        return config, data
    else:
        return config


if __name__ == '__main__':
    import os
    import opencolorio_config_aces

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(opencolorio_config_aces.__path__[0], '..',
                                   'build')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    config, data = generate_config_aces(
        config_name=os.path.join(build_directory,
                                 'config-aces-reference.ocio'),
        analytical=False,
        additional_data=True)
