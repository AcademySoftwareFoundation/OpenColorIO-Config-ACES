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
from typing import Any

import PyOpenColorIO as ocio

from opencolorio_config_aces.config.cg import (
    generate_config_cg,
)
from opencolorio_config_aces.config.generation import (
    BUILD_CONFIGURATIONS,
    BUILD_VARIANT_FILTERERS,
    BuildConfiguration,
    generate_config,
)
from opencolorio_config_aces.config.generation.common import ConfigData
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
    "main",
]

LOGGER: logging.Logger = logging.getLogger(__name__)

URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO: str = (
    "https://docs.google.com/spreadsheets/d/"
    "1PXjTzBVYonVFIceGkLDaqcEJvKR6OI63DwZX0aajl3A/"
    "export?format=csv&gid=1155125238"
)
"""
URL to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO : unicode
"""

PATH_TRANSFORMS_MAPPING_FILE_STUDIO: Path = next(
    (Path(__file__).parents[0] / "resources").glob("*Mapping.csv")
)
"""
Path to the *ACES* *CTL* transforms to *OpenColorIO* colorspaces mapping file.

PATH_TRANSFORMS_MAPPING_FILE_STUDIO : unicode
"""


def config_basename_studio(build_configuration: BuildConfiguration) -> str:
    """
    Generate the ACES* Studio *OpenColorIO* config basename, i.e., the filename
    devoid of directory affixe.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config basename.

    Examples
    --------
    >>> config_basename_studio(BuildConfiguration())
    'studio-config-v0.0.0_aces-v0.0_ocio-v2.0.ocio'
    """

    return (
        ("studio-config-{variant}-{colorspaces}_aces-{aces}_ocio-{ocio}.ocio")
        .format(**build_configuration.compact_fields())
        .replace("--", "-")
    )


def config_name_studio(build_configuration: BuildConfiguration) -> str:
    """
    Generate the ACES* Studio *OpenColorIO* config name.

    Parameters
    ----------
    build_configuration: BuildConfiguration
        Build configuration.

    Returns
    -------
    str
        ACES* Studio *OpenColorIO* config name.

    Examples
    --------
    >>> config_name_studio(BuildConfiguration())
    'Academy Color Encoding System - Studio Config [COLORSPACES v0.0.0] \
[ACES v0.0] [OCIO v2.0]'
    """

    return (
        (
            "Academy Color Encoding System - Studio Config {variant}"
            "[COLORSPACES {colorspaces}] "
            "[ACES {aces}] "
            "[OCIO {ocio}]"
        )
        .format(**build_configuration.extended_fields())
        .replace(")[", ") [")
    )


def config_description_studio(
    build_configuration: BuildConfiguration,
    describe: DescriptionStyle = DescriptionStyle.SHORT_UNION,
) -> str:
    """
    Generate the ACES* Studio *OpenColorIO* config description.

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
        ACES* Studio *OpenColorIO* config description.
    """

    name = config_name_studio(build_configuration)

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
    data: ConfigData | None = None,
    config_name: str | Path | None = None,
    build_configuration: BuildConfiguration = BuildConfiguration(),
    validate: bool = True,
    describe: DescriptionStyle = DescriptionStyle.SHORT_UNION,
    config_mapping_file_path: Path = PATH_TRANSFORMS_MAPPING_FILE_STUDIO,
    scheme: str = "Modern 1",
    additional_filterers: dict[str, dict[str, list[Any]]] | None = None,
    additional_data: bool = False,
) -> ocio.Config | tuple[ocio.Config, ConfigData, Any, Any, Any]:
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

    LOGGER.info(
        'Generating "%s" config...',
        config_name_studio(build_configuration),
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
            build_configuration=build_configuration,
            describe=describe,
            scheme=scheme,
            config_mapping_file_path=config_mapping_file_path,
            additional_filterers=additional_filterers,
            additional_data=True,
        )

    data.name = re.sub(  # pyright: ignore
        r"\.ocio$",
        "",
        config_basename_studio(build_configuration),
    )
    data.description = config_description_studio(  # pyright: ignore
        build_configuration, describe
    )
    config = generate_config(data, config_name, validate)  # pyright: ignore

    LOGGER.info(
        '"%s" config generation complete!',
        config_name_studio(build_configuration),
    )

    if additional_data:
        return config, data, ctl_transforms, clf_transforms, amf_components
    else:
        return config


def main(build_directory: Path) -> int:
    """
    Define the main entry point for the generation of all the *ACES* Studio
    *OpenColorIO* config versions and variants.

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
        config_basename = config_basename_studio(build_configuration)
        (
            config,
            data,
            ctl_transforms,
            clf_transforms,
            amf_components,
        ) = generate_config_studio(
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

    sys.exit(main((ROOT_BUILD_DEFAULT / "config" / "aces" / "studio").resolve()))
