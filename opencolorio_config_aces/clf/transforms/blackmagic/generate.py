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
    "generate_clf_bmdfilm",
    "generate_clf_davinci",
]

THIS_DIR = Path(__file__).parent.resolve()

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def generate_clf_bmdfilm():
    """Make the CLF file for BMDFilm_WideGamut_Gen5."""

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
        linSideBreak=[LIN_SB, LIN_SB, LIN_SB],
        logSideSlope=[LOG_SLP, LOG_SLP, LOG_SLP],
        logSideOffset=[LOG_OFF, LOG_OFF, LOG_OFF],
        linSideSlope=[LIN_SLP, LIN_SLP, LIN_SLP],
        linSideOffset=[LIN_OFF, LIN_OFF, LIN_OFF],
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix(
        "Blackmagic Wide Gamut", "ACES2065-1", "CAT02"
    )

    # Taking the color space name and IDT transform ID from:
    #   https://github.com/ampas/aces-dev/pull/126/files
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        + "IDT.BlackmagicDesign.BMDFilm_WideGamut_Gen5.a1.v1"
    )

    dest_dir = THIS_DIR / "input"
    if not dest_dir.exists():
        dest_dir.mkdir()

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
        dest_dir / ("BMDFilm-WideGamut-Gen5_to_ACES2065-1" + CLF_SUFFIX),
        "Blackmagic Film Wide Gamut (Gen 5)",
        "ACES2065-1",
        aces_transform_id,
    )


def generate_clf_davinci():
    """Make the CLF file for DaVinci Intermediate Wide Gamut."""

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
        linSideBreak=[LIN_SB, LIN_SB, LIN_SB],
        logSideSlope=[LOG_SLP, LOG_SLP, LOG_SLP],
        logSideOffset=[LOG_OFF, LOG_OFF, LOG_OFF],
        linSideSlope=[LIN_SLP, LIN_SLP, LIN_SLP],
        linSideOffset=[LIN_OFF, LIN_OFF, LIN_OFF],
        linearSlope=[LINEAR_SLOPE, LINEAR_SLOPE, LINEAR_SLOPE],
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = create_conversion_matrix("DaVinci Wide Gamut", "ACES2065-1", "CAT02")

    # This transform is not yet part of aces-dev, but an ID will be needed for AMF.
    # Proposing the following ID:
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        + "ACEScsc.Academy.DaVinci_Intermediate_WideGamut_to_ACES.a1.v1"
    )

    dest_dir = THIS_DIR / "input"
    if not dest_dir.exists():
        dest_dir.mkdir()

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
        dest_dir
        / ("DaVinci-Intermediate-WideGamut_to_ACES2065-1" + CLF_SUFFIX),
        "DaVinci Intermediate Wide Gamut",
        "ACES2065-1",
        aces_transform_id,
    )


def main():
    generate_clf_bmdfilm()
    generate_clf_davinci()
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
