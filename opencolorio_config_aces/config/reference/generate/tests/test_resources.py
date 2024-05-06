# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Defines the unit tests for the
:mod:`opencolorio_config_aces.config.reference.generate` module resources.
"""


import unittest

import requests

from opencolorio_config_aces.config.reference.generate.config import (
    PATH_TRANSFORMS_MAPPING_FILE_REFERENCE,
    URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE,
)

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
    Define the *aces-dev* reference *OpenColorIO* config resources unit tests
    methods.
    """

    def test_csv_mapping_file(self):
        """Test the *CSV* mapping file."""

        csv_local_path = PATH_TRANSFORMS_MAPPING_FILE_REFERENCE

        with open(str(csv_local_path)) as csv_local_file:
            csv_local_content = csv_local_file.read()

        csv_remote_content = requests.get(
            URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE, timeout=60
        ).text

        self.assertMultiLineEqual(
            "\n".join(csv_remote_content.splitlines()),
            "\n".join(csv_local_content.splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
