# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Blackmagic* CLF Transforms Generation
=======================================

Defines procedures for generating Blackmagic *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_bmdfilm`
-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_davinci`
"""

import math
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
    "generate_clf_transforms_bmdfilm",
    "generate_clf_transforms_davinci",
]

FAMILY = "BlackmagicDesign"
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


def generate_clf_transforms_bmdfilm(output_directory):
    """
    Make the CLF file for BMDFilm_WideGamut_Gen5 plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Blackmagic Design. (2021). Blackmagic Generation 5 Color Science.

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *Blackmagic*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

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

    mtx = matrix_RGB_to_RGB_transform("Blackmagic Wide Gamut", "ACES2065-1", "CAT02")

    # Taking the color space name and IDT transform ID from:
    #   https://github.com/ampas/aces-dev/pull/126/files
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        "IDT.BlackmagicDesign.BMDFilm_WideGamut_Gen5.a1.v1"
    )

    # Generate full transform.

    name = "BMDFilm_WideGamut_Gen5_to_ACES2065-1"
    input_descriptor = "Blackmagic Film Wide Gamut (Gen 5)"
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

    name = "Linear_BMD_WideGamut_Gen5_to_ACES2065-1"
    input_descriptor = "Linear Blackmagic Wide Gamut (Gen 5)"
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

    name = "BMDFilm_Gen5_Log-Curve_to_Linear"
    input_descriptor = "Blackmagic Film (Gen 5) Log"
    output_descriptor = "Blackmagic Film (Gen 5) Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [lct],
        clf_transform_id,
        f"{input_descriptor} to Linear Curve",
        input_descriptor,
        output_descriptor,
    )

    return clf_transforms


def generate_clf_transforms_davinci(output_directory):
    """
    Make the CLF file for DaVinci Intermediate Wide Gamut plus matrix/curve CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Blackmagic Design. (2020). Wide Gamut Intermediate DaVinci Resolve.
        Retrieved December 12, 2020, from
        https://documents.blackmagicdesign.com/InformationNotes/\
DaVinci_Resolve_17_Wide_Gamut_Intermediate.pdf?_v=1607414410000

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *Blackmagic*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

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
    # derivatives is 10.444266836 vs. the published value of 10.44426855. Based on
    # input from Blackmagic, it is preferable to set the linear slope value explicitly.
    LINEAR_SLOPE = m

    lct = transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
        base=BASE,
        linSideBreak=[LIN_SB] * 3,
        logSideSlope=[LOG_SLP] * 3,
        logSideOffset=[LOG_OFF] * 3,
        linSideSlope=[LIN_SLP] * 3,
        linSideOffset=[LIN_OFF] * 3,
        linearSlope=[LINEAR_SLOPE] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )

    mtx = matrix_RGB_to_RGB_transform("DaVinci Wide Gamut", "ACES2065-1", "CAT02")

    # This transform is not yet part of aces-dev, but an ID will be needed for AMF.
    # Proposing the following ID:
    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:"
        "ACEScsc.Academy.DaVinci_Intermediate_WideGamut_to_ACES.a1.v1"
    )

    # Generate full transform.

    name = "DaVinci_Intermediate_WideGamut_to_ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "DaVinci Intermediate Wide Gamut"
    output_descriptor = "ACES2065-1"
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

    name = "Linear_DaVinci_WideGamut_to_ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "Linear DaVinci Wide Gamut"
    output_descriptor = "ACES2065-1"
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

    name = "DaVinci_Intermediate_Log-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "DaVinci Intermediate Log"
    output_descriptor = "DaVinci Intermediate Linear"
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [lct],
        clf_transform_id,
        f"{input_descriptor} to Linear Curve",
        input_descriptor,
        output_descriptor,
    )

    return clf_transforms


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_bmdfilm(output_directory)
    generate_clf_transforms_davinci(output_directory)
