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
-   clf: Objects implementing support for *CLF* transforms generation.
-   config: Objects implementing support for the *OCIO* config generation.
-   utilities: Various utilities and data structures.
"""

from .config import (
    TRANSFORM_FACTORIES,
    colorspace_factory,
    group_transform_factory,
    look_factory,
    named_transform_factory,
    produce_transform,
    transform_factory,
    view_transform_factory,
)
from .config import (
    BUILTIN_TRANSFORMS,
    BUILD_CONFIGURATIONS,
    BUILD_VARIANT_FILTERERS,
    ConfigData,
    PROFILE_VERSION_DEFAULT,
    PROFILE_VERSIONS,
    BuildConfiguration,
    deserialize_config_data,
    generate_config,
    serialize_config_data,
    validate_config,
)
from .config import (
    build_aces_conversion_graph,
    classify_aces_ctl_transforms,
    conversion_path,
    ctl_transform_to_node,
    discover_aces_ctl_transforms,
    filter_amf_components,
    filter_ctl_transforms,
    filter_nodes,
    generate_amf_components,
    node_to_ctl_transform,
    plot_aces_conversion_graph,
    print_aces_taxonomy,
    unclassify_ctl_transforms,
    version_aces_dev,
)
from .config import (
    DescriptionStyle,
    generate_config_aces,
)
from .config import generate_config_cg, generate_config_studio
from .clf import (
    discover_clf_transforms,
    classify_clf_transforms,
    unclassify_clf_transforms,
    filter_clf_transforms,
    print_clf_taxonomy,
)
from .clf import generate_clf_transform

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "TRANSFORM_FACTORIES",
    "colorspace_factory",
    "group_transform_factory",
    "look_factory",
    "named_transform_factory",
    "produce_transform",
    "transform_factory",
    "view_transform_factory",
]
__all__ += [
    "BUILTIN_TRANSFORMS",
    "BUILD_CONFIGURATIONS",
    "BUILD_VARIANT_FILTERERS",
    "ConfigData",
    "PROFILE_VERSION_DEFAULT",
    "PROFILE_VERSIONS",
    "BuildConfiguration",
    "deserialize_config_data",
    "generate_config",
    "serialize_config_data",
    "validate_config",
]
__all__ += [
    "build_aces_conversion_graph",
    "classify_aces_ctl_transforms",
    "conversion_path",
    "ctl_transform_to_node",
    "discover_aces_ctl_transforms",
    "filter_amf_components",
    "filter_ctl_transforms",
    "filter_nodes",
    "generate_amf_components",
    "node_to_ctl_transform",
    "plot_aces_conversion_graph",
    "print_aces_taxonomy",
    "unclassify_ctl_transforms",
    "version_aces_dev",
]
__all__ += [
    "DescriptionStyle",
    "generate_config_aces",
]
__all__ += ["generate_config_cg", "generate_config_studio"]
__all__ += [
    "discover_clf_transforms",
    "classify_clf_transforms",
    "unclassify_clf_transforms",
    "filter_clf_transforms",
    "print_clf_taxonomy",
]
__all__ += ["generate_clf_transform"]

__application_name__ = "OpenColorIO Configuration for ACES"

__major_version__ = "3"
__minor_version__ = "0"
__patch_version__ = "0"
__version__ = f"{__major_version__}.{__minor_version__}.{__patch_version__}"
