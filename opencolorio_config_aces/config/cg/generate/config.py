# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
*ACES* Computer Graphics (CG) Config Generator
==============================================

Defines various objects related to the generation of the *ACES* Computer
Graphics (CG) *OpenColorIO* config:

-   :func:`opencolorio_config_aces.generate_config_cg`
"""

import logging
import re
from collections.abc import Mapping
from datetime import datetime

from opencolorio_config_aces.config.generation import generate_config
from opencolorio_config_aces.config.reference import generate_config_aces
from opencolorio_config_aces.utilities import git_describe, required

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = ['generate_config_cg']


@required('OpenColorIO')
def generate_config_cg(config_name=None,
                       validate=True,
                       additional_data=False,
                       **kwargs):
    """
    Generates the *ACES* Computer Graphics (CG) *OpenColorIO* config.

    Parameters
    ----------
    config_name : unicode, optional
        *OpenColorIO* config file name, if given the config will be written to
        disk.
    validate : bool, optional
        Whether to validate the config.
    additional_data : bool, optional
        Whether to return additional data.

    Other Parameters
    ----------------
    config_mapping_file_path : unicode, optional
        {:func:`opencolorio_config_aces.generate_config_aces`},
        Path to the *CSV* mapping file used by the *Mapping* method.
    describe : int, optional
        {:func:`opencolorio_config_aces.generate_config_aces`},
        Any value from the
        :class:`opencolorio_config_aces.ColorspaceDescriptionStyle` enum.

    Returns
    -------
    Config or tuple
        *OpenColorIO* config or tuple of *OpenColorIO* config and
        :class:`opencolorio_config_aces.ConfigData` class instance.
    """

    settings = {}
    settings.update(kwargs)
    settings['additional_data'] = True
    settings['analytical'] = False

    _config, data = generate_config_aces(**settings)

    data.description = (
        f'The "Academy Color Encoding System" (ACES) "CG Config"'
        f'\n'
        f'------------------------------------------------------'
        f'\n\n'
        f'This minimalistic "OpenColorIO" config is geared toward computer '
        f'graphics artists requiring a lean config that does not include '
        f'typical VFX colorspaces, displays and looks.'
        f'\n\n'
        f'Generated with "OpenColorIO-Config-ACES" {git_describe()} '
        f'on the {datetime.now().strftime("%Y/%m/%d at %H:%M")}.')

    def multi_filters(array, filterers):
        """
        Applies givens filterers on given array.
        """

        return [
            element for element in array if all(
                filterer(element) for filterer in filterers)
        ]

    # TODO: Investigate how to drive all that from the spreadsheet.
    colorspace_filterers = [
        lambda x: not x.get('family', '').startswith('Input/'),
        lambda x: 'ADX' not in x.get('name', ''),
    ]
    data.colorspaces = multi_filters(data.colorspaces, colorspace_filterers)

    display_filterers = [
            lambda x: not re.search(
                'P3-D60|P3-DCI|Rec\\.1886 / Rec\\.2020 Video|Rec\\.2100-HLG',
                x.get('display', '') if isinstance(x, Mapping) else x),
        ]
    data.colorspaces = multi_filters(data.colorspaces, colorspace_filterers)
    data.views = multi_filters(data.views, display_filterers)

    view_filterers = [
            lambda x: not re.search(
                '108|2000|4000|\\bsim\\b',
                x.get('view', '') if isinstance(x, Mapping) else x),
        ]
    data.shared_views = multi_filters(data.shared_views, view_filterers)
    data.views = multi_filters(data.views, view_filterers)
    data.view_transforms = multi_filters(data.view_transforms, view_filterers)

    data.active_displays = multi_filters(data.active_displays,
                                         display_filterers)
    data.active_views = multi_filters(data.active_views, view_filterers)

    config = generate_config(data, config_name, validate)

    if additional_data:
        return config, data
    else:
        return config


if __name__ == '__main__':
    import os
    import opencolorio_config_aces
    from opencolorio_config_aces import serialize_config_data

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    build_directory = os.path.join(opencolorio_config_aces.__path__[0], '..',
                                   'build')

    if not os.path.exists(build_directory):
        os.makedirs(build_directory)

    config, data = generate_config_cg(
        config_name=os.path.join(build_directory, 'config-aces-cg.ocio'),
        additional_data=True)

    serialize_config_data(data,
                          os.path.join(build_directory, 'config-aces-cg.json'))
