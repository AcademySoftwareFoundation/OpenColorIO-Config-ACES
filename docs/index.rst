OpenColorIO Configuration for ACES
==================================

..  image:: https://via.placeholder.com/720x320.png?text=WARNING: This+repository+is+under+construction!

The `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/>`__
is an open-source `Python <https://www.python.org/>`__ package implementing
support for the generation of the *OCIO* configuration for the
*Academy Color Encoding System* (ACES).

It is freely available under the
`New BSD License <https://opensource.org/licenses/BSD-3-Clause>`__ terms.

.. contents:: **Table of Contents**
    :backlinks: none
    :depth: 3

.. sectnum::

Features
--------

The following features are available:

-   Automatic *OCIO* **Reference** configuration generation for *aces-dev*
    *CTL* reference implementation.
-   Configurable generator producing the *OCIO* **Studio** configuration.

Installation
------------

Primary Dependencies
^^^^^^^^^^^^^^^^^^^^

-   `python>=3.7 <https://www.python.org/download/releases/>`__
-   `networkx <https://pypi.org/project/networkx/>`__

Plotting Dependencies
^^^^^^^^^^^^^^^^^^^^^

-   `graphviz <https://www.graphviz.org/>`__

Development Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^

-   `coverage <https://pypi.org/project/coverage/>`__
-   `coveralls <https://pypi.org/project/coveralls/>`__
-   `flake8 <https://pypi.org/project/flake8/>`__
-   `invoke <https://pypi.org/project/invoke/>`__
-   `nose <https://pypi.org/project/nose/>`__
-   `pre-commit <https://pypi.org/project/pre-commit/>`__
-   `pytest <https://pypi.org/project/pytest/>`__
-   `restructuredtext-lint <https://pypi.org/project/restructuredtext-lint/>`__
-   `sphinx <https://pypi.org/project/Sphinx/>`__
-   `sphinx-rtd-theme <https://pypi.org/project/sphinx-rtd-theme/>`__
-   `twine <https://pypi.org/project/twine/>`__
-   `yapf==0.23.0 <https://pypi.org/project/yapf/>`__

Pypi
^^^^

Once the dependencies satisfied, the **OpenColorIO Configuration for ACES** can
be installed from the `Python Package Index <http://pypi.python.org/pypi/opencolorio-config-aces>`__
by issuing this command in a shell::

	pip install opencolorio-config-aces

Usage
-----

API
^^^

The main reference for `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
is the manual:

.. toctree::
    :maxdepth: 4

    manual

About
-----

| **OpenColorIO Configuration for ACES** by OpenColorIO Contributors
| Copyright Contributors to the OpenColorIO Project – `ocio-dev@lists.aswf.io <ocio-dev@lists.aswf.io>`__
| This software is released under terms of New BSD License: https://opensource.org/licenses/BSD-3-Clause
| `https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
