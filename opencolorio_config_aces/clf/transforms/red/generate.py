# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*RED* CLF Transforms Generation
=====================================

Defines procedures for generating RED *Common LUT Format* (CLF)
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
    "generate_red",
]

DEST_DIR = Path(__file__).parent.resolve() / "input"

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def generate_red():
    """Make the CLF file for RED Log3G10 REDWideGamutRGB plus matrix/curve CLFs."""

    # Based on the document "White Paper on REDWIDEGAMUTRGB and LOG3G10.pdf"
    # dated November 2017.  The resulting CLF was reviewed by RED.

    if not DEST_DIR.exists():
        DEST_DIR.mkdir()

    linSideSlope = 155.975327
    linSideOffset = 0.01 * linSideSlope + 1.0
    logSideSlope = 0.224282
    logSideOffset = 0.0
    linSideBreak = -0.01
    base = 10.0

    lct = ocio.LogCameraTransform(
        base=base,
        linSideBreak=[linSideBreak] * 3,
        logSideSlope=[logSideSlope] * 3,
        logSideOffset=[logSideOffset] * 3,
        linSideSlope=[linSideSlope] * 3,
        linSideOffset=[linSideOffset] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix("REDWideGamutRGB", "ACES2065-1", "Bradford")

    # Generate full transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                lct,
                mtx,
            ]
        ),
        TF_ID_PREFIX + "RED:Input:Log3G10-RWG_to_ACES2065-1" + TF_ID_SUFFIX,
        "RED Log3G10 REDWideGamutRGB to ACES2065-1",
        DEST_DIR / ("Log3G10-RWG_to_ACES2065-1" + CLF_SUFFIX),
        "RED Log3G10 REDWideGamutRGB",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.RED.Log3G10_RWG.a1.v1",
    )

    # Generate transform for primaries only.

    generate_clf(
        ocio.GroupTransform([mtx]),
        TF_ID_PREFIX
        + "RED:Input:Linear-REDWideGamutRGB_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear REDWideGamutRGB to ACES2065-1",
        DEST_DIR / ("Linear-REDWideGamutRGB_to_ACES2065-1" + CLF_SUFFIX),
        "Linear REDWideGamutRGB",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    generate_clf(
        ocio.GroupTransform([lct]),
        TF_ID_PREFIX + "RED:Input:Log3G10_Log_to_Linear" + TF_ID_SUFFIX,
        "RED Log3G10 Log to Linear Curve",
        DEST_DIR / ("Log3G10-Curve" + CLF_SUFFIX),
        "RED Log3G10 (SUP v3) Log (arbitrary primaries)",
        "RED Log3G10 (SUP v3) Linear (arbitrary primaries)",
        None,
    )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(generate_red())
