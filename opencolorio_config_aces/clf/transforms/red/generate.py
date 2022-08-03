# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*RED* CLF Transforms Generation
===============================

Defines procedures for generating RED *Common LUT Format* (CLF)
transforms for the OpenColorIO project:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_red`
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
    "generate_clf_transforms_red",
]

VERSION_CLF = "1.0"
"""
*CLF* transforms version.

VERSION_CLF : unicode
"""


def generate_clf_transforms_red(output_directory):
    """
    Make the CLF file for RED Log3G10 REDWideGamutRGB plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* group transform.

    References
    ----------
    -   RED Digital Cinema. (2017). White Paper on REDWideGamutRGB and Log3G10.
        Retrieved January 16, 2021, from https://www.red.com/download/\
white-paper-on-redwidegamutrgb-and-log3g10

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *RED*.
    """

    output_directory.mkdir(exist_ok=True)

    clf_transforms = {}

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

    filename = output_directory / f"Log3G10-RWG_to_ACES2065-1{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                lct,
                mtx,
            ]
        ),
        format_clf_transform_id(
            "RED:Input:Log3G10-RWG_to_ACES2065-1", VERSION_CLF
        ),
        "RED Log3G10 REDWideGamutRGB to ACES2065-1",
        filename,
        "RED Log3G10 REDWideGamutRGB",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.RED.Log3G10_RWG.a1.v1",
    )

    # Generate transform for primaries only.

    filename = (
        output_directory
        / f"Linear-REDWideGamutRGB_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([mtx]),
        format_clf_transform_id(
            "RED:Input:Linear-REDWideGamutRGB_to_ACES2065-1", VERSION_CLF
        ),
        "Linear REDWideGamutRGB to ACES2065-1",
        filename,
        "Linear REDWideGamutRGB",
        "ACES2065-1",
        None,
    )

    # Generate named transform for log curve only.

    filename = output_directory / f"Log3G10-Curve{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([lct]),
        format_clf_transform_id(
            "RED:Input:Log3G10_Log_to_Linear", VERSION_CLF
        ),
        "RED Log3G10 Log to Linear Curve",
        filename,
        "RED Log3G10 (SUP v3) Log (arbitrary primaries)",
        "RED Log3G10 (SUP v3) Linear (arbitrary primaries)",
        None,
    )

    return clf_transforms


if __name__ == "__main__":
    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_red(output_directory)
