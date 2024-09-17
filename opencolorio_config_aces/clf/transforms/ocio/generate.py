# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*OpenColorIO* CLF Transforms Generation
=======================================

Defines procedures for generating specific *Common LUT Format* (CLF)
transforms:

-   :func:`opencolorio_config_aces.clf.generate_clf_transforms_ocio`
"""

from pathlib import Path

from opencolorio_config_aces.clf.transforms import (
    clf_basename,
    format_clf_transform_id,
    gamma_transform,
    generate_clf_transform,
    matrix_RGB_to_RGB_transform,
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
    "generate_clf_transforms_ocio",
]

FAMILY = "OCIO"
"""
*CLF* transforms family.
"""

GENUS = "Utility"
"""
*CLF* transforms genus.
"""

VERSION = "1.0"
"""
*CLF* transforms version.
"""


@required("Colour")
def generate_clf_transforms_ocio(output_directory):
    """Generate OCIO Utility CLF transforms."""

    import colour

    output_directory.mkdir(parents=True, exist_ok=True)

    clf_transforms = {}

    name = "Linear_to_Rec1886-Curve"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [gamma_transform(2.4)],
        clf_transform_id,
        "Linear to Rec.1886",
        "generic linear RGB",
        "Rec.1886 encoded RGB",
    )

    name = "Linear_to_sRGB-Curve"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [gamma_transform("sRGB")],
        clf_transform_id,
        "Linear to sRGB",
        "generic linear RGB",
        "sRGB encoded RGB",
    )

    name = "Linear_to_ST2084-Curve"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    style = "CURVE - LINEAR_to_ST-2084"
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [{"transform_type": "BuiltinTransform", "style": style}],
        clf_transform_id,
        "Linear to ST.2084",
        "generic linear RGB",
        "generic ST.2084 (PQ) encoded RGB mapping 1.0 to 100nits",
        style=style,
    )

    name = "AP0_to_CIE_XYZ-D65-Scene-referred"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    M_ACES = colour.RGB_COLOURSPACES["ACES2065-1"].matrix_RGB_to_XYZ
    XYZ_ACES = colour.xy_to_XYZ(colour.RGB_COLOURSPACES["ACES2065-1"].whitepoint)
    XYZ_D65 = colour.xy_to_XYZ(
        colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    )
    M_XYZ = colour.algebra.matrix_dot(
        colour.adaptation.matrix_chromatic_adaptation_VonKries(
            XYZ_ACES, XYZ_D65, "Bradford"
        ),
        M_ACES,
    )
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [matrix_transform(M_XYZ)],
        clf_transform_id,
        "AP0 to CIE XYZ-D65",
        "ACES2065-1",
        "CIE XYZ, D65 white point",
    )

    name = "AP0_to_Linear_P3-D65"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [matrix_RGB_to_RGB_transform("ACES2065-1", "P3-D65")],
        clf_transform_id,
        "AP0 to Linear P3-D65",
        "ACES2065-1",
        "linear P3 primaries, D65 white point",
    )

    name = "AP0_to_Linear_Rec2020"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.2020")],
        clf_transform_id,
        "AP0 to Linear Rec.2020",
        "ACES2065-1",
        "linear Rec.2020 primaries, D65 white point",
    )

    name = "AP0_to_Linear_Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.709")],
        clf_transform_id,
        "AP0 to Linear Rec.709 (sRGB)",
        "ACES2065-1",
        "linear Rec.709 primaries, D65 white point",
    )

    name = "AP0_to_Linear_AdobeRGB"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [matrix_RGB_to_RGB_transform("ACES2065-1", "Adobe RGB (1998)")],
        clf_transform_id,
        "AP0 to Linear Adobe RGB (1998)",
        "ACES2065-1",
        "linear Adobe RGB (1998) primaries, D65 white point",
    )

    name = "AP0_to_sRGB-Encoded-Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "sRGB"),
            gamma_transform("sRGB"),
        ],
        clf_transform_id,
        "AP0 to sRGB Encoded Rec.709 (sRGB)",
        "ACES2065-1",
        "sRGB",
    )

    name = "AP0_to_Gamma1.8_Encoded_Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.709"),
            gamma_transform(1.8),
        ],
        clf_transform_id,
        "AP0 to Gamma 1.8 Encoded Rec.709",
        "ACES2065-1",
        "1.8 gamma-corrected Rec.709 primaries, D65 white point",
    )

    name = "AP0_to_Gamma2.2_Encoded_Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.709"),
            gamma_transform(2.2),
        ],
        clf_transform_id,
        "AP0 to Gamma 2.2 Encoded Rec.709",
        "ACES2065-1",
        "2.2 gamma-corrected Rec.709 primaries, D65 white point",
    )

    name = "AP0_to_Gamma2.4_Encoded_Rec709"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ITU-R BT.709"),
            gamma_transform(2.4),
        ],
        clf_transform_id,
        "AP0 to Gamma 2.4 Encoded Rec.709",
        "ACES2065-1",
        "2.4 gamma-corrected Rec.709 primaries, D65 white point",
    )

    name = "AP0_to_Gamma2.2_Encoded_AP1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ACEScg"),
            gamma_transform(2.2),
        ],
        clf_transform_id,
        "AP0 to Gamma 2.2 Encoded AP1",
        "ACES2065-1",
        "2.2 gamma-corrected AP1 primaries, ACES ~=D60 white point",
    )

    name = "AP0_to_sRGB_Encoded_AP1"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "ACEScg"),
            gamma_transform("sRGB"),
        ],
        clf_transform_id,
        "AP0 to sRGB Encoded AP1",
        "ACES2065-1",
        "sRGB Encoded AP1 primaries, ACES ~=D60 white point",
    )

    name = "AP0_to_sRGB_Encoded_P3-D65"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "Display P3"),
            gamma_transform("sRGB"),
        ],
        clf_transform_id,
        "AP0 to sRGB Encoded P3-D65",
        "ACES2065-1",
        "sRGB Encoded P3-D65 primaries, D65 white point",
    )

    name = "AP0_to_Gamma2.2_Encoded_AdobeRGB"
    clf_transform_id = format_clf_transform_id(FAMILY, GENUS, name, VERSION)
    filename = output_directory / clf_basename(clf_transform_id)
    clf_transforms[filename] = generate_clf_transform(
        filename,
        [
            matrix_RGB_to_RGB_transform("ACES2065-1", "Adobe RGB (1998)"),
            gamma_transform(563 / 256),
        ],
        clf_transform_id,
        "AP0 to Gamma 2.2 Encoded AdobeRGB",
        "ACES2065-1",
        "2.2 gamma-corrected AdobeRGB primaries, D65 white point",
    )

    return clf_transforms


if __name__ == "__main__":
    import logging

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    output_directory = Path(__file__).parent.resolve()

    generate_clf_transforms_ocio(output_directory / "utility")
