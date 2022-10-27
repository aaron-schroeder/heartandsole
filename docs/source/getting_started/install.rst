.. currentmodule:: heartandsole

.. _install:

============
Installation
============

The easiest way to install pandas is to install it
from `PyPI <https://pypi.org/project/heartandsole>`__.

Instructions for installing a
`development version <https://github.com/aaron-schroeder/heartandsole>`__ are also provided.

.. _install.version:

Python version support
----------------------

Officially Python 3.7 and above.

Installing heartandsole
-----------------------

Installing from PyPI
~~~~~~~~~~~~~~~~~~~~

heartandsole can be installed via pip from
`PyPI <https://pypi.org/project/heartandsole>`__.

::

    pip install heartandsole

Installing from source
~~~~~~~~~~~~~~~~~~~~~~

The source code is hosted at http://github.com/aaron-schroeder/heartandsole. 
It can be checked out using git and installed like so:

::

  git clone git://github.com/aaron-schroeder/heartandsole.git
  cd heartandsole
  pip install -r requirements.txt
  pip install .


.. _install.dependencies:

Dependencies
------------

================================================================ ==========================
Package                                                          Minimum supported version
================================================================ ==========================
`NumPy <https://numpy.org>`__                                    1.15.0
`Pandas <https://pandas.pydata.org>`__                           1.0.0
================================================================ ==========================

.. _install.optional_dependencies:

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

heartandsole has some optional dependencies that are only used for specific methods.
For example, :meth:`Activity.from_tcx` requires the ``activereader`` package, while
:meth:`Activity.elevation.gain` requires the ``pandas-xyz`` package. If the
optional dependency is not installed, heartandsole will raise an ``ImportError`` when
the method requiring that dependency is called.

========================= ================== =============================================================
Dependency                Minimum Version    Notes
========================= ================== =============================================================
activereader              0.0.2              TCX/GPX file reader for :meth:`Activity.from_tcx` and 
                                             :meth:`Activity.from_gpx`
fitparse                  1.1.0              FIT file reader for :meth:`Activity.from_fit`
pandas-xyz                0.0.5              Geospatial calculations like elevation profile smoothing and
                                             determining distance between series of GPS coordinates
========================= ================== =============================================================
