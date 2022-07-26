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

from datetime import datetime
from pathlib import Path

from opencolorio_config_aces.config.generation import (
    generate_config,
)
from opencolorio_config_aces.config.reference import (
    ColorspaceDescriptionStyle,
)
from opencolorio_config_aces.config.cg import (
    generate_config_cg,
)
from opencolorio_config_aces.config.cg.generate.config import (
    dependency_versions,
)
from opencolorio_config_aces.utilities import (
    git_describe,
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
):
    """
    Generate the ACES* Studio *OpenColorIO* config basename, i.e. the filename
    devoid of directory affixe.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_studio()  # doctest: +SKIP
    'studio-config-v0.1.0_aces-v1.3_ocio-v2.1.2dev.ocio'
    """

    return ("studio-config-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio").format(
        **dependency_versions(config_mapping_file_path)
    )


def config_name_studio(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
):
    """
    Generate the ACES* Studio *OpenColorIO* config name.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_studio()  # doctest: +SKIP
    'Academy Color Encoding System - Studio Config [COLORSPACES v0.1.0] \
[ACES v1.3] [OCIO v2.1.2dev]'
    """

    return (
        "Academy Color Encoding System - Studio Config "
        "[COLORSPACES {colorspaces}] "
        "[ACES {aces}] "
        "[OCIO {ocio}]"
    ).format(**dependency_versions(config_mapping_file_path))


def config_description_studio(
    config_mapping_file_path=PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
):
    """
    Generate the ACES* Studio *OpenColorIO* config description.

    Parameters
    ----------
    config_mapping_file_path : str, optional
        Path to the *CSV* mapping file.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config description.
    """

    name = config_name_studio(config_mapping_file_path)
    underline = "-" * len(name)
    description = (
        'This "OpenColorIO" config is geared toward studios requiring a config '
        "that includes a wide variety of camera colorspaces, displays and "
        "looks."
    )
    timestamp = (
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
        f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.'
    )

    return "\n".join([name, underline, "", description, "", timestamp])


def generate_config_studio(
    data=None,
    config_name=None,
    validate=True,
    describe=ColorspaceDescriptionStyle.SHORT_UNION,
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
        f'Generating "{config_name_studio(config_mapping_file_path)}" config...'
    )

    scheme = validate_method(scheme, ["Legacy", "Modern 1"])

    if data is None:
        _config, data = generate_config_cg(
            describe=describe,
            scheme=scheme,
            additional_data=True,
        )

    data.name = re.sub(
        r"\.ocio$", "", config_basename_studio(config_mapping_file_path)
    )
    data.description = config_description_studio(config_mapping_file_path)
    config = generate_config(data, config_name, validate)

    logger.info(
        f'"{config_name_studio(config_mapping_file_path)}" config generation '
        f"complete!"
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
        "studio",
    )

    logging.info(f'Using "{build_directory}" build directory...')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    config_basename = config_basename_studio()
    config, data = generate_config_studio(
        config_name=os.path.join(build_directory, config_basename),
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
        logging.critical(error)
