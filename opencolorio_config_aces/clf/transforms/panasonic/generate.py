# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Panasonic* CLF Transforms Generation
=====================================

Defines procedures for generating Panasonic *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_panasonic`
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
    "generate_clf_transforms_panasonic",
]

FAMILY = "Panasonic"
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


def generate_clf_transforms_panasonic(output_directory):
    """
    Make the CLF file for V-Log - V-Gamut plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Panasonic. (2014). VARICAM V-Log/V-Gamut (pp. 1-7).
        http://pro-av.panasonic.net/en/varicam/common/pdf/\
VARICAM_V-Log_V-Gamut.pdf

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *Panasonic*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

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

    lct = transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=BASE,
        linSideBreak=[LIN_SB] * 3,
        logSideSlope=[LOG_SLP] * 3,
        logSideOffset=[LOG_OFF] * 3,
        linSideSlope=[LIN_SLP] * 3,
        linSideOffset=[LIN_OFF] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = matrix_RGB_to_RGB_transform("V-Gamut", "ACES2065-1", "Bradford")

    # Using the CSC ID here because there is a slight discrepancy between the matrix
    # coefficients of the CSC and IDT CTL and the CLF matches the CSC transform.
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:ACEScsc.Academy.VLog_VGamut_to_ACES.a1.1.0"
    )

    # Generate full transform.

    name = "VLog_VGamut_to_ACES2065-1"
    input_descriptor = "Panasonic V-Log - V-Gamut"
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

    name = "Linear_VGamut_to_ACES2065-1"
    input_descriptor = "Linear Panasonic V-Gamut"
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
    name = "VLog-Curve_to_Linear"
    input_descriptor = "Panasonic V-Log Log (arbitrary primaries)"
    output_descriptor = "Panasonic V-Log Linear (arbitrary primaries)"
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

    generate_clf_transforms_panasonic(output_directory)
