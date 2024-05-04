..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

OpenColorIO Configuration for ACES
==================================

The `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
is an open-source `Python <https://www.python.org>`__ package implementing
support for the generation of the *OCIO* configurations for the
`Academy Color Encoding System <https://www.oscars.org/science-technology/sci-tech-projects/aces>`__
(ACES).

It is freely available under the
`New BSD License <https://opensource.org/licenses/BSD-3-Clause>`__ terms.

.. sectnum::

Features
--------

The following features are available:

-   Automatic *OCIO* **Reference** configuration generation for *aces-dev*
    *CTL* reference implementation.

    -   Discovery of *aces-dev* *CTL* transforms.
    -   Generation of the *CTL* transforms graph.
    -   `Spreadsheet <https://docs.google.com/spreadsheets/d/1z3xsy3sF0I-8AN_tkMOEjHlAs13ba7VAVhrE8v4WIyo>`__-driven generation.

-   Generators producing the *OCIO* **CG** and **Studio** configurations.
    -   `Spreadsheet <https://docs.google.com/spreadsheets/d/1PXjTzBVYonVFIceGkLDaqcEJvKR6OI63DwZX0aajl3A>`__-driven generation.

-   Included *CLF* transforms along with generator and discovery support.

User Guide
----------

.. toctree::
    :maxdepth: 2

    user-guide

API Reference
-------------

.. toctree::
    :maxdepth: 2

    reference

About
-----

| **OpenColorIO Configuration for ACES** by OpenColorIO Contributors
| Copyright Contributors to the OpenColorIO Project – `ocio-dev@lists.aswf.io <ocio-dev@lists.aswf.io>`__
| This software is released under terms of New BSD License: https://opensource.org/licenses/BSD-3-Clause
| `https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
