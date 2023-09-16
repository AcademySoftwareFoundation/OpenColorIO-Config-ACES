..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Installation Guide
==================

Cloning the Repository
----------------------

The *OpenColorIO Configuration for ACES* repository uses `Git submodules <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`__
thus cloning the repository requires initializing them::

    git clone --recursive https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES.git

If you have already cloned the repository and forgot the `--recursive`
argument, it is possible to initialize the submodules as follows::

    git submodule update --init --recursive

Poetry
------

The *OpenColorIO Configuration for ACES* repository adopts `Poetry <https://poetry.eustace.io>`__
to help managing its dependencies, this is the recommended way to get started
with development.

Assuming `python >= 3.9 <https://www.python.org/download/releases>`__ is
available on your system along with `OpenColorIO >= 2 <https://opencolorio.org>`__,
the development dependencies are installed with `Poetry <https://poetry.eustace.io>`__
as follows::

    git clone --recursive https://github.com/AcademySoftwareFoundation/OpenColorIO-Config-ACES.git
    cd OpenColorIO-Config-ACES
    poetry install --with optional

The *aces-dev* *CTL* reference graph can be plotted but it requires `Graphviz <https://graphviz.org>`__
to be installed on the system and having installed the optional `pygraphviz <https://pypi.org/project/pygraphviz>`__:
python package::

    poetry install --with graphviz,optional

Docker
------

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
----

The **OpenColorIO Configuration for ACES** package requires various
dependencies in order to run and be able to generate the *OCIO* configurations:

Primary Dependencies
********************

-   `python >= 3.9, < 3.11 <https://www.python.org/download/releases>`__
-   `opencolorio <https://pypi.org/project/opencolorio>`__
-   `requests <https://pypi.org/project/requests>`__
-   `semver <https://pypi.org/project/semver>`__

Optional Dependencies
*********************

-   `colour-science <https://pypi.org/project/colour-science>`__
-   `graphviz <https://www.graphviz.org>`__
-   `jsonpickle <https://jsonpickle.github.io>`__
-   `networkx <https://pypi.org/project/networkx>`__
-   `pygraphviz <https://pypi.org/project/pygraphviz>`__

Development Dependencies
************************

-   `black <https://pypi.org/project/black>`__
-   `coverage <https://pypi.org/project/coverage>`__
-   `coveralls <https://pypi.org/project/coveralls>`__
-   `flynt <https://pypi.org/project/flynt>`__
-   `invoke <https://pypi.org/project/invoke>`__
-   `pre-commit <https://pypi.org/project/pre-commit>`__
-   `pydata-sphinx-theme <https://pypi.org/project/pydata-sphinx-theme>`__
-   `pytest <https://pypi.org/project/pytest>`__
-   `pytest-cov <https://pypi.org/project/pytest-cov>`__
-   `restructuredtext-lint <https://pypi.org/project/restructuredtext-lint>`__
-   `ruff <https://pypi.org/project/ruff>`__
-   `sphinx >= 4, < 5 <https://pypi.org/project/sphinx>`__
-   `twine <https://pypi.org/project/twine>`__
