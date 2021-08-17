# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Common CLF Transforms Generation
================================

Defines various objects related to the generation of the common
*Common LUT Format* (CLF) transforms:

-   :func:`opencolorio_config_aces.generate_clf`
"""

import logging
import re
from pathlib import Path

from opencolorio_config_aces.config.generation import (group_transform_factory,
                                                       transform_factory)
from opencolorio_config_aces.utilities import required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = ['matrix_3x3_to_4x4', 'generate_clf', 'generate_clf_common']


def matrix_3x3_to_4x4(M):
    """
    Converts given 3x3 matrix :math:`M` to a raveled 4x4 matrix.
    """

    import numpy as np

    M_I = np.identity(4)
    M_I[:3, :3] = M

    return np.ravel(M_I).tolist()


@required('OpenColorIO')
def generate_clf(clf_name, transforms, **kwargs):
    """
    Generates the *CLF* file for given transforms and given id.

    Parameters
    ----------
    clf_name : unicode
        *CLF* file name.
    transforms : array_like
        *OpenColorIO* transforms.

    Returns
    -------
    GroupTransform
        *OpenColorIO* group transform.
    """

    import PyOpenColorIO as ocio

    raw_config = ocio.Config.CreateRaw()
    group_transform = group_transform_factory(transforms)
    metadata = group_transform.getFormatMetadata()

    for kwarg, value in kwargs.items():
        method = re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(),
                        kwarg)
        method = f'set{method[0].upper()}{method[1:]}'
        if hasattr(metadata, method):
            getattr(metadata, method)(value)
        else:
            metadata.addChildElement(kwarg, value)

    group_transform.write('Academy/ASC Common LUT Format', str(clf_name),
                          raw_config)

    return group_transform


@required('Colour')
def generate_clf_common(directory):
    """
    Generates the *ACES* specific *Common LUT Format* (CLF) transforms.

    Parameters
    ----------
    directory : unicode
        Directory to write the *CLF* transforms to.

    Returns
    -------
    list
        *CLF* transform paths.
    """

    # import colour
    # import numpy as np

    directory = Path(directory)

    clf_transforms = []

    _M_dummy = [
        1.0000000000, 0.0000000000, 0.0000000000, 0.0000000000, 0.0000000000,
        1.0000000000, 0.0000000000, 0.0000000000, 0.0000000000, 0.0000000000,
        1.0000000000, 0.0000000000, 0.0000000000, 0.0000000000, 0.0000000000,
        1.0000000000
    ]
    _dummy_matrix_transform = transform_factory(**{
        'name': 'MatrixTransform',
        'matrix': _M_dummy,
    })
    _dummy_metadata = {
        'ID': 'Undefined',
        'name': 'Undefined',
        'description': 'Undefined'
    }

    # Common.OCIO.Linear_to_Rec1886.clf
    clf_path = directory / 'Common.OCIO.Linear_to_Rec1886.clf'
    _dummy_metadata['name'] = 'Linear to Rec.1886'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'Common.OCIO.Linear_to_Rec1886.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # Common.OCIO.Linear_to_sRGB.clf
    clf_path = directory / 'Common.OCIO.Linear_to_sRGB.clf'
    _dummy_metadata['name'] = 'Linear to sRGB'
    _dummy_metadata['ID'] = (
        'urn:aswf:ocio:transformId:v1.0:Common.OCIO.Linear_to_sRGB.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    return clf_transforms


if __name__ == '__main__':
    required('OpenColorIO')(lambda: None)()

    import opencolorio_config_aces
    import os
    import shutil

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(opencolorio_config_aces.__path__[0], '..',
                                   'build')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    matrix_transform = opencolorio_config_aces.transform_factory(
        **{
            'name':
            'MatrixTransform',
            'matrix': [
                0.4387956642, 0.3825367756, 0.1787151431, 0.0000000000,
                0.0890560064, 0.8126211313, 0.0982957371, 0.0000000000,
                0.0173063724, 0.1083658908, 0.8742745984, 0.0000000000,
                0.0000000000, 0.0000000000, 0.0000000000, 1.0000000000
            ],
        })
    generate_clf(
        os.path.join(build_directory, 'Utility_sRGB_Linear.clf'),
        [matrix_transform],
        ID='Utility-sRGB-Linear',
        name='Utility - sRGB - Linear',
        description='Conversion from sRGB gamut to ACES2065-1 gamut.')

    build_directory = os.path.join(
        opencolorio_config_aces.clf.discover.classify.CLF_TRANSFORMS_ROOT,
        'common')

    if os.path.exists(build_directory):
        shutil.rmtree(build_directory)

    os.makedirs(build_directory)

    clf_transforms = generate_clf_common(build_directory)
