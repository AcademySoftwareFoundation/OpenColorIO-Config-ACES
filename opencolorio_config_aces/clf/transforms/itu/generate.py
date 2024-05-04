# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ITU-R* CLF Transforms Generation
=================================

Defines procedures for generating specific *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_itu`
"""

from pathlib import Path

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
    format_clf_transform_id,
    gamma_transform,
    generate_clf_transform,
    matrix_RGB_to_RGB_transform,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "FAMILY",
    "GENUS",
    "VERSION",
    "generate_clf_transforms_itu",
]

FAMILY = "ITU"
"""
*CLF* transforms family.
"""

GENUS = "Utility"
"""
*CLF* transforms genus.
"""

VERSION = "1.0"
"""
*CLF* transforms version.
"""


def generate_clf_transforms_itu(output_directory):
    """Generate OCIO Utility CLF transforms."""

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    name = "AP0_to_Camera_Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.709"),
            gamma_transform("Rec709"),
        ],
        clf_transform_id,
        "AP0 to Camera Rec.709",
        "ACES2065-1",
        "Rec.709 camera OETF Rec.709 primaries, D65 white point",
    )

    name = "Linear_to_Rec709-Curve"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [gamma_transform("Rec709")],
        clf_transform_id,
        "Linear to Rec.709",
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    return clf_transforms


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve()

    generate_clf_transforms_itu(output_directory / "utility")
