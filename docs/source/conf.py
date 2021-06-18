# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import datetime
import inspect
import os
import sys

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('../..'))


# -- Project information -----------------------------------------------------
import heartandsole
project = 'heartandsole'
copyright = f'2019-{datetime.now().year}, Aaron Schroeder'
author = 'Aaron Schroeder'

# The short X.Y version.
version = heartandsole.__version__

# The full version, including alpha/beta/rc tags
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
  'sphinx.ext.autodoc',
  'sphinx.ext.autosummary',
  'sphinx_autosummary_accessors',
  'sphinx.ext.napoleon',
  'sphinx.ext.todo',
  'sphinx.ext.linkcode',
  'IPython.sphinxext.ipython_console_highlighting',
  'IPython.sphinxext.ipython_directive',
  'sphinx.ext.intersphinx',
]

# Napoleon options
# Full list here:
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration
#napoleon_google_docstring = False
#napoleon_use_param = False
#napoleon_use_ivar = True

# Add any paths that contain templates here, relative to this directory.
import sphinx_autosummary_accessors
templates_path = [
  '../_templates', 
  sphinx_autosummary_accessors.templates_path,
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# autodoc options
add_module_names = True
autoclass_content = 'both'

# autosummary options
autosummary_generate = True

# ipython options
ipython_execlines = [
  'import numpy as np',
  'import pandas as pd',
  'import heartandsole',
]

# Add mappings so I can link to external docs
intersphinx_mapping = {
  'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
  'activereader': ('https://activereader.readthedocs.io/en/stable', None),
  'pandas-xyz': ('https://pandas-xyz.readthedocs.io/en/stable', None),
  'fitparse': ('https://dtcooper.github.io/python-fitparse/', None),
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# based on pandas doc/source/conf.py
def linkcode_resolve(domain, info):
  """Determine the URL corresponding to Python object"""
  if domain != 'py':
    return None

  modname = info['module']
  fullname = info['fullname']

  submod = sys.modules.get(modname)
  if submod is None:
    return None

  obj = submod
  for part in fullname.split('.'):
    try:
      obj = getattr(obj, part)
    except AttributeError:
      return None

  try:
    fn = inspect.getsourcefile(inspect.unwrap(obj))
  except TypeError:
    fn = None
  if not fn:
    return None

  try:
    source, lineno = inspect.getsourcelines(obj)
  except OSError:
    lineno = None

  if lineno:
    linespec = f'#L{lineno}-L{lineno + len(source) - 1}'
  else:
    linespec = ''

  fn = os.path.relpath(fn, start=os.path.dirname(heartandsole.__file__))

  # if '+' in pandas_xyz.__version__:
  #     return f"https://github.com/pandas-dev/pandas/blob/master/pandas/{fn}{linespec}"
  # else:
  return (
      f'https://github.com/aaron-schroeder/heartandsole/blob/'
      # f'master/distance/{fn}{linespec}'
      f'v{heartandsole.__version__}/heartandsole/{fn}{linespec}'
  )


# meant to add custom css to allow tables to wrap
def setup(app):
  # app.add_javascript('custom.js')
  app.add_css_file('custom.css')