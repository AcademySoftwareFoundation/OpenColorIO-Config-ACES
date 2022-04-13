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
    colorspace_factory,
    named_transform_factory,
    generate_config,
)
from opencolorio_config_aces.config.reference import (
    ColorspaceDescriptionStyle,
    generate_config_aces,
)
from opencolorio_config_aces.utilities import git_describe

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "PATH_TRANSFORMS_MAPPING_FILE_CG",
    "clf_transform_to_description",
    "clf_transform_to_colorspace",
    "generate_config_cg",
]

PATH_TRANSFORMS_MAPPING_FILE_CG = (
    Path(__file__).parents[0]
    / "resources"
    / "OpenColorIO-Config-ACES _CG_ Transforms - CG Config - Mapping.csv"
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

CONFIG_MAPPING_FILE_PATH : unicode
"""


def clf_transform_to_description(
    clf_transform, describe=ColorspaceDescriptionStyle.LONG_UNION
):
    """
    Generate the *OpenColorIO* colorspace or named transform description for
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
        *OpenColorIO* colorspace or named transform description.
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
    Generate the *OpenColorIO* colorspace for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        Whether to use the full *CLF* transform description or just its ID.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* colorspace signature only, i.e. the
        arguments for its instantiation.

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
        "name": clf_transform.user_name,
        "family": clf_transform.family,
        "description": clf_transform_to_description(clf_transform, describe),
        "from_reference": {
            "transform_type": "FileTransform",
            "transform_factory": "CLF Transform to Group Transform",
            "src": clf_transform.path,
        },
    }
    signature.update(kwargs)

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
    Generate the *OpenColorIO* named transform for given *CLF* transform.

    Parameters
    ----------
    clf_transform : CLFTransform
        *CLF* transform.
    describe : bool, optional
        Whether to use the full *CLF* transform description or just its ID.
    signature_only : bool, optional
        Whether to return the *OpenColorIO* named transform signature only,
        i.e. the arguments for its instantiation.

    Other Parameters
    ----------------
    \\**kwargs : dict, optional
        Keywords arguments for the
        :func:`opencolorio_config_aces.named_transform_factory` definition.

    Returns
    -------
    Object
        *OpenColorIO* named transform.
    """

    signature = {
        "name": clf_transform.user_name,
        "family": clf_transform.family,
        "description": clf_transform_to_description(clf_transform, describe),
        "forward_transform": {
            "transform_type": "FileTransform",
            "transform_factory": "CLF Transform to Group Transform",
            "src": clf_transform.path,
        },
    }
    signature.update(kwargs)

    if signature_only:
        return signature
    else:
        named_transform = named_transform_factory(**signature)

        return named_transform


def generate_config_cg(
    data=None,
    config_name=None,
    validate=True,
    describe=ColorspaceDescriptionStyle.SHORT_UNION,
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_CG,
    additional_data=False,
):
    """
    Generate the *ACES* Computer Graphics (CG) *OpenColorIO* config.

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
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config and
        :class:`opencolorio_config_aces.ConfigData` class instance.
    """

    if data is None:
        _config, data = generate_config_aces(
            describe=describe, additional_data=True, analytical=False
        )

    clf_transforms = unclassify_clf_transforms(
        classify_clf_transforms(discover_clf_transforms())
    )

    config_mapping = defaultdict(list)
    with open(config_mapping_file_path) as csv_file:
        dict_reader = csv.DictReader(
            csv_file,
            delimiter=",",
            fieldnames=[
                "ordering",
                "transform_name",
                "aces_transform_id",
                "clf_transform_id",
                "linked_display_colorspace_style",
                "interface",
                "encoding",
                "categories",
            ],
        )

        # Skipping the first header line.
        next(dict_reader)

        for transform_data in dict_reader:
            config_mapping[transform_data["transform_name"]].append(
                transform_data
            )

    data.description = (
        f'The "Academy Color Encoding System" (ACES) "CG Config"'
        f"\n"
        f"------------------------------------------------------"
        f"\n\n"
        f'This minimalistic "OpenColorIO" config is geared toward computer '
        f"graphics artists requiring a lean config that does not include "
        f"typical VFX colorspaces, displays and looks."
        f"\n\n"
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
        f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.'
    )

    def multi_filters(array, filterers):
        """Apply given filterers on given array."""

        return [
            element
            for element in array
            if all(filterer(element) for filterer in filterers)
        ]

    # Colorspaces, Looks and View Transforms Filtering
    implicit_transforms = [
        transform["name"]
        for transform in data.colorspaces + data.view_transforms
        if transform.get("transforms_data") is None
    ]

    def transform_filterer(transform):
        """
        Filter the transforms, i.e. colorspaces, looks and view transforms
        present in the transforms mapping file.
        """

        if transform["name"] in implicit_transforms:
            return True

        for transforms_data in config_mapping.values():
            for transform_data in transforms_data:
                for data in transform["transforms_data"]:
                    aces_transform_id = transform_data["aces_transform_id"]
                    if not aces_transform_id:
                        continue

                    if aces_transform_id == data.get("aces_transform_id"):
                        return True

        return False

    colorspace_filterers = [transform_filterer]
    data.colorspaces = multi_filters(data.colorspaces, colorspace_filterers)

    look_filterers = [transform_filterer]
    data.looks = multi_filters(data.looks, look_filterers)

    view_transform_filterers = [transform_filterer]
    data.view_transforms = multi_filters(
        data.view_transforms, view_transform_filterers
    )

    # Views Filtering
    display_colorspaces = [
        colorspace["name"]
        for colorspace in data.colorspaces
        if colorspace.get("family") == "Display"
    ]

    def view_filterer(transform):
        """Filter the views supported by a colorspace."""

        if transform["display"] not in display_colorspaces:
            return False

        if (
            transform["view"] in implicit_transforms
            or transform.get("colorspace") in implicit_transforms
        ):
            return True

        for view_transform in data.view_transforms:
            if view_transform["name"] == transform["view"]:
                return True

        return False

    view_filterers = [view_filterer]
    data.views = multi_filters(data.views, view_filterers)
    data.shared_views = multi_filters(data.shared_views, view_filterers)

    # Active Displays Filtering
    data.active_displays = [
        display
        for display in data.active_displays
        if display in display_colorspaces
    ]

    # Active Views Filtering
    views = [view["view"] for view in data.views]
    data.active_views = [view for view in data.active_views if view in views]

    # CLF Transforms
    for transforms_data in config_mapping.values():
        for transform_data in transforms_data:
            # Finding the "CLFTransform" class instance that matches given
            # "CLFtransformID", if it does not exist, there is a critical
            # mismatch in the mapping file.
            clf_transform_id = transform_data["clf_transform_id"]
            if not clf_transform_id:
                continue

            filtered_clf_transforms = [
                clf_transform
                for clf_transform in clf_transforms
                if clf_transform.clf_transform_id.clf_transform_id
                == clf_transform_id
            ]

            clf_transform = next(iter(filtered_clf_transforms), None)

            assert (
                clf_transform
            ), f'"{clf_transform_id}" "CTL" transform does not exist!'

            interface = transform_data["interface"]

            if interface == "NamedTransform":
                data.named_transforms.append(
                    clf_transform_to_named_transform(
                        clf_transform,
                        describe=describe,
                        signature_only=True,
                        name=transform_data["transform_name"],
                        encoding=transform_data.get("encoding"),
                        categories=transform_data.get("categories"),
                    )
                )

            else:
                data.colorspaces.append(
                    clf_transform_to_colorspace(
                        clf_transform,
                        describe=describe,
                        signature_only=True,
                        name=transform_data["transform_name"],
                        encoding=transform_data.get("encoding"),
                        categories=transform_data.get("categories"),
                    )
                )

    # Roles Filtering
    for role in (
        # Config contains multiple possible rendering color spaces
        ocio.ROLE_RENDERING,
        # Reference role is deprecated
        ocio.ROLE_REFERENCE,
    ):
        data.roles.pop(role)

    config = generate_config(data, config_name, validate)

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
        "cg",
    )

    logging.info(f'Using "{build_directory}" build directory...')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    config, data = generate_config_cg(
        config_name=os.path.join(build_directory, "config-aces-cg.ocio"),
        additional_data=True,
    )

    # TODO: Pickling "PyOpenColorIO.ColorSpace" fails on early "PyOpenColorIO"
    # versions.
    try:
        serialize_config_data(
            data, os.path.join(build_directory, "config-aces-cg.json")
        )
    except TypeError as error:
        logging.critical(error)
