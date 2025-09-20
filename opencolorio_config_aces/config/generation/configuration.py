# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Build Configuration
======================================

Defines various objects related to *OpenColorIO* config build configuration:

-   :attr:`opencolorio_config_aces.BuildConfiguration`
-   :attr:`opencolorio_config_aces.BUILD_CONFIGURATIONS`
-   :attr:`opencolorio_config_aces.BUILD_VARIANT_FILTERERS`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from semver import Version

from opencolorio_config_aces.config.generation import PROFILE_VERSION_DEFAULT
from opencolorio_config_aces.utilities import slugify

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = ["BuildConfiguration", "BUILD_CONFIGURATIONS", "BUILD_VARIANT_FILTERERS"]


@dataclass
class BuildConfiguration:
    """
    Define an *OpenColorIO* config build configuration.

    Parameters
    ----------
    aces : :class:`semver.Version`, optional
        *aces-dev* version.
    colorspaces : :class:`semver.Version`, optional
        *OpenColorIO* colorspaces version.
    ocio : :class:`semver.Version`, optional
        *OpenColorIO* profile version.
    variant : str, optional
        Config variant, introduced to support ACES 2.0 to partition the D60
        views from the D65 views.
    """

    aces: Version = field(default_factory=lambda: Version(0))
    colorspaces: Version = field(default_factory=lambda: Version(0))
    ocio: Version = field(default_factory=lambda: PROFILE_VERSION_DEFAULT)
    variant: str = field(default_factory=lambda: "")

    def compact_fields(self) -> dict[str, str]:
        """
        Return the compact fields.

        Returns
        -------
        :class:`dict`
            Compact fields.
        """

        return {
            "aces": f"v{self.aces.major}.{self.aces.minor}",
            "colorspaces": f"v{self.colorspaces}",
            "ocio": f"v{self.ocio.major}.{self.ocio.minor}",
            "variant": f"{slugify(self.variant)}" if self.variant else "",
        }

    def extended_fields(self) -> dict[str, str]:
        """
        Return the extended fields.

        Returns
        -------
        :class:`dict`
            Extended fields.
        """

        return {
            **self.compact_fields(),
            "variant": f"({self.variant})" if self.variant else "",
        }


BUILD_CONFIGURATIONS: list[BuildConfiguration] = [
    BuildConfiguration(
        aces=Version(2, 0),
        colorspaces=Version(4, 0, 0),
        ocio=Version(2, 5),
        variant="",
    ),
    BuildConfiguration(
        aces=Version(2, 0),
        colorspaces=Version(4, 0, 0),
        ocio=Version(2, 5),
        variant="D60 Views",
    ),
    BuildConfiguration(
        aces=Version(2, 0),
        colorspaces=Version(4, 0, 0),
        ocio=Version(2, 5),
        variant="All Views",
    ),
]
"""
Build configurations.

BUILD_CONFIGURATIONS : list
"""

BUILD_VARIANT_FILTERERS: dict[str, dict[str, dict[str, Any]]] = {
    "": {
        "any": {},
        "all": {
            "view_transform_filterers": [lambda x: "D60 in" not in x["name"]],
            "shared_view_filterers": [lambda x: "D60 in" not in x["view_transform"]],
            "view_filterers": [lambda x: "D60 in" not in x["view"]],
            "amf_component_display_filterers": [
                lambda x: "-D60_" not in x["transform_id"]
            ],
        },
    },
    "D60 Views": {
        "any": {},
        "all": {
            "view_transform_filterers": [
                lambda x: "D60 in" in x["name"]
                or x["name"] == "Un-tone-mapped"
                or x["name"] == "Raw"
            ],
            "shared_view_filterers": [
                lambda x: "D60 in" in x["view_transform"]
                or x["view_transform"] == "Un-tone-mapped"
                or x["view_transform"] == "Raw"
            ],
            "view_filterers": [
                lambda x: "D60 in" in x["view"]
                or x["view"] == "Un-tone-mapped"
                or x["view"] == "Raw"
            ],
            "amf_component_display_filterers": [lambda x: "-D60_" in x["transform_id"]],
        },
    },
    "All Views": {"any": {}, "all": {}},
}
"""
Build variant filterers.

BUILD_VARIANT_FILTERERS : dict
"""
