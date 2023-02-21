"""
Data IO api
"""
from heartandsole.io.fit import read_fit
from heartandsole.io.json import read_json
from heartandsole.io.parsers import read_csv
from heartandsole.io.xml import(  # read_xml?
  read_gpx,
  read_tcx,
)


__all__ = [
  'read_csv',
  'read_fit'
  'read_gpx',
  'read_json',
  'read_tcx',
]