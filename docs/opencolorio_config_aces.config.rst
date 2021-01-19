..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Generation
==========

.. contents:: :local:

Config Generation Common Objects
--------------------------------

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    colorspace_factory
    view_transform_factory
    ConfigData
    validate_config
    generate_config

Reference Configuration
-----------------------

*aces-dev* Discovery
~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    discover_aces_ctl_transforms
    classify_aces_ctl_transforms
    unclassify_ctl_transforms
    filter_ctl_transforms
    print_aces_taxonomy

*aces-dev* Conversion Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    build_aces_conversion_graph
    node_to_builtin_transform
    node_to_ctl_transform
    ctl_transform_to_node
    filter_nodes
    conversion_path
    plot_aces_conversion_graph

*aces-dev* Reference Config Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    generate_config_aces
