..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Generation
==========

Config Generation Common Objects
--------------------------------

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    ConfigData
    VersionData
    deserialize_config_data
    generate_config
    serialize_config_data
    validate_config

Factories
~~~~~~~~~

``opencolorio_config_aces``

.. autosummary::
    :toctree: generated/

    TRANSFORM_FACTORIES
    colorspace_factory
    group_transform_factory
    look_factory
    named_transform_factory
    produce_transform
    transform_factory
    transform_factory_clf_transform_to_group_transform
    transform_factory_default
    view_transform_factory

Reference Configuration
-----------------------

*aces-dev* Discovery
~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    version_aces_dev
    classify_aces_ctl_transforms
    discover_aces_ctl_transforms
    filter_ctl_transforms
    print_aces_taxonomy
    unclassify_ctl_transforms

*aces-dev* Conversion Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    build_aces_conversion_graph
    conversion_path
    ctl_transform_to_node
    filter_nodes
    node_to_ctl_transform
    plot_aces_conversion_graph

*aces-dev* Reference Config Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    ColorspaceDescriptionStyle
    generate_config_aces

*ACES* Computer Graphics (CG) Config Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/

    generate_config_cg

*ACES* Studio Config Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opencolorio_config_aces``

.. currentmodule:: opencolorio_config_aces

.. autosummary::
    :toctree: generated/
