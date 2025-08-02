# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Version Utilities
====================================

Defines various objects related to *OpenColorIO* config version handling:

-   :attr:`opencolorio_config_aces.PROFILE_VERSION_DEFAULT`
-   :attr:`opencolorio_config_aces.PROFILE_VERSIONS`
"""

from __future__ import annotations

from semver import Version

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "PROFILE_VERSION_DEFAULT",
    "PROFILE_VERSIONS",
]


PROFILE_VERSION_DEFAULT: Version = Version(2, 0)
"""
Default *OpenColorIO* profile version.

PROFILE_VERSION_DEFAULT : Version
"""

PROFILE_VERSIONS: list[Version] = [
    Version(i, j) for i in range(2, 3) for j in range(1, 5)
]

"""
*OpenColorIO* profile versions.

PROFILE_VERSIONS : list
"""
