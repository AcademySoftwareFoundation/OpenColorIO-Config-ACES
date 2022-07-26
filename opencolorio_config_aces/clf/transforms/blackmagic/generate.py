# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Blackmagic* CLF Transforms Generation
=======================================

Defines procedures for generating Blackmagic *Common LUT Format* (CLF)
transforms for the OpenColorIO project.
"""

import PyOpenColorIO as ocio
from pathlib import Path
import math

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
    "main",
]

DEST_DIR = Path(__file__).parent.resolve() / "input"

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def _generate_clf_bmdfilm():
    """Make the CLF file for BMDFilm_WideGamut_Gen5 plus matrix/curve CLFs."""

    # Based on the document "Blackmagic Generation 5 Color Technical Reference.pdf"
    # dated May 2021.  The resulting CLF was reviewed by Blackmagic.

    cut = 0.005
    a = 0.08692876065491224
    b = 0.005494072432257808
    c = 0.5300133392291939
    # d = 8.283605932402494
    # e = 0.09246575342465753

    BASE = math.e
    LIN_SB = cut
    LOG_SLP = a
    LOG_OFF = c
    LIN_SLP = 1.0
    LIN_OFF = b

    # It is not necessary to set the linear_slope value in the LogCameraTransform
    # since the values automatically calculated by OCIO match the published values
    # to within double precision. This may be verified using the following formulas:
    # LINEAR_SLOPE =
    #     LOG_SLP * LIN_SLP / ( (LIN_SLP * LIN_SB + LIN_OFF) * math.log(BASE) )
    # LOG_SB = LOG_SLP * math.log(LIN_SLP * LIN_SB + LIN_OFF) + LOG_OFF
    # LINEAR_OFFSET = LOG_SB - LINEAR_SLOPE * LIN_SB
    # print(LINEAR_SLOPE, LINEAR_OFFSET)
    # This prints 8.283605932402494 0.09246575342465779, which is sufficiently close
    # to the specified d and e above.

    lct = ocio.LogCameraTransform(
        base=BASE,
        linSideBreak=[LIN_SB] * 3,
        logSideSlope=[LOG_SLP] * 3,
        logSideOffset=[LOG_OFF] * 3,
        linSideSlope=[LIN_SLP] * 3,
        linSideOffset=[LIN_OFF] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix(
        "Blackmagic Wide Gamut", "ACES2065-1", "CAT02"
    )

    # Taking the color space name and IDT transform ID from:
    #   https://github.com/ampas/aces-dev/pull/126/files
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        "IDT.BlackmagicDesign.BMDFilm_WideGamut_Gen5.a1.v1"
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
        + "BlackmagicDesign:Input:BMDFilm_WideGamut_Gen5_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Blackmagic Film Wide Gamut (Gen 5) to ACES2065-1",
        DEST_DIR / ("BMDFilm-WideGamut-Gen5_to_ACES2065-1" + CLF_SUFFIX),
        "Blackmagic Film Wide Gamut (Gen 5)",
        "ACES2065-1",
        aces_transform_id,
    )

    # Generate transform for primaries only.

    generate_clf(
        ocio.GroupTransform([mtx]),
        TF_ID_PREFIX
        + "BlackmagicDesign:Input:Linear_BMD_WideGamut_Gen5_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear Blackmagic Wide Gamut (Gen 5) to ACES2065-1",
        DEST_DIR / ("Linear-BMD-WideGamut-Gen5_to_ACES2065-1" + CLF_SUFFIX),
        "Linear Blackmagic Wide Gamut (Gen 5)",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    generate_clf(
        ocio.GroupTransform([lct]),
        TF_ID_PREFIX
        + "BlackmagicDesign:Input:BMDFilm_Gen5_Log_to_Linear"
        + TF_ID_SUFFIX,
        "Blackmagic Film (Gen 5) Log to Linear Curve",
        DEST_DIR / ("BMDFilm-WideGamut-Gen5-Curve" + CLF_SUFFIX),
        "Blackmagic Film (Gen 5) Log",
        "Blackmagic Film (Gen 5) Linear",
        None,
    )


def _generate_clf_davinci():
    """Make the CLF file for DaVinci Intermediate Wide Gamut plus matrix/curve CLFs."""

    # Based on the document "DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf"
    # dated 2021-07-31.  The resulting CLF was reviewed by Blackmagic.

    cut = 0.00262409
    a = 0.0075
    b = 7.0
    c = 0.07329248
    m = 10.44426855

    BASE = 2.0
    LIN_SB = cut
    LOG_SLP = c
    LOG_OFF = c * b
    LIN_SLP = 1.0
    LIN_OFF = a

    # The linear slope that would be calculated by OCIO based on continuity of the
    # derivatives is 10.444266836 vs. the published value of 10.44426855.  Based on
    # input from Blackmagic, it is preferable to set the linear slope value explicitly.
    LINEAR_SLOPE = m

    lct = ocio.LogCameraTransform(
        base=BASE,
        linSideBreak=[LIN_SB] * 3,
        logSideSlope=[LOG_SLP] * 3,
        logSideOffset=[LOG_OFF] * 3,
        linSideSlope=[LIN_SLP] * 3,
        linSideOffset=[LIN_OFF] * 3,
        linearSlope=[LINEAR_SLOPE] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix("DaVinci Wide Gamut", "ACES2065-1", "CAT02")

    # This transform is not yet part of aces-dev, but an ID will be needed for AMF.
    # Proposing the following ID:
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        "ACEScsc.Academy.DaVinci_Intermediate_WideGamut_to_ACES.a1.v1"
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
        + "BlackmagicDesign:Input:DaVinci_Intermediate_WideGamut_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "DaVinci Intermediate Wide Gamut to ACES2065-1",
        DEST_DIR
        / ("DaVinci-Intermediate-WideGamut_to_ACES2065-1" + CLF_SUFFIX),
        "DaVinci Intermediate Wide Gamut",
        "ACES2065-1",
        aces_transform_id,
    )

    # Generate transform for primaries only.

    generate_clf(
        ocio.GroupTransform([mtx]),
        TF_ID_PREFIX
        + "BlackmagicDesign:Input:Linear_DaVinci_WideGamut_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear DaVinci Wide Gamut to ACES2065-1",
        DEST_DIR / ("Linear-DaVinci-WideGamut_to_ACES2065-1" + CLF_SUFFIX),
        "Linear DaVinci Wide Gamut",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    generate_clf(
        ocio.GroupTransform([lct]),
        TF_ID_PREFIX
        + "BlackmagicDesign:Input:DaVinci_Intermediate_Log_to_Linear"
        + TF_ID_SUFFIX,
        "DaVinci Intermediate Log to Linear Curve",
        DEST_DIR / ("DaVinci-Intermediate-Curve" + CLF_SUFFIX),
        "DaVinci Intermediate Log",
        "DaVinci Intermediate Linear",
        None,
    )


def main():
    """Make all the Blackmagic CLFs."""

    if not DEST_DIR.exists():
        DEST_DIR.mkdir()

    _generate_clf_bmdfilm()
    _generate_clf_davinci()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
