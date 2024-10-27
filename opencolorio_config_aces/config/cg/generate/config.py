# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ACES* Computer Graphics (CG) Config Generator
==============================================

Defines various objects related to the generation of the *ACES* Computer
Graphics (CG) *OpenColorIO* config:

-   :func:`opencolorio_config_aces.generate_config_cg`
"""

import csv
import logging
import re
from collections import defaultdict
from pathlib import Path

import PyOpenColorIO as ocio

from opencolorio_config_aces.clf import (
    classify_clf_transforms,
    discover_clf_transforms,
    unclassify_clf_transforms,
)
from opencolorio_config_aces.config.generation import (
    BUILTIN_TRANSFORMS,
    DEPENDENCY_VERSIONS,
    SEPARATOR_BUILTIN_TRANSFORM_NAME,
    SEPARATOR_COLORSPACE_FAMILY,
    SEPARATOR_COLORSPACE_NAME,
    DependencyVersions,
    beautify_alias,
    beautify_colorspace_name,
    colorspace_factory,
    generate_config,
    named_transform_factory,
)
from opencolorio_config_aces.config.reference import (
    DescriptionStyle,
    generate_config_aces,
)
from opencolorio_config_aces.config.reference.generate.config import (
    COLORSPACE_SCENE_ENCODING_REFERENCE,
    HEADER_AMF_COMPONENTS,
    TEMPLATE_ACES_TRANSFORM_ID,
    format_optional_prefix,
    transform_data_aliases,
)
from opencolorio_config_aces.utilities import (
    attest,
    optional,
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
    "URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG",
    "PATH_TRANSFORMS_MAPPING_FILE_CG",
    "FILTERED_NAMESPACES",
    "TEMPLATE_CLF_TRANSFORM_ID",
    "is_reference",
    "clf_transform_to_colorspace_name",
    "clf_transform_to_description",
    "clf_transform_to_family",
    "clf_transform_to_colorspace",
    "clf_transform_to_named_transform",
    "style_to_colorspace",
    "style_to_named_transform",
    "config_basename_cg",
    "config_name_cg",
    "config_description_cg",
    "generate_config_cg",
]

LOGGER = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG = (
    "https://docs.google.com/spreadsheets/d/"
    "1PXjTzBVYonVFIceGkLDaqcEJvKR6OI63DwZX0aajl3A/"
    "export?format=csv&gid=365242296"
)
"""
URL to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG : unicode
"""

PATH_TRANSFORMS_MAPPING_FILE_CG = next(
    (Path(__file__).parents[0] / "resources").glob("*Mapping.csv")
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

PATH_TRANSFORMS_MAPPING_FILE_CG : unicode
"""

FILTERED_NAMESPACES = ("OCIO",)
"""
Filtered namespaces.

FILTERED_NAMESPACES : tuple
"""

TEMPLATE_CLF_TRANSFORM_ID = "CLFtransformID: {}"
"""
Template for the description of an *CLFtransformID*.

TEMPLATE_CLF_TRANSFORM_ID : unicode
"""


def is_reference(name):
    """
    Return whether given name represent a reference linear-like space.

    Parameters
    ----------
    name : str
        Name.

    Returns
    -------
    str
        Whether given name represent a reference linear-like space.
    """

    return name.lower() in (
        COLORSPACE_SCENE_ENCODING_REFERENCE.lower(),
        "ap0",
        "linear",
    )


def clf_transform_to_colorspace_name(clf_transform):
    """
    Generate the *OpenColorIO* `Colorspace` name for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform to generate the *OpenColorIO* `Colorspace` name for.

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` name.
    """

    if is_reference(clf_transform.source):
        name = clf_transform.target
    else:
        name = clf_transform.source

    return beautify_colorspace_name(name)


def clf_transform_to_description(
    clf_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    direction="Forward",
):
    """
    Generate the *OpenColorIO* `Colorspace` or `NamedTransform` description for
    given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        Whether to use the full *CLF* transform description  or just the
        first line.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    direction : str, optional
        Direction of transform -- determines order of transform descriptors.
        {"Forward", "Reverse"}
        Default: "Forward" (i.e., assume 'Forward' direction)

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` or `NamedTransform` description.
    """

    amf_components = optional(amf_components, {})

    description = None
    if describe != DescriptionStyle.NONE:
        description = []

        if describe in (
            DescriptionStyle.OPENCOLORIO,
            DescriptionStyle.SHORT,
            DescriptionStyle.SHORT_UNION,
        ):
            if clf_transform.description is not None:
                if direction.lower() == "forward":
                    description.append(
                        f"Convert {clf_transform.input_descriptor} "
                        f"to {clf_transform.output_descriptor}"
                    )
                else:
                    description.append(
                        f"Convert {clf_transform.output_descriptor} "
                        f"to {clf_transform.input_descriptor}"
                    )
        elif describe in (  # noqa: SIM102
            DescriptionStyle.OPENCOLORIO,
            DescriptionStyle.LONG,
            DescriptionStyle.LONG_UNION,
        ):
            if clf_transform.description is not None:
                description.append("\n" + clf_transform.description)

        if len(description) > 0:
            description.append("")

        description.append(
            TEMPLATE_CLF_TRANSFORM_ID.format(
                clf_transform.clf_transform_id.clf_transform_id
            ),
        )

        aces_transform_id = clf_transform.information.get("ACEStransformID")
        if aces_transform_id:
            aces_transform_id = aces_transform_id.aces_transform_id
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

        description = "\n".join(description).strip()

    return description


def clf_transform_to_family(clf_transform, filtered_namespaces=FILTERED_NAMESPACES):
    """
    Generate the *OpenColorIO* `Colorspace` or `NamedTransform` family for
    given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    filtered_namespaces : tuple, optional
        Filtered namespaces.

    Returns
    -------
    str
        *OpenColorIO* `Colorspace` or `NamedTransform` family.
    """

    family = (
        clf_transform.clf_transform_id.type
        if clf_transform.clf_transform_id.namespace in filtered_namespaces
        else (
            f"{clf_transform.clf_transform_id.type}"
            f"{SEPARATOR_COLORSPACE_FAMILY}"
            f"{clf_transform.clf_transform_id.namespace}"
        )
    )

    return family


def clf_transform_to_colorspace(
    clf_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    signature_only=False,
    **kwargs,
):
    """
    Generate the *OpenColorIO* `Colorspace` for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        *CLF* transform description style.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `Colorspace` signature only, i.e.,
        the arguments for its instantiation.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.colorspace_factory` definition.

    Returns
    -------
    Object
        *OpenColorIO* colorspace.
    """

    signature = {
        "name": clf_transform_to_colorspace_name(clf_transform),
        "family": clf_transform_to_family(clf_transform),
        "description": clf_transform_to_description(
            clf_transform, describe, amf_components, "Forward"
        ),
    }

    file_transform = {
        "transform_type": "FileTransform",
        "transform_factory": "CLF Transform to Group Transform",
        "src": clf_transform.path,
    }
    if is_reference(clf_transform.source):
        signature["from_reference"] = file_transform
    else:
        signature["to_reference"] = file_transform

    signature.update(kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def clf_transform_to_named_transform(
    clf_transform,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    signature_only=False,
    **kwargs,
):
    """
    Generate the *OpenColorIO* `NamedTransform` for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        *CLF* transform description style.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `NamedTransform` signature only,
        i.e., the arguments for its instantiation.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.named_transform_factory` definition.

    Returns
    -------
    Object
        *OpenColorIO* `NamedTransform`.
    """

    signature = {
        "name": clf_transform_to_colorspace_name(clf_transform),
        "family": clf_transform_to_family(clf_transform),
    }

    file_transform = {
        "transform_type": "FileTransform",
        "transform_factory": "CLF Transform to Group Transform",
        "src": clf_transform.path,
    }
    if is_reference(clf_transform.source):
        signature["inverse_transform"] = file_transform
        signature["description"] = clf_transform_to_description(
            clf_transform, describe, amf_components, direction="Reverse"
        )
    else:
        signature["forward_transform"] = file_transform
        signature["description"] = clf_transform_to_description(
            clf_transform, describe, amf_components, direction="Forward"
        )

    signature.update(kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        return signature
    else:
        named_transform = named_transform_factory(**signature)

        return named_transform


def style_to_colorspace(
    style,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    signature_only=False,
    scheme="Modern 1",  # noqa: ARG001
    **kwargs,
):
    """
    Create an *OpenColorIO* `Colorspace` or its signature for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* view `Colorspace` signature only,
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
    ocio.ViewTransform or dict
        *OpenColorIO* `Colorspace` or its signature for given style.
    """

    # TODO: Implement "BuiltinTransform" name beautification.
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

        description = "\n".join(description)

    signature = {}
    clf_transform = kwargs.pop("clf_transform", None)
    if clf_transform:
        colorspace_signature = clf_transform_to_colorspace(
            clf_transform, describe, amf_components, True, **kwargs
        )
        description = colorspace_signature["description"]
        signature.update(colorspace_signature)
        source = clf_transform.source
    else:
        # TODO: Implement solid "BuiltinTransform" source detection.
        source = (
            style.lower()
            .split(SEPARATOR_COLORSPACE_NAME, 1)[-1]
            .split(SEPARATOR_BUILTIN_TRANSFORM_NAME)[0]
        )

    if is_reference(source):
        signature.update(
            {
                "from_reference": builtin_transform,
                "description": description,
            }
        )
    else:
        signature.update(
            {
                "to_reference": builtin_transform,
                "description": description,
            }
        )
    signature.update(**kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        builtin_transform = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }
        if is_reference(source):
            signature["from_reference"] = builtin_transform
        else:
            signature["to_reference"] = builtin_transform

        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def style_to_named_transform(
    style,
    describe=DescriptionStyle.LONG_UNION,
    amf_components=None,
    signature_only=False,
    scheme="Modern 1",  # noqa: ARG001
    **kwargs,
):
    """
    Create an *OpenColorIO* `NamedTransform` or its signature for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
    amf_components : mapping, optional
        *ACES* *AMF* components used to extend the *ACES* *CTL* transform
        description.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* view `Colorspace` signature only,
        i.e., the arguments for its instantiation.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.named_transform_factory` definition.

    Returns
    -------
    ocio.ViewTransform or dict
        *OpenColorIO* `NamedTransform` or its signature for given style.
    """

    # TODO: Implement "BuiltinTransform" name beautification.
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

        description = "\n".join(description)

    signature = {}
    clf_transform = kwargs.pop("clf_transform", None)
    if clf_transform:
        colorspace_signature = clf_transform_to_colorspace(
            clf_transform, describe, amf_components, True, **kwargs
        )
        signature.update(colorspace_signature)
        signature.pop("from_reference", None)
        source = clf_transform.source
        description = clf_transform_to_description(
            clf_transform,
            describe,
            amf_components,
            "Reverse" if is_reference(source) else "Forward",
        )
    else:
        # TODO: Implement solid "BuiltinTransform" source detection.
        source = (
            style.lower()
            .split(SEPARATOR_COLORSPACE_NAME, 1)[-1]
            .split(SEPARATOR_BUILTIN_TRANSFORM_NAME)[0]
        )

    if is_reference(source):
        signature.update(
            {
                "inverse_transform": builtin_transform,
                "description": description,
            }
        )
    else:
        signature.update(
            {
                "forward_transform": builtin_transform,
                "description": description,
            }
        )
    signature.update(**kwargs)

    signature["aliases"] = list(
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])
    )

    if signature_only:
        builtin_transform = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }
        if is_reference(source):
            signature["inverse_transform"] = builtin_transform
        else:
            signature["forward_transform"] = builtin_transform

        return signature
    else:
        colorspace = named_transform_factory(**signature)

        return colorspace


def config_basename_cg(dependency_versions):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
    basename, i.e., the filename devoid of directory affix.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_cg(DependencyVersions())
    'cg-config-v0.0.0_aces-v0.0_ocio-v2.0.ocio'
    """

    return ("cg-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions.to_regularised_versions()
    )


def config_name_cg(dependency_versions):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_cg(DependencyVersions())
    'Academy Color Encoding System - CG Config [COLORSPACES v0.0.0] \
[ACES v0.0] [OCIO v2.0]'
    """

    return (
        "Academy Color Encoding System - CG Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions.to_regularised_versions())


def config_description_cg(
    dependency_versions,
    describe=DescriptionStyle.SHORT_UNION,
):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
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
        ACES* Computer Graphics (CG) *OpenColorIO* config description.
    """

    name = config_name_cg(dependency_versions)

    underline = "-" * len(name)

    summary = (
        'This minimalistic "OpenColorIO" config is geared toward computer '
        "graphics artists requiring a lean config that does not include "
        "camera colorspaces and the less common displays and looks."
    )

    description = [name, underline, "", summary]

    if describe in ((DescriptionStyle.LONG_UNION,)):
        description.extend(["", timestamp()])

    return "\n".join(description)


def generate_config_cg(
    data=None,
    config_name=None,
    dependency_versions=DependencyVersions(),
    validate=True,
    describe=DescriptionStyle.SHORT_UNION,
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
    scheme="Modern 1",
    additional_filterers=None,
    additional_data=False,
):
    """
    Generate the *ACES* Computer Graphics (CG) *OpenColorIO* config.

    The default process is as follows:

    -   The *ACES* CG *OpenColorIO* config generator invokes the *aces-dev*
        reference implementation *OpenColorIO* config generator via the
        :func:`opencolorio_config_aces.generate_config_aces` definition and the
        default reference config mapping file.
    -   The *ACES* CG *OpenColorIO* config generator filters and extends
        the data from the *aces-dev* reference implementation *OpenColorIO*
        config with the given CG config mapping file:

        -   The builtin *CLF* transforms are discovered and classified.
        -   The CG config mapping file is parsed.
        -   The list of implicit colorspaces is built, e.g., *ACES2065-1*,
            *Raw*, etc...
        -   The colorspaces, looks and view transforms are filtered according
            to the parsed CG config mapping file data.
        -   The displays, views, and shared views are filtered similarly.
        -   The active displays and views are also filtered.
        -   The builtin *CLF* transforms are filtered according to the parsed
            CG config mapping file data and converted to colorspaces (or named
            transforms).
        -   Finally, the roles and aliases are updated.

    Parameters
    ----------
    data : ConfigData, optional
        *OpenColorIO* config data to derive the config from, the default is to
        use the *aces-dev* reference implementation *OpenColorIO* config.
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
        Path to the *CSV* mapping file used to describe the transforms mapping.
    scheme : str, optional
        {"Legacy", "Modern 1"},
        Naming convention scheme to use.
    additional_filterers : dict, optional
        Additional filterers to further include or exclude transforms from the
        generated config.

        .. code-block:: python

            {
                "any": {},
                "all": {
                    "view_transform_filterers": [lambda x: "D60" not in x["name"]],
                    "view_filterers": [lambda x: "D60" not in x["view"]],
                },
            },

    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config and
        :class:`opencolorio_config_aces.ConfigData` class instance, *ACES*
        *CTL* transforms, *CLF* transforms and *ACES* *AMF* components.
    """

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    additional_filterers = optional(additional_filterers, {"any": {}, "all": {}})

    LOGGER.info(
        'Generating "%s" config...',
        config_name_cg(dependency_versions),
    )

    clf_transforms = unclassify_clf_transforms(
        classify_clf_transforms(discover_clf_transforms())
    )

    LOGGER.debug('Using %s "CLF" transforms...', clf_transforms)

    if data is None:
        _config, data, ctl_transforms, amf_components = generate_config_aces(
            dependency_versions=dependency_versions,
            describe=describe,
            scheme=scheme,
            analytical=False,
            additional_data=True,
        )

    def clf_transform_from_id(clf_transform_id):
        """
        Filter the "CLFTransform" instances matching given "CLFtransformID".
        """

        filtered_clf_transforms = [
            clf_transform
            for clf_transform in clf_transforms
            if clf_transform.clf_transform_id.clf_transform_id == clf_transform_id
        ]

        clf_transform = next(iter(filtered_clf_transforms), None)

        LOGGER.debug(
            'Filtered "CLF" transform with "%s" "CLFtransformID": %s.',
            clf_transform_id,
            clf_transform,
        )

        return clf_transform

    def clf_transform_from_style(style):
        """Filter the "CLFTransform" instances matching given style."""

        filtered_clf_transforms = [
            clf_transform
            for clf_transform in clf_transforms
            if clf_transform.information.get("BuiltinTransform") == style
        ]

        clf_transform = next(iter(filtered_clf_transforms), None)

        LOGGER.debug(
            'Filtered "CLF" transform with "%s" style: %s.',
            style,
            clf_transform,
        )

        return clf_transform

    LOGGER.info('Parsing "%s" config mapping file...', config_mapping_file_path)

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=",",
            fieldnames=[
                "ordering",
                "colorspace",
                "legacy",
                "aces_transform_id",
                "clf_transform_id",
                "interface",
                "builtin_transform_style",
                "aliases",
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
                attest(
                    style in BUILTIN_TRANSFORMS,
                    f'"{style}" "BuiltinTransform" style does not exist!',
                )

                if BUILTIN_TRANSFORMS[style] > dependency_versions.ocio:
                    LOGGER.warning(
                        '"%s" style is unavailable for "%s" profile version, '
                        "skipping transform!",
                        style,
                        dependency_versions.ocio,
                    )
                    continue

            # Finding the "CLFTransform" class instance that matches given
            # "CLFtransformID", if it does not exist, there is a critical
            # mismatch in the config mapping file.
            clf_transform_id = transform_data["clf_transform_id"]
            # NOTE: Contrary to the "aces-dev" "Reference" config, only a
            # subset of the transforms are represented with a "CLF" file.
            if clf_transform_id:
                filtered_clf_transforms = [
                    clf_transform
                    for clf_transform in clf_transforms
                    if clf_transform.clf_transform_id.clf_transform_id
                    == clf_transform_id
                ]

                clf_transform = next(iter(filtered_clf_transforms), None)

                attest(
                    clf_transform is not None,
                    f'"OpenColorIO-Config-ACES" has no transform with '
                    f'"{clf_transform_id}" ACEStransformID, please cross-check '
                    f'the "{config_mapping_file_path}" config mapping file!',
                )

                transform_data["clf_transform"] = clf_transform

            config_mapping[transform_data["colorspace"]].append(transform_data)

    def yield_from_config_mapping():
        """Yield the transform data stored in the *CSV* mapping file."""
        for transforms_data in config_mapping.values():
            yield from transforms_data

    data.name = re.sub(
        r"\.ocio$",
        "",
        config_basename_cg(dependency_versions),
    )
    data.description = config_description_cg(dependency_versions, describe)

    # Colorspaces, Looks and View Transforms Filtering
    transforms = data.colorspaces + data.view_transforms
    implicit_transforms = [
        a["name"] for a in transforms if a.get("transforms_data") is None
    ]

    LOGGER.info("Implicit transforms: %s.", implicit_transforms)

    def implicit_transform_filterer(transform):
        """Return whether given transform is an implicit transform."""

        return transform.get("name") in implicit_transforms

    def transform_filterer(transform):
        """Return whether given transform must be included."""

        for transform_data in yield_from_config_mapping():
            aces_transform_id = transform_data["aces_transform_id"]
            if not aces_transform_id:
                continue

            for data in transform.get("transforms_data", []):
                if aces_transform_id == data.get("aces_transform_id"):
                    return True

        return False

    def filter_any(array, filterers):
        """Filter array elements passing any of the filterers."""

        filtered = [a for a in array if any(filterer(a) for filterer in filterers)]

        return filtered

    def filter_all(array, filterers):
        """Filter array elements passing all of the filterers."""

        filtered = [a for a in array if all(filterer(a) for filterer in filterers)]

        return filtered

    # "Colorspaces" Filtering
    any_colorspace_filterers = [
        implicit_transform_filterer,
        transform_filterer,
        *additional_filterers["any"].get("colorspace_filterers", []),
    ]
    data.colorspaces = filter_any(data.colorspaces, any_colorspace_filterers)
    all_colorspace_filterers = [
        *additional_filterers["all"].get("colorspace_filterers", [])
    ]
    data.colorspaces = filter_all(data.colorspaces, all_colorspace_filterers)
    LOGGER.info(
        'Filtered "Colorspace" transforms: %s.',
        [a["name"] for a in data.colorspaces],
    )

    # "Looks" Filtering
    any_look_filterers = [
        implicit_transform_filterer,
        transform_filterer,
        *additional_filterers["any"].get("look_filterers", []),
    ]
    data.looks = filter_any(data.looks, any_look_filterers)
    all_look_filterers = [*additional_filterers["all"].get("look_filterers", [])]
    data.looks = filter_all(data.looks, all_look_filterers)
    LOGGER.info('Filtered "Look" transforms: %s ', [a["name"] for a in data.looks])

    # "View Transform" Filtering
    any_view_transform_filterers = [
        implicit_transform_filterer,
        transform_filterer,
        *additional_filterers["any"].get("view_transform_filterers", []),
    ]
    data.view_transforms = filter_any(
        data.view_transforms, any_view_transform_filterers
    )
    all_view_transform_filterers = [
        *additional_filterers["all"].get("view_transform_filterers", [])
    ]
    data.view_transforms = filter_all(
        data.view_transforms, all_view_transform_filterers
    )
    LOGGER.info(
        'Filtered "View" transforms: %s.',
        [a["name"] for a in data.view_transforms],
    )

    # "Views & Shared Views" Filtering
    display_names = [
        a["name"] for a in data.colorspaces if a.get("family") == "Display"
    ]

    def implicit_view_filterer(transform):
        """Return whether given transform is an implicit view."""

        return all(
            [
                transform.get("view") in implicit_transforms,
                transform.get("display") in display_names,
            ]
        )

    def view_filterer(transform):
        """Return whether given view transform must be included."""

        if transform["display"] not in display_names:
            return False

        for view_transform in data.view_transforms:
            if view_transform["name"] == transform["view"]:
                return True

        return False

    # "Shared Views" Filtering
    any_shared_view_filterers = [
        implicit_view_filterer,
        view_filterer,
        *additional_filterers["any"].get("shared_view_filterers", []),
    ]
    data.shared_views = filter_any(data.shared_views, any_shared_view_filterers)
    all_shared_view_filterers = [
        *additional_filterers["all"].get("shared_view_filterers", [])
    ]
    data.shared_views = filter_all(data.shared_views, all_shared_view_filterers)
    LOGGER.info(
        'Filtered shared "View(s)": %s.',
        [a["view"] for a in data.shared_views],
    )

    any_view_filterers = [
        implicit_view_filterer,
        view_filterer,
        *additional_filterers["any"].get("view_filterers", []),
    ]
    data.views = filter_any(data.views, any_view_filterers)
    all_view_filterers = [*additional_filterers["all"].get("view_filterers", [])]
    data.views = filter_all(data.views, all_view_filterers)
    LOGGER.info('Filtered "View(s)": %s.', [a["view"] for a in data.views])

    # "Active Displays" Filtering
    data.active_displays = [a for a in data.active_displays if a in display_names]
    LOGGER.info("Filtered active displays: %s.", data.active_displays)

    # "Active Views" Filtering
    views = [view["view"] for view in data.views]
    data.active_views = [view for view in data.active_views if view in views]
    LOGGER.info("Filtered active views: %s.", data.active_views)

    # CLF Transforms & BuiltinTransform Creation
    for transform_data in yield_from_config_mapping():
        # Inherited from the "Reference" config.
        if (
            transform_data["aces_transform_id"]
            and not transform_data["clf_transform_id"]
        ):
            continue

        kwargs = {
            "describe": describe,
            "amf_components": amf_components,
            "signature_only": True,
            "aliases": transform_data_aliases(transform_data),
            "encoding": transform_data.get("encoding"),
            "categories": transform_data.get("categories"),
        }

        style = transform_data["builtin_transform_style"]
        clf_transform_id = transform_data["clf_transform_id"]

        if style:
            kwargs.update(
                {
                    "style": style,
                    "clf_transform": clf_transform_from_style(style),
                }
            )

            if transform_data["interface"] == "ColorSpace":
                LOGGER.info(
                    'Creating a "Colorspace" transform for "%s" style...',
                    style,
                )

                colorspace = style_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.colorspaces.append(colorspace)
            elif transform_data["interface"] == "NamedTransform":
                LOGGER.info(
                    'Creating a "NamedTransform" transform for "%s" style...',
                    style,
                )

                colorspace = style_to_named_transform(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.named_transforms.append(colorspace)

            if style and clf_transform_id:
                LOGGER.warning(
                    '"%s" style was defined along side a "CTLtransformID", '
                    "hybrid transform generation was used!",
                    style,
                )
                continue

        if clf_transform_id:
            clf_transform = clf_transform_from_id(clf_transform_id)

            attest(
                clf_transform,
                f'"{clf_transform_id}" "CLF" transform does not exist!',
            )

            kwargs["clf_transform"] = clf_transform

            if transform_data["interface"] == "NamedTransform":
                LOGGER.info(
                    'Adding "%s" "CLF" transform as a "Named" transform.',
                    clf_transform_id,
                )

                named_transform = clf_transform_to_named_transform(**kwargs)
                named_transform["transforms_data"] = [transform_data]
                data.named_transforms.append(named_transform)
            else:
                LOGGER.info(
                    'Adding "%s" "CLF" transform as a "Colorspace" transform.',
                    clf_transform_id,
                )

                colorspace = clf_transform_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.colorspaces.append(colorspace)

    # Reordering the "Raw" colorspace for aesthetics.
    data.colorspaces.extend(
        data.colorspaces.pop(i)
        for i, a in enumerate(data.colorspaces[:])
        if a["name"] == "Raw"
    )

    # Inactive Colorspaces Filtering
    colorspace_named_transform_names = [a["name"] for a in data.colorspaces]
    inactive_colorspaces = []
    for colorspace in data.inactive_colorspaces:
        if colorspace not in colorspace_named_transform_names:
            LOGGER.info('Removing "%s" inactive colorspace.', colorspace)
            continue

        inactive_colorspaces.append(colorspace)

    data.inactive_colorspaces = [
        *inactive_colorspaces,
        # TODO: Consider handling inactivation of following colorspaces via
        # spreadsheet.
        "CIE XYZ-D65 - Display-referred",
        "CIE XYZ-D65 - Scene-referred",
    ]

    # Roles Filtering & Update
    for role in (
        # A config contains multiple possible "Rendering" color spaces.
        ocio.ROLE_RENDERING,
    ):
        LOGGER.info('Removing "%s" role.', role)

        data.roles.pop(role)

    data.roles.update(
        {
            ocio.ROLE_COLOR_PICKING: "sRGB Encoded Rec.709 (sRGB)",
            ocio.ROLE_COLOR_TIMING: format_optional_prefix("ACEScct", "ACES", scheme),
            ocio.ROLE_COMPOSITING_LOG: format_optional_prefix(
                "ACEScct", "ACES", scheme
            ),
            ocio.ROLE_DATA: "Raw",
            ocio.ROLE_INTERCHANGE_DISPLAY: "CIE XYZ-D65 - Display-referred",
            ocio.ROLE_INTERCHANGE_SCENE: format_optional_prefix(
                "ACES2065-1", "ACES", scheme
            ),
            ocio.ROLE_MATTE_PAINT: format_optional_prefix("ACEScct", "ACES", scheme),
            ocio.ROLE_SCENE_LINEAR: format_optional_prefix("ACEScg", "ACES", scheme),
            ocio.ROLE_TEXTURE_PAINT: "sRGB Encoded Rec.709 (sRGB)",
        }
    )

    data.profile_version = dependency_versions.ocio

    config = generate_config(data, config_name, validate)

    LOGGER.info(
        '"%s" config generation complete!',
        config_name_cg(dependency_versions),
    )

    if additional_data:
        return config, data, ctl_transforms, clf_transforms, amf_components
    else:
        return config


if __name__ == "__main__":
    from opencolorio_config_aces import serialize_config_data
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (ROOT_BUILD_DEFAULT / "config" / "aces" / "cg").resolve()

    logging.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for dependency_versions in DEPENDENCY_VERSIONS:
        config_basename = config_basename_cg(dependency_versions)
        (
            config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_cg(
            config_name=build_directory / config_basename,
            dependency_versions=dependency_versions,
            additional_data=True,
        )

        try:
            serialize_config_data(
                data, build_directory / config_basename.replace("ocio", "json")
            )
        except TypeError as error:
            logging.critical(error)
