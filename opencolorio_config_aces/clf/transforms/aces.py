# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ACES* CLF Transforms Generation
================================

Defines various objects related to the generation of the *ACES* specific
*Common LUT Format* (CLF) transforms.
"""

import logging
from pathlib import Path

from opencolorio_config_aces.clf import generate_clf, matrix_3x3_to_4x4
from opencolorio_config_aces.config.generation import transform_factory
from opencolorio_config_aces.utilities import required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = ['generate_clf_aces']


@required('Colour')
def generate_clf_aces(directory):
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

    import colour

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

    # ACES.OCIO.AP0_to_Rec709-sRGB
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.709-sRGB.clf'
    _dummy_metadata['name'] = 'AP0 to Rec.709 - sRGB'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.AP0_to_Rec709-sRGB.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.Rec709-sRGB_to_AP0
    clf_path = directory / 'ACES.OCIO.Rec.709-sRGB_to_AP0.clf'
    _dummy_metadata['name'] = 'sRGB - Rec.709 to AP0'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.Rec709-sRGB_to_AP0.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_Rec709-Gamma1pnt8
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.709-Gamma1.8.clf'
    _dummy_metadata['name'] = 'AP0 to Rec.709 - Gamma 1.8'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.AP0_to_Rec709-Gamma1pnt8.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_Rec709-Gamma2pnt2
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.709-Gamma2.2.clf'
    _dummy_metadata['name'] = 'AP0 to Rec.709 - Gamma 2.2'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.AP0_to_Rec709-Gamma2pnt2.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_Rec709-Gamma2pnt4
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.709-Gamma2.4.clf'
    _dummy_metadata['name'] = 'AP0 to Rec.709 - Gamma 2.4'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.AP0_to_Rec709-Gamma2pnt4.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_AP1-Gamma2pnt2
    clf_path = directory / 'ACES.OCIO.AP0_to_AP1-Gamma2.2.clf'
    _dummy_metadata['name'] = 'AP0 to AP1 - Gamma 2.2'
    _dummy_metadata['ID'] = ('urn:aswf:ocio:transformId:v1.0:'
                             'ACES.OCIO.AP0_to_AP1-Gamma2pnt2.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_P3-D65
    clf_path = directory / 'ACES.OCIO.AP0_to_P3-D65.clf'
    _dummy_metadata['name'] = 'AP0 to P3-D6'
    _dummy_metadata['ID'] = (
        'urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_P3-D65.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_Rec709
    M_AP0_to_Rec709 = matrix_3x3_to_4x4(
        colour.matrix_RGB_to_RGB(
            colour.RGB_COLOURSPACES['ACES2065-1'],
            colour.RGB_COLOURSPACES['ITU-R BT.709'],
            'CAT02',
        ))
    matrix_transform = transform_factory(**{
        'name': 'MatrixTransform',
        'matrix': M_AP0_to_Rec709,
    })
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.709.clf'
    metadata = {
        'ID': 'urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_Rec709.c1.v1',
        'name': 'AP0 to Rec.709',
        'description': 'Conversion from ACES2065-1 gamut to Rec.709 gamut.'
    }
    generate_clf(clf_path, [matrix_transform], **metadata)
    clf_transforms.append(clf_path)

    # ACES.OCIO.AP0_to_Rec2020
    clf_path = directory / 'ACES.OCIO.AP0_to_Rec.2020.clf'
    _dummy_metadata['name'] = 'AP0 to Rec.2020'
    _dummy_metadata['ID'] = (
        'urn:aswf:ocio:transformId:v1.0:ACES.OCIO.AP0_to_Rec2020.c1.v1')
    generate_clf(clf_path, [_dummy_matrix_transform], **_dummy_metadata)
    clf_transforms.append(clf_path)

    return clf_transforms


if __name__ == '__main__':
    import opencolorio_config_aces
    import os
    import shutil

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(
        opencolorio_config_aces.clf.discover.classify.ROOT_TRANSFORMS_CLF,
        'aces')

    if os.path.exists(build_directory):
        shutil.rmtree(build_directory)

    os.makedirs(build_directory)

    clf_transforms = generate_clf_aces(build_directory)
