# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Config Profile Version
==================================

Defines various objects related to *OpenColorIO* config profile version:

-   :class:`opencolorio_config_aces.ProfileVersion`
-   :attr:`opencolorio_config_aces.PROFILE_VERSION_DEFAULT`
-   :attr:`opencolorio_config_aces.SUPPORTED_PROFILE_VERSIONS`
"""

from distutils.version import StrictVersion

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "ProfileVersion",
    "PROFILE_VERSION_DEFAULT",
]


class ProfileVersion(StrictVersion):
    """
    Define the data container for an *OpenColorIO* config profile version.

    Parameters
    ----------
    major : int, optional
        Major version number.
    minor : int, optional
        Minor version number.

    Attributes
    ----------
    major
    minor

    Examples
    --------
    >>> profile_version = ProfileVersion()
    >>> profile_version.parse("2.0")
    >>> profile_version.major
    2
    >>> profile_version.minor
    0
    >>> profile_version_1 = PROFILE_VERSION_DEFAULT
    >>> profile_version_2 = ProfileVersion(2, 1)
    >>> profile_version_2 > profile_version_1
    True
    """

    def __init__(self, major=None, minor=None):
        if None not in (major, minor):
            self.parse(f"{major}.{minor}")

    @property
    def major(self):
        """
        Getter property for the major version number.

        Returns
        -------
        int
            Major version number.

        Notes
        -----
        -   This property is read only.
        """

        return self.version[0]

    @property
    def minor(self):
        """
        Getter property for the minor version number.

        Returns
        -------
        int
            Minor version number.

        Notes
        -----
        -   This property is read only.
        """

        return self.version[1]


PROFILE_VERSION_DEFAULT = ProfileVersion(2, 0)
"""
Default *OpenColorIO* profile version.

PROFILE_VERSION_DEFAULT : ProfileVersion
"""

SUPPORTED_PROFILE_VERSIONS = [
    ProfileVersion(i, j) for i in range(2, 3) for j in range(1, 4)
]

"""
Supported *OpenColorIO* profile versions.

SUPPORTED_PROFILE_VERSIONS : list
"""
