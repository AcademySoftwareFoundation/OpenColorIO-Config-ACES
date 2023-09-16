..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Process
=======

aces-dev Discovery & Classification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The config generation process starts with a set of definitions and classes to discover, parse and classify the CTL transforms from `aces-dev <https://github.com/ampas/aces-dev>`__:

-   :func:`opencolorio_config_aces.discover_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.classify_aces_ctl_transforms`
-   :func:`opencolorio_config_aces.print_aces_taxonomy`

.. note:: This approach allowed us to improve the consistency of the **CTL** transforms ``ACEStransformID`` while fixing various filename issues.

Using ``ACES2065-1`` and ``OCES`` as connection spaces, it is possible to build a colour conversion graph with all the high-level relevant transforms.

-   :func:`opencolorio_config_aces.build_aces_conversion_graph`
-   :func:`opencolorio_config_aces.plot_aces_conversion_graph`

.. only:: html

    .. image:: _static/ACES_Conversion_Graph.svg

Analytical & Reference Configs Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The colour conversion graph is then used to create the *Analytical* config that maps 1-to-1 the **aces-dev** **CTL** transforms to theoretical **OpenColorIO** builtin transforms.
This config does not work but it is useful to test basic generation capabilities whilst diagnosing issues in the mapping.

The *Reference* config is driven by a *CSV* file generated from a `spreadsheet <https://docs.google.com/spreadsheets/d/1SXPt-USy3HlV2G2qAvh9zit6ZCINDOlfKT07yXJdWLg>`__ mapping the ``ACEStransformID`` to **OpenColorIO** builtin transforms.

-   :func:`opencolorio_config_aces.generate_config_aces`

CLF Transforms Generation, Discovery & Classification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The working group decided to express additional colour transforms using `CLF <https://acescentral.com/knowledge-base-2/common-lut-format-clf>`__.
Some *CLF* transforms can be serialised into a config which reduces the need for external files. Each *CLF* transform has a ``CLFtransformID`` specified according to the `CLF Formatting for ACES OCIO Config <https://docs.google.com/document/d/1uYNnq1IlKqP8fRXnPviZHrAAu37ctvVsjJZeajOFF2A>`__ document.

The repository contains code to generate, discover and classify the additional *CLF* transforms that the *CG* and *Studio* configs require.

-   :func:`opencolorio_config_aces.discover_clf_transforms`
-   :func:`opencolorio_config_aces.classify_clf_transforms`
-   :func:`opencolorio_config_aces.print_clf_taxonomy`

CG Config Generation
^^^^^^^^^^^^^^^^^^^^

The *CG* config generator also uses a *CSV* file generated from a `spreadsheet <https://docs.google.com/spreadsheets/d/1nE95DEVtxtEkcIEaJk0WekyEH0Rcs8z_3fdwUtqP8V4>`__ that expresses which ``ACEStransformID`` should be used from the `Reference` config and which ``CLFtransformID`` should be used from the shipped *CLF* transforms.

-   :func:`opencolorio_config_aces.generate_config_cg`

The conversion process is as follows:

    *aces-dev Discovery & Classification* -> *Reference Config Generation* -> *CLF Transforms Generation, Discovery & Classification* -> *CG Config Generation*

Studio Config Generation
^^^^^^^^^^^^^^^^^^^^^^^^

The *Studio* config generator follows the same approach but uses a different `pivot table <https://docs.google.com/spreadsheets/d/1nE95DEVtxtEkcIEaJk0WekyEH0Rcs8z_3fdwUtqP8V4/edit#gid=1155125238>`__ of the spreadsheet.

-   :func:`opencolorio_config_aces.generate_config_studio`

The conversion process is as follows:

    *aces-dev Discovery & Classification* -> *Reference Config Generation* -> *CLF Transforms Generation, Discovery & Classification* -> *Studio Config Generation*
