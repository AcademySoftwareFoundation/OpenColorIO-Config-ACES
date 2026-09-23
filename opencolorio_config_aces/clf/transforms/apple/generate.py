# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Apple* CLF Transforms Generation
=================================

Defines procedures for generating Apple *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_apple`
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import PyOpenColorIO as ocio

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
    format_clf_transform_id,
    generate_clf_transform,
    matrix_transform,
)
from opencolorio_config_aces.utilities import required

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
    "generate_clf_transforms_apple",
]

FAMILY: str = "Apple"
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


@required("Colour")
def _build_apple_wg_mtx() -> ocio.MatrixTransform:
    """
    Build the `MatrixTransform` for the *Apple Wide Gamut* primaries.

    The *Apple Log 2* white paper publishes neither the matrix nor the
    chromatic adaptation transform to use, thus the matrix is derived from the
    primaries using *Bradford* adaptation, as it is the most consistent with
    *ACES* and matches the *OpenColorIO* `APPLE_LOG-APPLEWG_to_ACES2065-1`
    builtin transform.

    Returns
    -------
    :class:`ocio.MatrixTransform`
         *OpenColorIO* `MatrixTransform`.
    """

    import colour

    # Primaries as defined in: "Apple Log 2 Profile".
    colourspace = colour.RGB_Colourspace(
        "Apple Wide Gamut",
        np.array([[0.725, 0.301], [0.221, 0.814], [0.068, -0.076]]),
        np.array([0.3127, 0.3290]),
    )
    colourspace.use_derived_transformation_matrices(True)

    colourspace_ACES2065_1 = colour.RGB_COLOURSPACES["ACES2065-1"]
    colourspace_ACES2065_1.use_derived_transformation_matrices(True)

    return matrix_transform(
        colour.matrix_RGB_to_RGB(
            colourspace,
            colourspace_ACES2065_1,
            chromatic_adaptation_transform="Bradford",
        )
    )


def generate_clf_transforms_apple(
    output_directory: Path,
) -> dict[Path, ocio.GroupTransform]:
    """
    Generate the *CLF* transforms for *Apple Log*, *Apple Log 2* and for the
    *Apple Log* curve.

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
    -   Apple. (September 22, 2023). Apple Log Profile.
        Retrieved February 2, 2024, from
        https://developer.apple.com/download/all/?q=Apple%20log%20profile
    -   Apple. (2025). Apple Log 2 Profile.
        Retrieved from
        https://developer.apple.com/download/all/?q=Apple%20log%20profile

    Notes
    -----
    -   The resulting *CLF* transforms still need to be reviewed by *Apple*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    aces_transform_id = (
        "urn:ampas:aces:transformId:v2.0:CSC.Apple.AppleLog_BT2020_to_ACES.a2.v1"
    )

    name = "Apple_Log_to_ACES2065-1"
    input_descriptor = "Apple Log"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    style = "APPLE_LOG_to_ACES2065-1"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_transform_id=aces_transform_id,
        style=style,
    )

    # "Apple Log 2" uses the same transfer function as "Apple Log" but encodes
    # in the "Apple Wide Gamut" primaries rather than "ITU-R BT.2020".

    aces_transform_id = (
        "urn:ampas:aces:transformId:v2.0:CSC.Apple.AppleLog2_to_ACES.a2.v1"
    )

    name = "Apple_Log_2_to_ACES2065-1"
    input_descriptor = "Apple Log 2"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    style = "APPLE_LOG-APPLEWG_to_ACES2065-1"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
        aces_transform_id=aces_transform_id,
        style=style,
    )

    # Generate transform for primaries only.

    name = "Linear_Apple_Wide_Gamut_to_ACES2065-1"
    input_descriptor = "Linear Apple Wide Gamut"
    output_descriptor = "ACES2065-1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [_build_apple_wg_mtx()],
        clf_transform_id,
        f"{input_descriptor} to {output_descriptor}",
        input_descriptor,
        output_descriptor,
    )

    # Generate `NamedTransform` for log curve only.

    name = "Apple_Log-Curve_to_Linear"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    input_descriptor = "Apple Log (arbitrary primaries)"
    output_descriptor = "Linear (arbitrary primaries)"
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CURVE - APPLE_LOG_to_LINEAR"
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

    generate_clf_transforms_apple(output_directory)
