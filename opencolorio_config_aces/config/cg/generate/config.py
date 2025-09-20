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
from collections.abc import Callable
from pathlib import Path
from typing import Any

import PyOpenColorIO as ocio

from opencolorio_config_aces.clf import (
    classify_clf_transforms,
    discover_clf_transforms,
    unclassify_clf_transforms,
)
from opencolorio_config_aces.clf.discover.classify import CLFTransform
from opencolorio_config_aces.config.generation import (
    BUILD_CONFIGURATIONS,
    BUILD_VARIANT_FILTERERS,
    BUILTIN_TRANSFORMS,
    SEPARATOR_BUILTIN_TRANSFORM_NAME,
    SEPARATOR_COLORSPACE_FAMILY,
    SEPARATOR_COLORSPACE_NAME,
    BuildConfiguration,
    beautify_alias,
    beautify_colorspace_name,
    colorspace_factory,
    generate_config,
    named_transform_factory,
)
from opencolorio_config_aces.config.reference import (
    DescriptionStyle,
    filter_amf_components,
    generate_config_aces,
)
from opencolorio_config_aces.config.reference.generate.config import (
    COLORSPACE_SCENE_ENCODING_REFERENCE,
    TEMPLATE_ACES_TRANSFORM_ID,
    format_optional_prefix,
    transform_data_aliases,
)
from opencolorio_config_aces.utilities import (
    attest,
    filter_all,
    filter_any,
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
    "main",
]

LOGGER: logging.Logger = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG: str = (
    "https://docs.google.com/spreadsheets/d/"
    "1PXjTzBVYonVFIceGkLDaqcEJvKR6OI63DwZX0aajl3A/"
    "export?format=csv&gid=365242296"
)
"""
URL to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG : unicode
"""

PATH_TRANSFORMS_MAPPING_FILE_CG: Path = next(
    (Path(__file__).parents[0] / "resources").glob("*Mapping.csv")
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

PATH_TRANSFORMS_MAPPING_FILE_CG : unicode
"""

FILTERED_NAMESPACES: tuple[str, ...] = ("OCIO",)
"""
Filtered namespaces.

FILTERED_NAMESPACES : tuple
"""

TEMPLATE_CLF_TRANSFORM_ID: str = "CLFtransformID: {}"
"""
Template for the description of an *CLFtransformID*.

TEMPLATE_CLF_TRANSFORM_ID : unicode
"""


def is_reference(name: str) -> bool:
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


def clf_transform_to_colorspace_name(clf_transform: CLFTransform) -> str:
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
    clf_transform: CLFTransform,
    describe: DescriptionStyle = DescriptionStyle.LONG_UNION,
    direction: str = "Forward",
) -> str | None:
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
    direction : str, optional
        Direction of transform -- determines order of transform descriptors.
        {"Forward", "Reverse"}
        Default: "Forward" (i.e., assume 'Forward' direction)

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` or `NamedTransform` description.
    """

    description = None
    if describe != DescriptionStyle.NONE:
        description = []

        if describe in (DescriptionStyle.SHORT_UNION, DescriptionStyle.LONG_UNION):
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
        elif describe in (DescriptionStyle.LONG_UNION,):
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

        description = "\n".join(description).strip()

    return description


def clf_transform_to_family(
    clf_transform: CLFTransform,
    filtered_namespaces: tuple[str, ...] = FILTERED_NAMESPACES,
) -> str:
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
    clf_transform: CLFTransform,
    describe: DescriptionStyle = DescriptionStyle.LONG_UNION,
    signature_only: bool = False,
    **kwargs: Any,
) -> dict[str, Any] | ocio.ColorSpace:
    """
    Generate the *OpenColorIO* `Colorspace` for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        *CLF* transform description style.
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
        "description": clf_transform_to_description(clf_transform, describe, "Forward"),
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
    clf_transform: CLFTransform,
    describe: DescriptionStyle = DescriptionStyle.LONG_UNION,
    signature_only: bool = False,
    **kwargs: Any,
) -> dict[str, Any] | ocio.NamedTransform:
    """
    Generate the *OpenColorIO* `NamedTransform` for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        *CLF* transform description style.
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
        signature["inverse_transform"] = file_transform  # pyright: ignore
        signature["description"] = clf_transform_to_description(  # pyright: ignore
            clf_transform, describe, direction="Reverse"
        )
    else:
        signature["forward_transform"] = file_transform  # pyright: ignore
        signature["description"] = clf_transform_to_description(  # pyright: ignore
            clf_transform, describe, direction="Forward"
        )

    signature.update(kwargs)

    signature["aliases"] = list(  # pyright: ignore
        dict.fromkeys([beautify_alias(signature["name"])] + signature["aliases"])  # pyright: ignore
    )

    if signature_only:
        return signature
    else:
        named_transform = named_transform_factory(**signature)

        return named_transform


def style_to_colorspace(
    style: str,
    describe: DescriptionStyle = DescriptionStyle.LONG_UNION,
    signature_only: bool = False,
    scheme: str = "Modern 1",  # noqa: ARG001
    **kwargs: Any,
) -> dict[str, Any] | ocio.ColorSpace:
    """
    Create an *OpenColorIO* `Colorspace` or its signature for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
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
            clf_transform, describe, True, **kwargs
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
    style: str,
    describe: DescriptionStyle = DescriptionStyle.LONG_UNION,
    signature_only: bool = False,
    scheme: str = "Modern 1",  # noqa: ARG001
    **kwargs: Any,
) -> dict[str, Any] | ocio.NamedTransform:
    """
    Create an *OpenColorIO* `NamedTransform` or its signature for given style.

    Parameters
    ----------
    style : unicode
        *OpenColorIO* builtin transform style.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.
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
            clf_transform, describe, True, **kwargs
        )
        signature.update(colorspace_signature)
        signature.pop("from_reference", None)
        source = clf_transform.source
        description = clf_transform_to_description(
            clf_transform,
            describe,
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


def config_basename_cg(build_configuration: BuildConfiguration) -> str:
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
    basename, i.e., the filename devoid of directory affix.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_cg(BuildConfiguration())
    'cg-config-v0.0.0_aces-v0.0_ocio-v2.0.ocio'
    """

    return (
        ("cg-config-{variant}-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio")
        .format(**build_configuration.compact_fields())
        .replace("--", "-")
    )


def config_name_cg(build_configuration: BuildConfiguration) -> str:
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_cg(BuildConfiguration())
    'Academy Color Encoding System - CG Config [COLORSPACES v0.0.0] \
[ACES v0.0] [OCIO v2.0]'
    """

    return (
        (
            "Academy Color Encoding System - CG Config {variant}"
            "[COLORSPACES {colorspaces}] "
            "[ACES {aces}] "
            "[OCIO {ocio}]"
        )
        .format(**build_configuration.extended_fields())
        .replace(")[", ") [")
    )


def config_description_cg(
    build_configuration: BuildConfiguration,
    describe: DescriptionStyle = DescriptionStyle.SHORT_UNION,
) -> str:
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
    description.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.DescriptionStyle` enum.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config description.
    """

    name = config_name_cg(build_configuration)

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
    data: Any = None,
    config_name: str | Path | None = None,
    build_configuration: BuildConfiguration = BuildConfiguration(),
    validate: bool = True,
    describe: DescriptionStyle = DescriptionStyle.SHORT_UNION,
    config_mapping_file_path: Path = PATH_TRANSFORMS_MAPPING_FILE_CG,
    scheme: str = "Modern 1",
    additional_filterers: dict[str, dict[str, list[Callable[[Any], bool]]]]
    | None = None,
    additional_data: bool = False,
) -> ocio.Config | tuple[ocio.Config, Any, Any, list[CLFTransform], Any]:
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
    build_configuration: BuildConfiguration, optional
        Build configuration.
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
        config_name_cg(build_configuration),
    )

    clf_transforms = unclassify_clf_transforms(
        classify_clf_transforms(discover_clf_transforms())
    )

    LOGGER.debug('Using %s "CLF" transforms...', clf_transforms)

    if data is None:
        _config, data, ctl_transforms, amf_components = generate_config_aces(
            build_configuration=build_configuration,
            describe=describe,
            scheme=scheme,
            analytical=False,
            additional_filterers=additional_filterers,
            additional_data=True,
        )

    def clf_transform_from_id(clf_transform_id: str) -> CLFTransform | None:
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

    def clf_transform_from_style(style: str) -> CLFTransform | None:
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
                "interop_id",
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

                if BUILTIN_TRANSFORMS[style] > build_configuration.ocio:
                    LOGGER.warning(
                        '"%s" style is unavailable for "%s" profile version, '
                        "skipping transform!",
                        style,
                        build_configuration.ocio,
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

    def yield_from_config_mapping() -> Any:
        """Yield the transform data stored in the *CSV* mapping file."""
        for transforms_data in config_mapping.values():
            yield from transforms_data

    data.name = re.sub(
        r"\.ocio$",
        "",
        config_basename_cg(build_configuration),
    )
    data.description = config_description_cg(build_configuration, describe)

    # Colorspaces, Looks and View Transforms Filtering
    # ================================================
    transforms = data.colorspaces + data.view_transforms
    implicit_transforms = [
        a["name"] for a in transforms if a.get("transforms_data") is None
    ]

    LOGGER.info("Implicit transforms: %s.", implicit_transforms)

    def implicit_transform_filterer(transform: dict[str, Any]) -> bool:
        """Return whether given transform is an implicit transform."""

        return transform.get("name") in implicit_transforms

    def transform_filterer(transform: dict[str, Any]) -> bool:
        """Return whether given transform must be included."""

        for transform_data in yield_from_config_mapping():
            aces_transform_id = transform_data["aces_transform_id"]
            if not aces_transform_id:
                continue

            for data in transform.get("transforms_data", []):
                if aces_transform_id == data.get("aces_transform_id"):
                    return True

        return False

    # "Colorspaces" Filtering
    # =======================
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
    # =================
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
    # ==========================
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
    # ================================
    display_names = [
        a["name"] for a in data.colorspaces if a.get("family") == "Display"
    ]

    def implicit_view_filterer(transform: dict[str, Any]) -> bool:
        """Return whether given transform is an implicit view."""

        return all(
            [
                transform.get("view") in implicit_transforms,
                transform.get("display") in display_names,
            ]
        )

    def view_filterer(transform: dict[str, Any]) -> bool:
        """Return whether given view transform must be included."""

        if transform["display"] not in display_names:
            return False

        for view_transform in data.view_transforms:
            if view_transform["name"] == transform["view"]:
                return True

        return False

    # "Shared Views" Filtering
    # ========================
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
    # ===========================
    data.active_displays = [a for a in data.active_displays if a in display_names]
    LOGGER.info("Filtered active displays: %s.", data.active_displays)

    # "Active Views" Filtering
    # ========================
    views = [view["view"] for view in data.views]
    data.active_views = [view for view in data.active_views if view in views]
    LOGGER.info("Filtered active views: %s.", data.active_views)

    # CLF Transforms & BuiltinTransform Creation
    # ==========================================
    def remove_existing_colorspace(name: str) -> None:
        """Remove given existing *ColorSpace* from the current config data."""

        for i, colorspace in enumerate(data.colorspaces[:]):
            if colorspace["name"] == name:
                LOGGER.info(
                    'Removing existing "%s" "ColorSpace" transform from '
                    "current config data.",
                    name,
                )

                data.colorspaces.pop(i)

    def remove_existing_named_transform(name: str) -> None:
        """Remove given existing *NamedTransform* from the current config data."""

        for i, named_transform in enumerate(data.named_transforms[:]):
            if named_transform["name"] == name:
                LOGGER.info(
                    'Removing existing "%s" "NamedTransform" transform from '
                    "current config data.",
                    name,
                )

                data.named_transforms.pop(i)

    for transform_data in yield_from_config_mapping():
        # Inherited from the "Reference" config.
        if (
            transform_data["aces_transform_id"]
            and not transform_data["clf_transform_id"]
        ):
            continue

        kwargs = {
            "describe": describe,
            "signature_only": True,
            "aliases": transform_data_aliases(transform_data),
            "encoding": transform_data.get("encoding"),
            "categories": transform_data.get("categories"),
            "interop_id": transform_data.get("interop_id"),
        }

        style = transform_data["builtin_transform_style"]
        clf_transform_id = transform_data["clf_transform_id"]

        if style:
            clf_transform = clf_transform_from_style(style)

            filtered_amf_components = None
            if (
                aces_transform_id := clf_transform.information.get(  # pyright: ignore
                    "ACEStransformID"
                )
            ) is not None:
                filtered_amf_components = filter_amf_components(
                    amf_components,
                    aces_transform_id.aces_transform_id,
                )

            kwargs.update(
                {
                    "style": style,
                    "clf_transform": clf_transform,
                    "interchange_mapping": None
                    if filtered_amf_components is None
                    else {"amf_transform_ids": "\n".join(filtered_amf_components)},
                }
            )

            if transform_data["interface"] == "ColorSpace":
                LOGGER.info(
                    'Creating a "Colorspace" transform for "%s" style...',
                    style,
                )

                colorspace = style_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]

                remove_existing_colorspace(colorspace["name"])

                data.colorspaces.append(colorspace)
            elif transform_data["interface"] == "NamedTransform":
                LOGGER.info(
                    'Creating a "NamedTransform" transform for "%s" style...',
                    style,
                )

                named_transform = style_to_named_transform(**kwargs)
                named_transform["transforms_data"] = [transform_data]

                remove_existing_named_transform(named_transform["name"])

                data.named_transforms.append(named_transform)

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
                clf_transform is not None,
                f'"{clf_transform_id}" "CLF" transform does not exist!',
            )

            filtered_amf_components = None
            if (
                aces_transform_id := clf_transform.information.get(  # pyright: ignore
                    "ACEStransformID"
                )
            ) is not None:
                filtered_amf_components = filter_amf_components(
                    amf_components, aces_transform_id.aces_transform_id
                )

            kwargs.update(
                {
                    "clf_transform": clf_transform,
                    "interchange_mapping": None
                    if filtered_amf_components is None
                    else {"amf_transform_ids": "\n".join(filtered_amf_components)},
                }
            )

            if transform_data["interface"] == "NamedTransform":
                LOGGER.info(
                    'Adding "%s" "CLF" transform as a "Named" transform.',
                    clf_transform_id,
                )

                named_transform = clf_transform_to_named_transform(**kwargs)
                named_transform["transforms_data"] = [transform_data]

                remove_existing_named_transform(named_transform["name"])

                data.named_transforms.append(named_transform)
            else:
                LOGGER.info(
                    'Adding "%s" "CLF" transform as a "Colorspace" transform.',
                    clf_transform_id,
                )

                colorspace = clf_transform_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]

                remove_existing_colorspace(colorspace["name"])

                data.colorspaces.append(colorspace)

    # Inactive Colorspaces Filtering
    # ==============================
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
    # ========================
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

    # Ordering
    # ========
    def ordering(element: dict[str, Any]) -> int:
        """Return the ordering key for given element."""

        return int(
            next(iter(element.get("transforms_data", [{"ordering": 0}])))["ordering"]
        )

    data.colorspaces = sorted(data.colorspaces, key=ordering)
    data.colorspaces.extend(
        data.colorspaces.pop(i)
        for i, a in enumerate(data.colorspaces[:])
        if a["name"] == "Raw"
    )
    data.named_transforms = sorted(data.named_transforms, key=ordering)
    data.view_transforms = sorted(data.view_transforms, key=ordering)
    data.looks = sorted(data.looks, key=ordering)

    # Virtual Display Shared Views
    # ============================
    data.virtual_display_shared_views = list(
        {
            shared_view["view"]
            for shared_view in data.shared_views
            if shared_view["display"]
            in [
                a["name"]
                for a in data.colorspaces
                if a.get("family") == "Display" and a.get("encoding") == "sdr-video"
            ]
        }
    )

    # Virtual Display Views
    # =====================
    data.virtual_display_views = [
        {
            "view": "Raw",
            "view_transform": "",
            "colorspace": "Raw",
            "looks": "",
            "rule": "",
            "description": "",
        }
    ]

    data.profile_version = build_configuration.ocio

    config = generate_config(data, config_name, validate)

    LOGGER.info(
        '"%s" config generation complete!',
        config_name_cg(build_configuration),
    )

    if additional_data:
        return config, data, ctl_transforms, clf_transforms, amf_components
    else:
        return config


def main(build_directory: Path) -> int:
    """
    Define the main entry point for the generation of all the *ACES* Computer
    Graphics (CG) *OpenColorIO* config versions and variants.

    Parameters
    ----------
    build_directory : Path
        Build directory.

    Returns
    -------
    :class:`int`
        Return code.
    """

    logging.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for build_configuration in BUILD_CONFIGURATIONS:
        # Only building the D65 variant of the CG config.
        if build_configuration.variant in ("D60 Views", "All Views"):
            continue

        config_basename = config_basename_cg(build_configuration)
        (
            config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_cg(
            config_name=build_directory / config_basename,
            build_configuration=build_configuration,
            additional_filterers=BUILD_VARIANT_FILTERERS[build_configuration.variant],
            additional_data=True,
        )

        try:
            serialize_config_data(
                data, build_directory / config_basename.replace("ocio", "json")
            )
        except TypeError as error:
            logging.critical(error)

    return 0


if __name__ == "__main__":
    import sys

    from opencolorio_config_aces import serialize_config_data
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(main((ROOT_BUILD_DEFAULT / "config" / "aces" / "cg").resolve()))
