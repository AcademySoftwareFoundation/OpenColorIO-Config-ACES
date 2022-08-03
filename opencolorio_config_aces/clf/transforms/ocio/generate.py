# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*OpenColorIO* CLF Transforms Generation
=======================================

Defines procedures for generating specific *Common LUT Format* (CLF)
transforms from the OpenColorIO project:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_ocio_input`
-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_utility`
"""

import PyOpenColorIO as ocio
from pathlib import Path

from opencolorio_config_aces.clf.discover.classify import (
    EXTENSION_CLF,
)
from opencolorio_config_aces.clf.transforms import (
    create_conversion_matrix,
    create_gamma,
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
    "VERSION_CLF",
    "generate_clf_transforms_ocio_input",
    "generate_clf_transforms_utility",
]

VERSION_CLF = "1.0"
"""
*CLF* transforms version.

VERSION_CLF : unicode
"""


def generate_clf_transforms_ocio_input(output_directory):
    """
    Generate the *OpenColorIO* *Input* *CLF* transforms.

    Returns
    -------
    dict
        Dictionary of *CLF* transforms and *OpenColorIO* group transform.
    """

    output_directory.mkdir(exist_ok=True)

    clf_transforms = {}

    filename = (
        output_directory / f"OCIO.Input.AP0_to_Rec709-sRGB{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "sRGB"),
                create_gamma("sRGB"),
            ]
        ),
        format_clf_transform_id("OCIO:Input:AP0_to_Rec709-sRGB", VERSION_CLF),
        "AP0 to Rec.709 - sRGB",
        filename,
        "ACES2065-1",
        "sRGB",
    )

    return clf_transforms


def generate_clf_transforms_utility(output_directory):
    """Generate OCIO Utility CLF transforms."""

    output_directory.mkdir(exist_ok=True)

    clf_transforms = {}

    filename = (
        output_directory / f"OCIO.Utility.Linear_to_Rec1886{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(transforms=[create_gamma(2.4)]),
        format_clf_transform_id("OCIO:Utility:Linear_to_Rec1886", VERSION_CLF),
        "Linear to Rec.1886",
        filename,
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    filename = output_directory / f"OCIO.Utility.Linear_to_sRGB{EXTENSION_CLF}"
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(transforms=[create_gamma("sRGB")]),
        format_clf_transform_id("OCIO:Utility:Linear_to_sRGB", VERSION_CLF),
        "Linear to sRGB",
        filename,
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    filename = (
        output_directory
        / f"OCIO.Utility.Linear_to_Rec709-Camera{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(transforms=[create_gamma("Rec709")]),
        format_clf_transform_id(
            "OCIO:Utility:Linear_to_Rec709-Camera", VERSION_CLF
        ),
        "Linear to Rec709-Camera",
        filename,
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    filename = (
        output_directory / f"OCIO.Utility.Linear_to_ST2084{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                ocio.BuiltinTransform(style="CURVE - LINEAR_to_ST-2084")
            ]
        ),
        format_clf_transform_id("OCIO:Utility:Linear_to_ST2084", VERSION_CLF),
        "Linear to ST2084",
        filename,
        "generic linear RGB",
        "generic ST2084 (PQ) encoded RGB",
    )

    filename = (
        output_directory / f"OCIO.Utility.AP0_to_P3-D65-Linear{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "P3-D65")]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_P3-D65-Linear", VERSION_CLF
        ),
        "AP0 to P3-D65 - Linear",
        filename,
        "ACES2065-1",
        "linear P3 primaries, D65 white point",
    )

    filename = (
        output_directory / f"OCIO.Utility.AP0_to_Rec2020-Linear{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.2020")
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec2020-Linear", VERSION_CLF
        ),
        "AP0 to Rec.2020 - Linear",
        filename,
        "ACES2065-1",
        "linear Rec.2020 primaries, D65 white point",
    )

    filename = (
        output_directory / f"OCIO.Utility.AP0_to_Rec709-Linear{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "ITU-R BT.709")]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec709-Linear", VERSION_CLF
        ),
        "AP0 to Rec.709 - Linear",
        filename,
        "ACES2065-1",
        "linear Rec.709 primaries, D65 white point",
    )

    filename = (
        output_directory
        / f"OCIO.Utility.AP0_to_Rec709-Gamma1.8{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(1.8),
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec709-Gamma1.8", VERSION_CLF
        ),
        "AP0 to Rec.709 - Gamma 1.8",
        filename,
        "ACES2065-1",
        "1.8 gamma-corrected Rec.709 primaries, D65 white point",
    )

    filename = (
        output_directory
        / f"OCIO.Utility.AP0_to_Rec709-Gamma2.2{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.2),
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec709-Gamma2.2", VERSION_CLF
        ),
        "AP0 to Rec.709 - Gamma 2.2",
        filename,
        "ACES2065-1",
        "2.2 gamma-corrected Rec.709 primaries, D65 white point",
    )

    filename = (
        output_directory
        / f"OCIO.Utility.AP0_to_Rec709-Gamma2.4{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.4),
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec709-Gamma2.4", VERSION_CLF
        ),
        "AP0 to Rec.709 - Gamma 2.4",
        filename,
        "ACES2065-1",
        "2.4 gamma-corrected Rec.709 primaries, D65 white point",
    )

    filename = (
        output_directory / f"OCIO.Utility.AP0_to_Rec709-Camera{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma("Rec709"),
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_Rec709-Camera", VERSION_CLF
        ),
        "AP0 to Rec.709 - Camera",
        filename,
        "ACES2065-1",
        "Rec.709 camera OETF Rec.709 primaries, D65 white point",
    )

    filename = (
        output_directory / f"OCIO.Utility.AP0_to_AP1-Gamma2.2{EXTENSION_CLF}"
    )
    clf_transforms[filename] = generate_clf_transform(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ACEScg"),
                create_gamma(2.2),
            ]
        ),
        format_clf_transform_id(
            "OCIO:Utility:AP0_to_AP1-Gamma2.2", VERSION_CLF
        ),
        "AP0 to AP1 - Gamma 2.2",
        filename,
        "ACES2065-1",
        "2.2 gamma-corrected AP1 primaries, D60 white point",
    )

    return clf_transforms


if __name__ == "__main__":
    output_directory = Path(__file__).parent.resolve()

    generate_clf_transforms_ocio_input(output_directory / "input")
    generate_clf_transforms_utility(output_directory / "utility")
