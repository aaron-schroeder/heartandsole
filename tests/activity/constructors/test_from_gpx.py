import unittest

from heartandsole import Activity
from tests.common import datapath
from tests.activity.constructors.common import FileReaderTestMixin


class TestTrk(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'gpx', 'trk.gpx')
  READER = Activity.from_gpx
  EXPECTED_SUMMARY_ROWS = ['timestamp_start', 'title', 'sport']
  EXPECTED_LAP_COLS = []
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'cadence', 'heartrate']


class TestRte(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'gpx', 'rte.gpx')
  READER = Activity.from_gpx
  EXPECTED_SUMMARY_ROWS = ['title']
  EXPECTED_LAP_COLS = []
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation']