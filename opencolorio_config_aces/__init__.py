# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
OpenColorIO Configuration for ACES
==================================

The `OpenColorIO Configuration for ACES \
<https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/>`__ is
an open-source `Python <https://www.python.org/>`__ package implementing
support for the generation of the *OCIO* configuration for the
*Academy Color Encoding System* (ACES).

It is freely available under the
`New BSD License <https://opensource.org/licenses/BSD-3-Clause>`__ terms.

Sub-packages
------------
-   config: Objects implementing support for the *OCIO* config generation.
-   utilities: Various utilities and data structures.
"""

from .config import (
    ConfigData, build_aces_conversion_graph, classify_aces_ctl_transforms,
    colorspace_factory, conversion_path, ctl_transform_to_node,
    deserialize_config_data, discover_aces_ctl_transforms,
    filter_ctl_transforms, filter_nodes, generate_config, generate_config_aces,
    generate_config_cg, group_transform_factory, look_factory,
    produce_transform, node_to_ctl_transform, plot_aces_conversion_graph,
    print_aces_taxonomy, serialize_config_data, transform_factory,
    unclassify_ctl_transforms, validate_config, view_transform_factory)

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'ConfigData', 'build_aces_conversion_graph',
    'classify_aces_ctl_transforms', 'colorspace_factory', 'conversion_path',
    'ctl_transform_to_node', 'deserialize_config_data',
    'discover_aces_ctl_transforms', 'filter_ctl_transforms', 'filter_nodes',
    'generate_config', 'generate_config_aces', 'generate_config_cg',
    'group_transform_factory', 'look_factory', 'produce_transform',
    'node_to_ctl_transform', 'plot_aces_conversion_graph',
    'print_aces_taxonomy', 'serialize_config_data', 'transform_factory',
    'unclassify_ctl_transforms', 'validate_config', 'view_transform_factory'
]

__application_name__ = 'OpenColorIO Configuration for ACES'

__major_version__ = '0'
__minor_version__ = '1'
__change_version__ = '1'
__version__ = '.'.join(
    (__major_version__,
     __minor_version__,
     __change_version__))  # yapf: disable
