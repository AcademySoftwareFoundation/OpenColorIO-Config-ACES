..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

OpenColorIO Configuration for ACES
==================================

.. start-badges

|actions| |artefacts|

.. |actions| image:: https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/actions/workflows/continuous-integration-quality-unit-tests.yml/badge.svg
    :target: https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/actions/workflows/continuous-integration-quality-unit-tests.yml
    :alt: Continuous Integration - Quality & Unit Tests

.. |artefacts| image:: https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/actions/workflows/configuration-artifacts.yml/badge.svg
    :target: https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES/actions/workflows/configuration-artifacts.yml
    :alt: Configuration Artifacts

.. end-badges

The `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
is an open-source `Python <https://www.python.org>`__ package implementing
support for the generation of the *OCIO* configurations for the
`Academy Color Encoding System <https://www.oscars.org/science-technology/sci-tech-projects/aces>`__
(ACES).

It is freely available under the
`New BSD License <https://opensource.org/licenses/BSD-3-Clause>`__ terms.

.. contents:: **Table of Contents**
    :backlinks: none
    :depth: 2

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

Installation
^^^^^^^^^^^^

Cloning the Repository
~~~~~~~~~~~~~~~~~~~~~~

The *OpenColorIO Configuration for ACES* repository uses `Git submodules <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`__
thus cloning the repository requires initializing them::

    git clone --recursive https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES.git

If you have already cloned the repository and forgot the ``--recursive``
argument, it is possible to initialize the submodules as follows::

    git submodule update --init --recursive

uv
~~

The *OpenColorIO Configuration for ACES* repository adopts `uv <https://github.com/astral-sh/uv>`__
to help managing its dependencies, this is the recommended way to get started
with development.

Assuming `python >= 3.10 <https://www.python.org/download/releases>`__ is
available on your system along with `OpenColorIO <https://opencolorio.org>`__,
the development dependencies are installed with `uv <https://github.com/astral-sh/uv>`__
as follows::

    git clone --recursive https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES.git
    cd OpenColorIO-Config-ACES
    uv sync --all-extras

The *aces-dev* *CTL* reference graph can be plotted but it requires `Graphviz <https://graphviz.org>`__
to be installed on the system.

Docker
~~~~~~

Installing the dependencies for the `previous config generator <https://github.com/imageworks/OpenColorIO-Configs>`__
was not a trivial task. For ease of use an `aswf-docker <https://github.com/AcademySoftwareFoundation/aswf-docker>`__
based container is now available.

Creating the container from the `Dockerfile <https://docs.docker.com/engine/reference/builder>`__
is done as follows::

    docker build -t aswf/opencolorio-config-aces:latest .

or alternatively, if the dependencies described in the next section are
satisfied::

    invoke docker build

Then, to run *bash* in the container::

    docker run -it -v ${PWD}:/home/aswf/OpenColorIO-Config-ACES aswf/opencolorio-config-aces:latest /bin/bash

Pypi
~~~~

The **OpenColorIO Configuration for ACES** package requires various
dependencies in order to run and be able to generate the *OCIO* configurations:

Primary Dependencies
********************

-   `python >= 3.10, < 3.14 <https://www.python.org/download/releases>`__
-   `opencolorio <https://pypi.org/project/opencolorio>`__
-   `requests <https://pypi.org/project/requests>`__
-   `semver <https://pypi.org/project/semver>`__

Optional Dependencies
*********************

-   `colour-science <https://pypi.org/project/colour-science>`__
-   `graphviz <https://www.graphviz.org>`__
-   `jsonpickle <https://jsonpickle.github.io>`__
-   `networkx <https://pypi.org/project/networkx>`__
-   `pydot <https://pypi.org/project/pydot>`__

Docs Dependencies
*****************

-   `pydata-sphinx-theme <https://pypi.org/project/pydata-sphinx-theme>`__
-   `sphinx <https://pypi.org/project/sphinx>`__

Development Dependencies
************************

-   `coverage <https://pypi.org/project/coverage>`__
-   `coveralls <https://pypi.org/project/coveralls>`__
-   `hatch <https://pypi.org/project/hatch>`__
-   `invoke <https://pypi.org/project/invoke>`__
-   `pre-commit <https://pypi.org/project/pre-commit>`__
-   `pyright <https://pypi.org/project/pyright>`__
-   `pytest <https://pypi.org/project/pytest>`__
-   `pytest-cov <https://pypi.org/project/pytest-cov>`__
-   `pytest-xdist <https://pypi.org/project/pytest-xdist>`__

Components Status
^^^^^^^^^^^^^^^^^

+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Component                     | Status         | Notes                                                                            |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *aces-dev* Discovery          | Complete       | Minor updates might be required when *aces-dev* is updated.                      |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Common Config Generator       | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *Reference* Config Generation | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *CG* Config Generation        | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Custom Config Generation      | In-Progress    | We are designing the components so that one can generate a custom *ACES* config. |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *Studio* Config Generation    | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *CLF* Transforms Discovery    | Complete       | Minor updates will be required if classification changes.                        |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| *CLF* Transforms Generation   | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Public API Surfacing          | In-Progress    | What is part of the Public API is not well defined currently.                    |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Unit Tests                    | In-Progress    |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| API Documentation             | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Continuous Integration        | Complete       |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| CLI                           | In-Progress    |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Containerisation              | Complete       | Minor updates will be required as the CLI evolves.                               |
+-------------------------------+----------------+----------------------------------------------------------------------------------+
| Pypi Package                  | Unavailable    |                                                                                  |
+-------------------------------+----------------+----------------------------------------------------------------------------------+

Usage
^^^^^

Tasks
~~~~~

Various tasks are currently exposed via `invoke <https://pypi.org/project/invoke>`__.

This is currently the recommended way to build the configuration until a
dedicated CLI is provided.

Listing the tasks is done as follows::

    invoke --list

Reference Config
****************

+-----------------------+----------------------------------------------+
| Task                  | Command                                      |
+-----------------------+----------------------------------------------+
| Build                 | ``invoke build-config-reference``            |
+-----------------------+----------------------------------------------+
| Build (Docker)        | ``invoke docker-run-build-config-reference`` |
+-----------------------+----------------------------------------------+
| Updating Mapping File | ``invoke update-mapping-file-reference``     |
+-----------------------+----------------------------------------------+

CG Config
*********

+-----------------------+---------------------------------------+
| Task                  | Command                               |
+-----------------------+---------------------------------------+
| Build                 | ``invoke build-config-cg``            |
+-----------------------+---------------------------------------+
| Build (Docker)        | ``invoke docker-run-build-config-cg`` |
+-----------------------+---------------------------------------+
| Updating Mapping File | ``invoke update-mapping-file-cg``     |
+-----------------------+---------------------------------------+

Studio Config
*************

+-----------------------+-------------------------------------------+
| Task                  | Command                                   |
+-----------------------+-------------------------------------------+
| Build                 | ``invoke build-config-studio``            |
+-----------------------+-------------------------------------------+
| Build (Docker)        | ``invoke docker-run-build-config-studio`` |
+-----------------------+-------------------------------------------+
| Updating Mapping File | ``invoke update-mapping-file-studio``     |
+-----------------------+-------------------------------------------+

API Reference
-------------

The main technical reference for `OpenColorIO Configuration for ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
is the `API Reference <https://opencolorio-config-aces.readthedocs.io>`__.

About
-----

| **OpenColorIO Configuration for ACES** by OpenColorIO Contributors
| Copyright Contributors to the OpenColorIO Project – `ocio-dev@lists.aswf.io <ocio-dev@lists.aswf.io>`__
| This software is released under terms of New BSD License: https://opensource.org/licenses/BSD-3-Clause
| `https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES <https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES>`__
