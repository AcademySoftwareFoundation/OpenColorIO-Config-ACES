..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

OpenColorIO Configuration for ACES
==================================

..  image:: https://via.placeholder.com/720x320.png?text=WARNING: This+repository+is+under+construction!

The `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/>`__
is an open-source `Python <https://www.python.org/>`__ package implementing
support for the generation of the *OCIO* configurations for the
`Academy Color Encoding System <https://www.oscars.org/science-technology/sci-tech-projects/aces>`__
(ACES).

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

Docker
^^^^^^

Installing the dependencies for the `previous config generator <https://github.com/imageworks/OpenColorIO-Configs>`__
was not a trivial task. For ease of use an `aswf-docker <https://github.com/AcademySoftwareFoundation/aswf-docker>`__
based container is now available.

Creating the container from the `Dockerfile <https://docs.docker.com/engine/reference/builder/>`__
is done as follows::

    docker build -t aswf/opencolorio-config-aces:latest .

or alternatively, if the dependencies described in the next section are
satisfied::

    invoke docker build

Then, to run *bash* in the container::

    docker run -it -v ${PWD}:/home/aswf/OpenColorIO-Config-ACES aswf/opencolorio-config-aces:latest /bin/bash


Pypi
^^^^

The **OpenColorIO Configuration for ACES** package requires various
dependencies in order to run and be able to generate the *OCIO* configurations:

Primary Dependencies
********************

-   `python>=3.7 <https://www.python.org/download/releases/>`__
-   `networkx <https://pypi.org/project/networkx/>`__
-   `OpenColorIO <https://opencolorio.org/>`__

Plotting Dependencies
*********************

-   `graphviz <https://www.graphviz.org/>`__
-   `pygraphviz <https://pypi.org/project/pygraphviz/>`__

Development Dependencies
************************

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

Once the dependencies are satisfied, the **OpenColorIO Configuration for ACES**
package can be installed from the `Python Package Index <http://pypi.python.org/pypi/opencolorio-config-aces>`__
by issuing this command in a shell::

    pip install --user opencolorio-config-aces

Usage
-----

Tasks
^^^^^

Various tasks are currently exposed via `invoke <https://pypi.org/project/invoke/>`__.

This is currently the recommended way to build the configuration until a
dedicated CLI is provided.

Listing the tasks is done as follows::

    invoke --list

Assuming the dependencies are satisfied, the task to build the reference
configuration is::

    invoke build-reference-config

Alternatively, with the docker container built::

    invoke docker-run-build-reference-config

API
^^^

The main reference for `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
is the `manual <https://opencolorio-config-aces.readthedocs.io/>`__.

.. toctree::
    :maxdepth: 3

    manual

About
-----

| **OpenColorIO Configuration for ACES** by OpenColorIO Contributors
| Copyright Contributors to the OpenColorIO Project – `ocio-dev@lists.aswf.io <ocio-dev@lists.aswf.io>`__
| This software is released under terms of New BSD License: https://opensource.org/licenses/BSD-3-Clause
| `https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
