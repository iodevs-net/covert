"""Configuration file for Sphinx documentation.

Covert Documentation Configuration
"""

import os
import sys
from datetime import datetime

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Covert"
copyright = f"{datetime.now().year}, iodevs-net"
author = "iodevs-net"

# The full version, including alpha/beta/rc tags
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Sphinx core extensions
    "sphinx.ext.autodoc",  # Automatically generate documentation from docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.extlinks",  # Add external links
    "sphinx.ext.todo",  # Support for todo notes
    "sphinx.ext.coverage",  # Check documentation coverage
    # Markdown support
    "myst_parser",  # Parse Markdown files
    # Additional features
    "sphinx.ext.intersphinx",  # Link to other Sphinx projects
    "sphinx_autodoc_typehints",  # Type hints in autodoc
]

# Enable MyST parser
myst_enable_extensions = [
    "amsmath",
    "dollarmath",
    "fieldlist",
    "tasklist",
    "deflist",
]

# Configure autodoc
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "show-inheritance": True,
}

# Configure type hints for autodoc
autodoc_typehints = "description"
autodoc_typehints_description_mode = "doc"

# List of patterns to exclude from source
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

html_title = "Covert Documentation"

html_short_title = "Covert"

# Theme options are theme-specific and customize the look and feel of a theme
html_theme_options = {
    "canonical_url": "",
    "analytics_id": "",
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "style_nav_header_background": "#3073BB",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Custom CSS
html_css_files = [
    "css/custom.css",
]

# -- Options for LaTeX output ------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-latex-output

latex_elements = {
    "preamble": r"""
\usepackage{amsmath}
""",
    "tableusebooktabs": True,
}

# Grouping the document tree into LaTeX files
latex_documents = [
    ("index", "covert.tex", "Covert Documentation", "iodevs-net", "manual"),
]

# -- Options for manual page output -----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-manual-page-output

man_pages = [
    ("index", "covert", "Covert Documentation", ["iodevs-net"], 1),
]

# -- Options for Texinfo output ---------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-texinfo-output

texinfo_documents = [
    (
        "index",
        "covert",
        "Covert Documentation",
        "iodevs-net",
        "Covert",
        "Safe package updater for Python/Django projects",
        "Development",
    ),
]

# -- Extension configuration -------------------------------------------------

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pip": ("https://pip.pypa.io/en/stable/", None),
    "pytest": ("https://docs.pytest.org/en/stable/", None),
}

# Extlinks
extlinks = {
    "issue": ("https://github.com/iodevs-net/covert/issues/%s", "Issue #%s"),
    "pr": ("https://github.com/iodevs-net/covert/pull/%s", "PR #%s"),
    "repo": ("https://github.com/iodevs-net/covert", "GitHub"),
}

# -- Options for sphinx-autodoc2 --------------------------------------------
# https://sphinx-autodoc2.readthedocs.io/

autodoc2_typehints = "description"
autodoc2_show_source = True

# -- Mermaid diagrams -------------------------------------------------------

mermaid_output_format = "svg"

# -- Autodoc configurations -------------------------------------------------

# Order of members
autodoc_member_order = "alphabetical"

# -- Nitpicky mode ---------------------------------------------------------

nitpicky = False  # Set to True to catch broken links

# -- Source file configuration ----------------------------------------------

# The suffix(es) of source filenames.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document
master_doc = "index"

# -- Timeouts --------------------------------------------------------------

# Timeout for autodoc (in seconds)
autodoc_mock_imports = ["rich", "yaml", "toml", "packaging"]
