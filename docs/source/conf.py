import os
import sys

# Point to the project's source directory
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'Querexfuzz'
copyright = '2025 Stephen J Mildenhall'
author = 'Stephen J Mildenhall'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Automatically generate docs from docstrings
    'sphinx.ext.napoleon',     # Support for Google-style docstrings
    'sphinx.ext.viewcode',     # Add links to source code
    'myst_parser',             # Parse Markdown files
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
