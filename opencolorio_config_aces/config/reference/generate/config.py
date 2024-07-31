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
from enum import Flag, auto
from pathlib import Path

import PyOpenColorIO as ocio

from opencolorio_config_aces.config.generation import (
    BUILTIN_TRANSFORMS,
    DEPENDENCY_VERSIONS,
    SEPARATOR_COLORSPACE_FAMILY,
    SEPARATOR_COLORSPACE_NAME,
    ConfigData,
    DependencyVersions,
    beautify_alias,
    beautify_colorspace_name,
    beautify_display_name,
    beautify_look_name,
    beautify_transform_family,
    beautify_view_transform_name,
    colorspace_factory,
    generate_config,
    look_factory,
    produce_transform,
    view_transform_factory,
)
from opencolorio_config_aces.config.reference import (
    classify_aces_ctl_transforms,
    discover_aces_ctl_transforms,
    filter_ctl_transforms,
    generate_amf_components,
    unclassify_ctl_transforms,
)
from opencolorio_config_aces.utilities import (
    attest,
    timestamp,
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
    "TEMPLATE_ACES_TRANSFORM_ID",
    "HEADER_AMF_COMPONENTS",
    "DescriptionStyle",
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
    "transform_data_aliases",
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

TEMPLATE_ACES_TRANSFORM_ID = "ACEStransformID: {}"
"""
Template for the description of an *ACEStransformID*.

TEMPLATE_ACES_TRANSFORM_ID : unicode
"""

HEADER_AMF_COMPONENTS = "AMF Components\n--------------"
"""
Header for the description of the *ACES* *AMF* components.

HEADER_AMF_COMPONENTS : unicode
"""


class DescriptionStyle(Flag):
    """
    Enum storing the various *OpenColorIO* description styles.
    """

    NONE = auto()
    ACES = auto()
    OPENCOLORIO = auto()
    SHORT = auto()
    LONG = auto()
    AMF = auto()
    SHORT_UNION = ACES | OPENCOLORIO | SHORT | AMF
    LONG_UNION = ACES | OPENCOLORIO | LONG | AMF


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

    return f"{prefix}{SEPARATOR_COLORSPACE_NAME}{name}" if scheme == "legacy" else name


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
        f"{affix}{SEPARATOR_COLORSPACE_NAME}{name}"
        if scheme == "legacy"
        else f"{name}{SEPARATOR_COLORSPACE_NAME}{affix}"
    )


def ctl_transform_to_colorspace_name(ctl_transform):
    """
    Generate the *OpenColorIO* `Colorspace` name for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* `Colorspace` name
        for.

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` name.
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
    Generate the *OpenColorIO* `Look` name for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* `Look` name for.

    Returns
    -------
    unicode
        *OpenColorIO* `Look` name.
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
        analytically matches the given *ACES* *CTL* transform, i.e., true to
        the *aces-dev* reference but not necessarily user-friendly.

    Returns
    -------
    unicode
        *OpenColorIO* transform family.
    """

    if analytical:
        if ctl_transform.family == "csc" and ctl_transform.namespace == "Academy":
            family = "CSC"
        elif ctl_transform.family == "input_transform":
            family = f"Input{SEPARATOR_COLORSPACE_FAMILY}{ctl_transform.genus}"
        elif ctl_transform.family == "output_transform":
            family = "Output"
        elif ctl_transform.family == "lmt":
            family = "LMT"
    else:  # noqa: PLR5501
        if ctl_transform.family == "csc" and ctl_transform.namespace == "Academy":
            if re.match("ACES|ADX", ctl_transform.name):
                family = "ACES"
            else:
                family = f"Input{SEPARATOR_COLORSPACE_FAMILY}{ctl_transform.genus}"
        elif ctl_transform.family == "input_transform":
            family = f"Input{SEPARATOR_COLORSPACE_FAMILY}{ctl_transform.genus}"
        elif ctl_transform.family == "output_transform":
            family = "Output"
        elif ctl_transform.family == "lmt":
            family = "LMT"

    return beautify_transform_family(family)


def ctl_transform_to_description(
    ctl_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    factory=colorspace_factory,
    **kwargs,
):
    """
    Generate the *OpenColorIO* `Colorspace` or `Look` description for given
    *ACES* *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* `Colorspace` for.
    describe : bool, optional
        *ACES* *CTL* transform description style. Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    factory : callable, optional
        Factory used to adjust the code paths because of slight difference
        of signature between the *OpenColorIO* `Colorspace` and `Look`.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` or `Look` description.
    """

    if amf_components is None:
        amf_components = {}

    description = None
    if describe != DescriptionStyle.NONE:
        description = []

        if describe in (
            DescriptionStyle.OPENCOLORIO,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
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
            DescriptionStyle.ACES,
            DescriptionStyle.ACES | DescriptionStyle.SHORT,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
        ):
            if len(description) > 0:
                description.append("")

            aces_transform_id = ctl_transform.aces_transform_id.aces_transform_id

            if describe in (
                DescriptionStyle.ACES,
                DescriptionStyle.ACES | DescriptionStyle.SHORT,
                DescriptionStyle.SHORT_UNION,
            ):
                description.append(TEMPLATE_ACES_TRANSFORM_ID.format(aces_transform_id))
            else:
                description.append("CTL Transform")
                description.append(f'{"=" * len(description[-1])}\n')
                description.append(f"{ctl_transform.description}\n")
                description.append(TEMPLATE_ACES_TRANSFORM_ID.format(aces_transform_id))

            if describe in (
                DescriptionStyle.AMF,
                DescriptionStyle.SHORT_UNION,
                DescriptionStyle.LONG_UNION,
            ):
                amf_components_description = [
                    TEMPLATE_ACES_TRANSFORM_ID.format(amf_aces_transform_id)
                    for amf_aces_transform_id in amf_components.get(
                        aces_transform_id, []
                    )
                ]
                if amf_components_description:
                    description.append("")
                    description.append(HEADER_AMF_COMPONENTS)
                    description.extend(amf_components_description)

        description = "\n".join(description)

    return description


def ctl_transform_to_colorspace(
    ctl_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    analytical=True,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Generate the *OpenColorIO* `Colorspace` or its signature for given *ACES*
    *CTL* transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* `Colorspace` for.
    describe : bool, optional
        *ACES* *CTL* transform description style. Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    amf_components : mapping, optional
       *ACES* *AMF* components used to extend the *OpenColorIO* `Colorspace`
        description.
    analytical : bool, optional
        Whether to generate the *OpenColorIO* transform family that
        analytically matches the given *ACES* *CTL* transform, i.e., true to
        the *aces-dev* reference but not necessarily user-friendly.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `Colorspace` signature only, i.e.,
        the arguments for its instantiation.
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
    ocio.ColorSpace or dict
        *OpenColorIO* `Colorspace` or its signature.
    """

    name = ctl_transform_to_colorspace_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)
    description = ctl_transform_to_description(
        ctl_transform, describe, amf_components, colorspace_factory, **kwargs
    )

    signature = {
        "name": format_optional_prefix(name, beautify_colorspace_name(family), scheme),
        "family": family,
        "description": description,
    }
    signature.update(kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def ctl_transform_to_look(
    ctl_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    analytical=True,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Generate the *OpenColorIO* `Look` or its signature for given *ACES* *CTL*
    transform.

    Parameters
    ----------
    ctl_transform : CTLTransform
        *ACES* *CTL* transform to generate the *OpenColorIO* `Look` for.
    describe : bool, optional
        *ACES* *CTL* transform description style. Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *OpenColorIO* `Look`
        description.
    analytical : bool, optional
        Whether to generate the *OpenColorIO* transform family that
        analytically matches the given *ACES* *CTL* transform, i.e., true to
        the *aces-dev* reference but not necessarily user-friendly.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `Look` signature only, i.e., the
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
    ocio.ColorSpace or dict
        *OpenColorIO* `Look` or its signature.
    """

    name = ctl_transform_to_look_name(ctl_transform)
    family = ctl_transform_to_transform_family(ctl_transform, analytical)
    description = ctl_transform_to_description(
        ctl_transform, describe, amf_components, look_factory, **kwargs
    )

    signature = {
        "name": format_optional_prefix(name, beautify_colorspace_name(family), scheme),
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
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Create an *OpenColorIO* `ViewTransform` or its signature for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style
    ctl_transforms : array_like
        Array of :class:`opencolorio_config_aces.config.reference.CTLTransform`
        class instances corresponding to the given style.
    describe : int, optional
        Any value from the :class:`opencolorio_config_aces.DescriptionStyle`
        enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *OpenColorIO* `ViewTransform`
        description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `ViewTransform` signature only,
        i.e., the arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.view_transform_factory` definition.

    Returns
    -------
    ocio.ViewTransform or dict
        *OpenColorIO* `ViewTransform` or its signature for given style.
    """

    name = beautify_view_transform_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != DescriptionStyle.NONE:
        description = []

        if describe in (
            DescriptionStyle.OPENCOLORIO,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
        ):
            description.append(builtin_transform.getDescription())

        if describe in (
            DescriptionStyle.ACES,
            DescriptionStyle.ACES | DescriptionStyle.SHORT,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
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
                DescriptionStyle.ACES | DescriptionStyle.SHORT,
                DescriptionStyle.SHORT_UNION,
            ):
                description.extend(
                    [
                        f"ACEStransformID: {aces_transform_id}"
                        for aces_transform_id in aces_transform_ids
                    ]
                )
            else:
                description.append(
                    f'CTL Transform{"s" if len(aces_transform_ids) >= 2 else ""}'
                )
                description.append(f'{"=" * len(description[-1])}\n')

                description.append(
                    f'\n{"-" * 80}\n\n'.join(
                        [
                            (
                                f"{aces_descriptions[i]}\n\n"
                                f"ACEStransformID: {aces_transform_id}\n"
                            )
                            for i, aces_transform_id in enumerate(aces_transform_ids)
                        ]
                    )
                )

            if describe in (
                DescriptionStyle.AMF,
                DescriptionStyle.SHORT_UNION,
                DescriptionStyle.LONG_UNION,
            ):
                amf_components_description = []
                for aces_transform_id in aces_transform_ids:
                    amf_components_description.extend(
                        [
                            TEMPLATE_ACES_TRANSFORM_ID.format(amf_aces_transform_id)
                            for amf_aces_transform_id in amf_components.get(
                                aces_transform_id, []
                            )
                        ]
                    )
                if amf_components_description:
                    description.append("")
                    description.append(HEADER_AMF_COMPONENTS)
                    description.extend(amf_components_description)

        description = "\n".join(description)

    version = style.split(SEPARATOR_COLORSPACE_NAME)[-1].split("_")[-1]
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
    describe=DescriptionStyle.OPENCOLORIO,
    amf_components=None,
    signature_only=False,
    scheme="Modern 1",
    **kwargs,
):
    """
    Create an *OpenColorIO* display `Colorspace` or its signature for given
    style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style
    describe : int, optional
        Any value from the :class:`opencolorio_config_aces.DescriptionStyle`
        enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *OpenColorIO* display
        `Colorspace` description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* display `Colorspace` signature only,
        i.e., the arguments for its instantiation.
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
    ocio.ColorSpace or dict
        *OpenColorIO* display `Colorspace` or its signature for given style.
    """

    kwargs.setdefault("family", FAMILY_DISPLAY_REFERENCE)

    name = beautify_display_name(style)
    builtin_transform = ocio.BuiltinTransform(style)

    description = None
    if describe != DescriptionStyle.NONE:
        description = []

        if describe in (
            DescriptionStyle.OPENCOLORIO,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
        ):
            description.append(builtin_transform.getDescription())

        if len(description) > 0:
            description.append("")

        if describe in (
            DescriptionStyle.AMF,
            DescriptionStyle.SHORT_UNION,
            DescriptionStyle.LONG_UNION,
        ):
            amf_components_description = [
                TEMPLATE_ACES_TRANSFORM_ID.format(amf_aces_transform_id)
                for amf_aces_transform_id in amf_components.get(style, [])
            ]
            if amf_components_description:
                description.append(HEADER_AMF_COMPONENTS)
                description.extend(amf_components_description)

        description = "\n".join(description)

    signature = {
        "name": format_swapped_affix(name, "Display", scheme),
        "family": FAMILY_DISPLAY_REFERENCE,
        "description": description,
        "from_reference": builtin_transform,
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }
    signature.update(kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        signature["from_reference"] = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }

        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def transform_data_aliases(transform_data):
    """
    Return the aliases from given transform data.

    Parameters
    ----------
    transform_data : dict
        Transform data containing the aliases.

    Returns
    -------
    list
        Aliases.
    """

    aliases = re.split("[,;]+", transform_data.get("aliases", ""))

    if not aliases:
        aliases = []

    if transform_data["legacy"] == "TRUE":
        return [transform_data["colorspace"], *aliases]
    else:
        return aliases


def config_basename_aces(dependency_versions):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    basename, i.e., the filename devoid of directory affixe.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_aces()  # doctest: +SKIP
    'reference-config-v2.0.0_aces-v1.3_ocio-v2.0.ocio'
    """

    return ("reference-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions.to_regularised_versions()
    )


def config_name_aces(dependency_versions):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config name.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_aces(DependencyVersions())
    'Academy Color Encoding System - Reference Config [COLORSPACES v0.0.0] \
[ACES v0.0] [OCIO v2.0]'
    """

    return (
        "Academy Color Encoding System - Reference Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions.to_regularised_versions())


def config_description_aces(dependency_versions, describe=DescriptionStyle.SHORT_UNION):
    """
    Generate the *aces-dev* reference implementation *OpenColorIO* config
    description.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.

    Returns
    -------
    str
        *aces-dev* reference implementation *OpenColorIO* config description.
    """

    name = config_name_aces(dependency_versions)

    underline = "-" * len(name)

    summary = (
        'This "OpenColorIO" config is a strict and quasi-analytical '
        'implementation of "aces-dev" and is designed as a reference to '
        'validate the implementation of the "ampas/aces-dev" "GitHub" "CTL" '
        "transforms in OpenColorIO. It is not a replacement for the previous "
        '"ACES" configs nor the "ACES Studio Config".'
    )

    description = [name, underline, "", summary]

    if describe in ((DescriptionStyle.LONG_UNION,)):
        description.extend(["", timestamp()])

    return "\n".join(description)


def generate_config_aces(
    config_name=None,
    dependency_versions=DependencyVersions(),
    validate=True,
    describe=DescriptionStyle.SHORT_UNION,
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
    dependency_versions: DependencyVersions, optional
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.
    validate : bool, optional
        Whether to validate the config.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    config_mapping_file_path : unicode, optional
        Path to the *CSV* mapping file used by the *Mapping* method.
    analytical : bool, optional
        Whether to generate *OpenColorIO* transform families that analytically
        match the given *ACES* *CTL* transform, i.e., true to the *aces-dev*
        reference but not necessarily user-friendly.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config,
        :class:`opencolorio_config_aces.ConfigData` class instance, *ACES*
        *CTL* transforms and *ACES* *AMF* components.
    """

    logger.info(
        'Generating "%s" config...',
        config_name_aces(dependency_versions),
    )

    logger.debug('Using %s "Builtin" transforms...', list(BUILTIN_TRANSFORMS.keys()))

    ctl_transforms = unclassify_ctl_transforms(
        classify_aces_ctl_transforms(discover_aces_ctl_transforms())
    )
    amf_components = generate_amf_components(ctl_transforms)

    logger.debug('Using %s "CTL" transforms...', ctl_transforms)

    logger.info('Parsing "%s" config mapping file...', config_mapping_file_path)

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=",",
            fieldnames=[
                "ordering",
                "aces_transform_id",
                "colorspace",
                "legacy",
                "builtin_transform_style",
                "linked_display_colorspace_style",
                "interface",
                "encoding",
                "categories",
                "aliases",
            ],
        )

        # Skipping the first header line.
        next(dict_reader)

        for transform_data in dict_reader:
            # Checking whether the "BuiltinTransform" style exists.
            style = transform_data["builtin_transform_style"]
            if style:
                attest(
                    style in BUILTIN_TRANSFORMS,
                    f'"{style}" "BuiltinTransform" style does not exist!',
                )

                if BUILTIN_TRANSFORMS[style] > dependency_versions.ocio:
                    logger.warning(
                        '"%s" style is unavailable for "%s" profile version, '
                        "skipping transform!",
                        style,
                        dependency_versions.ocio,
                    )
                    continue

            # Checking whether the linked "DisplayColorspace"
            # "BuiltinTransform" style exists.
            style = transform_data["linked_display_colorspace_style"]
            if style:
                attest(
                    style in BUILTIN_TRANSFORMS,
                    f'"{style}" "BuiltinTransform" style does not exist!"',
                )

                if BUILTIN_TRANSFORMS[style] > dependency_versions.ocio:
                    logger.warning(
                        '"%s" style is unavailable for "%s" profile version, '
                        "skipping transform!",
                        style,
                        dependency_versions.ocio,
                    )
                    continue

            # Finding the "CTLTransform" class instance that matches given
            # "ACEStransformID", if it does not exist, there is a critical
            # mismatch in the mapping with *aces-dev*.
            aces_transform_id = transform_data["aces_transform_id"]
            filtered_ctl_transforms = filter_ctl_transforms(
                ctl_transforms,
                [
                    lambda x, y=aces_transform_id: (
                        x.aces_transform_id.aces_transform_id == y
                    )
                ],
            )

            ctl_transform = next(iter(filtered_ctl_transforms), None)

            attest(
                ctl_transform is not None,
                (
                    f'"aces-dev" has no transform with "{aces_transform_id}" '
                    f"ACEStransformID, please cross-check the "
                    f'"{config_mapping_file_path}" config mapping file and '
                    f'the "aces-dev" "CTL" transforms!'
                ),
            )

            transform_data["ctl_transform"] = ctl_transform

            # Extending the "AMF" relations.
            if not amf_components.get(style):
                amf_components[style] = []

            amf_components[style].extend(
                [ctl_transform.aces_transform_id.aces_transform_id]
                + [
                    sibling.aces_transform_id.aces_transform_id
                    for sibling in ctl_transform.siblings
                ]
            )

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
        "categories": ["file-io"],
    }
    scene_reference_colorspace["aliases"] = [
        beautify_alias(scene_reference_colorspace["name"]),
        "ACES - ACES2065-1",
        "lin_ap0",
    ]

    display_reference_colorspace = {
        "name": "CIE-XYZ-D65",
        "description": 'The "CIE XYZ (D65)" display connection colorspace.',
        "reference_space": "REFERENCE_SPACE_DISPLAY",
    }
    display_reference_colorspace["aliases"] = [
        beautify_alias(display_reference_colorspace["name"])
    ]

    raw_colorspace = {
        "name": format_optional_prefix("Raw", "Utility", scheme),
        "family": "Utility",
        "description": 'The utility "Raw" colorspace.',
        "is_data": True,
        "categories": ["file-io", "texture"],
    }
    raw_colorspace["aliases"] = [
        beautify_alias(raw_colorspace["name"]),
        "Utility - Raw",
    ]

    colorspaces += [
        scene_reference_colorspace,
        display_reference_colorspace,
        raw_colorspace,
    ]

    logger.info('Implicit colorspaces: "%s"', [a["name"] for a in colorspaces])

    for style, transforms_data in config_mapping.items():
        if transforms_data[0]["interface"] == "ViewTransform":
            logger.info('Creating a "View" transform for "%s" style...', style)
            view_transform = style_to_view_transform(
                style,
                [transform_data["ctl_transform"] for transform_data in transforms_data],
                describe,
                amf_components,
                signature_only=True,
                scheme=scheme,
            )
            view_transform["transforms_data"] = transforms_data
            view_transforms.append(view_transform)
            view_transform_name = view_transform["name"]
            view_transform_names.append(view_transform_name)

            for transform_data in transforms_data:
                display_style = transform_data["linked_display_colorspace_style"]

                display = style_to_display_colorspace(
                    display_style,
                    describe,
                    amf_components,
                    signature_only=True,
                    scheme=scheme,
                    encoding=transform_data.get("encoding"),
                    categories=transform_data.get("categories"),
                    aliases=transform_data_aliases(transform_data),
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
                    'Adding "%s" shared view to "%s" display.',
                    shared_view["view"],
                    display_name,
                )
                shared_views.append(shared_view)
        else:
            for transform_data in transforms_data:
                ctl_transform = transform_data["ctl_transform"]

                if transform_data["interface"] == "Look":
                    logger.info('Creating a "Look" transform for "%s" style...', style)
                    look = ctl_transform_to_look(
                        ctl_transform,
                        describe,
                        amf_components,
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
                        'Creating a "Colorspace" transform for "%s" style...',
                        style,
                    )

                    colorspace = ctl_transform_to_colorspace(
                        ctl_transform,
                        describe,
                        amf_components,
                        analytical=analytical,
                        signature_only=True,
                        scheme=scheme,
                        to_reference={
                            "transform_type": "BuiltinTransform",
                            "style": style,
                        },
                        encoding=transform_data.get("encoding"),
                        categories=transform_data.get("categories"),
                        aliases=transform_data_aliases(transform_data),
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
            'Adding "%s" shared view to "%s" display.',
            untonemapped_shared_view["view"],
            display_name,
        )
        shared_views.append(untonemapped_shared_view)

    for display_name in display_names:
        raw_view = {
            "display": display_name,
            "view": "Raw",
            "colorspace": raw_colorspace["name"],
        }
        logger.info('Adding "%s" view to "%s" display.', raw_view["view"], display_name)
        views.append(raw_view)

    data = ConfigData(
        name=re.sub(
            r"\.ocio$",
            "",
            config_basename_aces(dependency_versions),
        ),
        description=config_description_aces(dependency_versions, describe),
        roles={
            ocio.ROLE_COLOR_TIMING: format_optional_prefix(
                "ACEScct", aces_family_prefix, scheme
            ),
            ocio.ROLE_COMPOSITING_LOG: format_optional_prefix(
                "ACEScct", aces_family_prefix, scheme
            ),
            ocio.ROLE_DATA: raw_colorspace["name"],
            ocio.ROLE_INTERCHANGE_DISPLAY: display_reference_colorspace["name"],
            ocio.ROLE_INTERCHANGE_SCENE: scene_reference_colorspace["name"],
            ocio.ROLE_RENDERING: format_optional_prefix(
                "ACEScg", aces_family_prefix, scheme
            ),
            ocio.ROLE_SCENE_LINEAR: format_optional_prefix(
                "ACEScg", aces_family_prefix, scheme
            ),
        },
        colorspaces=colorspaces + displays,
        looks=looks,
        view_transforms=[*view_transforms, untonemapped_view_transform],
        shared_views=shared_views,
        views=shared_views + views,
        active_displays=display_names,
        active_views=[*view_transform_names, "Un-tone-mapped", "Raw"],
        file_rules=[
            {
                "name": "Default",
                "colorspace": scene_reference_colorspace["name"],
            }
        ],
        default_view_transform=untonemapped_view_transform["name"],
        profile_version=dependency_versions.ocio,
    )

    config = generate_config(data, config_name, validate)

    logger.info(
        '"%s" config generation complete!',
        config_name_aces(dependency_versions),
    )

    if additional_data:
        return config, data, ctl_transforms, amf_components
    else:
        return config


if __name__ == "__main__":
    from opencolorio_config_aces import serialize_config_data
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (ROOT_BUILD_DEFAULT / "config" / "aces" / "reference").resolve()

    logger.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for dependency_versions in DEPENDENCY_VERSIONS:
        config_basename = config_basename_aces(dependency_versions)
        (
            config,
            data,
            ctl_transforms,
            amf_components,
        ) = generate_config_aces(
            config_name=build_directory / config_basename,
            dependency_versions=dependency_versions,
            analytical=False,
            additional_data=True,
        )

        # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
        # versions.
        try:
            serialize_config_data(
                data, build_directory / config_basename.replace("ocio", "json")
            )
        except TypeError as error:
            logger.critical(error)
