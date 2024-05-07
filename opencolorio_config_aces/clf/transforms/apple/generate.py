# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Apple* CLF Transforms Generation
=================================

Defines procedures for generating Apple *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_apple`
"""

from pathlib import Path

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
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
    "FAMILY",
    "GENUS",
    "VERSION",
    "generate_clf_transforms_apple",
]

FAMILY = "Apple"
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


def generate_clf_transforms_apple(output_directory):
    """
    Make the CLF file for Apple Log and for Apple Log curve CLF.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* `GroupTransform`
        instances.

    References
    ----------
    -   Apple. (September 22, 2023). Apple Log Profile.
        Retrieved February 2, 2024, from
        https://developer.apple.com/download/all/?q=Apple%20log%20profile

    Notes
    -----
    -   The resulting *CLF* transforms still need to be reviewed by *Apple*.
    """

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    aces_transform_id = (
        "urn:ampas:aces:transformId:v1.5:IDT.Apple.AppleLog_BT2020.a1.v1"
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
