# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Invoke - Tasks
==============
"""

from __future__ import annotations

from invoke import Context, task
from invoke.exceptions import Failure

import opencolorio_config_aces
from opencolorio_config_aces.utilities import message_box

__author__ = "OpenColorIO Contributors"
__copyright__ = "Copyright Contributors to the OpenColorIO Project."
__license__ = "New BSD License - https://opensource.org/licenses/BSD-3-Clause"
__maintainer__ = "OpenColorIO Contributors"
__email__ = "ocio-dev@lists.aswf.io"
__status__ = "Production"

__all__ = [
    "APPLICATION_NAME",
    "APPLICATION_VERSION",
    "PYTHON_PACKAGE_NAME",
    "GITHUB_REPOSITORY_NAME",
    "PYPI_PACKAGE_NAME",
    "ORG",
    "CONTAINER",
    "clean",
    "precommit",
    "tests",
    "preflight",
    "docs",
    "build_clfs",
    "build_aces_conversion_graph",
    "build_config_common_tests",
    "build_config_reference_analytical",
    "build_config_reference",
    "build_config_cg",
    "requirements",
    "docker_build",
    "docker_remove",
    "run_in_container",
    "docker_run_docs",
    "docker_run_build_clfs",
    "docker_run_build_aces_conversion_graph",
    "docker_run_build_config_common_tests",
    "docker_run_build_config_reference_analytical",
    "docker_run_build_config_reference",
    "docker_run_build_config_cg",
]

APPLICATION_NAME = opencolorio_config_aces.__application_name__

APPLICATION_VERSION = opencolorio_config_aces.__version__

PYTHON_PACKAGE_NAME = opencolorio_config_aces.__name__

GITHUB_REPOSITORY_NAME = "OpenColorIO-Config-ACES"

PYPI_PACKAGE_NAME = "opencolorio-config-aces"

ORG = "aswf"

CONTAINER = PYPI_PACKAGE_NAME


def _patch_invoke_annotations_support():
    """See https://github.com/pyinvoke/invoke/issues/357."""

    import invoke
    from unittest.mock import patch
    from inspect import getfullargspec, ArgSpec

    def patched_inspect_getargspec(function):
        spec = getfullargspec(function)
        return ArgSpec(*spec[0:4])

    org_task_argspec = invoke.tasks.Task.argspec

    def patched_task_argspec(*args, **kwargs):
        with patch(
            target="inspect.getargspec", new=patched_inspect_getargspec
        ):
            return org_task_argspec(*args, **kwargs)

    invoke.tasks.Task.argspec = patched_task_argspec


_patch_invoke_annotations_support()


@task
def clean(
    ctx: Context,
    docs: bool = True,
    bytecode: bool = False,
    mypy: bool = True,
    pytest: bool = True,
):
    """
    Clean the project.

    Parameters
    ----------
    ctx
        Context.
    docs
        Whether to clean the *docs* directory.
    bytecode
        Whether to clean the bytecode files, e.g. *.pyc* files.
    mypy
        Whether to clean the *Mypy* cache directory.
    pytest
        Whether to clean the *Pytest* cache directory.
    """

    message_box("Cleaning project...")

    patterns = ["build", "*.egg-info", "dist"]

    if docs:
        patterns.append("docs/_build")
        patterns.append("docs/generated")

    if bytecode:
        patterns.append("**/__pycache__")
        patterns.append("**/*.pyc")

    if mypy:
        patterns.append(".mypy_cache")

    if pytest:
        patterns.append(".pytest_cache")

    for pattern in patterns:
        ctx.run(f"rm -rf {pattern}")


@task
def precommit(ctx: Context):
    """
    Run the "pre-commit" hooks on the codebase.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Running "pre-commit" hooks on the codebase...')
    ctx.run("pre-commit run --all-files")


@task
def tests(ctx: Context):
    """
    Run the unit tests with *Pytest*.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Running "Pytest"...')
    ctx.run(
        "py.test "
        "--disable-warnings "
        "--doctest-modules "
        f"--ignore={PYTHON_PACKAGE_NAME}/config/reference/aces-dev "
        f"{PYTHON_PACKAGE_NAME}",
    )


@task(precommit, tests)
def preflight(ctx: Context):
    """
    Perform the preflight tasks, i.e. *formatting* and *quality*.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Finishing "Preflight"...')


@task
def docs(ctx: Context, html: bool = True, pdf: bool = True):
    """
    Build the documentation.

    Parameters
    ----------
    ctx
        Context.
    html
        Whether to build the *HTML* documentation.
    pdf
        Whether to build the *PDF* documentation.
    """

    with ctx.cd("docs"):
        if html:
            message_box('Building "HTML" documentation...')
            ctx.run("make html")

        if pdf:
            message_box('Building "PDF" documentation...')
            ctx.run("make latexpdf")


@task
def build_clfs(ctx: Context):
    """
    Build the *CLF* transforms.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "CLF" transform files...')
    with ctx.cd("opencolorio_config_aces/clf/transforms/ocio"):
        ctx.run("python generate.py")


@task
def build_aces_conversion_graph(ctx: Context):
    """
    Build the *aces-dev* conversion graph.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the ""aces-dev" conversion graph...')
    with ctx.cd("opencolorio_config_aces/config/reference/discover"):
        ctx.run("python graph.py")


@task
def build_config_common_tests(ctx: Context):
    """
    Build the common tests *OpenColorIO* Config(s).

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the common tests "OpenColorIO" Config(s)...')
    with ctx.cd("opencolorio_config_aces/config/generation"):
        ctx.run("python common.py")


@task
def build_config_reference_analytical(ctx: Context):
    """
    Build the *aces-dev* reference analytical *OpenColorIO* Config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box(
        'Building the "aces-dev" reference analytical "OpenColorIO" Config...'
    )
    with ctx.cd("opencolorio_config_aces/config/reference/generate"):
        ctx.run("python analytical.py")


@task
def build_config_reference(ctx: Context):
    """
    Build the *aces-dev* reference *OpenColorIO* Config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "aces-dev" reference "OpenColorIO" Config...')
    with ctx.cd("opencolorio_config_aces/config/reference/generate"):
        ctx.run("python config.py")


@task
def build_config_cg(ctx: Context):
    """
    Build the *ACES* Computer Graphics (CG) *OpenColorIO* Config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box(
        'Building the "ACES" Computer Graphics (CG) "OpenColorIO" config...'
    )
    with ctx.cd("opencolorio_config_aces/config/cg/generate"):
        ctx.run("python config.py")


@task
def requirements(ctx: Context):
    """
    Export the *requirements.txt* file.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Exporting "requirements.txt" file...')
    ctx.run(
        "poetry run pip list --format=freeze | "
        'egrep -v "opencolorio-config-aces" '
        "> requirements.txt"
    )


@task(requirements)
def docker_build(ctx: Context):
    """
    Build the *docker* image.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building "docker" image...')
    ctx.run(
        f"docker build -t {ORG}/{CONTAINER}:latest "
        f"-t {ORG}/{CONTAINER}:v{APPLICATION_VERSION} ."
    )


@task
def docker_remove(ctx: Context):
    """
    Stop and remove the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Stopping "docker" container...')
    try:
        ctx.run(f"docker stop {CONTAINER}")
    except Failure:
        pass

    message_box('Removing "docker" container...')
    try:
        ctx.run(f"docker rm {CONTAINER}")
    except Failure:
        pass


def run_in_container(ctx: Context, command: str):
    """
    Run given command in *docker* container.

    Parameters
    ----------
    ctx
        Context.
    command
        Command to run in the *docker* container.
    """

    message_box(f'Running "docker" container with "{command}" command...')
    ctx.run(
        f"docker run -v ${{PWD}}:/home/{ORG}/{GITHUB_REPOSITORY_NAME} "
        f"{ORG}/{CONTAINER}:latest {command}"
    )


@task
def docker_run_docs(ctx, html: bool = True, pdf: bool = True):
    """
    Build the documentation in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    html
        Whether to build the *HTML* documentation.
    pdf
        Whether to build the *PDF* documentation.
    """

    command = "invoke docs"

    if html is False:
        command += " --no-html"

    if pdf is False:
        command += " --no-pdf"

    run_in_container(ctx, command)


@task
def docker_run_build_clfs(ctx: Context):
    """
    Build the *CLF* transforms in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-clfs")


@task
def docker_run_build_aces_conversion_graph(ctx: Context):
    """
    Build the *aces-dev* conversion graph in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-aces-conversion-graph")


@task
def docker_run_build_config_common_tests(ctx: Context):
    """
    Build the common tests *OpenColorIO* Config(s) in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-common")


@task
def docker_run_build_config_reference_analytical(ctx: Context):
    """
    Build the *aces-dev* reference analytical *OpenColorIO* Config in the
    *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-reference-analytical")


@task
def docker_run_build_config_reference(ctx: Context):
    """
    Build the *aces-dev* reference *OpenColorIO* Config in the *docker*
    container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-reference")


@task
def docker_run_build_config_cg(ctx: Context):
    """
    Build the *ACES* Computer Graphics (CG) *OpenColorIO* Config in the
    *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-cg")
