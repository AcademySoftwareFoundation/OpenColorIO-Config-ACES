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

from opencolorio_config_aces.config.generation import (
    PROFILE_VERSION_DEFAULT,
    generate_config,
)
from opencolorio_config_aces.config.reference import (
    DescriptionStyle,
)
from opencolorio_config_aces.config.cg import (
    generate_config_cg,
)
from opencolorio_config_aces.config.cg.generate.config import (
    dependency_versions,
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

logger = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO = (
    "https://docs.google.com/spreadsheets/d/"
    "1nE95DEVtxtEkcIEaJk0WekyEH0Rcs8z_3fdwUtqP8V4/"
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


def config_basename_studio(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
    profile_version=PROFILE_VERSION_DEFAULT,
):
    """
    Generate the ACES* Studio *OpenColorIO* config basename, i.e. the filename
    devoid of directory affixe.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_studio()  # doctest: +SKIP
    'studio-config-v0.2.0_aces-v1.3_ocio-v2.0.ocio'
    """

    return ("studio-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions(config_mapping_file_path, profile_version)
    )


def config_name_studio(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
    profile_version=PROFILE_VERSION_DEFAULT,
):
    """
    Generate the ACES* Studio *OpenColorIO* config name.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_studio()  # doctest: +SKIP
    'Academy Color Encoding System - Studio Config [COLORSPACES v0.2.0] \
[ACES v1.3] [OCIO v2.0]'
    """

    return (
        "Academy Color Encoding System - Studio Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions(config_mapping_file_path, profile_version))


def config_description_studio(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
    profile_version=PROFILE_VERSION_DEFAULT,
):
    """
    Generate the ACES* Studio *OpenColorIO* config description.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config description.
    """

    name = config_name_studio(config_mapping_file_path, profile_version)
    underline = "-" * len(name)
    description = (
        'This "OpenColorIO" config is geared toward studios requiring a config '
        "that includes a wide variety of camera colorspaces, displays and "
        "looks."
    )

    return "\n".join([name, underline, "", description, "", timestamp()])


def generate_config_studio(
    data=None,
    config_name=None,
    profile_version=PROFILE_VERSION_DEFAULT,
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
    profile_version : ProfileVersion, optional
        *OpenColorIO* config profile version.
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

    logger.info(
        'Generating "%s" config...',
        config_name_studio(config_mapping_file_path, profile_version),
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
            profile_version=profile_version,
            describe=describe,
            scheme=scheme,
            config_mapping_file_path=config_mapping_file_path,
            additional_data=True,
        )

    data.name = re.sub(
        r"\.ocio$",
        "",
        config_basename_studio(config_mapping_file_path, profile_version),
    )
    data.description = config_description_studio(
        config_mapping_file_path, profile_version
    )
    config = generate_config(data, config_name, validate)

    logger.info(
        '"%s" config generation complete!',
        config_name_studio(config_mapping_file_path, profile_version),
    )

    if additional_data:
        return config, data, ctl_transforms, clf_transforms, amf_components
    else:
        return config


if __name__ == "__main__":
    from opencolorio_config_aces import (
        SUPPORTED_PROFILE_VERSIONS,
        serialize_config_data,
    )
    from opencolorio_config_aces.utilities import ROOT_BUILD_DEFAULT

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = (
        ROOT_BUILD_DEFAULT / "config" / "aces" / "studio"
    ).resolve()

    logging.info('Using "%s" build directory...', build_directory)

    build_directory.mkdir(parents=True, exist_ok=True)

    for profile_version in SUPPORTED_PROFILE_VERSIONS:
        config_basename = config_basename_studio(
            profile_version=profile_version
        )
        (
            config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_studio(
            config_name=build_directory / config_basename,
            profile_version=profile_version,
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
