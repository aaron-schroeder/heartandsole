import datetime
import io
import math
import os
import unittest

from numpy.testing import assert_array_equal, assert_allclose
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from heartandsole import Activity


# Expected dtypes for elements in the 'summary' Series.
SUMMARY_TYPE_CHECKERS = {
  'timestamp_start': lambda x: isinstance(x, pd.Timestamp), # check awareness
  'time_elapsed': pd.api.types.is_float,
  'time_timer': pd.api.types.is_float,
  'distance_total': pd.api.types.is_float,
  'speed_avg': pd.api.types.is_float,
  'speed_max': pd.api.types.is_float,
  'elevation_gain': pd.api.types.is_integer,
  'elevation_loss': pd.api.types.is_integer,
  'heartrate_avg': pd.api.types.is_integer,
  'heartrate_max': pd.api.types.is_integer,
  'cadence_avg': pd.api.types.is_integer,
  'cadence_max': pd.api.types.is_integer,
  'calories': pd.api.types.is_integer,

  # These are found in TCX/GPX files only.
  'title': lambda x: isinstance(x, str),
  'sport': lambda x: isinstance(x, str),
  'device': lambda x: isinstance(x, str),
  'unit_id': pd.api.types.is_integer,
  'product_id': pd.api.types.is_integer,
}

# Expected dtypes for columns in the 'lap' DataFrame.
LAP_DTYPE_CHECKERS = {
  'time_timer': pd.api.types.is_float_dtype,
  'timestamp_start': pd.api.types.is_datetime64tz_dtype,
  'timestamp_end': pd.api.types.is_datetime64tz_dtype,
  'distance_total': pd.api.types.is_float_dtype,
  'speed_max': pd.api.types.is_float_dtype,
  'speed_avg': pd.api.types.is_float_dtype,
  'cadence_avg': pd.api.types.is_integer_dtype,
  'cadence_max': pd.api.types.is_integer_dtype,
  'heartrate_avg': pd.api.types.is_integer_dtype,
  'heartrate_max': pd.api.types.is_integer_dtype,
  'trigger_method': pd.api.types.is_string_dtype,
  'calories': pd.api.types.is_integer_dtype,

  # TCX only
  'intensity': pd.api.types.is_string_dtype,
}

# Expected dtypes for columns in the 'records' DataFrame.
RECORD_DTYPE_CHECKERS = {
  # Few dtypes for datetime cols in pandas
  # 'timestamp': pd.api.types.is_datetime64_any_dtype,
  # 'timestamp': pd.api.types.is_datetime64_ns_dtype,
  # 'timestamp': pd.api.types.is_datetime64_dtype,
  'timestamp': pd.api.types.is_datetime64tz_dtype,
  'time': pd.api.types.is_integer_dtype,
  'lat': pd.api.types.is_float_dtype,
  'lon': pd.api.types.is_float_dtype,
  'elevation': pd.api.types.is_float_dtype,
  'cadence': pd.api.types.is_integer_dtype,
  'heartrate': pd.api.types.is_integer_dtype,
  'speed': pd.api.types.is_float_dtype,
  'distance': pd.api.types.is_float_dtype,
}


class FileReaderTestMixin(object):
  
  def setUp(self):
    # self.rdr = self.READER_CLASS(self.TESTDATA_FILENAME)
    self.act = self.READER(self.TESTDATA_FILENAME)

  def assertHasAttr(self, obj, attr_name):
    self.assertTrue(
      hasattr(obj, attr_name),
      msg=f'{obj} does not have attr {attr_name}'
    )

  def test_summary(self):
    self.assertHasAttr(self.act, 'summary')
    for row_name in self.EXPECTED_SUMMARY_ROWS:
      self.assertIn(row_name, self.act.summary.index)
      self.assertTrue(
        SUMMARY_TYPE_CHECKERS[row_name](self.act.summary[row_name]),
        msg=f'{row_name}: {type(self.act.summary[row_name])}'
      )

  def test_laps(self):
    self.assertHasAttr(self.act, 'laps')
    for col_name in self.EXPECTED_LAP_COLS:
      self.assertIn(col_name, self.act.laps.columns)
      self.assertTrue(
        LAP_DTYPE_CHECKERS[col_name](self.act.laps[col_name]),
        msg=f'{col_name}: {self.act.laps[col_name].dtype}'
      )

  def test_records(self):
    self.assertHasAttr(self.act, 'records')
    for col_name in self.EXPECTED_RECORD_COLS:
      self.assertIn(col_name, self.act.records.columns)
      self.assertTrue(
        RECORD_DTYPE_CHECKERS[col_name](self.act.records[col_name]),
        msg=f'{col_name}: {self.act.records[col_name].dtype}'
      )


class TestGpx(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testdata.gpx')
  READER = Activity.from_gpx
  EXPECTED_SUMMARY_ROWS = ['timestamp_start', 'title', 'sport']
  EXPECTED_LAP_COLS = []
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'cadence', 'heartrate']


class TestGpxCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testcourse.gpx')
  READER = Activity.from_gpx
  EXPECTED_SUMMARY_ROWS = ['title']
  EXPECTED_LAP_COLS = []
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation']


class TestTcx(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testdata.tcx')
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


class TestTcxCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testcourse.tcx')
  READER = Activity.from_tcx
  EXPECTED_SUMMARY_ROWS = []
  EXPECTED_LAP_COLS = ['time_timer', 'distance_total']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation',
    'distance']


class TestFit(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testdata.fit')
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


class TestFitCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testcourse.fit')
  READER = Activity.from_fit
  EXPECTED_SUMMARY_ROWS = []
  EXPECTED_LAP_COLS = ['timestamp_start', 'timestamp_end']
  EXPECTED_RECORD_COLS = ['timestamp', 'time', 'lat', 'lon', 'elevation', 'distance']


class TestCompare(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.fit = Activity.from_fit(TestFit.TESTDATA_FILENAME)
    cls.tcx = Activity.from_tcx(TestTcx.TESTDATA_FILENAME)
    cls.gpx = Activity.from_gpx(TestGpx.TESTDATA_FILENAME)

    # Drop the elevation column from the .tcx DataFrame so we can
    # compare it to the .fit DataFrame, which has no file elevations.
    # cls.tcx.data.drop(columns=['elevation'], inplace=True)

  def test_records(self):
    """Checks that dataframes are identical.

    Structure, indexes, columns, dtypes, and values.
    """
    # print(self.fit.records)
    # print(self.tcx.records)

    # NOT elevation - garmin corrects it in tcx files
    expected_identical_fields = ['timestamp', 'lat', 'lon', 'distance', 
      'heartrate', 'speed', 'cadence', 'time']
    assert_frame_equal(
      self.fit.records[expected_identical_fields],
      self.tcx.records_unique[expected_identical_fields],
      check_like=True,   # ignore row/col order
      check_dtype=False, # checked in individual TestCases
    )

  def test_summary(self):
    self.assertEqual(
      self.fit.summary['sport'].lower(),
      self.tcx.summary['sport'].lower()
    )
    self.assertEqual(
      self.gpx.summary['sport'].lower(),
      self.tcx.summary['sport'].lower()
    )

  def test_laps(self):
    """Checks that dataframes are identical.

    Structure, indexes, columns, dtypes, and values.
    """
    # print(self.fit.laps)
    # print(self.tcx.laps)

    # NOT elevation - garmin corrects it in tcx files
    expected_identical_fields = ['timestamp_start', 'time_timer', 
      'distance_total', 'speed_max', 'speed_avg', 'calories', 'heartrate_avg',
      'heartrate_max', 'cadence_avg', 'cadence_max']
    assert_frame_equal(
      self.fit.laps[expected_identical_fields],
      self.tcx.laps[expected_identical_fields],
      check_dtype=False, # checked in individual TestCases
    )


@unittest.skip('Need to create a test CSV file.')
class TestCsv(unittest.TestCase):

  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testdata.csv')

  @classmethod
  def setUpClass(cls):
    cls.act = Activity.from_csv(cls.TESTDATA_FILENAME)

  def test_1(self):
    pass