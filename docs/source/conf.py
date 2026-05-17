import os
import sys
from importlib.metadata import version as _pkg_version, PackageNotFoundError

sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
project = 'Querexfuzz'
copyright = '2026, Stephen J Mildenhall'
author = 'Stephen J Mildenhall'

try:
    release = _pkg_version('querexfuzz')
except PackageNotFoundError:
    release = 'unknown'
version = '.'.join(release.split('.')[:2]) if '.' in release else release

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'myst_parser',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build']

autodoc_member_order = 'bysource'
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- HTML output -------------------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_favicon = '../favicon.ico'
html_logo = '../banner.png'

html_theme_options = {
    'logo_only': False,
    'collapse_navigation': False,
    'sticky_navigation': True,
}
