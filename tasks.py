# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Invoke - Tasks
==============
"""

from __future__ import annotations

import contextlib
import inspect
import os
from pathlib import Path

import requests
from invoke.exceptions import Failure

import opencolorio_config_aces
from opencolorio_config_aces.config.cg.generate.config import (
    URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG,
)
from opencolorio_config_aces.config.reference.generate.config import (
    URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE,
)
from opencolorio_config_aces.config.studio.generate.config import (
    URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO,
)
from opencolorio_config_aces.utilities import google_sheet_title, message_box

if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec

from invoke.context import Context
from invoke.tasks import task

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
    "quality",
    "precommit",
    "tests",
    "preflight",
    "docs",
    "build_clf_transforms",
    "build_aces_conversion_graph",
    "build_config_common_tests",
    "build_config_reference_analytical",
    "update_mapping_file_reference",
    "build_config_reference",
    "update_mapping_file_cg",
    "build_config_cg",
    "build_config_studio",
    "requirements",
    "docker_build",
    "docker_remove",
    "run_in_container",
    "docker_run_docs",
    "docker_run_build_clf_transforms",
    "docker_run_build_aces_conversion_graph",
    "docker_run_build_config_common_tests",
    "docker_run_build_config_reference_analytical",
    "docker_run_update_mapping_file_reference",
    "docker_run_build_config_reference",
    "docker_run_update_mapping_file_cg",
    "docker_run_build_config_cg",
    "docker_run_update_mapping_file_studio",
    "docker_run_build_config_studio",
]

APPLICATION_NAME: str = opencolorio_config_aces.__application_name__

APPLICATION_VERSION: str = opencolorio_config_aces.__version__

PYTHON_PACKAGE_NAME: str = opencolorio_config_aces.__name__

GITHUB_REPOSITORY_NAME: str = "OpenColorIO-Config-ACES"

PYPI_PACKAGE_NAME: str = "opencolorio-config-aces"

ORG: str = "aswf"

CONTAINER: str = PYPI_PACKAGE_NAME


@task
def clean(
    ctx: Context,
    docs: bool = True,
    bytecode: bool = False,
    mypy: bool = True,
    pytest: bool = True,
) -> None:
    """
    Clean the project.

    Parameters
    ----------
    ctx
        Context.
    docs
        Whether to clean the *docs* directory.
    bytecode
        Whether to clean the bytecode files, e.g., *.pyc* files.
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
def quality(
    ctx: Context,
    pyright: bool = True,
) -> None:
    """
    Check the codebase with *Pyright* and lints various *restructuredText*
    files with *rst-lint*.

    Parameters
    ----------
    ctx
        Context.
    pyright
        Whether to check the codebase with *Pyright*.
    """

    if pyright:
        message_box('Checking codebase with "Pyright"...')
        ctx.run("pyright --threads --skipunannotated --level warning")


@task
def precommit(ctx: Context) -> None:
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
def tests(ctx: Context) -> None:
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


@task(quality, precommit, tests)
def preflight(ctx: Context) -> None:  # noqa: ARG001
    """
    Perform the preflight tasks, i.e., *formatting* and *quality*.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Finishing "Preflight"...')


@task
def docs(ctx: Context, html: bool = True, pdf: bool = True) -> None:
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
def build_clf_transforms(ctx: Context) -> None:
    """
    Build the *CLF* transforms.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "CLF" transform files...')
    for family in [
        "apple",
        "arri",
        "blackmagic",
        "canon",
        "itu",
        "ocio",
        "panasonic",
        "red",
        "sony",
    ]:
        with ctx.cd(f"opencolorio_config_aces/clf/transforms/{family}"):
            ctx.run("python generate.py")


@task
def build_aces_conversion_graph(ctx: Context) -> None:
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
def build_config_common_tests(ctx: Context) -> None:
    """
    Build the common tests *OpenColorIO* config(s).

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the common tests "OpenColorIO" config(s)...')
    with ctx.cd("opencolorio_config_aces/config/generation"):
        ctx.run("python common.py")


@task
def build_config_reference_analytical(ctx: Context) -> None:
    """
    Build the *aces-dev* reference analytical *OpenColorIO* config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "aces-dev" reference analytical "OpenColorIO" config...')
    with ctx.cd("opencolorio_config_aces/config/reference/generate"):
        ctx.run("python analytical.py")


@task
def update_mapping_file_reference(ctx: Context) -> None:  # noqa: ARG001
    """
    Update the *aces-dev* reference *OpenColorIO* config mapping file.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box(
        'Updating the "aces-dev" reference "OpenColorIO" config mapping file...'
    )

    title = google_sheet_title(URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE)

    directory = Path(
        "opencolorio_config_aces/config/reference/generate/resources/"
    ).absolute()

    for csv_file in directory.glob("*Mapping.csv"):
        os.remove(csv_file)

    filename = str(directory / f"{title} - Reference Config - Mapping.csv").replace(
        '"', ""
    )

    with open(filename, "w") as csv_file:
        csv_file.write(
            requests.get(URL_EXPORT_TRANSFORMS_MAPPING_FILE_REFERENCE, timeout=60).text
        )


@task
def build_config_reference(ctx: Context) -> None:
    """
    Build the *aces-dev* reference *OpenColorIO* config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "aces-dev" reference "OpenColorIO" config...')
    with ctx.cd("opencolorio_config_aces/config/reference/generate"):
        ctx.run("python config.py")


@task
def update_mapping_file_cg(ctx: Context) -> None:  # noqa: ARG001
    """
    Update the *ACES* Computer Graphics (CG) *OpenColorIO* mapping file.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box(
        'Updating the "ACES" Computer Graphics (CG) "OpenColorIO" config '
        "mapping file..."
    )

    title = google_sheet_title(URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG)

    directory = Path("opencolorio_config_aces/config/cg/generate/resources/").absolute()

    for csv_file in directory.glob("*Mapping.csv"):
        os.remove(csv_file)

    filename = str(directory / f"{title} - CG Config - Mapping.csv").replace('"', "")

    with open(filename, "w") as csv_file:
        csv_file.write(
            requests.get(URL_EXPORT_TRANSFORMS_MAPPING_FILE_CG, timeout=60).text
        )


@task
def build_config_cg(ctx: Context) -> None:
    """
    Build the *ACES* Computer Graphics (CG) *OpenColorIO* config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "ACES" Computer Graphics (CG) "OpenColorIO" config...')
    with ctx.cd("opencolorio_config_aces/config/cg/generate"):
        ctx.run("python config.py")


@task
def update_mapping_file_studio(ctx: Context) -> None:  # noqa: ARG001
    """
    Update the *ACES* Studio *OpenColorIO* mapping file.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Updating the "ACES" Studio "OpenColorIO" config mapping file...')

    title = google_sheet_title(URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO)

    directory = Path(
        "opencolorio_config_aces/config/studio/generate/resources/"
    ).absolute()

    for csv_file in directory.glob("*Mapping.csv"):
        os.remove(csv_file)

    filename = str(directory / f"{title} - Studio Config - Mapping.csv").replace(
        '"', ""
    )

    with open(filename, "w") as csv_file:
        csv_file.write(
            requests.get(URL_EXPORT_TRANSFORMS_MAPPING_FILE_STUDIO, timeout=60).text
        )


@task
def build_config_studio(ctx: Context) -> None:
    """
    Build the *ACES* Studio *OpenColorIO* config.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Building the "ACES" Studio (CG) "OpenColorIO" config...')
    with ctx.cd("opencolorio_config_aces/config/studio/generate"):
        ctx.run("python config.py")


@task
def requirements(ctx: Context) -> None:
    """
    Export the *requirements.txt* file.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Exporting "requirements.txt" file...')
    ctx.run(
        "uv export --no-annotate --no-hashes --all-extras | "
        'grep -v "-e \\." > requirements.txt'
    )

    message_box('Exporting "docs/requirements.txt" file...')
    ctx.run(
        "uv export --no-annotate --no-hashes --all-extras --no-dev | "
        'grep -v "-e \\." > docs/requirements.txt'
    )


@task(requirements)
def docker_build(ctx: Context) -> None:
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
def docker_remove(ctx: Context) -> None:
    """
    Stop and remove the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    message_box('Stopping "docker" container...')
    with contextlib.suppress(Failure):
        ctx.run(f"docker stop {CONTAINER}")

    message_box('Removing "docker" container...')
    with contextlib.suppress(Failure):
        ctx.run(f"docker rm {CONTAINER}")


def run_in_container(ctx: Context, command: str) -> None:
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
def docker_run_docs(ctx: Context, html: bool = True, pdf: bool = True) -> None:
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
def docker_run_build_clf_transforms(ctx: Context) -> None:
    """
    Build the *CLF* transforms in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-clfs")


@task
def docker_run_build_aces_conversion_graph(ctx: Context) -> None:
    """
    Build the *aces-dev* conversion graph in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-aces-conversion-graph")


@task
def docker_run_build_config_common_tests(ctx: Context) -> None:
    """
    Build the common tests *OpenColorIO* config(s) in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-common")


@task
def docker_run_build_config_reference_analytical(ctx: Context) -> None:
    """
    Build the *aces-dev* reference analytical *OpenColorIO* config in the
    *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-reference-analytical")


def docker_run_update_mapping_file_reference(ctx: Context) -> None:
    """
    Update the *aces-dev* reference *OpenColorIO* config mapping file in the
    *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke update-mapping-file-reference")


@task
def docker_run_build_config_reference(ctx: Context) -> None:
    """
    Build the *aces-dev* reference *OpenColorIO* config in the *docker*
    container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-reference")


def docker_run_update_mapping_file_cg(ctx: Context) -> None:
    """
    Update the *ACES* Computer Graphics (CG) *OpenColorIO* config mapping file
    in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke update-mapping-file-cg")


@task
def docker_run_build_config_cg(ctx: Context) -> None:
    """
    Build the *ACES* Computer Graphics (CG) *OpenColorIO* config in the
    *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-cg")


def docker_run_update_mapping_file_studio(ctx: Context) -> None:
    """
    Update the *ACES* Studio *OpenColorIO* config mapping file in the *docker*
    container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke update-mapping-file-studio")


@task
def docker_run_build_config_studio(ctx: Context) -> None:
    """
    Build the *ACES* Studio *OpenColorIO* config in the *docker* container.

    Parameters
    ----------
    ctx
        Context.
    """

    run_in_container(ctx, "invoke build-config-studio")
