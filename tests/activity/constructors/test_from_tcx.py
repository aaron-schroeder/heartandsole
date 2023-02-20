import unittest

from heartandsole import Activity
from tests.common import datapath
from tests.activity.constructors.common import FileReaderTestMixin


class TestActivity(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'tcx', 'activity.tcx')
  READER = Activity.from_tcx
  EXPECTED_SUMMARY_ROWS = ['sport', 'device', 'unit_id', 'product_id']
  EXPECTED_LAP_COLS = ['time_timer', 'timestamp_start', 'distance_total', 
    'speed_max', 'speed_avg', 'calories', 'cadence_avg', 'cadence_max', 
    'heartrate_avg', 'heartrate_max', 'intensity', 'trigger_method']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'cadence', 'heartrate', 'speed', 'distance']

  # @classmethod
  # def setUpClass(cls):
  #   # This file contains data for all available fields.
  #   cls.tcx_full = TcxFileReader('activity_files/activity_4257833732.tcx')

  #   # This file contains no elevation, speed, or cadence data.
  #   cls.tcx_sparse = TcxFileReader('activity_files/20190425_110505_Running.tcx')


class TestCourses(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'tcx', 'course.tcx')
  READER = Activity.from_tcx
  EXPECTED_SUMMARY_ROWS = []
  EXPECTED_LAP_COLS = ['time_timer', 'distance_total']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'distance']
