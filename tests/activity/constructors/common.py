import os

import pandas as pd


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
