# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Invoke - Tasks
==============
"""

from __future__ import unicode_literals

import os
from invoke import task
from invoke.exceptions import Failure

import opencolorio_config_aces
from opencolorio_config_aces.utilities import message_box

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = [
    'APPLICATION_NAME', 'APPLICATION_VERSION', 'PYTHON_PACKAGE_NAME',
    'GITHUB_REPOSITORY_NAME', 'PYPI_PACKAGE_NAME', 'ORG', 'CONTAINER', 'clean',
    'formatting', 'tests', 'quality', 'preflight', 'docs',
    'build_reference_config', 'requirements', 'docker_build', 'docker_remove',
    'run_in_container', 'docker_run_docs', 'docker_run_build_reference_config'
]

APPLICATION_NAME = opencolorio_config_aces.__application_name__

APPLICATION_VERSION = opencolorio_config_aces.__version__

PYTHON_PACKAGE_NAME = opencolorio_config_aces.__name__

GITHUB_REPOSITORY_NAME = 'OpenColorIO-Config-ACES'

PYPI_PACKAGE_NAME = 'opencolorio-config-aces'

ORG = 'aswf'

CONTAINER = PYPI_PACKAGE_NAME


@task
def clean(ctx, docs=True, bytecode=False):
    """
    Cleans the project.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    docs : bool, optional
        Whether to clean the *docs* directory.
    bytecode : bool, optional
        Whether to clean the bytecode files, e.g. *.pyc* files.

    Returns
    -------
    bool
        Task success.
    """
    message_box('Cleaning project...')

    patterns = ['build', '*.egg-info', 'dist']

    if docs:
        patterns.append('docs/_build')
        patterns.append('docs/generated')

    if bytecode:
        patterns.append('**/*.pyc')

    for pattern in patterns:
        ctx.run(f'rm -rf {pattern}')


@task
def formatting(ctx, yapf=True):
    """
    Formats the codebase with *Yapf*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    yapf : bool, optional
        Whether to format the codebase with *Yapf*.

    Returns
    -------
    bool
        Task success.
    """

    if yapf:
        message_box('Formatting codebase with "Yapf"...')
        ctx.run(
            'yapf -p -i -r '
            '--exclude \'.git\' '
            '--exclude \'opencolorio_config_aces/config/reference/aces-dev\' .'
        )


@task
def tests(ctx, nose=True):
    """
    Runs the unit tests with *Nose* or *Pytest*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    nose : bool, optional
        Whether to use *Nose* or *Pytest*.

    Returns
    -------
    bool
        Task success.
    """

    if nose:
        message_box('Running "Nosetests"...')
        ctx.run(f'nosetests --with-doctest --with-coverage '
                f'--cover-package={PYTHON_PACKAGE_NAME} {PYTHON_PACKAGE_NAME}')
    else:
        message_box('Running "Pytest"...')
        ctx.run(f'py.test --disable-warnings --doctest-modules '
                f'{PYTHON_PACKAGE_NAME}')


@task
def quality(ctx, flake8=True):
    """
    Checks the codebase with *Flake8*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    flake8 : bool, optional
        Whether to check the codebase with *Flake8*.

    Returns
    -------
    bool
        Task success.
    """

    if flake8:
        message_box('Checking codebase with "Flake8"...')
        ctx.run('flake8 opencolorio_config_aces --exclude=aces-dev')


@task(formatting, tests, quality)
def preflight(ctx):
    """
    Performs the preflight tasks, i.e. *formatting* and *quality*.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Finishing "Preflight"...')


@task
def docs(ctx, html=True, pdf=True):
    """
    Builds the documentation.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    html : bool, optional
        Whether to build the *HTML* documentation.
    pdf : bool, optional
        Whether to build the *PDF* documentation.

    Returns
    -------
    bool
        Task success.
    """

    with ctx.cd('.'):
        message_box('Updating "index.rst" file...')
        readme_file_path = os.path.join(ctx.cwd, 'README.rst')
        with open(readme_file_path, 'r') as readme_file:
            readme_file_content = readme_file.read()

        readme_file_content = readme_file_content.replace(
            '.. {MANUAL-URL}', """
.. toctree::
    :maxdepth: 3

    manual
""" [1:-1])

        index_file_path = os.path.join(ctx.cwd, 'docs', 'index.rst')
        with open(index_file_path, 'w') as index_file:
            index_file.write(readme_file_content)

    with ctx.cd('docs'):
        if html:
            message_box('Building "HTML" documentation...')
            ctx.run('make html')

        if pdf:
            message_box('Building "PDF" documentation...')
            ctx.run('make latexpdf')


@task
def build_reference_config(ctx):
    """
    Builds the *aces-dev* reference *OpenColorIO* Config.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box(f'Building the "aces-dev" reference *OpenColorIO* config...')
    with ctx.cd('opencolorio_config_aces/config/reference/generate'):
        ctx.run('python config.py')


@task
def requirements(ctx):
    """
    Exports the *requirements.txt* file.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Exporting "requirements.txt" file...')
    ctx.run('poetry run pip freeze > requirements.txt')


@task(requirements)
def docker_build(ctx):
    """
    Builds the *docker* image.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Building "docker" image...')
    ctx.run(f'docker build -t {ORG}/{CONTAINER}:latest '
            f'-t {ORG}/{CONTAINER}:v{APPLICATION_VERSION} .')


@task
def docker_remove(ctx):
    """
    Stops and remove the *docker* container.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    message_box('Stopping "docker" container...')
    try:
        ctx.run(f'docker stop {CONTAINER}')
    except Failure:
        pass

    message_box('Removing "docker" container...')
    try:
        ctx.run(f'docker rm {CONTAINER}')
    except Failure:
        pass


def run_in_container(ctx, command):
    """
    Runs given command in *docker* container.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    command : unicode
        Command to run in the *docker* container.

    Returns
    -------
    bool
        Task success.
    """

    message_box(f'Running "docker" container with "{command}" command...')
    ctx.run(f'docker run -v ${{PWD}}:/home/{ORG}/{GITHUB_REPOSITORY_NAME} '
            f'{ORG}/{CONTAINER}:latest {command}')


@task
def docker_run_docs(ctx, html=True, pdf=True):
    """
    Builds the documentation in the *docker* container.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.
    html : bool, optional
        Whether to build the *HTML* documentation.
    pdf : bool, optional
        Whether to build the *PDF* documentation.

    Returns
    -------
    bool
        Task success.
    """

    command = 'invoke docs'

    if html is False:
        command += ' --no-html'

    if pdf is False:
        command += ' --no-pdf'

    run_in_container(ctx, command)


@task
def docker_run_build_reference_config(ctx):
    """
    Builds the *aces-dev* reference *OpenColorIO* Config in the *docker*
    container.

    Parameters
    ----------
    ctx : invoke.context.Context
        Context.

    Returns
    -------
    bool
        Task success.
    """

    run_in_container(ctx, 'invoke build-reference-config')
