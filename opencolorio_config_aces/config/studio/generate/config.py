# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ACES* Studio Config Generator
==============================

Defines various objects related to the generation of the *ACES* Studio
*OpenColorIO* config:

-   :func:`opencolorio_config_aces.generate_config_studio`
"""

import logging
import re
from pathlib import Path

import PyOpenColorIO as ocio

from opencolorio_config_aces.config.cg import (
    generate_config_cg,
)
from opencolorio_config_aces.config.generation import (
    DEPENDENCY_VERSIONS,
    DependencyVersions,
    generate_config,
)
from opencolorio_config_aces.config.reference import (
    DescriptionStyle,
)
from opencolorio_config_aces.utilities import (
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
    "URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO",
    "PATH_TRANSFORMS_MAPPING_FILE_STUDIO",
    "config_basename_studio",
    "config_name_studio",
    "config_description_studio",
    "generate_config_studio",
]

LOGGER = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO = (
    "https://docs.google.com/spreadsheets/d/"
    "1PXjTzBVYonVFIceGkLDaqcEJvKR6OI63DwZX0aajl3A/"
    "export?format=csv&gid=1155125238"
)
"""
URL to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO : unicode
"""

PATH_TRANSFORMS_MAPPING_FILE_STUDIO = next(
    (Path(__file__).parents[0] / "resources").glob("*Mapping.csv")
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

PATH_TRANSFORMS_MAPPING_FILE_STUDIO : unicode
"""


def config_basename_studio(dependency_versions):
    """
    Generate the ACES* Studio *OpenColorIO* config basename, i.e., the filename
    devoid of directory affixe.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_studio(DependencyVersions())
    'studio-config-v0.0.0_aces-v0.0_ocio-v2.0.ocio'
    """

    return ("studio-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions.to_regularised_versions()
    )


def config_name_studio(dependency_versions):
    """
    Generate the ACES* Studio *OpenColorIO* config name.

    Parameters
    ----------
    dependency_versions: DependencyVersions
        Dependency versions, e.g., *aces-dev*, *colorspaces*, and *OpenColorIO*.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_studio(DependencyVersions())
    'Academy Color Encoding System - Studio Config [COLORSPACES v0.0.0] \
[ACES v0.0] [OCIO v2.0]'
    """

    return (
        "Academy Color Encoding System - Studio Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions.to_regularised_versions())


def config_description_studio(
    dependency_versions,
    describe=DescriptionStyle.SHORT_UNION,
):
    """
    Generate the ACES* Studio *OpenColorIO* config description.

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
        ACES* Studio *OpenColorIO* config description.
    """

    name = config_name_studio(dependency_versions)

    underline = "-" * len(name)

    summary = (
        'This "OpenColorIO" config is geared toward studios requiring a config '
        "that includes a wide variety of camera colorspaces, displays and "
        "looks."
    )

    description = [name, underline, "", summary]

    if describe in ((DescriptionStyle.LONG_UNION,)):
        description.extend(["", timestamp()])

    return "\n".join(description)


def generate_config_studio(
    data=None,
    config_name=None,
    dependency_versions=DependencyVersions(),
    validate=True,
    describe=DescriptionStyle.SHORT_UNION,
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
    scheme="Modern 1",
    additional_data=False,
):
    """
    Generate the *ACES* Studio *OpenColorIO* config.

    The default process is as follows:

    -   The *ACES* Studio *OpenColorIO* config generator invokes the *ACES* CG
        *OpenColorIO* config generator with the given studio config mapping
        file via the :func:`opencolorio_config_aces.generate_config_cg`
        definition.
    -   The *ACES* CG *OpenColorIO* config generator invokes the *aces-dev*
        reference implementation *OpenColorIO* config generator via the
        :func:`opencolorio_config_aces.generate_config_aces` definition and the
        default reference config mapping file.
    -   With the data from the *aces-dev* reference implementation
        *OpenColorIO* config generated, the *ACES* CG *OpenColorIO* config
        generator produces the *ACES* Studio *OpenColorIO* config by filtering
        and extending it with the given studio config mapping file.

    Parameters
    ----------
    data : ConfigData, optional
        *OpenColorIO* config data to derive the config from, the default is to
        use the *ACES* CG *OpenColorIO* config.
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
    additional_data : bool, optional
        Whether to return additional data.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config and
        :class:`opencolorio_config_aces.ConfigData` class instance, *ACES*
        *CTL* transforms, *CLF* transforms and *ACES* *AMF* components.
    """

    LOGGER.info(
        'Generating "%s" config...',
        config_name_studio(dependency_versions),
    )

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    if data is None:
        (
            _config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_cg(
            dependency_versions=dependency_versions,
            describe=describe,
            scheme=scheme,
            config_mapping_file_path=config_mapping_file_path,
            additional_data=True,
        )

    data.name = re.sub(
        r"\.ocio$",
        "",
        config_basename_studio(dependency_versions),
    )
    data.description = config_description_studio(dependency_versions, describe)
    config = generate_config(data, config_name, validate)

    LOGGER.info(
        '"%s" config generation complete!',
        config_name_studio(dependency_versions),
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

    build_directory = (ROOT_BUILD_DEFAULT / "config" / "aces" / "studio").resolve()

    logging.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for dependency_versions in DEPENDENCY_VERSIONS:
        config_basename = config_basename_studio(dependency_versions)
        (
            config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_studio(
            config_name=build_directory / config_basename,
            dependency_versions=dependency_versions,
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

        if dependency_versions.ocio.minor <= 3:
            config = ocio.Config.CreateFromFile(  # pyright:ignore
                str(build_directory / config_basename)
            )
            view_transforms = list(config.getViewTransforms())
            view_transforms = [view_transforms[-1], *view_transforms[:-1]]
            config.clearViewTransforms()
            for view_transform in view_transforms:
                config.addViewTransform(view_transform)

            with open(build_directory / config_basename, "w") as file:
                file.write(config.serialize())
