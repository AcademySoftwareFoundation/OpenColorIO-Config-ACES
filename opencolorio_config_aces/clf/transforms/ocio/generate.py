# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*OpenColorIO* CLF Transforms Generation
=======================================

Defines procedures for generating specific *Common LUT Format* (CLF)
transforms from the OpenColorIO project.
"""

import PyOpenColorIO as ocio
from pathlib import Path

from opencolorio_config_aces.clf import (
    create_conversion_matrix,
    create_gamma,
    generate_clf
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = ["generate_clf_input", "generate_clf_utility"]

THIS_DIR = Path(__file__).parent.resolve()

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:OCIO:"
TF_ID_SUFFIX = ":1.0"

CLF_PREFIX = "OCIO."
CLF_SUFFIX = ".clf"


def generate_clf_input():
    """Generate OCIO Input CLF transforms."""

    dest_dir = THIS_DIR / "input"
    if not dest_dir.exists():
        dest_dir.mkdir()

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "sRGB"),
                create_gamma("sRGB"),
            ]
        ),
        TF_ID_PREFIX + "Input:AP0_to_Rec709-sRGB" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - sRGB",
        dest_dir / (CLF_PREFIX + "Input.AP0_to_Rec709-sRGB" + CLF_SUFFIX),
        "ACES2065-1",
        "sRGB",
    )


def generate_clf_utility():
    """Generate OCIO Utility CLF transforms."""

    dest_dir = THIS_DIR / "utility"
    if not dest_dir.exists():
        dest_dir.mkdir()

    generate_clf(
        ocio.GroupTransform(transforms=[create_gamma(2.4)]),
        TF_ID_PREFIX + "Utility:Linear_to_Rec1886" + TF_ID_SUFFIX,
        "Linear to Rec.1886",
        dest_dir / (CLF_PREFIX + "Utility.Linear_to_Rec1886" + CLF_SUFFIX),
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    generate_clf(
        ocio.GroupTransform(transforms=[create_gamma("sRGB")]),
        TF_ID_PREFIX + "Utility:Linear_to_sRGB" + TF_ID_SUFFIX,
        "Linear to sRGB",
        dest_dir / (CLF_PREFIX + "Utility.Linear_to_sRGB" + CLF_SUFFIX),
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "P3-D65")]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_P3-D65-Linear" + TF_ID_SUFFIX,
        "AP0 to P3-D65 - Linear",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_P3-D65-Linear" + CLF_SUFFIX),
        "ACES2065-1",
        "linear P3 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.2020")
            ]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_Rec2020-Linear" + TF_ID_SUFFIX,
        "AP0 to Rec.2020 - Linear",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_Rec2020-Linear" + CLF_SUFFIX),
        "ACES2065-1",
        "linear Rec.2020 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "ITU-R BT.709")]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_Rec709-Linear" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Linear",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_Rec709-Linear" + CLF_SUFFIX),
        "ACES2065-1",
        "linear Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(1.8),
            ]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_Rec709-Gamma1.8" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 1.8",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_Rec709-Gamma1.8" + CLF_SUFFIX),
        "ACES2065-1",
        "1.8 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.2),
            ]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_Rec709-Gamma2.2" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 2.2",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_Rec709-Gamma2.2" + CLF_SUFFIX),
        "ACES2065-1",
        "2.2 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.4),
            ]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_Rec709-Gamma2.4" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 2.4",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_Rec709-Gamma2.4" + CLF_SUFFIX),
        "ACES2065-1",
        "2.4 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ACEScg"),
                create_gamma(2.2),
            ]
        ),
        TF_ID_PREFIX + "Utility:AP0_to_AP1-Gamma2.2" + TF_ID_SUFFIX,
        "AP0 to AP1 - Gamma 2.2",
        dest_dir / (CLF_PREFIX + "Utility.AP0_to_AP1-Gamma2.2" + CLF_SUFFIX),
        "ACES2065-1",
        "2.2 gamma-corrected AP1 primaries, D60 white point",
    )


if __name__ == "__main__":
    generate_clf_input()
    generate_clf_utility()
