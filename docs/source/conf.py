



# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys, os
sys.path.insert(0, os.path.abspath("../.."))

import liger_iris_pipeline


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Liger IRIS Data Reduction Software'
copyright = '2025, Liger IRIS DRS Teams'
author = 'Liger IRIS DRS Teams'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    #'sphinx.ext.imgmath',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
    'sphinx_automodapi.automodapi',
    'nbsphinx',
]

# Don't execute notebooks yet
#nbsphinx_execute = "never"

autosummary_generate = True  # Generate autosummary stubs automatically
autodoc_default_options = {
    'members': True,          # Include all class members
    'undoc-members': False,    # Include undocumented members
    'show-inheritance': True, # Show class inheritance
}

templates_path = ['_templates']
exclude_patterns = []

# Add the custom CSS file
html_css_files = [
    'custom.css'
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://sphinxawesome.xyz/how-to/configure/
html_theme = 'sphinxawesome_theme'
from sphinxawesome_theme.postprocess import Icons
#from pygments.styles import get_all_styles
pygments_style = "friendly"
pygments_style_dark = "friendly"
html_permalinks_icon = Icons.permalinks_icon
html_static_path = ['_static']

# Version
version = liger_iris_pipeline.__version__
# The full version, including alpha/beta/rc tags.
#release = hispecdrp.__version__

# URL
html_baseurl = 'https://oirlab.github.io/liger_iris_pipeline/'