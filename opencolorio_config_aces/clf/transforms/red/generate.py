# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*RED* CLF Transforms Generation
===============================

Defines procedures for generating RED *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_red`
"""

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
    "generate_clf_transforms_red",
]

FAMILY = "RED"
"""
*CLF* transforms family.
"""

GENUS = "Input"
"""
*CLF* transforms genus.
"""

VERSION = "1.0"
"""
*CLF* transforms version.
"""


def generate_clf_transforms_red(output_directory):
    """
    Make the CLF file for RED Log3G10 REDWideGamutRGB plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   RED Digital Cinema. (2017). White Paper on REDWideGamutRGB and Log3G10.
        Retrieved January 16, 2021, from https://www.red.com/download/\
white-paper-on-redwidegamutrgb-and-log3g10

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *RED*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    linSideSlope = 155.975327
    linSideOffset = 0.01 * linSideSlope + 1.0
    logSideSlope = 0.224282
    logSideOffset = 0.0
    linSideBreak = -0.01
    base = 10.0

    lct = transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=base,
        linSideBreak=[linSideBreak] * 3,
        logSideSlope=[logSideSlope] * 3,
        logSideOffset=[logSideOffset] * 3,
        linSideSlope=[linSideSlope] * 3,
        linSideOffset=[linSideOffset] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = matrix_RGB_to_RGB_transform("REDWideGamutRGB", "ACES2065-1", "Bradford")

    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:IDT.RED.Log3G10_REDWideGamutRGB.a1.v1"
    )

    # Generate full transform.

    name = "Log3G10_REDWideGamutRGB_to_ACES2065-1"
    input_descriptor = "RED Log3G10 REDWideGamutRGB"
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

    name = "Linear_REDWideGamutRGB_to_ACES2065-1"
    input_descriptor = "Linear REDWideGamutRGB"
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

    name = "Log3G10-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "RED Log3G10 Log (arbitrary primaries)"
    output_descriptor = "RED Log3G10 Linear (arbitrary primaries)"
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

    generate_clf_transforms_red(output_directory)
