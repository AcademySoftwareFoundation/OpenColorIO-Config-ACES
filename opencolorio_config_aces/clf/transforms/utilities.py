# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
CLF Generation Utilities
========================

Defines various utility functions for generating *Common LUT Format*
(CLF) transforms.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

import numpy as np
import PyOpenColorIO as ocio
from numpy.typing import ArrayLike

from opencolorio_config_aces.clf.discover.classify import (
    EXTENSION_CLF,
    SEPARATOR_ID_CLF,
    URN_CLF,
)
from opencolorio_config_aces.config import produce_transform, transform_factory
from opencolorio_config_aces.utilities import required

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "matrix_transform",
    "matrix_RGB_to_RGB_transform",
    "gamma_transform",
    "generate_clf_transform",
    "format_clf_transform_id",
    "clf_basename",
]

LOGGER = logging.getLogger(__name__)


@required("Colour")
def matrix_transform(
    matrix: ArrayLike, offset: ArrayLike | None = None
) -> ocio.MatrixTransform:
    """
    Convert given *NumPy* array into an *OpenColorIO* `MatrixTransform`.

    Parameters
    ----------
    matrix
        3x3 matrix.
    offset
        Optional RGB offsets.

    Returns
    -------
    :class:`ocio.MatrixTransform`
        `MatrixTransform` representation of provided array(s).
    """

    matrix44 = np.zeros((4, 4))
    matrix44[3, 3] = 1.0
    for i in range(3):
        matrix44[i, 0:3] = matrix[i, :]  # pyright: ignore

    offset4 = np.zeros(4)
    if offset is not None:
        offset4[0:3] = offset

    return transform_factory(
        transform_type="MatrixTransform",
        matrix=list(matrix44.ravel()),
        offset=list(offset4),
    )


@required("Colour")
def matrix_RGB_to_RGB_transform(
    input_primaries: str,
    output_primaries: str,
    adaptation: colour.hints.LiteralChromaticAdaptationTransform = "Bradford",  # noqa: F821  # pyright: ignore
) -> ocio.MatrixTransform:
    """
    Calculate the *RGB* to *RGB* matrix for a pair of primaries and produce an
    *OpenColorIO* `MatrixTransform`.

    Parameters
    ----------
    input_primaries
        Input RGB colourspace name, as defined by colour-science.
    output_primaries
        Output RGB colourspace name, as defined by colour-science.
    adaptation
        Chromatic adaptation method to use, as defined by colour-science.
        Defaults to "Bradford" to match what is most commonly used in ACES.

    Returns
    -------
    :class:`ocio.MatrixTransform`
        *OpenColorIO* `MatrixTransform`.
    """

    import colour

    input_space = colour.RGB_COLOURSPACES[input_primaries]
    input_space.use_derived_transformation_matrices(True)
    output_space = colour.RGB_COLOURSPACES[output_primaries]
    output_space.use_derived_transformation_matrices(True)

    return matrix_transform(
        colour.matrix_RGB_to_RGB(
            input_space,
            output_space,
            chromatic_adaptation_transform=adaptation,
        )
    )


def gamma_transform(
    gamma: float | Literal["sRGB", "Rec709"],
) -> ocio.ExponentTransform | ocio.ExponentWithLinearTransform:
    """
    Convert a gamma value into an *OpenColorIO* `ExponentTransform` or
    `ExponentWithLinearTransform`.

    Parameters
    ----------
    gamma
        Exponent value or special gamma keyword (currently only 'sRGB' is
        supported).

    Returns
    -------
    :class:`ocio.ExponentTransform` or :class:`ocio.ExponentWithLinearTransform`
         *OpenColorIO* `ExponentTransform` or `ExponentWithLinearTransform`.
    """

    # NB: Preference of working group during 2021-11-23 mtg was *not* to clamp.
    direction = ocio.TRANSFORM_DIR_INVERSE

    if gamma == "sRGB":
        value = np.zeros(4)
        value[0:3] = 2.4
        value[3] = 1.0

        offset = np.zeros(4)
        offset[0:3] = 0.055

        exp_tf = transform_factory(
            transform_type="ExponentWithLinearTransform",
            gamma=value,
            offset=offset,
            negativeStyle=ocio.NEGATIVE_LINEAR,
            direction=direction,
        )

    elif gamma == "Rec709":
        value = np.zeros(4)
        value[0:3] = 1.0 / 0.45
        value[3] = 1.0

        offset = np.zeros(4)
        offset[0:3] = 0.099

        exp_tf = transform_factory(
            transform_type="ExponentWithLinearTransform",
            gamma=value,
            offset=offset,
            negativeStyle=ocio.NEGATIVE_LINEAR,
            direction=direction,
        )

    else:
        value = np.ones(4)
        value[0:3] = gamma

        exp_tf = transform_factory(
            transform_type="ExponentTransform",
            value=value,
            negativeStyle=ocio.NEGATIVE_PASS_THRU,
            direction=direction,
        )

    return exp_tf


def generate_clf_transform(
    filename: Path | str,
    transforms: list,
    clf_transform_id: str,
    name: str,
    input_desc: str,
    output_desc: str,
    aces_transform_id: str | None = None,
    style: str | None = None,
) -> ocio.GroupTransform:
    """
    Take a list of transforms and some metadata and write a *CLF* transform
    file.

    Parameters
    ----------
    filename
        *CLF* filename.
    transforms
        Transforms to generate the *CLF* transform file for.
    clf_transform_id
        *CLFtransformID*.
    name
        *CLF* transform name.
    input_desc
        *CLF* input descriptor.
    output_desc
        *CLF* output descriptor.
    aces_transform_id
        *ACEStransformID*.
    style
        *OpenColorIO* builtin transform style.

    Returns
    -------
    :class:`ocio.GroupTransform`
        Updated `GroupTransform`.
    """

    LOGGER.info('Creating "%s" "CLF" transform...', clf_transform_id)

    group_tf = produce_transform(transforms)

    metadata = group_tf.getFormatMetadata()
    metadata.setID(clf_transform_id)
    metadata.setName(name)
    metadata.addChildElement("InputDescriptor", input_desc)
    metadata.addChildElement("OutputDescriptor", output_desc)

    if aces_transform_id is not None or style is not None:
        metadata.addChildElement("Info", "")
        info = metadata.getChildElements()[2]

        if aces_transform_id:
            info.addChildElement("ACEStransformID", aces_transform_id)

        if style:
            info.addChildElement("BuiltinTransform", style)

    LOGGER.info('Writing "%s" "CLF" transform to "%s".', clf_transform_id, filename)

    group_tf.write(
        formatName="Academy/ASC Common LUT Format",
        config=ocio.Config.CreateRaw(),
        fileName=str(filename),
    )

    return group_tf


def format_clf_transform_id(family: str, genus: str, name: str, version: str) -> str:
    """
    Format given *CLF* transform attributes to produce a *CLFtransformID*.

    Parameters
    ----------
    family
        *CLF* transform family.
    genus
        *CLF* transform genus.
    name
        *CLF* transform name.
    version
        *CLF* transform version.

    Returns
    -------
    :class:`str`
        *CLFtransformID*.

    Examples
    --------
    >>> format_clf_transform_id("OCIO", "Input", "AP0_to_sRGB-Rec709", "1.0")
    'urn:aswf:ocio:transformId:1.0:OCIO:Input:AP0_to_sRGB-Rec709:1.0'
    """

    return SEPARATOR_ID_CLF.join([URN_CLF, family, genus, name, version])


def clf_basename(clf_transform_id: str) -> str:
    """
    Generate a *CLF* basename from given *CLFtransformID*.

    Parameters
    ----------
    clf_transform_id
        *CLFtransformID*

    Returns
    -------
    :class:`str`
        *CLF* transform filename.

    Examples
    --------
    >>> clf_basename(
    ...     "urn:aswf:ocio:transformId:1.0:OCIO:Input:AP0_to_sRGB-Rec709:1.0")
    'OCIO.Input.AP0_to_sRGB-Rec709.clf'
    """

    tokens = clf_transform_id.replace(f"{URN_CLF}{SEPARATOR_ID_CLF}", "").split(
        SEPARATOR_ID_CLF
    )

    stem = ".".join(tokens[:-1])
    stem = re.sub(r"\.Linear_to_", ".", stem)
    stem = re.sub("_to_Linear$", "", stem)

    return f"{stem}{EXTENSION_CLF}"
