..
  SPDX-License-Identifier: CC-BY-4.0
  Copyright Contributors to the OpenColorIO Project.

Usage
=====

Tasks
^^^^^

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
