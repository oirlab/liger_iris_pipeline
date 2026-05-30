# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys, os
sys.path.insert(0, os.path.abspath("../.."))
#sys.path.insert(0, os.path.abspath('..'))

import liger_iris_pipeline
from liger_iris_pipeline import LigerIRISStep


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Liger and IRIS Data Reduction Software'
copyright = '2025, Liger and IRIS DRS Teams'
author = 'Liger and IRIS DRS Teams'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    "sphinx.ext.autosectionlabel",
    #"sphinx.ext.autodoc.typehints",
    #"sphinx.ext.autolink",
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
    'sphinx_automodapi.automodapi',
    'sphinx.ext.napoleon',
    'nbsphinx',
]

napoleon_custom_sections = [
    ('Calibrations', 'params_style'),
    ('Returns', 'params_style')
]

# Don't execute notebooks
nbsphinx_execute = "never"

autosummary_generate = True  # Generate autosummary stubs automatically
autodoc_default_options = {
    'members': True,          # Include all class members
    'undoc-members': False,    # Include undocumented members
    'show-inheritance': True, # Show class inheritance
}

# Default `` to :py:class:
default_role = "any"

templates_path = ['_templates']
exclude_patterns = []

# Add the custom CSS file
html_css_files = [
    'custom.css'
]

intersphinx_mapping = {
    "koa_middleware": ("https://oirlab.github.io/KOA_Middleware/", None),
}

# Unclear why sphinx is stupid and throws a warning without this.
#autodoc_type_aliases = {'CalibrationSelector': 'koa_middleware.selector_base.CalibrationSelector'}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://sphinxawesome.xyz/how-to/configure/
html_theme = 'sphinxawesome_theme'
#html_theme = 'sphinx_rtd_theme'
from sphinxawesome_theme.postprocess import Icons
#from pygments.styles import get_all_styles
pygments_style = "friendly"
pygments_style_dark = "friendly"
html_permalinks_icon = Icons.permalinks_icon
html_static_path = ['_static']

# Version
version = liger_iris_pipeline.__version__

# URL
html_baseurl = 'https://oirlab.github.io/liger_iris_pipeline/'

suppress_warnings = ["autosectionlabel.*"]


########################
# Sphinx Cusomizations #
########################


# import inspect
# import re

# def _parse_spec(spec):
#     """
#     Parse stpipe-style spec into rows:
#     name, type, default, description
#     """
#     rows = []

#     for line in spec.strip().splitlines():
#         line = line.strip()
#         if not line or line.startswith("#"):
#             continue

#         # name = type(default=...) # comment
#         m = re.match(
#             r"(?P<name>\w+)\s*=\s*(?P<type>\w+)"
#             r"\(default\s*=\s*(?P<default>[^)]*)\)\s*"
#             r"(?:#\s*(?P<desc>.*))?",
#             line,
#         )
#         if not m:
#             continue

#         rows.append(
#             (
#                 m.group("name"),
#                 m.group("type"),
#                 m.group("default"),
#                 m.group("desc") or "",
#             )
#         )

#     return rows

# def _render_table(headers, rows):
#     """
#     Render a simple RST grid table.
#     """
#     cols = list(zip(*([headers] + rows)))
#     widths = [max(len(str(v)) for v in col) for col in cols]

#     def row(vals):
#         return " ".join(v.ljust(w) for v, w in zip(vals, widths))

#     lines = [
#         row(headers),
#         row(["=" * w for w in widths]),
#     ]

#     for r in rows:
#         lines.append(row([str(v) for v in r]))

#     return lines

# def step_autodoc(app, what, name, obj, options, lines):

#     # TODO: Add class_alias if not auto included

#     if not inspect.isclass(obj):
#         return

#     # Only proceed for LigerIRISStep-like classes
#     if not hasattr(obj, "spec") and not hasattr(obj, "calibrations"):
#         return

#     # ---- Handle Parameters section ----
#     spec = getattr(obj, "spec", None)
#     rows = _parse_spec(spec) if spec else []

#     # Find existing Parameters section
#     params_idx = _find_parameters_section(lines)

#     # Render spec entries
#     rendered_spec = _render_table(
#         ["Name", "Type", "Default", "Description"],
#         rows
#     ) if rows else []

#     if params_idx is None and rendered_spec:
#         # No Parameters section exists → create one
#         lines.extend([
#             "",
#             "Parameters",
#             "----------",
#             "",
#         ])
#         lines.extend(rendered_spec)
#     elif rendered_spec:
#         # Parameters section exists → append spec after user-written content
#         lines.extend([""])
#         lines.extend(rendered_spec)

#     # ---- Handle Reference Files ----
#     ref_files = getattr(obj, "calibrations", None)
#     if ref_files:
#         lines.extend([
#             "",
#             "Reference Files",
#             "---------------",
#             "",
#         ])
#         for key in ref_files:
#             lines.append(f"- **{key}**")

# def _find_parameters_section(lines):
#     """Return index of 'Parameters' header, or None if missing."""
#     for i, line in enumerate(lines):
#         if line.strip() == "Parameters":
#             return i
#     return None


# def setup(app):
#     app.connect("autodoc-process-docstring", step_autodoc)

def autodoc_add_ref_type(app, what, name, obj, options, lines):
    if what != "class" or not hasattr(obj, "_ref_type"):
        return

    # Find the insertion point: after the first non-empty line(s) but before Parameters
    insert_idx = None
    for i, line in enumerate(lines):
        # first line of a section header (e.g., Parameters)
        if line.strip() == "Parameters":
            insert_idx = i
            break

    if insert_idx is None:
        # fallback: after first non-empty line
        for i, line in enumerate(lines):
            if line.strip():
                insert_idx = i + 1
                break
        else:
            insert_idx = len(lines)

    # Insert the reference type
    lines[insert_idx:insert_idx] = [
        "",
        f"**Calibration types:** ``{obj._ref_type}``",
        "",
    ]

autosectionlabel_prefix_document = True  # Prefix section labels with document path to avoid duplicates

# conf.py
import re
from sphinx.application import Sphinx
from liger_iris_pipeline import datamodels

def parse_literal_table(lines):
    """
    Detect a fixed-width table starting with 'HDU Name ... Description'.
    Returns header and rows.
    """
    table_started = False
    rows = []
    header = None
    for line in lines:
        if re.match(r"HDU Name\s+HDU Type\s+Data Type", line):
            table_started = True
            header = re.split(r'\s{2,}', line.strip())
            continue
        if table_started:
            if not line.strip() or re.match(r"-{2,}", line):
                continue
            row = re.split(r'\s{2,}', line.strip())
            rows.append(row)
    return (header, rows) if header and rows else (None, None)

def convert_table_to_csv_directive(header, rows):
    """
    Build a .. csv-table:: directive from header + rows
    """
    lines = ['.. csv-table::',
             '    :header: ' + ', '.join(f'"{h}"' for h in header),
             '']
    for row in rows:
        lines.append("    " + ", ".join(f'"{c}"' for c in row))
    return lines

def replace_literal_table_for_html(app, what, name, obj, options, lines):
    # Only HTML build
    if app.builder.name != "html":
        return
    # Only classes
    if not isinstance(obj, type):
        return
    # Only subclasses of CalibrationModel
    if isinstance(obj, type) and not issubclass(obj, datamodels.LigerIRISDataModel):
        return

    header, rows = parse_literal_table(lines)
    if header and rows:
        csv_lines = convert_table_to_csv_directive(header, rows)
        # Find the start of the literal table
        start_index = next((i for i, l in enumerate(lines) if "HDU Name" in l), None)
        if start_index is not None:
            # Remove original table (header + separator + rows)
            end_index = start_index + len(rows) + 2  # +2 for header & separator
            lines[start_index:end_index] = csv_lines


def skip_pipeline_member(app, what, name, obj, skip, options):
    if name in {"step_defs", "process", "spec"}:
        return True
    return skip

def setup(app):
    app.connect("autodoc-process-docstring", autodoc_add_ref_type)
    app.connect("autodoc-process-docstring", replace_literal_table_for_html)
    app.connect("autodoc-skip-member", skip_pipeline_member)