from heartandsole.core.activity import Activity

import heartandsole.api

from heartandsole.io.api import (
  # "parsers"
  read_csv,
  # "misc"
  read_fit,
  read_gpx,  # read_xml?
  read_tcx,
  read_json,
)

# from heartandsole.util import time_from_timestring, timestring_from_time

__version__ = '0.0.25'

 
class ActivityMixin:
  """Provide familiar Activity interface to various data container classes."""
  pass


class DataContainerMixin:
  """Common methods and properties implemented by all classes"""
  @classmethod
  def from_file(cls, fname):
    pass


# Top-level activity-like classes

class GpxRte(DataContainerMixin):
  pass


class GpxTrk(DataContainerMixin):
  pass


class TcxCourse(DataContainerMixin):
  pass


class TcxActivity(DataContainerMixin):
  pass


class FitCourse(DataContainerMixin):
  pass


class FitActivity(DataContainerMixin):
  pass


# Use __all__ to indicate what is part of the public API.
# The public API is determined based on the documentation.
__all__ = [
  'Activity',  # to be deprecated
  # 'CsvActivity',  # to be implemented
  'FitCourse',
  'FitActivity',
  'GpxRte',
  'GpxTrk',
  # 'JsonStravaStreams',  # to be implemented
  'TcxCourse',
  'TcxActivity',
  'read_csv',
  'read_fit'
  'read_gpx',
  'read_json',
  'read_tcx',
]