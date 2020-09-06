# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*aces-dev* Reference Config Generator
=====================================

Defines various objects related to the generation of the *aces-dev* reference
*OpenColorIO* Config:

-   :func:`opencolorio_config_aces.ctl_transform_to_colorspace`
-   :func:`opencolorio_config_aces.generate_config_aces`
"""

import logging
import re

from opencolorio_config_aces.config.generation import (
    ConfigData, colorspace_factory, generate_config)
from opencolorio_config_aces.config.reference import (
    build_aces_conversion_graph, classify_aces_ctl_transforms,
    discover_aces_ctl_transforms, filter_nodes, filter_ctl_transforms,
    node_to_ctl_transform)
from opencolorio_config_aces.utilities import required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'ACES_CONFIG_COLORSPACE_NAME_SEPARATOR',
    'ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR',
    'COLORSPACE_NAME_SUBSTITUTION_PATTERNS',
    'COLORSPACE_FAMILY_SUBSTITUTION_PATTERNS',
    'VIEW_NAME_SUBSTITUTION_PATTERNS', 'DISPLAY_NAME_SUBSTITUTION_PATTERNS',
    'COLORSPACE_TO_CTL_TRANSFORM', 'beautify_name', 'beautify_colorspace_name',
    'beautify_colorspace_family', 'beautify_view_name',
    'beautify_display_name', 'ctl_transform_to_colorspace_name',
    'ctl_transform_to_colorspace_family', 'ctl_transform_to_colorspace',
    'generate_config_aces'
]

ACES_CONFIG_COLORSPACE_NAME_SEPARATOR = ' - '
"""
*OpenColorIO* colorspace name separator.

ACES_CONFIG_COLORSPACE_NAME_SEPARATOR : unicode
"""

ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR = '/'
"""
*OpenColorIO* colorspace family separator.

ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR : unicode
"""

COLORSPACE_NAME_SUBSTITUTION_PATTERNS = {
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

COLORSPACE_FAMILY_SUBSTITUTION_PATTERNS = {
    '\\\\': ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR,
    'vendorSupplied[/\\\\]': '',
    'arri': 'ARRI',
    'alexa': 'Alexa',
    'sony': 'Sony',
}
"""
*OpenColorIO* colorspace family substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

COLORSPACE_FAMILY_SUBSTITUTION_PATTERNS : dict
"""

VIEW_NAME_SUBSTITUTION_PATTERNS = {
    '\\(100 nits\\) dim': '',
    '\\(100 nits\\)': '',
    '\\(48 nits\\)': '',
    f'Output{ACES_CONFIG_COLORSPACE_NAME_SEPARATOR}': '',
}
"""
*OpenColorIO* view name substitution patterns.

VIEW_NAME_SUBSTITUTION_PATTERNS : dict
"""

DISPLAY_NAME_SUBSTITUTION_PATTERNS = {
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

COLORSPACE_TO_CTL_TRANSFORM = {}
"""
Mapping between an *OpenColorIO* colorspace and an *ACES* *CTL* transform.

The mapping is filled by :func:`opencolorio_config_aces.\
ctl_transform_to_colorspace` definition.

COLORSPACE_TO_CTL_TRANSFORM : dict
"""


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


def beautify_colorspace_family(name):
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
    >>> beautify_colorspace_family('vendorSupplied/arri/alexa/v3/EI800')
    'ARRI/Alexa/v3/EI800'
    """

    return beautify_name(name, COLORSPACE_FAMILY_SUBSTITUTION_PATTERNS)


def beautify_view_name(name):
    """
    Beautifies given *OpenColorIO* view name by applying in succession the
    relevant patterns.

    Parameters
    ----------
    name : unicode
        *OpenColorIO* view name to beautify.

    Returns
    -------
    unicode
        Beautified *OpenColorIO* view name.

    Examples
    --------
    >>> beautify_view_name('Rec. 709 (100 nits) dim')
    'Rec. 709'
    """

    return beautify_name(name, VIEW_NAME_SUBSTITUTION_PATTERNS)


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
    >>> beautify_display_name('rec709')
    'Rec. 709'
    """

    return beautify_name(name, DISPLAY_NAME_SUBSTITUTION_PATTERNS)


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

    if ctl_transform.source in ('ACES2065-1', 'OCES'):
        name = ctl_transform.target
    else:
        name = ctl_transform.source

    return beautify_colorspace_name(name)


def ctl_transform_to_colorspace_family(ctl_transform):
    """
    Generates the *OpenColorIO* colorspace family for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* colorspace family
        for.

    Returns
    -------
    unicode
        *OpenColorIO* colorspace family.
    """

    if ctl_transform.family == 'csc' and ctl_transform.namespace == 'Academy':
        family = 'ACES'
    elif ctl_transform.family == 'input_transform':
        family = (f'Input{ACES_CONFIG_COLORSPACE_FAMILY_SEPARATOR}'
                  f'{ctl_transform.genus}')
    elif ctl_transform.family == 'output_transform':
        family = 'Output'
    elif ctl_transform.family == 'lmt':
        family = 'LMT'

    return beautify_colorspace_family(family)


def ctl_transform_to_colorspace(ctl_transform, complete_description=True):
    """
    Generates the *OpenColorIO* colorspace for given *ACES* *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* colorspace for.
    complete_description : bool, optional
        Whether to use the full *ACES* *CTL* transform description or just the
        first line.

    Returns
    -------
    ColorSpace
        *OpenColorIO* colorspace.
    """

    name = ctl_transform_to_colorspace_name(ctl_transform)
    family = ctl_transform_to_colorspace_family(ctl_transform)

    colorspace = colorspace_factory(
        f'{beautify_colorspace_name(family)}'
        f'{ACES_CONFIG_COLORSPACE_NAME_SEPARATOR}{name}',
        family,
        description=ctl_transform.description
        if complete_description else ctl_transform.description.split('\n')[0])

    COLORSPACE_TO_CTL_TRANSFORM[colorspace.getName()] = ctl_transform

    return colorspace


@required('OpenColorIO')
def generate_config_aces(config_name=None,
                         validate=True,
                         complete_description=True):
    """
    Generates the *aces-dev* reference implementation *OpenColorIO* Config.

    Parameters
    ----------
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    validate : bool, optional
        Whether to validate the config.
    complete_description : bool, optional
        Whether to output the full *ACES* *CTL* transform descriptions.

    Returns
    -------
    Config
        *OpenColorIO* config.
    """

    import PyOpenColorIO as ocio

    ctl_transforms = discover_aces_ctl_transforms()
    classified_ctl_transforms = classify_aces_ctl_transforms(ctl_transforms)
    filtered_ctl_transforms = filter_ctl_transforms(classified_ctl_transforms)

    graph = build_aces_conversion_graph(filtered_ctl_transforms)

    colorspaces = []

    colorspaces += [
        colorspace_factory(
            'ACES - ACES2065-1',
            'ACES',
            description=(
                'The "Academy Color Encoding System" reference colorspace.')),
        colorspace_factory(
            'ACES - OCES',
            'ACES',
            description=(
                'The "Output Color Encoding Specification" colorspace.')),
    ]

    # "CSC"
    csc = []
    for node in filter_nodes(graph, [lambda x: x.family == 'csc']):
        csc.append(
            ctl_transform_to_colorspace(
                node_to_ctl_transform(graph, node), complete_description))
    colorspaces += csc

    # "Input Transforms"
    input_transforms = []
    for node in filter_nodes(graph, [lambda x: x.family == 'input_transform']):
        input_transforms.append(
            ctl_transform_to_colorspace(
                node_to_ctl_transform(graph, node), complete_description))
    colorspaces += input_transforms

    # "LMTs"
    lmts = []
    for node in filter_nodes(graph, [lambda x: x.family == 'lmt']):
        lmts.append(
            ctl_transform_to_colorspace(
                node_to_ctl_transform(graph, node), complete_description))
    colorspaces += lmts

    # "Output Transforms"
    output_transforms = []
    displays = set()
    views = []
    for node in filter_nodes(graph,
                             [lambda x: x.family == 'output_transform']):
        ctl_transform = node_to_ctl_transform(graph, node)
        colorspace = ctl_transform_to_colorspace(ctl_transform,
                                                 complete_description)
        output_transforms.append(colorspace)
        display = beautify_display_name(ctl_transform.genus)
        displays.add(display)
        view = beautify_view_name(colorspace.getName())
        views.append({
            'display': display,
            'view': view,
            'colorspace': colorspace.getName()
        })
    displays = sorted(list(displays))
    displays.insert(0, displays.pop(displays.index('sRGB')))
    views = sorted(views, key=lambda x: (x['display'], x['view']))
    colorspaces += output_transforms

    # Utility Raw
    colorspaces.append(
        colorspace_factory(
            'Utility - Raw',
            'Utility',
            description='The utility "Raw" colorspace.',
            is_data=True))
    for display in displays:
        view = beautify_view_name(colorspaces[-1].getName())
        views.append({
            'display': display,
            'view': view,
            'colorspace': colorspaces[-1].getName()
        })

    # Config Data
    data = ConfigData(
        description='The "Academy Color Encoding System" reference config.',
        roles={'ACES - ACEScg': ocio.ROLE_SCENE_LINEAR},
        colorspaces=colorspaces,
        views=views,
        active_displays=displays,
        active_views=list(dict.fromkeys([view['view'] for view in views])),
        file_rules=[{
            'name': 'Default',
            'colorspace': 'ACES - ACEScg'
        }],
        profile_version=2)

    return generate_config(data, config_name, validate)


if __name__ == '__main__':
    from pprint import pprint

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    generate_config_aces('config-aces-v2.ocio')

    pprint(COLORSPACE_TO_CTL_TRANSFORM)
