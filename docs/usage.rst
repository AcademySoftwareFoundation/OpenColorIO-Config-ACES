..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Usage
=====

Tasks
^^^^^

Various tasks are currently exposed via `invoke <https://pypi.org/project/invoke/>`__.

This is currently the recommended way to build the configuration until a
dedicated CLI is provided.

Listing the tasks is done as follows::

    invoke --list

Assuming the dependencies are satisfied, the task to build the **Reference**
configuration is::

    invoke build-config-reference

Alternatively, with the docker container built::

    invoke docker-run-build-config-reference

Likewise, for the **CG** configuration::

    invoke build-config-cg

Or::

    invoke docker-run-build-config-cg
