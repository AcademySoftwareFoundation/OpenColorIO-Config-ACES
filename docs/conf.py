# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.

"""
OpenColorIO Configuration for ACES - Documentation Configuration
================================================================
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import opencolorio_config_aces as package  # noqa: E402

basename = package.__name__.replace("_", "-")

# -- General configuration ------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3.13", None)}

autosummary_generate = True

autodoc_mock_imports = []

autoclass_content = "both"

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project = package.__application_name__
copyright = package.__copyright__  # noqa: A001
version = f"{package.__major_version__}.{package.__minor_version__}"
release = package.__version__

exclude_patterns = ["_build"]

pygments_style = "lovelace"

# -- Options for HTML output ----------------------------------------------

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "show_nav_level": 2,
    "icon_links": [
        {
            "name": "Email",
            "url": "https://lists.aswf.io/g/ocio-dev",
            "icon": "fas fa-envelope",
        },
        {
            "name": "GitHub",
            "url": (
                "https://github.com/AcademySoftwareFoundation/"
                "OpenColorIO-Config-ACES"
            ),
            "icon": "fab fa-github",
        },
    ],
}
html_static_path = ["_static"]
htmlhelp_basename = f"{basename}Doc"

# -- Options for LaTeX output ---------------------------------------------
latex_elements = {
    "papersize": "a4paper",
    "pointsize": "10pt",
    "preamble": """
        \\usepackage{charter}
        \\usepackage[defaultsans]{lato}
        \\usepackage{inconsolata}
        """,
}
latex_documents = [
    (
        "index",
        f"{basename}.tex",
        f"{package.__application_name__} Documentation",
        package.__author__,
        "manual",
    ),
]

# -- Options for manual page output ---------------------------------------
man_pages = [
    (
        "index",
        basename,
        f"{package.__application_name__} Documentation",
        [package.__author__],
        1,
    )
]

# -- Options for Texinfo output -------------------------------------------
texinfo_documents = [
    (
        "index",
        basename,
        f"{package.__application_name__} Documentation",
        package.__author__,
        package.__application_name__,
        basename,
        "Miscellaneous",
    ),
]
# -- Options for Epub output ----------------------------------------------
epub_title = package.__application_name__
epub_author = package.__author__
epub_publisher = package.__author__
epub_copyright = package.__copyright__.replace("Copyright (C)", "")
epub_exclude_files = ["search.html"]
