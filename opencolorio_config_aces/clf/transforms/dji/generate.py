# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*DJI* CLF Transforms Generation
================================

Defines procedures for generating DJI *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_dji`
"""

from __future__ import annotations

from pathlib import Path

import PyOpenColorIO as ocio

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
    format_clf_transform_id,
    generate_clf_transform,
    matrix_RGB_to_RGB_transform,
)
from opencolorio_config_aces.config import transform_factory

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
    "generate_clf_transforms_dji",
]

FAMILY: str = "DJI"
"""
*CLF* transforms family.
"""

GENUS: str = "Input"
"""
*CLF* transforms genus.
"""

VERSION: str = "1.0"
"""
*CLF* transforms version.
"""


def generate_clf_transforms_dji(
    output_directory: Path,
) -> dict[Path, ocio.GroupTransform]:
    """
    Generate the *CLF* transforms for *D-Log - D-Gamut* plus matrix/curve.

    Parameters
    ----------
    output_directory
        Directory to write the *CLF* transform(s) to.

    Returns
    -------
    :class:`dict`
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Dji. (2017). White Paper on D-Log and D-Gamut of DJI Cinema Color
    System (pp. 1-5). https://dl.djicdn.com/downloads/zenmuse+x7/20171010/\
D-Log_D-Gamut_Whitepaper.pdf
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    base = 10.0

    # Mathematically correct for transition at log = 0.14:
    # lin_side_break = (0.14 - 0.0929) / 6.025 = 0.007817427385892119
    # Optimized:
    lin_side_break = 0.00758078675

    log_side_slope = 1.0 / 3.89616
    log_side_offset = 2.27752 / 3.89616
    lin_side_slope = 0.9892
    lin_side_offset = 0.0108

    lct = transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=base,
        linSideBreak=[lin_side_break] * 3,
        logSideSlope=[log_side_slope] * 3,
        logSideOffset=[log_side_offset] * 3,
        linSideSlope=[lin_side_slope] * 3,
        linSideOffset=[lin_side_offset] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = matrix_RGB_to_RGB_transform("DJI D-Gamut", "ACES2065-1", "CAT02")

    # ACES transform ID from the CTL file
    aces_transform_id = (
        "urn:ampas:aces:transformId:v2.0:CSC.DJI.DLog_DGamut_to_ACES.a1.v1"
    )

    # Generate full transform.
    name = "DLog_DGamut_to_ACES2065-1"
    input_descriptor = "DJI D-Log - D-Gamut"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [lct, mtx],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_transform_id,
    )

    # Generate transform for primaries only.
    name = "Linear_DGamut_to_ACES2065-1"
    input_descriptor = "Linear DJI D-Gamut"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [mtx],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate `NamedTransform` for log curve only.
    name = "DLog-Curve_to_Linear"
    input_descriptor = "DJI D-Log Log (arbitrary primaries)"
    output_descriptor = "DJI D-Log Linear (arbitrary primaries)"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [lct],
        clf_transform_id,
        f'{input_descriptor.replace(" (arbitrary primaries)", "")} to Linear Curve',
        input_descriptor,
        output_descriptor,
    )

    return clf_transforms


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_dji(output_directory)
