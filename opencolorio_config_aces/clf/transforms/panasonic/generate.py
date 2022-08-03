# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Panasonic* CLF Transforms Generation
=====================================

Defines procedures for generating Panasonic *Common LUT Format* (CLF)
transforms for the OpenColorIO project:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_panasonic`
"""

import PyOpenColorIO as ocio
from pathlib import Path

from opencolorio_config_aces.clf.discover.classify import (
    EXTENSION_CLF,
)
from opencolorio_config_aces.clf.transforms import (
    create_conversion_matrix,
    format_clf_transform_id,
    generate_clf_transform,
)

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "VERSION_CLF",
    "generate_clf_transforms_panasonic",
]

VERSION_CLF = "1.0"
"""
*CLF* transforms version.

VERSION_CLF : unicode
"""


def generate_clf_transforms_panasonic(output_directory):
    """
    Make the CLF file for V-Log - V-Gamut plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* group transform.

    References
    ----------
    -   Panasonic. (2014). VARICAM V-Log/V-Gamut (pp. 1–7).
        http://pro-av.panasonic.net/en/varicam/common/pdf/\
VARICAM_V-Log_V-Gamut.pdf

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *Panasonic*.
    """

    output_directory.mkdir(exist_ok=True)

    clf_transforms = {}

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

    filename = output_directory / f"VLog-VGamut_to_ACES2065-1{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                lct,
                mtx,
            ]
        ),
        format_clf_transform_id(
            "Panasonic:Input:VLog-VGamut_to_ACES2065-1", VERSION_CLF
        ),
        "Panasonic V-Log - V-Gamut (SUP v3) to ACES2065-1",
        filename,
        "Panasonic V-Log - V-Gamut (SUP v3)",
        "ACES2065-1",
        aces_transform_id,
    )

    # Generate transform for primaries only.

    filename = output_directory / f"Linear-VGamut_to_ACES2065-1{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([mtx]),
        format_clf_transform_id(
            "Panasonic:Input:Linear-VGamut_to_ACES2065-1", VERSION_CLF
        ),
        "Linear Panasonic V-Gamut (SUP v3) to ACES2065-1",
        filename,
        "Linear Panasonic V-Gamut (SUP v3)",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    filename = output_directory / f"VLog-Curve{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([lct]),
        format_clf_transform_id(
            "Panasonic:Input:VLog_Log_to_Linear", VERSION_CLF
        ),
        "Panasonic V-Log (SUP v3) Log to Linear Curve",
        filename,
        "Panasonic V-Log (SUP v3) Log (arbitrary primaries)",
        "Panasonic V-Log (SUP v3) Linear (arbitrary primaries)",
        None,
    )

    return clf_transforms


if __name__ == "__main__":
    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_panasonic(output_directory)
