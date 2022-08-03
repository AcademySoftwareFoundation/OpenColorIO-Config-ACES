# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Sony* CLF Transforms Generation
================================

Defines procedures for generating Sony *Common LUT Format* (CLF)
transforms for the OpenColorIO project:

-   :func:`opencolorio_config_aces.clf.generate_clf_sony`
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
    "generate_clf_sony",
]

VERSION_CLF = "1.0"
"""
*CLF* transforms version.

VERSION_CLF : unicode
"""


def _build_slog3_curve():
    """Build the Log transform for the S-Log3 curve."""
    linSideSlope = 1.0 / (0.18 + 0.01)
    linSideOffset = 0.01 / (0.18 + 0.01)
    logSideSlope = 261.5 / 1023.0
    logSideOffset = 420.0 / 1023.0
    linSideBreak = 0.01125000
    linearSlope = ((171.2102946929 - 95.0) / 0.01125000) / 1023.0
    base = 10.0

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
    """Build the Matrix transform for the S-Gamut3 primaries."""
    mtx = create_conversion_matrix("S-Gamut3", "ACES2065-1", "CAT02")
    return mtx


def _build_sgamut3_cine_mtx():
    """Build the Matrix transform for the S-Gamut3.Cine primaries."""
    mtx = create_conversion_matrix("S-Gamut3.Cine", "ACES2065-1", "CAT02")
    return mtx


def _build_venice_sgamut3_mtx():
    """Build the Matrix transform for the Venice S-Gamut3 primaries."""
    mtx = create_conversion_matrix("Venice S-Gamut3", "ACES2065-1", "CAT02")
    return mtx


def _build_venice_sgamut3_cine_mtx():
    """Build the Matrix transform for the Venice S-Gamut3.Cine primaries."""
    mtx = create_conversion_matrix(
        "Venice S-Gamut3.Cine", "ACES2065-1", "CAT02"
    )
    return mtx


def generate_clf_sony(output_directory):
    """
    Make all the Sony CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* group transform.

    Notes
    -----
    -   The full transforms generated here were developed in collaboration with
        Sony.
    """

    output_directory.mkdir(exist_ok=True)

    clf_transforms = {}

    # Generate full S-Log3 - S-Gamut3 transform.

    filename = output_directory / f"SLog3-SGamut3_to_ACES2065-1{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_sgamut3_mtx(),
            ]
        ),
        format_clf_transform_id(
            "Sony:Input:SLog3_SGamut3_to_ACES2065-1", VERSION_CLF
        ),
        "Sony S-Log3 S-Gamut3 to ACES2065-1",
        filename,
        "Sony S-Log3 S-Gamut3",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear S-Gamut3 transform.

    filename = (
        output_directory / f"Linear-SGamut3_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([_build_sgamut3_mtx()]),
        format_clf_transform_id(
            "Sony:Input:Linear_SGamut3_to_ACES2065-1", VERSION_CLF
        ),
        "Linear S-Gamut3 to ACES2065-1",
        filename,
        "Linear S-Gamut3",
        "ACES2065-1",
        None,
    )

    # Generate full S-Log3 - S-Gamut3.Cine transform.

    filename = (
        output_directory / f"SLog3-SGamut3Cine_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_sgamut3_cine_mtx(),
            ]
        ),
        format_clf_transform_id(
            "Sony:Input:SLog3_SGamut3Cine_to_ACES2065-1", VERSION_CLF
        ),
        "Sony S-Log3 S-Gamut3.Cine to ACES2065-1",
        filename,
        "Sony S-Log3 S-Gamut3.Cine",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear S-Gamut3.Cine transform.

    filename = (
        output_directory / f"Linear-SGamut3Cine_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([_build_sgamut3_cine_mtx()]),
        format_clf_transform_id(
            "Sony:Input:Linear_SGamut3Cine_to_ACES2065-1", VERSION_CLF
        ),
        "Linear S-Gamut3.Cine to ACES2065-1",
        filename,
        "Linear S-Gamut3.Cine",
        "ACES2065-1",
        None,
    )

    # Generate full Venice S-Log3 - S-Gamut3 transform.

    filename = (
        output_directory / f"Venice-SLog3-SGamut3_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_venice_sgamut3_mtx(),
            ]
        ),
        format_clf_transform_id(
            "Sony:Input:Venice_SLog3_SGamut3_to_ACES2065-1", VERSION_CLF
        ),
        "Sony Venice S-Log3 S-Gamut3 to ACES2065-1",
        filename,
        "Sony Venice S-Log3 S-Gamut3",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3 transform.

    filename = (
        output_directory
        / f"Linear-Venice-SGamut3_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([_build_venice_sgamut3_cine_mtx()]),
        format_clf_transform_id(
            "Sony:Input:Linear_Venice_SGamut3_to_ACES2065-1", VERSION_CLF
        ),
        "Linear Venice S-Gamut3 to ACES2065-1",
        filename,
        "Linear Venice S-Gamut3",
        "ACES2065-1",
        None,
    )

    # Generate full Venice S-Log3 - S-Gamut3.Cine transform.

    filename = (
        output_directory
        / f"Venice-SLog3-SGamut3Cine_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                _build_slog3_curve(),
                _build_venice_sgamut3_cine_mtx(),
            ]
        ),
        format_clf_transform_id(
            "Sony:Input:Venice_SLog3_SGamut3Cine_to_ACES2065-1", VERSION_CLF
        ),
        "Sony Venice S-Log3 S-Gamut3.Cine to ACES2065-1",
        filename,
        "Sony Venice S-Log3 S-Gamut3.Cine",
        "ACES2065-1",
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3.Cine transform.

    filename = (
        output_directory
        / f"Linear-Venice-SGamut3Cine_to_ACES2065-1{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([_build_venice_sgamut3_cine_mtx()]),
        format_clf_transform_id(
            "Sony:Input:Linear_Venice_SGamut3Cine_to_ACES2065-1", VERSION_CLF
        ),
        "Linear Venice S-Gamut3.Cine to ACES2065-1",
        filename,
        "Linear Venice S-Gamut3.Cine",
        "ACES2065-1",
        None,
    )

    # Generate named transform for S-Log3 curve only.

    filename = output_directory / f"SLog3-Curve{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform([_build_slog3_curve()]),
        format_clf_transform_id("Sony:Input:SLog3_Log_to_Linear", VERSION_CLF),
        "S-Log3 Log to Linear Curve",
        filename,
        "S-Log3 Log (arbitrary primaries)",
        "S-Log3 Linear (arbitrary primaries)",
        None,
    )

    return clf_transforms


if __name__ == "__main__":
    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_sony(output_directory)
