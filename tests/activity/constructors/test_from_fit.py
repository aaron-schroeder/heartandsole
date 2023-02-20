import os
import unittest

from heartandsole import Activity
from tests.common import datapath
from tests.activity.constructors.common import FileReaderTestMixin


class TestActivity(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'fit', 'activity.fit')
  READER = Activity.from_fit
  EXPECTED_SUMMARY_ROWS = ['timestamp_start', 'time_elapsed', 'time_timer',
    'distance_total', 'calories', 'speed_avg', 'speed_max', 'elevation_gain',
    'elevation_loss', 'heartrate_avg', 'heartrate_max', 'cadence_avg',
    'cadence_max', 'sport']
  EXPECTED_LAP_COLS = ['timestamp_start', 'distance_total', 'speed_max',
    'speed_avg', 'calories', 'cadence_avg', 'cadence_max', 'heartrate_avg', 
    'trigger_method']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'cadence', 'heartrate']

  # @classmethod
  # def setUpClass(cls):
  #   # This file does not contain elevation or running dynamics data.
  #   cls.fit_wahoo = FitFileReader(
  #       'activity_files/2019-05-11-144658-UBERDROID6944-216-1.fit')

  #   # This file does not contain elevation or running dynamics data.
  #   cls.fit_garmin = FitFileReader('activity_files/3981100861.fit')


class TestCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'fit', 'course.fit')
  READER = Activity.from_fit
  EXPECTED_SUMMARY_ROWS = []
  EXPECTED_LAP_COLS = ['timestamp_start', 'timestamp_end']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation', 'distance']