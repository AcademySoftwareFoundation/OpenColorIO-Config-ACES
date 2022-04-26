# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
CLF Generation Utilities
========================

Defines various utility functions for generating *Common LUT Format*
(CLF) transforms.
"""

import PyOpenColorIO as ocio

from opencolorio_config_aces.utilities import required

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "create_matrix",
    "create_conversion_matrix",
    "create_gamma",
    "generate_clf",
]


@required("Colour")
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
def create_conversion_matrix(input_primaries, output_primaries):
    """
    Calculate the RGB to RGB matrix for a pair of primaries as an OCIO
    MatrixTransform.

    Parameters
    ----------
    input_primaries : str
        Input RGB colourspace name, as defined by colour-science.
    output_primaries : str
        Output RGB colourspace name, as defined by colour-science.

    Returns
    -------
    ocio.MatrixTransform
        Conversion MatrixTransform.
    """

    import colour

    return create_matrix(
        colour.matrix_RGB_to_RGB(
            colour.RGB_COLOURSPACES[input_primaries],
            colour.RGB_COLOURSPACES[output_primaries],
            chromatic_adaptation_transform="Bradford",
        )
    )


@required("Colour")
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


def generate_clf(group_tf, tf_id, tf_name, filename, input_desc, output_desc, aces_id=None):
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
    aces_id : str
        ACES TransformID (default is None).
    """

    metadata = group_tf.getFormatMetadata()
    metadata.setID(tf_id)
    metadata.setName(tf_name)
    metadata.addChildElement("InputDescriptor", input_desc)
    metadata.addChildElement("OutputDescriptor", output_desc)
    if aces_id is not None:
        fmdg.addChildElement('Info', '')
        info = fmdg.getChildElements()[2]
        info.addChildElement('ACEStransformID', aces_id)

    group_tf.write(
        formatName="Academy/ASC Common LUT Format",
        config=ocio.Config.CreateRaw(),
        fileName=str(filename),
    )
