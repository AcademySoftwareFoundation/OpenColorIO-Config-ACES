# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ARRI* CLF Transforms Generation
=======================================

Defines procedures for generating ARRI *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_arri`
"""

from math import log, log10
import PyOpenColorIO as ocio
from pathlib import Path
import sys

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
    "generate_clf_arri",
]

FAMILY = "ARRI"
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


def _build_awg3_mtx():
    """
    Build the `MatrixTransform` for ARRI Wide Gamut 3 primaries.

    Matrix precision is insufficient for Float64 comparison in the LogC
    White Paper, values are derived from the primaries here.

    Returns
    -------
    ocio.MatrixTransform
         *OpenColorIO* `MatrixTransform`.
    """

    mtx = matrix_RGB_to_RGB_transform(
        "ALEXA Wide Gamut", "ACES2065-1", "CAT02"
    )
    return mtx


def _build_logc3_curve(ei=800, info=False):
    """
    Build the `LogCameraTransform` for ARRI LogC3 Curve.

    Parameter values are derived from the published aces-dev IDT formula.

    Parameters
    ----------
    ei : int, optional
        *Exposure Index* of the LogC3 Curve to generate.
    info : bool, optional
        Whether to print additional informative text.

    Returns
    -------
    ocio.LogCameraTransform
         *OpenColorIO* `LogCameraTransform`.
    """

    if not (160 <= ei <= 1280):
        print(
            f"Error: Unsupported EI{ei:d} requested, must be 160 <= EI <= 1280".format(
                ei
            )
        )
        return False

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

    for i in range(0, 3):
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

        print(f"White Paper Values for EI{ei:d}")
        print(f"cut: {cut:.6f} :: {cut:.15f}")
        print(f"a:   {a:.6f} :: {a:.15f}")
        print(f"b:   {b:.6f} :: {b:.15f}")
        print(f"c:   {c:.6f} :: {c:.15f}")
        print(f"d:   {d:.6f} :: {d:.15f}")
        print(f"e:   {e:.6f} :: {e:.15f}")
        print(f"f:   {f:.6f} :: {f:.15f}")

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


def _build_awg4_mtx():
    """
    Build the `MatrixTransform` for ARRI Wide Gamut 4 primaries.

    Values are copied directly from the LogC4 Specification.

    Returns
    -------
    ocio.MatrixTransform
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


def _build_logc4_curve():
    """
    Build the `LogCameraTransform` for ARRI LogC4 Curve.

    Parameter values are derived from the published LogC4 Specification.

    Returns
    -------
    ocio.LogCameraTransform
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
    transforms_set, output_directory, ei_list=[800]
):
    """
    Generate the collection LogC3 of transforms.

    Parameters
    ----------
    transforms_set : dict
        A `dict` of transforms to append to.
    output_directory : PosixPath or WindowsPath
        Directory where generated CTL files should be saved.
    ei_list : array_like of int, optional
        List of EI values to generate LogC3 and LogC3 Curve transforms for.

    Returns
    -------
    dict
        Dictionary of *OpenColorIO* `Transform` instances.
    """

    for ei in ei_list:

        # Genereate ARRI LogC3 to ACES 2065-1 Transform
        name = f"ARRI_LogC3_EI{ei}_to_ACES2065-1"
        aces_id = f"urn:ampas:aces:transformId:v1.5:IDT.ARRI.Alexa-v3-logC-EI{ei}.a1.v2"
        input_descriptor = f"ARRI LogC3 (EI{ei})"
        output_descriptor = "ACES2065-1"
        clf_transform_id = format_clf_transform_id(
            FAMILY, GENUS, name, VERSION
        )
        filename = output_directory / clf_basename(clf_transform_id)
        transforms_set[filename] = generate_clf_transform(
            filename,
            [_build_logc3_curve(ei), _build_awg3_mtx()],
            clf_transform_id,
            f"{input_descriptor} to {output_descriptor}",
            input_descriptor,
            output_descriptor,
            aces_id,
        )

        # Genereate ARRI LogC3 Curve Transform
        name = f"ARRI_LogC3_Curve_EI{ei:d}_to_Linear"
        input_descriptor = f"ARRI LogC3 Curve (EI{ei:d})"
        output_descriptor = "Relative Scene Linear"
        clf_transform_id = format_clf_transform_id(
            FAMILY, GENUS, name, VERSION
        )
        filename = output_directory / clf_basename(clf_transform_id)
        transforms_set[filename] = generate_clf_transform(
            filename,
            [_build_logc3_curve(ei)],
            clf_transform_id,
            f"{input_descriptor} to {output_descriptor}",
            input_descriptor,
            output_descriptor,
        )

    # Genereate Linear ARRI Wide Gamut 3 to ACES 2065-1 Transform
    name = "Linear_ARRI_Wide_Gamut_3_to_ACES2065-1"
    input_descriptor = "Linear ARRI Wide Gamut 3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms_set[filename] = generate_clf_transform(
        filename,
        [_build_awg3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    return transforms_set


def _generate_logc4_transforms(transforms_set, output_directory):
    """
    Generate the collection LogC4 of transforms.

    Parameters
    ----------
    transforms_set : dict
        A `dict` of transforms to append to.
    output_directory : PosixPath or WindowsPath
        Directory where generated CTL files should be saved.

    Returns
    -------
    dict
        Dictionary of *OpenColorIO* `Transform` instances.
    """

    # Genereate ARRI LogC4 to ACES 2065-1 Transform
    name = "ARRI_LogC4_to_ACES2065-1"
    aces_id = "urn:ampas:aces:transformId:v1.5:IDT.ARRI.LogC4.a1.v1"
    input_descriptor = "ARRI LogC4"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms_set[filename] = generate_clf_transform(
        filename,
        [_build_logc4_curve(), _build_awg4_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_id,
    )

    # Genereate ARRI LogC4 Curve Transform
    name = "ARRI_LogC4_Curve_to_Linear"
    input_descriptor = "ARRI LogC4 Curve"
    output_descriptor = "Relative Scene Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms_set[filename] = generate_clf_transform(
        filename,
        [_build_logc4_curve()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Genereate Linear ARRI Wide Gamut 4 to ACES 2065-1 Transform
    name = "Linear_ARRI_Wide_Gamut_4_to_ACES2065-1"
    input_descriptor = "Linear ARRI Wide Gamut 4"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    transforms_set[filename] = generate_clf_transform(
        filename,
        [_build_awg4_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    return transforms_set


def generate_clf_arri(output_directory):
    """
    Generate CLF files for ARRI color encodings and save to disk.

    Parameters
    ----------
    output_directory : PosixPath or WindowsPath
        Directory where generated CTL files should be saved.

    Returns
    -------
    dict
        Dictionary of *OpenColorIO* `Transform` instances.

    References
    ----------
    -

    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}
    clf_transforms = _generate_logc3_transforms(
        clf_transforms, output_directory, ei_list=[800]
    )
    clf_transforms = _generate_logc4_transforms(
        clf_transforms, output_directory
    )

    return clf_transforms


def _main():
    """
    Generate files, initiate logging, and provide exit code.

    Returns
    -------
    int
        Software exit code for successful termination.
    """
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_arri(output_directory)

    return 0


if __name__ == "__main__":
    sys.exit(_main())
