# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Version Utilities
====================================

Defines various objects related to *OpenColorIO* config version handling:

-   :attr:`opencolorio_config_aces.PROFILE_VERSION_DEFAULT`
-   :attr:`opencolorio_config_aces.PROFILE_VERSIONS`
-   :attr:`opencolorio_config_aces.DependencyVersions`
-   :attr:`opencolorio_config_aces.DEPENDENCY_VERSIONS`
"""

from semver import Version
from dataclasses import dataclass, field

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "PROFILE_VERSION_DEFAULT",
    "PROFILE_VERSIONS",
    "DependencyVersions",
]


PROFILE_VERSION_DEFAULT = Version(2, 0)
"""
Default *OpenColorIO* profile version.

PROFILE_VERSION_DEFAULT : Version
"""

PROFILE_VERSIONS = [Version(i, j) for i in range(2, 3) for j in range(1, 5)]

"""
*OpenColorIO* profile versions.

PROFILE_VERSIONS : list
"""


@dataclass
class DependencyVersions:
    """
    Define the container used for the dependency versions.

    Parameters
    ----------
    aces : :class:`semver.Version`, optional
        *aces-dev* version.
    colorspaces : :class:`semver.Version`, optional
        *OpenColorIO* colorspaces version.
    ocio : :class:`semver.Version`, optional
        *OpenColorIO* profile version.
    """

    aces: Version = field(default_factory=lambda: Version(0))
    colorspaces: Version = field(default_factory=lambda: Version(0))
    ocio: Version = field(default_factory=lambda: PROFILE_VERSION_DEFAULT)

    def to_regularised_versions(self):
        """
        Return the regularised dependency versions.

        Returns
        -------
        :class:`dict`
            Regularised dependency versions.
        """

        return {
            "aces": f"v{self.aces.major}.{self.aces.minor}",
            "colorspaces": f"v{self.colorspaces}",
            "ocio": f"v{self.ocio.major}.{self.ocio.minor}",
        }


DEPENDENCY_VERSIONS = [
    DependencyVersions(
        aces=Version(1, 3),
        colorspaces=Version(2, 0, 0),
        ocio=Version(2, 1),
    ),
    DependencyVersions(
        aces=Version(1, 3),
        colorspaces=Version(2, 0, 0),
        ocio=Version(2, 2),
    ),
    DependencyVersions(
        aces=Version(1, 3),
        colorspaces=Version(2, 1, 0),
        ocio=Version(2, 3),
    ),
    DependencyVersions(
        aces=Version(1, 3),
        colorspaces=Version(2, 1, 0),
        ocio=Version(2, 4),
    ),
]
"""
Dependency versions.

DEPENDENCY_VERSIONS : list
"""
