# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Defines the unit tests for the
:mod:`opencolorio_config_aces.config.cg.generate` module resources.
"""


import unittest
import urllib.request

from pathlib import Path

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "TestConfigResources",
]


class TestConfigResources(unittest.TestCase):
    """
    Define the *ACES* Computer Graphics (CG) *OpenColorIO* config resources
    unit tests methods.
    """

    def test_csv_mapping_file(self):
        """Test the *CSV* mapping file."""

        csv_local_path = (
            Path(__file__).parents[0]
            / ".."
            / "resources"
            / "OpenColorIO-Config-ACES _CG_ Transforms - CG Config - Mapping.csv"
        )

        with open(str(csv_local_path)) as csv_local_file:
            csv_local_content = csv_local_file.read()

        csv_remote_url = (
            "https://docs.google.com/spreadsheets/d/"
            "1DqxmtZpnhL_9N1wayvcW0y3bZoHRom7A1c58YLlr89g/"
            "export?format=csv&gid=609660164"
        )

        csv_remote_content = (
            urllib.request.urlopen(csv_remote_url).read().decode("utf-8")
        )

        self.assertMultiLineEqual(
            "\n".join(csv_remote_content.splitlines()),
            "\n".join(csv_local_content.splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
