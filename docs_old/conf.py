# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import liger_iris_pipeline


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Liger IRIS Data Reduction Software'
copyright = '2025, Bryson Cale, Andrea Zonca, Shelley Wright'
author = 'Bryson Cale, Andrea Zonca, Shelley Wright'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_automodapi.automodapi',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'nbsphinx',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']


# Version
version = liger_iris_pipeline.__version__
# The full version, including alpha/beta/rc tags.
#release = hispecdrp.__version__


# By default, highlight as Python 3.
highlight_language = "python3"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_templates']

# html_theme_options = {
#     "logotext1": "liger_iris_pipeline",  # white,  semi-bold
#     "logotext2": "",  # orange, light
#     "logotext3": ":docs",  # white,  light
# }


# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = f"Liger IRIS Data Reduction Software v{liger_iris_pipeline.__version__}"

# Output file base name for HTML help builder.
htmlhelp_basename = project + "doc"


# -- Options for LaTeX output -------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ("index", project + ".tex", project + u" Documentation", author, "manual")
]


# -- Options for manual page output -------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
# man_pages = [("index", project.lower(), project + u" Documentation", [author], 1)]


# -- Options for the edit_on_github extension ---------------------------------

# -- Resolving issue number to links in changelog -----------------------------
github_issues_url = "https://github.com/oirlab/liger_iris_pipeline/issues/"

# -- Turn on nitpicky mode for sphinx (to warn about references not found) ----
#
# nitpicky = True
# nitpick_ignore = []
#
# Some warnings are impossible to suppress, and you can list specific references
# that should be ignored in a nitpick-exceptions file which should be inside
# the docs/ directory. The format of the file should be:
#
# <type> <class>
#
# for example:
#
# py:class astropy.io.votable.tree.Element
# py:class astropy.io.votable.tree.SimpleElement
# py:class astropy.io.votable.tree.SimpleElementWithContent
#
# Uncomment the following lines to enable the exceptions:
#
# for line in open('nitpick-exceptions'):
#     if line.strip() == "" or line.startswith("#"):
#         continue
#     dtype, target = line.split(None, 1)
#     target = target.strip()
#     nitpick_ignore.append((dtype, six.u(target)))

intersphinx_mapping = {
    "jwst": ("https://jwst-pipeline.readthedocs.io/en/latest", None)
}

# latex_elements = {
#     # Additional stuff for the LaTeX preamble.
#     "preamble": "".join(
#         (
#             "\DeclareUnicodeCharacter{00A0}{ }",  # NO-BREAK SPACE
#             "\DeclareUnicodeCharacter{251C}{+}",  # BOX DRAWINGS LIGHT VERTICAL AND RIGHT
#             "\DeclareUnicodeCharacter{2514}{+}",  # BOX DRAWINGS LIGHT UP AND RIGHT
#         )
#     ),
# }

nbsphinx_kernel_name = "python3"
nbsphinx_timeout = 600
nbsphinx_allow_errors = False
nbsphinx_execute = 'never'