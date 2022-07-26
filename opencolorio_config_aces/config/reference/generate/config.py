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
import PyOpenColorIO as ocio
import re
from collections import defaultdict
from datetime import datetime
from enum import Flag, auto
from pathlib import Path

from opencolorio_config_aces.config.generation import (
    VersionData,
    ConfigData,
    colorspace_factory,
    generate_config,
    look_factory,
    produce_transform,
    view_transform_factory,
)
from opencolorio_config_aces.config.reference import (
    classify_aces_ctl_transforms,
    discover_aces_ctl_transforms,
    unclassify_ctl_transforms,
    version_aces_dev,
)
from opencolorio_config_aces.utilities import (
    git_describe,
    multi_replace,
    regularise_version,
    validate_method,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE",
    "PATH_TRANSFORMS_MAPPING_FILE_REFERENCE",
    "COLORSPACE_SCENE_ENCODING_REFERENCE",
    "COLORSPACE_OUTPUT_ENCODING_REFERENCE",
    "FAMILY_DISPLAY_REFERENCE",
    "SEPARATOR_COLORSPACE_NAME_REFERENCE",
    "SEPARATOR_COLORSPACE_FAMILY_REFERENCE",
    "SEPARATOR_BUILTIN_TRANSFORM_NAME_REFERENCE",
    "PATTERNS_COLORSPACE_NAME_REFERENCE",
    "PATTERNS_LOOK_NAME_REFERENCE",
    "PATTERNS_TRANSFORM_FAMILY_REFERENCE",
    "PATTERNS_VIEW_TRANSFORM_NAME_REFERENCE",
    "PATTERNS_DISPLAY_NAME_REFERENCE",
    "ColorspaceDescriptionStyle",
    "version_config_mapping_file",
    "beautify_name",
    "beautify_colorspace_name",
    "beautify_look_name",
    "beautify_transform_family",
    "beautify_view_transform_name",
    "beautify_display_name",
    "format_optional_prefix",
    "format_swapped_affix",
    "ctl_transform_to_colorspace_name",
    "ctl_transform_to_look_name",
    "ctl_transform_to_transform_family",
    "ctl_transform_to_description",
    "ctl_transform_to_colorspace",
    "ctl_transform_to_look",
    "style_to_view_transform",
    "style_to_display_colorspace",
    "dependency_versions",
    "config_basename_aces",
    "config_description_aces",
    "generate_config_aces",
]

logger = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE = (
    "https://docs.google.com/spreadsheets/d/"
    "1SXPt-USy3HlV2G2qAvh9zit6ZCINDOlfKT07yXJdWLg/"
    "export?format=csv&gid=273921464"
)
"""
URL to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE : unicode
"""

PATH_TRANSFORMS_MAPPING_FILE_REFERENCE = next(
    (Path(__file__).parents[0] / "resources").glob("*Mapping.csv")
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

PATH_TRANSFORMS_MAPPING_FILE_REFERENCE : unicode
"""


COLORSPACE_SCENE_ENCODING_REFERENCE = "ACES2065-1"
"""
*OpenColorIO* config reference colorspace.

COLORSPACE_SCENE_ENCODING_REFERENCE : unicode
"""

COLORSPACE_OUTPUT_ENCODING_REFERENCE = "OCES"
"""
*OpenColorIO* config output encoding colorspace.

COLORSPACE_OUTPUT_ENCODING_REFERENCE : unicode
"""

FAMILY_DISPLAY_REFERENCE = "Display"
"""
*OpenColorIO* config display family.

FAMILY_DISPLAY_REFERENCE : unicode
"""

SEPARATOR_COLORSPACE_NAME_REFERENCE = " - "
"""
*OpenColorIO* config colorspace name separator.

SEPARATOR_COLORSPACE_NAME_REFERENCE : unicode
"""

SEPARATOR_COLORSPACE_FAMILY_REFERENCE = "/"
"""
*OpenColorIO* config colorspace family separator.

SEPARATOR_COLORSPACE_FAMILY_REFERENCE : unicode
"""

SEPARATOR_BUILTIN_TRANSFORM_NAME_REFERENCE = "_to_"
"""
*OpenColorIO* config *BuiltinTransform* name separator.

SEPARATOR_BUILTIN_TRANSFORM_NAME_REFERENCE : unicode
"""

PATTERNS_COLORSPACE_NAME_REFERENCE = {
    "ACES_0_1_1": "ACES 0.1.1",
    "ACES_0_2_2": "ACES 0.2.2",
    "ACES_0_7_1": "ACES 0.7.1",
    "_7nits": "",
    "_15nits": "",
    "_": " ",
    "-raw": "",
    "-": " ",
    "\\b(\\w+)limited\\b": "(\\1 Limited)",
    "\\b(\\d+)nits\\b": "(\\1 nits)",
    "RGBmonitor": "sRGB",
    "Rec709": "Rec. 709",
    "Rec2020": "Rec. 2020",
}
"""
*OpenColorIO* colorspace name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_COLORSPACE_NAME_REFERENCE : dict
"""

PATTERNS_COLORSPACE_NAME_REFERENCE.update(
    {
        # Input transforms also use the "family" name and thus need beautifying.
        (
            f"{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}Alexa"
            f"{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}v\\d+"
            f"{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}.*"
        ): "",
        f"{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}": SEPARATOR_COLORSPACE_NAME_REFERENCE,
    }
)

PATTERNS_LOOK_NAME_REFERENCE = {
    # TODO: Implement support for callable patterns.
    # The following ones should be a dedicated definition/callable.
    "BlueLightArtifactFix": "Blue Light Artifact Fix",
    "GamutCompress": "ACES 1.3 Reference Gamut Compression",
}
"""
*OpenColorIO* look name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_LOOK_NAME_REFERENCE : dict
"""

PATTERNS_TRANSFORM_FAMILY_REFERENCE = {
    "\\\\": SEPARATOR_COLORSPACE_FAMILY_REFERENCE,
    "vendorSupplied[/\\\\]": "",
    "arri": "ARRI",
    "alexa": "Alexa",
    "canon": "Canon",
    "panasonic": "Panasonic",
    "red": "RED",
    "sony": "Sony",
}
"""
*OpenColorIO* transform family substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_TRANSFORM_FAMILY_REFERENCE : dict
"""

PATTERNS_VIEW_TRANSFORM_NAME_REFERENCE = {
    "7.2nit": "&",
    "15nit": "&",
    "lim": " lim",
    "nit": " nits",
    "sim": " sim on",
    "CINEMA": "Cinema",
    "VIDEO": "Video",
    "REC1886": "Rec.1886",
    "REC709": "Rec.709",
    "REC2020": "Rec.2020",
    "-": " ",
}
"""
*OpenColorIO* view transform name substitution patterns.

PATTERNS_VIEW_TRANSFORM_NAME_REFERENCE : dict
"""

PATTERNS_DISPLAY_NAME_REFERENCE = {
    "G2.6-": "",
    "-BFD": "",
    "REC.1886": "Rec.1886",
    "REC.709": "Rec.709 Video",
    "REC.2020": "Rec.2020 Video",
    "REC.2100": "Rec.2100",
    "-Rec.": " / Rec.",
    "-1000nit": "",
    # Legacy Substitutions
    "dcdm": "DCDM",
    "p3": "P3",
    "rec709": "Rec. 709",
    "rec2020": "Rec. 2020",
}
"""
*OpenColorIO* display name substitution patterns.

Notes
-----
- The substitutions are evaluated in order.

PATTERNS_DISPLAY_NAME_REFERENCE : dict
"""


class ColorspaceDescriptionStyle(Flag):
    """Enum storing the various *OpenColorIO* colorspace description styles."""

    NONE = auto()
    ACES = auto()
    OPENCOLORIO = auto()
    SHORT = auto()
    LONG = auto()
    SHORT_UNION = ACES | OPENCOLORIO | SHORT
    LONG_UNION = ACES | OPENCOLORIO | LONG


def version_config_mapping_file(path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE):
    """
    Return the current version of given *CSV* mapping file.

    No parsing of the file content is perform, a simple regex is used to
    extract the version of the file name.

    Parameters
    ----------
    path : Path or str, optional
         Path to the *CSV* mapping file.

    Returns
    -------
    str
        *CSV* mapping file version.

    Examples
    --------
    >>> path = (
    ...     "/tmp/OpenColorIO-Config-ACES Reference Transforms - v0.1.0 - "
    ...     "Reference Config - Mapping.csv"
    ... )
    >>> version_config_mapping_file(path)
    'v0.1.0'
    >>> path = (
    ...     "/tmp/OpenColorIO-Config-ACES Reference Transforms - "
    ...     "Reference Config - Mapping.csv"
    ... )
    >>> version_config_mapping_file(path)
    ''
    """

    search = re.search(r"- (v\d\.\d\.\d) -", Path(path).stem)
    if search:
        return search.group(1)
    else:
        return ""


def beautify_name(name, patterns):
    """
    Beautify given name by applying in succession the given patterns.

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
    ...     PATTERNS_COLORSPACE_NAME_REFERENCE)
    'Rec. 709 (100 nits) dim'
    """

    return multi_replace(name, patterns).strip()


def beautify_colorspace_name(name):
    """
    Beautify given *OpenColorIO* colorspace name by applying in succession
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

    return beautify_name(name, PATTERNS_COLORSPACE_NAME_REFERENCE)


def beautify_look_name(name):
    """
    Beautify given *OpenColorIO* look name by applying in succession the
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

    return beautify_name(name, PATTERNS_LOOK_NAME_REFERENCE)


def beautify_transform_family(name):
    """
    Beautify given *OpenColorIO* colorspace family by applying in succession
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

    return beautify_name(name, PATTERNS_TRANSFORM_FAMILY_REFERENCE)


def beautify_view_transform_name(name):
    """
    Beautify given *OpenColorIO* view transform name by applying in
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
    'SDR Cinema'
    """

    basename = name.split(SEPARATOR_COLORSPACE_NAME_REFERENCE)[-1].split("_")[
        0
    ]

    tokens = basename.split("-")
    family, genus = (
        ["-".join(tokens[:2]), "-".join(tokens[2:])]
        if len(tokens) > 2
        else [basename, None]
    )

    family = beautify_name(family, PATTERNS_VIEW_TRANSFORM_NAME_REFERENCE)

    genus = (
        beautify_name(genus, PATTERNS_VIEW_TRANSFORM_NAME_REFERENCE)
        if genus is not None
        else genus
    )

    return f"{family} ({genus})" if genus is not None else family


def beautify_display_name(name):
    """
    Beautify given *OpenColorIO* display name by applying in succession the
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
    'sRGB'
    >>> beautify_display_name('rec709')
    'Rec. 709'
    """

    basename = name.split(SEPARATOR_BUILTIN_TRANSFORM_NAME_REFERENCE)[-1]

    name = beautify_name(basename, PATTERNS_DISPLAY_NAME_REFERENCE)

    return name


def format_optional_prefix(name, prefix, scheme="Modern 1"):
    """
    Format given name according to given prefix and naming convention scheme.

    Parameters
    ----------
    name : str
        Name to format.
    prefix : str
        Prefix to use during the formatting.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Returns
    -------
    str
        Formatted name

    Examples
    --------
    >>> format_optional_prefix("ACEScg", "ACES")
    'ACEScg'
    >>> format_optional_prefix("ACEScg", "ACES", "Legacy")
    'ACES - ACEScg'
    """

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    return (
        f"{prefix}{SEPARATOR_COLORSPACE_NAME_REFERENCE}{name}"
        if scheme == "legacy"
        else name
    )


def format_swapped_affix(name, affix, scheme="Modern 1"):
    """
    Format given name according to given prefix and naming convention scheme.

    Parameters
    ----------
    name : str
        Name to format.
    affix : str
        affix to use during the formatting.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Returns
    -------
    str
        Formatted name

    Examples
    --------
    >>> format_swapped_affix("sRGB", "Display")
    'sRGB - Display'
    >>> format_swapped_affix("sRGB", "Display", "Legacy")
    'Display - sRGB'
    """

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    return (
        f"{affix}{SEPARATOR_COLORSPACE_NAME_REFERENCE}{name}"
        if scheme == "legacy"
        else f"{name}{SEPARATOR_COLORSPACE_NAME_REFERENCE}{affix}"
    )


def ctl_transform_to_colorspace_name(ctl_transform):
    """
    Generate the *OpenColorIO* colorspace name for given *ACES* *CTL*
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

    if ctl_transform.source in (
        COLORSPACE_SCENE_ENCODING_REFERENCE,
        COLORSPACE_OUTPUT_ENCODING_REFERENCE,
    ):
        name = ctl_transform.target
    else:
        name = ctl_transform.source

    return beautify_colorspace_name(name)


def ctl_transform_to_look_name(ctl_transform):
    """
    Generate the *OpenColorIO* look name for given *ACES* *CTL*
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

    if ctl_transform.source in (
        COLORSPACE_SCENE_ENCODING_REFERENCE,
        COLORSPACE_OUTPUT_ENCODING_REFERENCE,
    ):
        name = ctl_transform.target
    else:
        name = ctl_transform.source

    return beautify_look_name(name)


def ctl_transform_to_transform_family(ctl_transform, analytical=True):
    """
    Generate the *OpenColorIO* transform family for given *ACES* *CTL*
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
        if (
            ctl_transform.family == "csc"
            and ctl_transform.namespace == "Academy"
        ):
            family = "CSC"
        elif ctl_transform.family == "input_transform":
            family = (
                f"Input{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}"
                f"{ctl_transform.genus}"
            )
        elif ctl_transform.family == "output_transform":
            family = "Output"
        elif ctl_transform.family == "lmt":
            family = "LMT"
    else:
        if (
            ctl_transform.family == "csc"
            and ctl_transform.namespace == "Academy"
        ):
            if re.match("ACES|ADX", ctl_transform.name):
                family = "ACES"
            else:
                family = (
                    f"Input{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}"
                    f"{ctl_transform.genus}"
                )
        elif ctl_transform.family == "input_transform":
            family = (
                f"Input{SEPARATOR_COLORSPACE_FAMILY_REFERENCE}"
                f"{ctl_transform.genus}"
            )
        elif ctl_transform.family == "output_transform":
            family = "Output"
        elif ctl_transform.family == "lmt":
            family = "LMT"

    return beautify_transform_family(family)


def ctl_transform_to_description(
    ctl_transform,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    factory=colorspace_factory,
    **kwargs,
):
    """
    Generate the *OpenColorIO* colorspace or look description for given
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

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):

            forward, inverse = (
                [
                    "to_reference",
                    "from_reference",
                ]
                if factory is colorspace_factory
                else [
                    "forward_transform",
                    "inverse_transform",
                ]
            )
            transforms = [
                transform
                for transform in (kwargs.get(forward), kwargs.get(inverse))
                if transform is not None
            ]
            transform = produce_transform(next(iter(transforms), None))
            if isinstance(transform, ocio.BuiltinTransform):
                description.append(transform.getDescription())

        if describe in (
            ColorspaceDescriptionStyle.ACES,
            ColorspaceDescriptionStyle.ACES | ColorspaceDescriptionStyle.SHORT,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            if len(description) > 0:
                description.append("")

            aces_transform_id = (
                ctl_transform.aces_transform_id.aces_transform_id
            )

            if describe in (
                ColorspaceDescriptionStyle.ACES,
                ColorspaceDescriptionStyle.ACES
                | ColorspaceDescriptionStyle.SHORT,
                ColorspaceDescriptionStyle.SHORT_UNION,
            ):
                description.append(f"ACEStransformID: {aces_transform_id}")
            else:
                description.append("CTL Transform")
                description.append(f'{"=" * len(description[-1])}\n')

                description.append(f"{ctl_transform.description}\n")
                description.append(f"ACEStransformID: {aces_transform_id}")

        description = "\n".join(description)

    return description


def ctl_transform_to_colorspace(
    ctl_transform,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    analytical=True,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Generate the *OpenColorIO* colorspace or its signature for given *ACES*
    *CTL* transform.

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
    signature_only : bool, optional
        Whether to return the *OpenColorIO* colorspace signature only, i.e. the
        arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    ColorSpace or dict
        *OpenColorIO* colorspace or its signature.
    """

    name = ctl_transform_to_colorspace_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)
    description = ctl_transform_to_description(
        ctl_transform, describe, colorspace_factory, **kwargs
    )

    signature = {
        "name": format_optional_prefix(
            name, beautify_colorspace_name(family), scheme
        ),
        "family": family,
        "description": description,
    }
    signature.update(kwargs)

    if signature_only:
        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def ctl_transform_to_look(
    ctl_transform,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    analytical=True,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Generate the *OpenColorIO* look or its signature for given *ACES* *CTL*
    transform.

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
    signature_only : bool, optional
        Whether to return the *OpenColorIO* look signature only, i.e. the
        arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.look_factory` definition.

    Returns
    -------
    ColorSpace or dict
        *OpenColorIO* look or its signature.
    """

    name = ctl_transform_to_look_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)
    description = ctl_transform_to_description(
        ctl_transform, describe, look_factory, **kwargs
    )

    signature = {
        "name": format_optional_prefix(
            name, beautify_colorspace_name(family), scheme
        ),
        "description": description,
    }
    signature.update(kwargs)

    if signature_only:
        return signature
    else:
        look = look_factory(**signature)

        return look


def style_to_view_transform(
    style,
    ctl_transforms,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Create an *OpenColorIO* view transform or its signature for given style.

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
    signature_only : bool, optional
        Whether to return the *OpenColorIO* view colorspace signature only,
        i.e. the arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    ViewTransform or dict
        *OpenColorIO* view transform or its signature for given style.
    """

    name = beautify_view_transform_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            description.append(builtin_transform.getDescription())

        if describe in (
            ColorspaceDescriptionStyle.ACES,
            ColorspaceDescriptionStyle.ACES | ColorspaceDescriptionStyle.SHORT,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            aces_transform_ids, aces_descriptions = zip(
                *[
                    (
                        ctl_transform.aces_transform_id.aces_transform_id,
                        ctl_transform.description,
                    )
                    for ctl_transform in ctl_transforms
                ]
            )

            if len(description) > 0:
                description.append("")

            if describe in (
                ColorspaceDescriptionStyle.ACES
                | ColorspaceDescriptionStyle.SHORT,
                ColorspaceDescriptionStyle.SHORT_UNION,
            ):
                description.extend(
                    [
                        f"ACEStransformID: {aces_transform_id}"
                        for aces_transform_id in aces_transform_ids
                    ]
                )
            else:
                description.append(
                    f"CTL Transform"
                    f'{"s" if len(aces_transform_ids) >= 2 else ""}'
                )
                description.append(f'{"=" * len(description[-1])}\n')

                description.append(
                    f'\n{"-" * 80}\n\n'.join(
                        [
                            (
                                f"{aces_descriptions[i]}\n\n"
                                f"ACEStransformID: {aces_transform_id}\n"
                            )
                            for i, aces_transform_id in enumerate(
                                aces_transform_ids
                            )
                        ]
                    )
                )

        description = "\n".join(description)

    version = style.split(SEPARATOR_COLORSPACE_NAME_REFERENCE)[-1].split("_")[
        -1
    ]
    signature = {
        "name": format_swapped_affix(
            f"ACES {version}",
            format_optional_prefix(name, "Output", scheme),
            scheme,
        ),
        "from_reference": builtin_transform,
        "description": description,
    }
    signature.update(**kwargs)

    if signature_only:
        signature["from_reference"] = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }
        return signature
    else:
        view_transform = view_transform_factory(**signature)

        return view_transform


def style_to_display_colorspace(
    style,
    describe=ColorspaceDescriptionStyle.OPENCOLORIO,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Create an *OpenColorIO* display colorspace or its signature for given
    style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* display colorspace signature only,
        i.e. the arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    ColorSpace or dict
        *OpenColorIO* display colorspace or its signature for given style.
    """

    kwargs.setdefault("family", FAMILY_DISPLAY_REFERENCE)

    name = beautify_display_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            description.append(builtin_transform.getDescription())

        description = "\n".join(description)

    signature = {
        "name": format_swapped_affix(name, "Display", scheme),
        "family": FAMILY_DISPLAY_REFERENCE,
        "description": description,
        "from_reference": builtin_transform,
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }
    signature.update(kwargs)

    if signature_only:
        signature["from_reference"] = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }

        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def dependency_versions(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
):
    """
    Return the dependency versions of the *aces-dev* reference implementation
    *OpenColorIO* config.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    dict
        Dependency versions.

    Examples
    --------
    >>> dependency_versions()  # doctest: +SKIP
    {'aces': 'v1.3', 'ocio': 'v2.1.2dev', 'colorspaces': 'v0.1.0'}
    """

    versions = {
        "aces": regularise_version(version_aces_dev()),
        "ocio": regularise_version(ocio.__version__),
        "colorspaces": regularise_version(
            version_config_mapping_file(config_mapping_file_path)
        ),
    }

    return versions


def config_basename_aces(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    basename, i.e. the filename devoid of directory affixe.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_aces()  # doctest: +SKIP
    'reference-config-v0.1.0_aces-v1.3_ocio-v2.1.2dev.ocio'
    """

    return (
        "reference-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio"
    ).format(**dependency_versions(config_mapping_file_path))


def config_name_aces(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config name.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_aces()  # doctest: +SKIP
    'Academy Color Encoding System - Reference Config [COLORSPACES v0.1.0] \
[ACES v1.3] [OCIO v2.1.2dev]'
    """

    return (
        "Academy Color Encoding System - Reference Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions(config_mapping_file_path))


def config_description_aces(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    description.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config description.
    """

    name = config_name_aces(config_mapping_file_path)
    underline = "-" * len(name)
    description = (
        'This "OpenColorIO" config is a strict and quasi-analytical '
        'implementation of "aces-dev" and is designed as a reference to '
        'validate the implementation of the "ampas/aces-dev" "GitHub" "CTL" '
        "transforms in OpenColorIO. It is not a replacement for the previous "
        '"ACES" configs nor the "ACES Studio Config".'
    )
    timestamp = (
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
        f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.'
    )

    return "\n".join([name, underline, "", description, "", timestamp])


def generate_config_aces(
    config_name=None,
    validate=True,
    describe=ColorspaceDescriptionStyle.SHORT_UNION,
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
    analytical=True,
    scheme="Modern 1",
    additional_data=False,
):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    using the *Mapping* method.

    The config generation is constrained by a *CSV* file exported from the
    *Reference Config - Mapping* sheet from a
    `Google Sheets file <https://docs.google.com/spreadsheets/d/\
    1SXPt-USy3HlV2G2qAvh9zit6ZCINDOlfKT07yXJdWLg>`__. The *Google Sheets* file
    was originally authored using the output of the *aces-dev* conversion graph
    to support the discussions of the *OpenColorIO* *Working Group* on the
    design of the  *aces-dev* reference implementation *OpenColorIO* config.
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
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config and
        :class:`opencolorio_config_aces.ConfigData` class instance.
    """

    logger.info(
        f'Generating "{config_name_aces(config_mapping_file_path)}" config...'
    )

    ctl_transforms = unclassify_ctl_transforms(
        classify_aces_ctl_transforms(discover_aces_ctl_transforms())
    )

    logger.debug(f'Using {ctl_transforms} "CTL" transforms...')

    builtin_transforms = [
        builtin for builtin in ocio.BuiltinTransformRegistry()
    ]

    logger.debug(f'Using {builtin_transforms} "Builtin" transforms...')

    logger.info(f'Parsing "{config_mapping_file_path}" config mapping file...')

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=",",
            fieldnames=[
                "ordering",
                "aces_transform_id",
                "builtin_transform_style",
                "linked_display_colorspace_style",
                "interface",
                "encoding",
                "categories",
            ],
        )

        # Skipping the first header line.
        next(dict_reader)

        for transform_data in dict_reader:
            # Checking whether the "BuiltinTransform" style exists.
            style = transform_data["builtin_transform_style"]
            if style:
                assert (
                    style in builtin_transforms
                ), f'"{style}" "BuiltinTransform" style does not exist!'

            # Checking whether the linked "DisplayColorspace"
            # "BuiltinTransform" style exists.
            style = transform_data["linked_display_colorspace_style"]
            if style:
                assert (
                    style in builtin_transforms
                ), f'"{style}" "BuiltinTransform" style does not exist!"'

            # Finding the "CTLTransform" class instance that matches given
            # "ACEStransformID", if it does not exist, there is a critical
            # mismatch in the mapping with *aces-dev*.
            aces_transform_id = transform_data["aces_transform_id"]
            filtered_ctl_transforms = [
                ctl_transform
                for ctl_transform in ctl_transforms
                if ctl_transform.aces_transform_id.aces_transform_id
                == aces_transform_id
            ]

            ctl_transform = next(iter(filtered_ctl_transforms), None)

            assert ctl_transform is not None, (
                f'"aces-dev" has no transform with "{aces_transform_id}" '
                f"ACEStransformID, please cross-check the "
                f'"{config_mapping_file_path}" config mapping file and '
                f'the "aces-dev" "CTL" transforms!'
            )

            transform_data["ctl_transform"] = ctl_transform

            config_mapping[transform_data["builtin_transform_style"]].append(
                transform_data
            )

    colorspaces = []
    looks = []
    displays, display_names = [], []
    view_transforms, view_transform_names = [], []
    shared_views, views = [], []

    aces_family_prefix = "CSC" if analytical else "ACES"
    scene_reference_colorspace = {
        "name": format_optional_prefix(
            COLORSPACE_SCENE_ENCODING_REFERENCE, aces_family_prefix, scheme
        ),
        "family": "ACES",
        "description": 'The "Academy Color Encoding System" reference colorspace.',
        "encoding": "scene-linear",
    }

    display_reference_colorspace = {
        "name": "CIE-XYZ-D65",
        "description": 'The "CIE XYZ (D65)" display connection colorspace.',
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }

    raw_colorspace = {
        "name": format_optional_prefix("Raw", "Utility", scheme),
        "family": "Utility",
        "description": 'The utility "Raw" colorspace.',
        "is_data": True,
        "categories": ["file-io"],
    }

    colorspaces += [
        scene_reference_colorspace,
        display_reference_colorspace,
        raw_colorspace,
    ]

    logger.info(
        f'Implicit colorspaces: "{list(a["name"] for a in colorspaces)}"'
    )

    for style, transforms_data in config_mapping.items():
        if transforms_data[0]["interface"] == "ViewTransform":
            logger.info(f'Creating a "View" transform for "{style}" style...')
            view_transform = style_to_view_transform(
                style,
                [
                    transform_data["ctl_transform"]
                    for transform_data in transforms_data
                ],
                describe,
                signature_only=True,
                scheme=scheme,
            )
            view_transform["transforms_data"] = transforms_data
            view_transforms.append(view_transform)
            view_transform_name = view_transform["name"]
            view_transform_names.append(view_transform_name)

            for transform_data in transforms_data:
                display_style = transform_data[
                    "linked_display_colorspace_style"
                ]

                display = style_to_display_colorspace(
                    display_style,
                    signature_only=True,
                    scheme=scheme,
                    encoding=transform_data.get("encoding"),
                    categories=transform_data.get("categories"),
                )
                display["transforms_data"] = [transform_data]
                display_name = display["name"]

                if display_name not in display_names:
                    displays.append(display)
                    display_names.append(display_name)

                shared_view = {
                    "display": display_name,
                    "view": view_transform_name,
                    "view_transform": view_transform_name,
                }
                logger.info(
                    f'Adding {shared_view["view"]} shared view to '
                    f'"{display_name}" display.'
                )
                shared_views.append(shared_view)
        else:
            for transform_data in transforms_data:
                ctl_transform = transform_data["ctl_transform"]

                if transform_data["interface"] == "Look":
                    logger.info(
                        f'Creating a "Look" transform for "{style}" style...'
                    )
                    look = ctl_transform_to_look(
                        ctl_transform,
                        describe,
                        analytical=analytical,
                        signature_only=True,
                        scheme=scheme,
                        forward_transform={
                            "transform_type": "BuiltinTransform",
                            "style": style,
                        },
                        process_space=scene_reference_colorspace["name"],
                    )
                    look["transforms_data"] = [transform_data]
                    looks.append(look)
                else:
                    logger.info(
                        f'Creating a "Colorspace" transform for "{style}" style...'
                    )

                    colorspace = ctl_transform_to_colorspace(
                        ctl_transform,
                        describe,
                        analytical=analytical,
                        signature_only=True,
                        scheme=scheme,
                        to_reference={
                            "transform_type": "BuiltinTransform",
                            "style": style,
                        },
                        encoding=transform_data.get("encoding"),
                        categories=transform_data.get("categories"),
                    )
                    colorspace["transforms_data"] = [transform_data]
                    colorspaces.append(colorspace)

    untonemapped_view_transform = {
        "name": "Un-tone-mapped",
        "from_reference": {
            "transform_type": "BuiltinTransform",
            "style": "UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD",
        },
    }
    for display_name in display_names:
        untonemapped_shared_view = {
            "display": display_name,
            "view": untonemapped_view_transform["name"],
            "view_transform": untonemapped_view_transform["name"],
        }
        logger.info(
            f'Adding "{untonemapped_shared_view["view"]}" shared view to '
            f'"{display_name}" display.'
        )
        shared_views.append(untonemapped_shared_view)

    for display_name in display_names:
        raw_view = {
            "display": display_name,
            "view": "Raw",
            "colorspace": raw_colorspace["name"],
        }
        logger.info(
            f'Adding "{raw_view["view"]}" view to "{display_name}" display.'
        )
        views.append(raw_view)

    data = ConfigData(
        name=re.sub(
            r"\.ocio$", "", config_basename_aces(config_mapping_file_path)
        ),
        description=config_description_aces(config_mapping_file_path),
        roles={
            ocio.ROLE_COLOR_TIMING: format_optional_prefix(
                "ACEScct", aces_family_prefix, scheme
            ),
            ocio.ROLE_COMPOSITING_LOG: format_optional_prefix(
                "ACEScct", aces_family_prefix, scheme
            ),
            ocio.ROLE_DATA: raw_colorspace["name"],
            ocio.ROLE_DEFAULT: scene_reference_colorspace["name"],
            ocio.ROLE_INTERCHANGE_DISPLAY: display_reference_colorspace[
                "name"
            ],
            ocio.ROLE_INTERCHANGE_SCENE: scene_reference_colorspace["name"],
            ocio.ROLE_REFERENCE: scene_reference_colorspace["name"],
            ocio.ROLE_RENDERING: format_optional_prefix(
                "ACEScg", aces_family_prefix, scheme
            ),
            ocio.ROLE_SCENE_LINEAR: format_optional_prefix(
                "ACEScg", aces_family_prefix, scheme
            ),
        },
        colorspaces=colorspaces + displays,
        looks=looks,
        view_transforms=view_transforms + [untonemapped_view_transform],
        shared_views=shared_views,
        views=shared_views + views,
        active_displays=display_names,
        active_views=view_transform_names + ["Raw"],
        file_rules=[
            {
                "name": "Default",
                "colorspace": scene_reference_colorspace["name"],
            }
        ],
        inactive_colorspaces=["CIE-XYZ-D65"],
        default_view_transform=untonemapped_view_transform["name"],
        profile_version=VersionData(2, 1),
    )

    config = generate_config(data, config_name, validate)

    logger.info(
        f'"{config_name_aces(config_mapping_file_path)}" config generation complete!'
    )

    if additional_data:
        return config, data
    else:
        return config


if __name__ == "__main__":
    import os
    import opencolorio_config_aces
    from opencolorio_config_aces import serialize_config_data

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(
        opencolorio_config_aces.__path__[0],
        "..",
        "build",
        "config",
        "aces",
        "reference",
    )

    logger.info(f'Using "{build_directory}" build directory...')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    config_basename = config_basename_aces()
    config, data = generate_config_aces(
        config_name=os.path.join(build_directory, config_basename),
        analytical=False,
        additional_data=True,
    )

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(
            data,
            os.path.join(
                build_directory, config_basename.replace("ocio", "json")
            ),
        )
    except TypeError as error:
        logger.critical(error)
