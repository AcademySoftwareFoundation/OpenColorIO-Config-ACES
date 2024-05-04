# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Canon* CLF Transforms Generation
=================================

Defines procedures for generating Canon *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_canon`
"""

from pathlib import Path

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
    format_clf_transform_id,
    generate_clf_transform,
    matrix_RGB_to_RGB_transform,
)

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
    "generate_clf_transforms_canon",
]

FAMILY = "Canon"
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


def generate_clf_transforms_canon(output_directory):
    """
    Make the CLF file for Canon C-Log2 / C-Log3 Cinema Gamut plus matrix/curve
    CLFs.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Canon. (2018). White Paper on Canon Log.
        Retrieved September 22, 2022, from http://downloads.canon.com/nw/learn/\
white-papers/cinema-eos/white-paper-canon-log-gamma-curves.pdf

    Notes
    -----
    -   The resulting *CLF* transforms were reviewed by *Canon*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    mtx = matrix_RGB_to_RGB_transform("Cinema Gamut", "ACES2065-1", "CAT02")

    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:ACEScsc.Academy.CLog2_CGamut_to_ACES.a1.1.0"
    )

    name = "CanonLog2_CinemaGamut-D55_to_ACES2065-1"
    input_descriptor = "Canon Log 2 Cinema Gamut (Daylight)"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CANON_CLOG2-CGAMUT_to_ACES2065-1"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_transform_id,
        style=style,
    )

    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:ACEScsc.Academy.CLog3_CGamut_to_ACES.a1.1.0"
    )

    name = "CanonLog3_CinemaGamut-D55_to_ACES2065-1"
    input_descriptor = "Canon Log 3 Cinema Gamut (Daylight)"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CANON_CLOG3-CGAMUT_to_ACES2065-1"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_transform_id,
        style=style,
    )

    # Generate transform for primaries only.

    name = "Linear-CinemaGamut-D55_to_ACES2065-1"
    input_descriptor = "Linear Canon Cinema Gamut (Daylight)"
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

    name = "CLog2-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "CLog2 Log (arbitrary primaries)"
    output_descriptor = "CLog2 Linear (arbitrary primaries)"
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CURVE - CANON_CLOG2_to_LINEAR"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f'{input_descriptor.replace(" (arbitrary primaries)", "")} to Linear Curve',
        input_descriptor,
        output_descriptor,
        style=style,
    )

    name = "CLog3-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "CLog3 Log (arbitrary primaries)"
    output_descriptor = "CLog3 Linear (arbitrary primaries)"
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CURVE - CANON_CLOG3_to_LINEAR"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f'{input_descriptor.replace(" (arbitrary primaries)", "")} to Linear Curve',
        input_descriptor,
        output_descriptor,
        style=style,
    )

    return clf_transforms


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve() / "input"

    generate_clf_transforms_canon(output_directory)
