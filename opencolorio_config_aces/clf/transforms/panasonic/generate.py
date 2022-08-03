# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Panasonic* CLF Transforms Generation
=====================================

Defines procedures for generating Panasonic *Common LUT Format* (CLF)
transforms for the OpenColorIO project.
"""

import PyOpenColorIO as ocio
from pathlib import Path

from opencolorio_config_aces.clf import (
    create_conversion_matrix,
    generate_clf,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "generate_panasonic",
]

DEST_DIR = Path(__file__).parent.resolve() / "input"

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def generate_panasonic():
    """Make the CLF file for V-Log - V-Gamut plus matrix/curve CLFs."""

    # Based on the document "VARICAM_V-Log_V-Gamut.pdf" dated November 28, 2014.
    # The resulting CLF was reviewed by Panasonic.

    if not DEST_DIR.exists():
        DEST_DIR.mkdir()

    cut1 = 0.01
    b = 0.00873
    c = 0.241514
    d = 0.598206

    LIN_SLP = 1.0
    LIN_OFF = b
    LOG_SLP = c
    LOG_OFF = d
    LIN_SB = cut1
    BASE = 10.0

    lct = ocio.LogCameraTransform(
        base=BASE,
        linSideBreak=[LIN_SB] * 3,
        logSideSlope=[LOG_SLP] * 3,
        logSideOffset=[LOG_OFF] * 3,
        linSideSlope=[LIN_SLP] * 3,
        linSideOffset=[LIN_OFF] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix("V-Gamut", "ACES2065-1", "Bradford")

    # Using the CSC ID here because there is a slight discrepancy between the matrix
    # coefficients of the CSC and IDT CTL and the CLF matches the CSC transform.
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        "ACEScsc.Academy.VLog_VGamut_to_ACES.a1.1.0"
    )

    # Generate full transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                lct,
                mtx,
            ]
        ),
        TF_ID_PREFIX
        + "Panasonic:Input:VLog-VGamut_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Panasonic V-Log - V-Gamut (SUP v3) to ACES2065-1",
        DEST_DIR / ("VLog-VGamut_to_ACES2065-1" + CLF_SUFFIX),
        "Panasonic V-Log - V-Gamut (SUP v3)",
        "ACES2065-1",
        aces_transform_id,
    )

    # Generate transform for primaries only.

    generate_clf(
        ocio.GroupTransform([mtx]),
        TF_ID_PREFIX
        + "Panasonic:Input:Linear-VGamut_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear Panasonic V-Gamut (SUP v3) to ACES2065-1",
        DEST_DIR / ("Linear-VGamut_to_ACES2065-1" + CLF_SUFFIX),
        "Linear Panasonic V-Gamut (SUP v3)",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    generate_clf(
        ocio.GroupTransform([lct]),
        TF_ID_PREFIX + "Panasonic:Input:VLog_Log_to_Linear" + TF_ID_SUFFIX,
        "Panasonic V-Log (SUP v3) Log to Linear Curve",
        DEST_DIR / ("VLog-Curve" + CLF_SUFFIX),
        "Panasonic V-Log (SUP v3) Log (arbitrary primaries)",
        "Panasonic V-Log (SUP v3) Linear (arbitrary primaries)",
        None,
    )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(generate_panasonic())
