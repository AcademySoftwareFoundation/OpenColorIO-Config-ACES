# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Sony* CLF Transforms Generation
================================

Defines procedures for generating Sony *Common LUT Format* (CLF)
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
    "generate_sony",
]

DEST_DIR = Path(__file__).parent.resolve() / "input"

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:"
TF_ID_SUFFIX = ":1.0"

CLF_SUFFIX = ".clf"


def _build_slog3_curve():
    """ Build the Log transform for the S-Log3 curve. """
    linSideSlope  = 1. / (0.18 + 0.01)
    linSideOffset = 0.01 / (0.18 + 0.01)
    logSideSlope  = 261.5 / 1023.
    logSideOffset = 420. / 1023.
    linSideBreak  = 0.01125000
    linearSlope   = ( (171.2102946929 - 95.) / 0.01125000) / 1023.
    base          = 10.

    lct = ocio.LogCameraTransform(
        base=base,
        linSideBreak=[linSideBreak] * 3,
        logSideSlope=[logSideSlope] * 3,
        logSideOffset=[logSideOffset] * 3,
        linSideSlope=[linSideSlope] * 3,
        linSideOffset=[linSideOffset] * 3,
        linearSlope=[linearSlope] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )
    return lct

def _build_sgamut3_mtx():
    """ Build the Matrix transform for the S-Gamut3 primaries. """
    mtx = create_conversion_matrix(
        "S-Gamut3", "ACES2065-1", "CAT02"
    )
    return mtx

def _build_sgamut3_cine_mtx():
    """ Build the Matrix transform for the S-Gamut3.Cine primaries. """
    mtx = create_conversion_matrix(
        "S-Gamut3.Cine", "ACES2065-1", "CAT02"
    )
    return mtx

def _build_venice_sgamut3_mtx():
    """ Build the Matrix transform for the Venice S-Gamut3 primaries. """
    mtx = create_conversion_matrix(
        "Venice S-Gamut3", "ACES2065-1", "CAT02"
    )
    return mtx

def _build_venice_sgamut3_cine_mtx():
    """ Build the Matrix transform for the Venice S-Gamut3.Cine primaries. """
    mtx = create_conversion_matrix(
        "Venice S-Gamut3.Cine", "ACES2065-1", "CAT02"
    )
    return mtx

def generate_sony():
    """Make all the Sony CLFs."""

    if not DEST_DIR.exists():
        DEST_DIR.mkdir()

    # Note: The full transforms generated here were developed in collaboration with Sony.

    # Generate full S-Log3 - S-Gamut3 transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_sgamut3_mtx(),
            ]
        ),
        TF_ID_PREFIX
        + "Sony:Input:SLog3_SGamut3_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Sony S-Log3 S-Gamut3 to ACES2065-1",
        DEST_DIR / ("SLog3-SGamut3_to_ACES2065-1" + CLF_SUFFIX),
        "Sony S-Log3 S-Gamut3",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear S-Gamut3 transform.

    generate_clf(
        ocio.GroupTransform([_build_sgamut3_mtx()]),
        TF_ID_PREFIX
        + "Sony:Input:Linear_SGamut3_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear S-Gamut3 to ACES2065-1",
        DEST_DIR / ("Linear-SGamut3_to_ACES2065-1" + CLF_SUFFIX),
        "Linear S-Gamut3",
        "ACES2065-1",
        None,
    )

    # Generate full S-Log3 - S-Gamut3.Cine transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_sgamut3_cine_mtx(),
            ]
        ),
        TF_ID_PREFIX
        + "Sony:Input:SLog3_SGamut3Cine_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Sony S-Log3 S-Gamut3.Cine to ACES2065-1",
        DEST_DIR / ("SLog3-SGamut3Cine_to_ACES2065-1" + CLF_SUFFIX),
        "Sony S-Log3 S-Gamut3.Cine",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear S-Gamut3.Cine transform.

    generate_clf(
        ocio.GroupTransform([_build_sgamut3_cine_mtx()]),
        TF_ID_PREFIX
        + "Sony:Input:Linear_SGamut3Cine_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear S-Gamut3.Cine to ACES2065-1",
        DEST_DIR / ("Linear-SGamut3Cine_to_ACES2065-1" + CLF_SUFFIX),
        "Linear S-Gamut3.Cine",
        "ACES2065-1",
        None,
    )

    # Generate full Venice S-Log3 - S-Gamut3 transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_venice_sgamut3_mtx(),
            ]
        ),
        TF_ID_PREFIX
        + "Sony:Input:Venice_SLog3_SGamut3_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Sony Venice S-Log3 S-Gamut3 to ACES2065-1",
        DEST_DIR / ("Venice-SLog3-SGamut3_to_ACES2065-1" + CLF_SUFFIX),
        "Sony Venice S-Log3 S-Gamut3",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3 transform.

    generate_clf(
        ocio.GroupTransform([_build_venice_sgamut3_cine_mtx()]),
        TF_ID_PREFIX
        + "Sony:Input:Linear_Venice_SGamut3_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear Venice S-Gamut3 to ACES2065-1",
        DEST_DIR / ("Linear-Venice-SGamut3_to_ACES2065-1" + CLF_SUFFIX),
        "Linear Venice S-Gamut3",
        "ACES2065-1",
        None,
    )

    # Generate full Venice S-Log3 - S-Gamut3.Cine transform.

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_venice_sgamut3_cine_mtx(),
            ]
        ),
        TF_ID_PREFIX
        + "Sony:Input:Venice_SLog3_SGamut3Cine_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Sony Venice S-Log3 S-Gamut3.Cine to ACES2065-1",
        DEST_DIR / ("Venice-SLog3-SGamut3Cine_to_ACES2065-1" + CLF_SUFFIX),
        "Sony Venice S-Log3 S-Gamut3.Cine",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3.Cine transform.

    generate_clf(
        ocio.GroupTransform([_build_venice_sgamut3_cine_mtx()]),
        TF_ID_PREFIX
        + "Sony:Input:Linear_Venice_SGamut3Cine_to_ACES2065-1"
        + TF_ID_SUFFIX,
        "Linear Venice S-Gamut3.Cine to ACES2065-1",
        DEST_DIR / ("Linear-Venice-SGamut3Cine_to_ACES2065-1" + CLF_SUFFIX),
        "Linear Venice S-Gamut3.Cine",
        "ACES2065-1",
        None,
    )

    # Generate named transform for S-Log3 curve only.

    generate_clf(
        ocio.GroupTransform([_build_slog3_curve()]),
        TF_ID_PREFIX
        + "Sony:Input:SLog3_Log_to_Linear"
        + TF_ID_SUFFIX,
        "S-Log3 Log to Linear Curve",
        DEST_DIR / ("SLog3-Curve" + CLF_SUFFIX),
        "S-Log3 Log (arbitrary primaries)",
        "S-Log3 Linear (arbitrary primaries)",
        None,
    )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(generate_sony())
