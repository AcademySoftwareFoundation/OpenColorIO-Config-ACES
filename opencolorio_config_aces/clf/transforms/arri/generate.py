# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ARRI* CLF Transforms Generation
================================

Defines procedures for generating ARRI *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_arri`
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from math import log, log10
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
    "generate_clf_transforms_arri",
]

LOGGER = logging.getLogger(__name__)

FAMILY: str = "ARRI"
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


def _build_awg3_mtx() -> ocio.MatrixTransform:
    """
    Build the `MatrixTransform` for *ARRI* *Wide Gamut 3* primaries.

    Matrix precision is insufficient for Float64 comparison in the *LogC*
    White Paper, values are derived from the primaries here.

    Returns
    -------
    :class:`ocio.MatrixTransform`
         *OpenColorIO* `MatrixTransform`.
    """

    mtx = matrix_RGB_to_RGB_transform("ARRI Wide Gamut 3", "ACES2065-1", "CAT02")
    return mtx


def _build_logc3_curve(ei: int = 800, info: bool = False) -> ocio.LogCameraTransform:
    """
    Build the `LogCameraTransform` for *ARRI* *LogC3* Curve.

    Parameter values are derived from the published aces-dev IDT formula.

    Parameters
    ----------
    ei
        *Exposure Index* of the *LogC3* Curve to generate.
    info
        Whether to print additional informative text.

    Returns
    -------
    :class:`ocio.LogCameraTransform`
         *OpenColorIO* `LogCameraTransform`.

    Raises
    ------
    ValueError
        If `ei` is not in the supported range.
    """

    if not (160 <= ei <= 1280):
        raise ValueError(f"Unsupported EI{ei:d} requested, must be 160 <= EI <= 1280")

    # v3_IDT_maker.py parameters
    nominalEI = 400
    midGraySignal = 0.01
    encodingGain = 500 / 1023 * 0.525  # was: 0.256598
    encodingOffset = 400 / 1023  # was: 0.391007
    cutPoint = 1 / 9  # renamed from "cut"
    slope = 1 / (cutPoint * log(10))
    offset = log10(cutPoint) - slope * cutPoint
    gain = ei / nominalEI
    gray = midGraySignal / gain
    encGain = (log(gain) / log(2) * (0.89 - 1) / 3 + 1) * encodingGain
    encOffset = encodingOffset

    for _ in range(3):
        nz = ((95 / 1023 - encOffset) / encGain - offset) / slope
        encOffset = encodingOffset - log10(1 + nz) * encGain

    # derived "ALEXA Log C Curve Usage in VFX 09-Mar-17" style parameters
    # compatible with CLF cameraLogToLin parameters
    cut = (cutPoint - nz) * gray * (0.18 / (midGraySignal * nominalEI / ei))
    a = 1.0 / (gray * 0.18 / (midGraySignal * nominalEI / ei))
    b = nz
    c = encGain
    d = encOffset

    # print informative text if requested
    if info:
        # compute unused variables for completeness

        # follows CLF 6.6 Log specification
        e = c * (a / ((a * cut + b) * log(10)))

        # follows CLF 6.6 Log specification
        f = c * log10(a * cut + b) + d

        LOGGER.info("White Paper Values for EI%s", ei)
        LOGGER.info("cut: {%.6f} :: {%.15f}", cut, cut)
        LOGGER.info("a:   {%.6f} :: {%.15f}", a, a)
        LOGGER.info("b:   {%.6f} :: {%.15f}", b, b)
        LOGGER.info("c:   {%.6f} :: {%.15f}", c, c)
        LOGGER.info("d:   {%.6f} :: {%.15f}", d, d)
        LOGGER.info("e:   {%.6f} :: {%.15f}", e, e)
        LOGGER.info("f:   {%.6f} :: {%.15f}", f, f)

    # OCIO LogCameraTransform translation variables
    base = 10.0
    linSideBreak = [cut] * 3
    logSideSlope = [c] * 3
    logSideOffset = [d] * 3
    linSideSlope = [a] * 3
    linSideOffset = [b] * 3
    direction = ocio.TRANSFORM_DIR_INVERSE

    return transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=base,
        linSideBreak=linSideBreak,
        logSideSlope=logSideSlope,
        logSideOffset=logSideOffset,
        linSideSlope=linSideSlope,
        linSideOffset=linSideOffset,
        direction=direction,
    )


def _build_awg4_mtx() -> ocio.MatrixTransform:
    """
    Build the `MatrixTransform` for *ARRI* *Wide Gamut 4* primaries.

    Values are copied directly from the *LogC4* Specification.

    Returns
    -------
    :class:`ocio.MatrixTransform`
         *OpenColorIO* `MatrixTransform`.
    """

    # Values as defined in: "ARRI LogC4 Logarithmic Color Space Specification".
    # Extra row and column for OCIO alpha channel.
    mtx = [
        0.750957362824734131,
        0.144422786709757084,
        0.104619850465508965,
        0.0,
        0.000821837079380207,
        1.007397584885003194,
        -0.008219421964383583,
        0.0,
        -0.000499952143533471,
        -0.000854177231436971,
        1.001354129374970370,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]

    return transform_factory(transform_type="MatrixTransform", matrix=mtx)


def _build_logc4_curve() -> ocio.LogCameraTransform:
    """
    Build the `LogCameraTransform` for *ARRI* *LogC4* Curve.

    Parameter values are derived from the published *LogC4* Specification.

    Returns
    -------
    :class:`ocio.LogCameraTransform`
         *OpenColorIO* `LogCameraTransform`.
    """

    # Parameters as defined in "ARRI LogC4 Logarithmic Color Space Specification"
    # Parameters as defined in aces-dev CTL
    a = (2.0**18.0 - 16.0) / 117.45
    b = (1023.0 - 95.0) / 1023.0
    c = 95.0 / 1023.0
    t = (pow(2.0, 14.0 * (-c / b) + 6.0) - 64.0) / a

    # OCIO LogCameraTransform translation variables
    linSideSlope = [a] * 3
    linSideOffset = [64.0] * 3
    logSideSlope = [b / 14.0] * 3
    logSideOffset = [-6.0 * b / 14.0 + c] * 3
    linSideBreak = [t] * 3
    base = 2.0
    direction = ocio.TRANSFORM_DIR_INVERSE

    return transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=base,
        linSideBreak=linSideBreak,
        logSideSlope=logSideSlope,
        logSideOffset=logSideOffset,
        linSideSlope=linSideSlope,
        linSideOffset=linSideOffset,
        direction=direction,
    )


def _generate_logc3_transforms(
    output_directory: Path, ei_list: Sequence[int] = (800,)
) -> dict[Path, ocio.GroupTransform]:
    """
    Generate the collection of *LogC3* transforms.

    Parameters
    ----------
    output_directory
        Directory to write the *CLF* transform(s) to.
    ei_list
        List of EI values to generate *LogC3* and *LogC3* Curve transforms for.

    Returns
    -------
    :class:`dict`
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.
    """

    transforms = {}

    for ei in ei_list:
        # Generate ARRI LogC3 to ACES 2065-1 Transform
        name = f"ARRI_LogC3_EI{ei}_to_ACES2065-1"
        aces_id = f"urn:ampas:aces:transformId:v1.5:IDT.ARRI.Alexa-v3-logC-EI{ei}.a1.v2"

        if ei == 800:
            aces_id = "urn:ampas:aces:transformId:v2.0:CSC.Arri.LogC3_to_ACES.a2.v1"

        input_descriptor = f"ARRI LogC3 (EI{ei})"
        output_descriptor = "ACES2065-1"
        clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
        filename = output_directory / clf_basename(clf_transform_id)
        transforms[filename] = generate_clf_transform(
            filename,
            [_build_logc3_curve(ei), _build_awg3_mtx()],
            clf_transform_id,
            f"{input_descriptor} to {output_descriptor}",
            input_descriptor,
            output_descriptor,
            aces_id,
        )

        # Generate ARRI LogC3 Curve Transform
        name = f"ARRI_LogC3_Curve_EI{ei:d}_to_Linear"
        input_descriptor = f"ARRI LogC3 Curve (EI{ei:d})"
        output_descriptor = "Relative Scene Linear"
        clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
        filename = output_directory / clf_basename(clf_transform_id)
        transforms[filename] = generate_clf_transform(
            filename,
            [_build_logc3_curve(ei)],
            clf_transform_id,
            f"{input_descriptor} to {output_descriptor}",
            input_descriptor,
            output_descriptor,
        )

    # Generate Linear ARRI Wide Gamut 3 to ACES 2065-1 Transform
    name = "Linear_ARRI_Wide_Gamut_3_to_ACES2065-1"
    input_descriptor = "Linear ARRI Wide Gamut 3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms[filename] = generate_clf_transform(
        filename,
        [_build_awg3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    return transforms


def _generate_logc4_transforms(
    output_directory: Path,
) -> dict[Path, ocio.GroupTransform]:
    """
    Generate the collection of *LogC4* transforms.

    Parameters
    ----------
    output_directory
        Directory to write the *CLF* transform(s) to.

    Returns
    -------
    :class:`dict`
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.
    """

    transforms = {}

    # Generate ARRI LogC4 to ACES 2065-1 Transform
    name = "ARRI_LogC4_to_ACES2065-1"
    aces_id = "urn:ampas:aces:transformId:v2.0:CSC.Arri.LogC4_to_ACES.a2.v1"
    input_descriptor = "ARRI LogC4"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms[filename] = generate_clf_transform(
        filename,
        [_build_logc4_curve(), _build_awg4_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_id,
    )

    # Generate ARRI LogC4 Curve Transform
    name = "ARRI_LogC4_Curve_to_Linear"
    input_descriptor = "ARRI LogC4 Curve"
    output_descriptor = "Relative Scene Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms[filename] = generate_clf_transform(
        filename,
        [_build_logc4_curve()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate Linear ARRI Wide Gamut 4 to ACES 2065-1 Transform
    name = "Linear_ARRI_Wide_Gamut_4_to_ACES2065-1"
    input_descriptor = "Linear ARRI Wide Gamut 4"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms[filename] = generate_clf_transform(
        filename,
        [_build_awg4_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    return transforms


def generate_clf_transforms_arri(
    output_directory: Path,
) -> dict[Path, ocio.GroupTransform]:
    """
    Generate the *CLF* transforms for *ARRI* color encodings and save to disk.

    Parameters
    ----------
    output_directory
        Directory to write the *CLF* transform(s) to.

    Returns
    -------
    :class:`dict`
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    logc3_transforms = _generate_logc3_transforms(output_directory, ei_list=[800])
    logc4_transforms = _generate_logc4_transforms(output_directory)

    clf_transforms = {**logc3_transforms, **logc4_transforms}

    return clf_transforms


def _main() -> int:
    """
    Generate files, initiate logging, and provide exit code.

    Returns
    -------
    :class:`int`
        Software exit code for successful termination.
    """

    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_arri(output_directory)

    return 0


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(_main())
