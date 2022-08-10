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

import PyOpenColorIO as ocio
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from opencolorio_config_aces.clf import (
    discover_clf_transforms,
    classify_clf_transforms,
    unclassify_clf_transforms,
)
from opencolorio_config_aces.config.generation import (
    SEPARATOR_COLORSPACE_NAME,
    SEPARATOR_BUILTIN_TRANSFORM_NAME,
    SEPARATOR_COLORSPACE_FAMILY,
    VersionData,
    beautify_alias,
    beautify_colorspace_name,
    colorspace_factory,
    generate_config,
    named_transform_factory,
)
from opencolorio_config_aces.config.reference import (
    ColorspaceDescriptionStyle,
    version_aces_dev,
    version_config_mapping_file,
    generate_config_aces,
)
from opencolorio_config_aces.config.reference.generate.config import (
    COLORSPACE_SCENE_ENCODING_REFERENCE,
    format_optional_prefix,
    format_swapped_affix,
)
from opencolorio_config_aces.utilities import (
    git_describe,
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
    "URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG",
    "PATH_TRANSFORMS_MAPPING_FILE_CG",
    "is_reference",
    "clf_transform_to_description",
    "clf_transform_to_colorspace",
    "clf_transform_to_named_transform",
    "style_to_colorspace",
    "style_to_named_transform",
    "dependency_versions",
    "config_basename_cg",
    "config_name_cg",
    "config_description_cg",
    "generate_config_cg",
]

logger = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG = (
    "https://docs.google.com/spreadsheets/d/"
    "1DqxmtZpnhL_9N1wayvcW0y3bZoHRom7A1c58YLlr89g/"
    "export?format=csv&gid=609660164"
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
    clf_transform, describe=ColorspaceDescriptionStyle.LONG_UNION
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

    Returns
    -------
    unicode
        *OpenColorIO* `Colorspace` or `NamedTransform` description.
    """

    description = None
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.SHORT,
            ColorspaceDescriptionStyle.SHORT_UNION,
        ):
            if clf_transform.description is not None:
                description.append(
                    f"Convert {clf_transform.input_descriptor} "
                    f"to {clf_transform.output_descriptor}"
                )

        elif describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.LONG,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            if clf_transform.description is not None:
                description.append("\n" + clf_transform.description)

        description.append(
            f"\nCLFtransformID: "
            f"{clf_transform.clf_transform_id.clf_transform_id}"
        )

        description = "\n".join(description).strip()

    return description


def clf_transform_to_colorspace(
    clf_transform,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
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
        Whether to use the full *CLF* transform description or just its ID.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `Colorspace` signature only, i.e.
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
        "family": (
            f"{clf_transform.clf_transform_id.type}"
            f"{SEPARATOR_COLORSPACE_FAMILY}"
            f"{clf_transform.clf_transform_id.namespace}"
        ),
        "description": clf_transform_to_description(clf_transform, describe),
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
        dict.fromkeys(
            [beautify_alias(signature["name"])] + signature["aliases"]
        )
    )

    if signature_only:
        return signature
    else:
        colorspace = colorspace_factory(**signature)

        return colorspace


def clf_transform_to_named_transform(
    clf_transform,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
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
        Whether to use the full *CLF* transform description or just its ID.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* `NamedTransform` signature only,
        i.e. the arguments for its instantiation.

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
        "family": (
            f"{clf_transform.clf_transform_id.type}"
            f"{SEPARATOR_COLORSPACE_FAMILY}"
            f"{clf_transform.clf_transform_id.namespace}"
        ),
        "description": clf_transform_to_description(clf_transform, describe),
    }

    file_transform = {
        "transform_type": "FileTransform",
        "transform_factory": "CLF Transform to Group Transform",
        "src": clf_transform.path,
    }
    if is_reference(clf_transform.source):
        signature["forward_transform"] = file_transform
    else:
        signature["inverse_transform"] = file_transform

    signature.update(kwargs)

    signature["aliases"] = list(
        dict.fromkeys(
            [beautify_alias(signature["name"])] + signature["aliases"]
        )
    )

    if signature_only:
        return signature
    else:
        named_transform = named_transform_factory(**signature)

        return named_transform


def style_to_colorspace(
    style,
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    signature_only=False,
    scheme="Modern 1",
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
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* view `Colorspace` signature only,
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
    ocio.ViewTransform or dict
        *OpenColorIO* `Colorspace` or its signature for given style.
    """

    # TODO: Implement "BuiltinTransform" name beautification.
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

    signature = {}
    clf_transform = kwargs.pop("clf_transform", None)
    if clf_transform:
        signature.update(
            clf_transform_to_colorspace(
                clf_transform, signature_only=True, **kwargs
            )
        )
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
        dict.fromkeys(
            [beautify_alias(signature["name"])] + signature["aliases"]
        )
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
    describe=ColorspaceDescriptionStyle.LONG_UNION,
    signature_only=False,
    scheme="Modern 1",
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
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* view `Colorspace` signature only,
        i.e. the arguments for its instantiation.
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
    if describe != ColorspaceDescriptionStyle.NONE:
        description = []

        if describe in (
            ColorspaceDescriptionStyle.OPENCOLORIO,
            ColorspaceDescriptionStyle.SHORT_UNION,
            ColorspaceDescriptionStyle.LONG_UNION,
        ):
            description.append(builtin_transform.getDescription())

        description = "\n".join(description)

    signature = {}
    clf_transform = kwargs.pop("clf_transform", None)
    if clf_transform:
        signature.update(
            clf_transform_to_colorspace(
                clf_transform, signature_only=True, **kwargs
            )
        )
        signature.pop("from_reference", None)
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
                "forward_transform": builtin_transform,
                "description": description,
            }
        )
    else:
        signature.update(
            {
                "inverse_transform": builtin_transform,
                "description": description,
            }
        )
    signature.update(**kwargs)

    signature["aliases"] = list(
        dict.fromkeys(
            [beautify_alias(signature["name"])] + signature["aliases"]
        )
    )

    if signature_only:
        builtin_transform = {
            "transform_type": "BuiltinTransform",
            "style": style,
        }
        if is_reference(source):
            signature["forward_transform"] = builtin_transform
        else:
            signature["inverse_transform"] = builtin_transform

        return signature
    else:
        colorspace = named_transform_factory(**signature)

        return colorspace


def dependency_versions(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
):
    """
    Return the dependency versions of the ACES* Computer Graphics (CG)
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


def config_basename_cg(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
    basename, i.e. the filename devoid of directory affix.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_cg()  # doctest: +SKIP
    'cg-config-v0.1.0_aces-v1.3_ocio-v2.1.2dev.ocio'
    """

    return ("cg-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions(config_mapping_file_path)
    )


def config_name_cg(config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_cg()  # doctest: +SKIP
    'Academy Color Encoding System - CG Config [COLORSPACES v0.1.0] \
[ACES v1.3] [OCIO v2.1.2dev]'
    """

    return (
        "Academy Color Encoding System - CG Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions(config_mapping_file_path))


def config_description_cg(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
):
    """
    Generate the ACES* Computer Graphics (CG) *OpenColorIO* config
    description.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Computer Graphics (CG) *OpenColorIO* config description.
    """

    name = config_name_cg(config_mapping_file_path)
    underline = "-" * len(name)
    description = (
        'This minimalistic "OpenColorIO" config is geared toward computer '
        "graphics artists requiring a lean config that does not include "
        "camera colorspaces and the less common displays and looks."
    )
    timestamp = (
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
        f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.'
    )

    return "\n".join([name, underline, "", description, "", timestamp])


def generate_config_cg(
    data=None,
    config_name=None,
    validate=True,
    describe=ColorspaceDescriptionStyle.SHORT_UNION,
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
    scheme="Modern 1",
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
        -   The list of implicit colorspaces is built, e.g. *ACES2065-1*,
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
    validate : bool, optional
        Whether to validate the config.
    describe : int, optional
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.
    config_mapping_file_path : unicode, optional
        Path to the *CSV* mapping file used to describe the transforms mapping.
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
        f'Generating "{config_name_cg(config_mapping_file_path)}" config...'
    )

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    if data is None:
        _config, data = generate_config_aces(
            describe=describe,
            analytical=False,
            scheme=scheme,
            additional_data=True,
        )

    clf_transforms = unclassify_clf_transforms(
        classify_clf_transforms(discover_clf_transforms())
    )

    logger.debug(f'Using {clf_transforms} "CLF" transforms...')

    builtin_transforms = [
        builtin for builtin in ocio.BuiltinTransformRegistry()
    ]
    logger.debug(f'Using {builtin_transforms} "Builtin" transforms...')

    def transform_aliases(transform_data):
        """Return the aliases from given transform."""

        return [transform_data["legacy_name"]] + re.split(
            "[,;]+", transform_data.get("aliases", "")
        )

    def clf_transform_from_id(clf_transform_id):
        """Filter the "CLFTransform" instances matching given "CLFtransformID"."""

        filtered_clf_transforms = [
            clf_transform
            for clf_transform in clf_transforms
            if clf_transform.clf_transform_id.clf_transform_id
            == clf_transform_id
        ]

        clf_transform = next(iter(filtered_clf_transforms), None)

        logger.debug(
            f'Filtered "CLF" transform with "{clf_transform_id}" '
            f'"CLFtransformID": {clf_transform}.'
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

        logger.debug(
            f'Filtered "CLF" transform with "{style}" style: {clf_transform}.'
        )

        return clf_transform

    logger.info(f'Parsing "{config_mapping_file_path}" config mapping file...')

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=",",
            fieldnames=[
                "ordering",
                "legacy_name",
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
                assert (
                    style in builtin_transforms
                ), f'"{style}" "BuiltinTransform" style does not exist!'

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

                assert clf_transform is not None, (
                    f'"OpenColorIO-Config-ACES" has no transform with '
                    f'"{clf_transform_id}" ACEStransformID, please cross-check '
                    f'the "{config_mapping_file_path}" config mapping file!'
                )

                transform_data["clf_transform"] = clf_transform

            config_mapping[transform_data["legacy_name"]].append(
                transform_data
            )

    def yield_from_config_mapping():
        """Yield the transform data stored in the *CSV* mapping file."""
        for transforms_data in config_mapping.values():
            yield from transforms_data

    data.name = re.sub(
        r"\.ocio$", "", config_basename_cg(config_mapping_file_path)
    )
    data.description = config_description_cg(config_mapping_file_path)

    # Colorspaces, Looks and View Transforms Filtering
    transforms = data.colorspaces + data.view_transforms
    implicit_transforms = [
        a["name"] for a in transforms if a.get("transforms_data") is None
    ]

    logger.info(f"Implicit transforms: {implicit_transforms}.")

    def implicit_filterer(transform):
        """Return whether given transform is an implicit transform."""

        return transform.get("name") in implicit_transforms

    def transform_filterer(transform):
        """Return whether given transform must be included."""

        for transform_data in yield_from_config_mapping():
            for data in transform["transforms_data"]:
                aces_transform_id = transform_data["aces_transform_id"]
                if not aces_transform_id:
                    continue

                if aces_transform_id == data.get("aces_transform_id"):
                    return True

        return False

    def multi_filters(array, filterers):
        """Apply given filterers on given array."""

        filtered = [
            a for a in array if any(filterer(a) for filterer in filterers)
        ]

        return filtered

    colorspace_filterers = [implicit_filterer, transform_filterer]
    data.colorspaces = multi_filters(data.colorspaces, colorspace_filterers)
    logger.info(
        'Filtered "Colorspace" transforms: '
        f'{[a["name"] for a in data.colorspaces]} '
    )

    look_filterers = [implicit_filterer, transform_filterer]
    data.looks = multi_filters(data.looks, look_filterers)
    logger.info(
        'Filtered "Look" transforms: ' f'{[a["name"] for a in data.looks]} '
    )

    view_transform_filterers = [implicit_filterer, transform_filterer]
    data.view_transforms = multi_filters(
        data.view_transforms, view_transform_filterers
    )
    logger.info(
        'Filtered "View" transforms: '
        f'{[a["name"] for a in data.view_transforms]} '
    )

    # Views Filtering
    display_names = [
        a["name"] for a in data.colorspaces if a.get("family") == "Display"
    ]

    def implicit_filterer(transform):
        """Return whether given transform is an implicit transform."""

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

    shared_view_filterers = [implicit_filterer, view_filterer]
    data.shared_views = multi_filters(data.shared_views, shared_view_filterers)
    logger.info(
        f'Filtered shared "View(s)": {[a["view"] for a in data.shared_views]} '
    )

    view_filterers = [implicit_filterer, view_filterer]
    data.views = multi_filters(data.views, view_filterers)
    logger.info('Filtered "View(s)": ' f'{[a["view"] for a in data.views]} ')

    # Active Displays Filtering
    data.active_displays = [
        a for a in data.active_displays if a in display_names
    ]
    logger.info(f"Filtered active displays: {data.active_displays}")

    # Active Views Filtering
    views = [view["view"] for view in data.views]
    data.active_views = [view for view in data.active_views if view in views]
    logger.info(f"Filtered active views: {data.active_views}")

    # CLF Transforms & BuiltinTransform Creation
    for transform_data in yield_from_config_mapping():
        kwargs = {
            "describe": describe,
            "signature_only": True,
            "aliases": transform_aliases(transform_data),
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
                logger.info(
                    f'Creating a "Colorspace" transform for "{style}" style...'
                )

                colorspace = style_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.colorspaces.append(colorspace)
            elif transform_data["interface"] == "NamedTransform":
                logger.info(
                    f'Creating a "NamedTransform" transform for "{style}" style...'
                )

                colorspace = style_to_named_transform(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.named_transforms.append(colorspace)

            if style and clf_transform_id:
                logger.warning(
                    '"{style}" was defined along side a "CTLtransformID", '
                    "hybrid transform generation was used!"
                )
                continue

        if clf_transform_id:
            clf_transform = clf_transform_from_id(clf_transform_id)

            assert (
                clf_transform
            ), f'"{clf_transform_id}" "CLF" transform does not exist!'

            kwargs["clf_transform"] = clf_transform

            if transform_data["interface"] == "NamedTransform":
                logger.info(
                    f'Adding "{clf_transform_id}" "CLF" transform as a '
                    f'"Named" transform.'
                )

                named_transform = clf_transform_to_named_transform(**kwargs)
                named_transform["transforms_data"] = [transform_data]
                data.named_transforms.append(named_transform)
            else:
                logger.info(
                    f'Adding "{clf_transform_id}" "CLF" transform as a '
                    f'"Colorspace" transform.'
                )

                colorspace = clf_transform_to_colorspace(**kwargs)
                colorspace["transforms_data"] = [transform_data]
                data.colorspaces.append(colorspace)

    # Roles Filtering & Update
    for role in (
        # A config contains multiple possible "Rendering" color spaces.
        ocio.ROLE_RENDERING,
        # The "Reference" role is deprecated.
        ocio.ROLE_REFERENCE,
    ):
        logger.info(f'Removing "{role}" role.')

        data.roles.pop(role)

    data.roles.update(
        {
            ocio.ROLE_COLOR_PICKING: format_swapped_affix(
                "sRGB", "Display", scheme
            ),
            ocio.ROLE_COLOR_TIMING: format_optional_prefix(
                "ACEScct", "ACES", scheme
            ),
            ocio.ROLE_COMPOSITING_LOG: format_optional_prefix(
                "ACEScct", "ACES", scheme
            ),
            ocio.ROLE_DATA: "Raw",
            ocio.ROLE_DEFAULT: "sRGB - Texture",
            ocio.ROLE_INTERCHANGE_DISPLAY: "CIE-XYZ-D65",
            ocio.ROLE_INTERCHANGE_SCENE: format_optional_prefix(
                "ACES2065-1", "ACES", scheme
            ),
            ocio.ROLE_MATTE_PAINT: format_optional_prefix(
                "ACEScct", "ACES", scheme
            ),
            ocio.ROLE_SCENE_LINEAR: format_optional_prefix(
                "ACEScg", "ACES", scheme
            ),
            ocio.ROLE_TEXTURE_PAINT: "sRGB - Texture",
        }
    )

    data.profile_version = VersionData(2, 0)

    config = generate_config(data, config_name, validate)

    logger.info(
        f'"{config_name_cg(config_mapping_file_path)}" config generation complete!'
    )

    if additional_data:
        return config, data
    else:
        return config


if __name__ == "__main__":
    import opencolorio_config_aces
    from opencolorio_config_aces import serialize_config_data
    from pathlib import Path

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (
        Path(opencolorio_config_aces.__path__[0])
        / ".."
        / "build"
        / "config"
        / "aces"
        / "cg"
    ).resolve()

    logging.info(f'Using "{build_directory}" build directory...')

    build_directory.mkdir(parents=True, exist_ok=True)

    config_basename = config_basename_cg()
    config, data = generate_config_cg(
        config_name=build_directory / config_basename,
        additional_data=True,
    )

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(
            data, build_directory / config_basename.replace("ocio", "json")
        )
    except TypeError as error:
        logging.critical(error)
