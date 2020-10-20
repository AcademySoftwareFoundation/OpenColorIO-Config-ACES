# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.
"""
Invoke - Tasks
==============
"""

from __future__ import unicode_literals

from invoke import task

import opencolorio_config_aces
from opencolorio_config_aces.utilities import message_box

__author__ = 'OpenColorIO Contributors'
__copyright__ = 'Copyright Contributors to the OpenColorIO Project.'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'OpenColorIO Contributors'
__email__ = 'ocio-dev@lists.aswf.io'
__status__ = 'Production'

__all__ = ['clean', 'formatting', 'quality', 'preflight']

APPLICATION_NAME = opencolorio_config_aces.__application_name__

APPLICATION_VERSION = opencolorio_config_aces.__version__

PYTHON_PACKAGE_NAME = opencolorio_config_aces.__name__

PYPI_PACKAGE_NAME = 'opencolorio-config-aces'


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
        ctx.run("rm -rf {}".format(pattern))


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
        ctx.run(
            'nosetests --with-doctest --with-coverage --cover-package={0} {0}'.
            format(PYTHON_PACKAGE_NAME))
    else:
        message_box('Running "Pytest"...')
        ctx.run('py.test --disable-warnings --doctest-modules '.format(
            PYTHON_PACKAGE_NAME))


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

    with ctx.cd('docs'):
        if html:
            message_box('Building "HTML" documentation...')
            ctx.run('make html')

        if pdf:
            message_box('Building "PDF" documentation...')
            ctx.run('make latexpdf')
