# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*Utility* CLF Transforms Generation
===================================

Defines various objects related to the generation of the *Utility* specific
*Common LUT Format* (CLF) transforms.
"""

from pathlib import Path

from opencolorio_config_aces.utilities import required

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = ["generate_clf", "generate_clf_utility"]

THIS_DIR = Path(__file__).parent.resolve()
DEST_DIR = THIS_DIR / "ocio" / "utility"

TF_ID_PREFIX = "urn:aswf:ocio:transformId:1.0:OCIO:Utility:"
TF_ID_SUFFIX = ":1.0"


@required("Colour")
@required("OpenColorIO")
def create_matrix(matrix, offset=None):
    """
    Convert an NumPy array into an OCIO MatrixTransform.

    Parameters
    ----------
    matrix : array_like
        3x3 matrix.
    offset : array_like
        Optional RGB offsets.

    Returns
    -------
    ocio.MatrixTransform
        MatrixTransform representation of provided array(s).
    """

    import numpy as np
    import PyOpenColorIO as ocio

    matrix44 = np.zeros((4, 4))
    matrix44[3, 3] = 1.0
    for i in range(3):
        matrix44[i, 0:3] = matrix[i, :]

    offset4 = np.zeros(4)
    if offset is not None:
        offset4[0:3] = offset

    return ocio.MatrixTransform(
        matrix=list(matrix44.ravel()), offset=list(offset4)
    )


@required("Colour")
def create_conversion_matrix(input_prims, output_prims):
    """
    Calculate the RGB to RGB matrix for a pair of primaries as an OCIO
    MatrixTransform.

    Parameters
    ----------
    input_prims : str
        Input RGB colourspace name, as defined by colour-science.
    output_prims : str
        Output RGB colourspace name, as defined by colour-science.

    Returns
    -------
    ocio.MatrixTransform
        Conversion MatrixTransform.
    """

    import colour

    return create_matrix(
        colour.matrix_RGB_to_RGB(
            colour.RGB_COLOURSPACES[input_prims],
            colour.RGB_COLOURSPACES[output_prims],
            chromatic_adaptation_transform="Bradford",
        )
    )


@required("Colour")
@required("OpenColorIO")
def create_gamma(gamma):
    """
    Convert an gamma value into an OCIO ExponentTransform or
    ExponentWithLinearTransform.

    Parameters
    ----------
    gamma : float | str
        Exponent value or special gamma keyword (currently only 'sRGB' is
        supported).

    Returns
    -------
    ocio.Transform
        ExponentTransform or ExponentWithLinearTransform.
    """

    import numpy as np
    import PyOpenColorIO as ocio

    # NB: Preference of working group during 2021-11-23 mtg was *not* to clamp.
    direction = ocio.TRANSFORM_DIR_INVERSE

    if gamma == "sRGB":
        value = np.zeros(4)
        value[0:3] = 2.4
        value[3] = 1.0

        offset = np.zeros(4)
        offset[0:3] = 0.055

        exp_tf = ocio.ExponentWithLinearTransform(
            gamma=value,
            offset=offset,
            negativeStyle=ocio.NEGATIVE_LINEAR,
            direction=direction,
        )

    else:
        value = np.ones(4)
        value[0:3] = gamma

        exp_tf = ocio.ExponentTransform(
            value=value,
            negativeStyle=ocio.NEGATIVE_PASS_THRU,
            direction=direction,
        )

    return exp_tf


@required("OpenColorIO")
def generate_clf(group_tf, tf_id, tf_name, filename, input_desc, output_desc):
    """
    Take a GroupTransform and some metadata and write a CLF file.

    Parameters
    ----------
    group_tf : ocio.GroupTransform
        GroupTransform to build CLF operators from.
    tf_id : str
        CLF transform ID.
    tf_name : str
        CLF transform name.
    filename : str
        CLF filename.
    input_desc : str
        CLF input descriptor.
    output_desc : str
        CLF output descriptor.
    """

    import PyOpenColorIO as ocio

    metadata = group_tf.getFormatMetadata()
    metadata.setID(tf_id)
    metadata.setName(tf_name)
    metadata.addChildElement("InputDescriptor", input_desc)
    metadata.addChildElement("OutputDescriptor", output_desc)

    group_tf.write(
        formatName="Academy/ASC Common LUT Format",
        config=ocio.Config.CreateRaw(),
        fileName=str(DEST_DIR / filename),
    )


@required("OpenColorIO")
def generate_clf_utility():
    """Generate OCIO Utility CLF transforms."""

    import PyOpenColorIO as ocio

    if not DEST_DIR.exists():
        DEST_DIR.mkdir()

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "sRGB"),
                create_gamma("sRGB"),
            ]
        ),
        TF_ID_PREFIX + "AP0_to_Rec709-sRGB" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - sRGB",
        "OCIO.Utility.AP0_to_Rec709-sRGB.clf",
        "ACES2065-1",
        "sRGB",
    )

    generate_clf(
        ocio.GroupTransform(transforms=[create_gamma(2.4)]),
        TF_ID_PREFIX + "Linear_to_Rec1886" + TF_ID_SUFFIX,
        "Linear to Rec.1886",
        "OCIO.Utility.Linear_to_Rec1886.clf",
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    generate_clf(
        ocio.GroupTransform(transforms=[create_gamma("sRGB")]),
        TF_ID_PREFIX + "Linear_to_sRGB" + TF_ID_SUFFIX,
        "Linear to sRGB",
        "OCIO.Utility.Linear_to_sRGB.clf",
        "generic linear RGB",
        "generic gamma-corrected RGB",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "P3-D65")]
        ),
        TF_ID_PREFIX + "AP0_to_P3-D65-Linear" + TF_ID_SUFFIX,
        "AP0 to P3-D65 - Linear",
        "OCIO.Utility.AP0_to_P3-D65-Linear.clf",
        "ACES2065-1",
        "linear P3 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.2020")
            ]
        ),
        TF_ID_PREFIX + "AP0_to_Rec2020-Linear" + TF_ID_SUFFIX,
        "AP0 to Rec.2020 - Linear",
        "OCIO.Utility.AP0_to_Rec2020-Linear.clf",
        "ACES2065-1",
        "linear Rec.2020 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[create_conversion_matrix("ACES2065-1", "ITU-R BT.709")]
        ),
        TF_ID_PREFIX + "AP0_to_Rec709-Linear" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Linear",
        "OCIO.Utility.AP0_to_Rec709-Linear.clf",
        "ACES2065-1",
        "linear Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(1.8),
            ]
        ),
        TF_ID_PREFIX + "AP0_to_Rec709-Gamma1.8" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 1.8",
        "OCIO.Utility.AP0_to_Rec709-Gamma1.8.clf",
        "ACES2065-1",
        "1.8 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.2),
            ]
        ),
        TF_ID_PREFIX + "AP0_to_Rec709-Gamma2.2" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 2.2",
        "OCIO.Utility.AP0_to_Rec709-Gamma2.2.clf",
        "ACES2065-1",
        "2.2 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ITU-R BT.709"),
                create_gamma(2.4),
            ]
        ),
        TF_ID_PREFIX + "AP0_to_Rec709-Gamma2.4" + TF_ID_SUFFIX,
        "AP0 to Rec.709 - Gamma 2.4",
        "OCIO.Utility.AP0_to_Rec709-Gamma2.4.clf",
        "ACES2065-1",
        "2.4 gamma-corrected Rec.709 primaries, D65 white point",
    )

    generate_clf(
        ocio.GroupTransform(
            transforms=[
                create_conversion_matrix("ACES2065-1", "ACEScg"),
                create_gamma(2.2),
            ]
        ),
        TF_ID_PREFIX + "AP0_to_AP1-Gamma2.2" + TF_ID_SUFFIX,
        "AP0 to AP1 - Gamma 2.2",
        "OCIO.Utility.AP0_to_AP1-Gamma2.2.clf",
        "ACES2065-1",
        "2.2 gamma-corrected AP1 primaries, D60 white point",
    )


if __name__ == "__main__":
    generate_clf_utility()
