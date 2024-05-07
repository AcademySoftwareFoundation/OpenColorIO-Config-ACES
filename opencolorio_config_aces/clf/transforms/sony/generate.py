# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Sony* CLF Transforms Generation
================================

Defines procedures for generating Sony *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_sony`
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
    "generate_clf_transforms_sony",
]

FAMILY = "Sony"
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


def _build_slog2_curve():
    """Build the Log transform for the S-Log2 curve."""
    b = 64.0 / 1023.0
    w = 940.0 / 1023.0
    ab = 90.0 / 1023.0
    linSideSlope = 155.0 / (0.9 * 219.0)
    linSideOffset = 0.037584
    logSideSlope = 0.432699 * (w - b)
    logSideOffset = (0.616596 + 0.03) * (w - b) + b
    linearSlope = 3.53881278538813 * (w - b) / 0.9
    base = 10.0
    logSideBreak = ab
    linSideBreak = (
        pow(base, (logSideBreak - logSideOffset) / logSideSlope) - linSideOffset
    ) / linSideSlope

    lct = transform_factory(
        transform_type="LogCameraTransform",
        transform_factory="Constructor",
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


def _build_slog3_curve():
    """Build the Log transform for the S-Log3 curve."""
    linSideSlope = 1.0 / (0.18 + 0.01)
    linSideOffset = 0.01 / (0.18 + 0.01)
    logSideSlope = 261.5 / 1023.0
    logSideOffset = 420.0 / 1023.0
    linSideBreak = 0.01125000
    linearSlope = ((171.2102946929 - 95.0) / 0.01125000) / 1023.0
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
        linearSlope=[linearSlope] * 3,
        direction=ocio.TRANSFORM_DIR_INVERSE,
    )
    return lct


def _build_sgamut_mtx():
    """Build the `MatrixTransform` for the S-Gamut primaries."""
    mtx = matrix_RGB_to_RGB_transform("S-Gamut", "ACES2065-1", "CAT02")
    return mtx


def _build_sgamut3_mtx():
    """Build the `MatrixTransform` for the S-Gamut3 primaries."""
    mtx = matrix_RGB_to_RGB_transform("S-Gamut3", "ACES2065-1", "CAT02")
    return mtx


def _build_sgamut3_cine_mtx():
    """Build the `MatrixTransform` for the S-Gamut3.Cine primaries."""
    mtx = matrix_RGB_to_RGB_transform("S-Gamut3.Cine", "ACES2065-1", "CAT02")
    return mtx


def _build_venice_sgamut3_mtx():
    """Build the `MatrixTransform` for the Venice S-Gamut3 primaries."""
    mtx = matrix_RGB_to_RGB_transform("Venice S-Gamut3", "ACES2065-1", "CAT02")
    return mtx


def _build_venice_sgamut3_cine_mtx():
    """Build the `MatrixTransform` for the Venice S-Gamut3.Cine primaries."""
    mtx = matrix_RGB_to_RGB_transform("Venice S-Gamut3.Cine", "ACES2065-1", "CAT02")
    return mtx


def generate_clf_transforms_sony(output_directory):
    """
    Make all the Sony CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    Notes
    -----
    -   The full transforms generated here were developed in collaboration with
        Sony.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    # Generate full S-Log2 - S-Gamut transform.

    name = "SLog2_SGamut_to_ACES2065-1"
    input_descriptor = "Sony S-Log2 S-Gamut"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog2_curve(), _build_sgamut_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate the Linear S-Gamut transform.

    name = "Linear_SGamut_to_ACES2065-1"
    input_descriptor = "Linear S-Gamut"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_sgamut_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate `NamedTransform` for S-Log2 curve only.

    name = "SLog2-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "S-Log2 Log (arbitrary primaries)"
    output_descriptor = "S-Log2 Linear (arbitrary primaries)"
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog2_curve()],
        clf_transform_id,
        f'{input_descriptor.replace(" (arbitrary primaries)", "")} to Linear Curve',
        input_descriptor,
        output_descriptor,
    )

    # Generate full S-Log3 - S-Gamut3 transform.

    name = "SLog3_SGamut3_to_ACES2065-1"
    input_descriptor = "Sony S-Log3 S-Gamut3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog3_curve(), _build_sgamut3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear S-Gamut3 transform.

    name = "Linear_SGamut3_to_ACES2065-1"
    input_descriptor = "Linear S-Gamut3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_sgamut3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate full S-Log3 - S-Gamut3.Cine transform.

    name = "SLog3_SGamut3Cine_to_ACES2065-1"
    input_descriptor = "Sony S-Log3 S-Gamut3.Cine"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog3_curve(), _build_sgamut3_cine_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear S-Gamut3.Cine transform.

    name = "Linear_SGamut3Cine_to_ACES2065-1"
    input_descriptor = "Linear S-Gamut3.Cine"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_sgamut3_cine_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate full S-Log3 - Venice S-Gamut3 transform.

    name = "SLog3_Venice_SGamut3_to_ACES2065-1"
    input_descriptor = "Sony S-Log3 Venice S-Gamut3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog3_curve(), _build_venice_sgamut3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3 transform.

    name = "Linear_Venice_SGamut3_to_ACES2065-1"
    input_descriptor = "Linear Venice S-Gamut3"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_venice_sgamut3_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate full S-Log3 - Venice S-Gamut3.Cine transform.

    name = "SLog3_Venice_SGamut3Cine_to_ACES2065-1"
    input_descriptor = "Sony S-Log3 Venice S-Gamut3.Cine"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog3_curve(), _build_venice_sgamut3_cine_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        "urn:ampas:aces:transformId:v1.5:IDT.Sony.Venice_SLog3_SGamut3Cine.a1.v1",
    )

    # Generate the Linear Venice S-Gamut3.Cine transform.

    name = "Linear_Venice_SGamut3Cine_to_ACES2065-1"
    input_descriptor = "Linear Venice S-Gamut3.Cine"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_venice_sgamut3_cine_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate `NamedTransform` for S-Log3 curve only.

    name = "SLog3-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "S-Log3 Log (arbitrary primaries)"
    output_descriptor = "S-Log3 Linear (arbitrary primaries)"
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_slog3_curve()],
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

    generate_clf_transforms_sony(output_directory)
