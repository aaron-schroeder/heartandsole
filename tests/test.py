import datetime
import math

import fitparse
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas
from pandas.util.testing import assert_frame_equal, assert_series_equal
import spatialfriend
import unittest

from heartandsole.activity import Activity
from heartandsole.filereaders import FitFileReader, TcxFileReader
import heartandsole.powerutils as pu
import heartandsole.util
import config


class TestRunPower(unittest.TestCase):

  # Generate some dummy data, both as lists and series.
  speeds_ms = [3.0, 3.0, 3.0, 3.0]
  grades = [0.1, 0.0, 0.2, 0.2]
  expected_powers = [0.0, 0.0, 0.0, 0.0] # TODO(aschroeder) calculate.
  speed_series = pandas.Series(speeds_ms)
  grade_series = pandas.Series(grades)
  expected_array = np.array(expected_powers)

  # Integration test: calc running power from lists, series, mixture.
  from_list = pu.run_power(speeds_ms, grades)
  from_series = pu.run_power(speed_series, grade_series)
  from_mixed_1 = pu.run_power(speed_series, grades)
  from_mixed_2 = pu.run_power(speeds_ms, grade_series)

  def test_c_r_float_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(pu.run_cost(self.speeds_ms[0], self.grades[0]),
                          float,
                          "Cr should be a float.")

  def test_c_r_series_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(pu.run_cost(self.speed_series, self.grade_series),
                          pandas.Series,
                          "Cr should be a Series.")

  def test_calc_power_float_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(pu.flat_run_power(self.speeds_ms[0]),
                          float,
                          "flat_run_power should return a float.")

  def test_calc_power_str_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(pu.flat_run_power('6:30'),
                          float,
                          "flat_run_power should return a float.")

  def test_power_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list,
                          np.ndarray,
                          "Power should be a ndarray.")

class TestTcxFileReader(unittest.TestCase):
  def setUp(self):
    # Integration test: create a TcxFileReader from .tcx file.
    #self.tcx = TcxFileReader('activity_files/20190425_110505_Running.tcx')
    self.tcx = TcxFileReader('activity_files/activity_3993313372.tcx')
                           # 'boulderhikes/activity_4257833732.tcx')
  
  def test_create(self):
    self.assertIsInstance(self.tcx,
                          TcxFileReader,
                          "tcx is not a TcxFileReader...")

  def test_hdr(self):
    print(self.tcx.date)
    print(self.tcx.device)
    print(self.tcx.distance)
    print(self.tcx.calories)
    print(self.tcx.lap_time_seconds)
    print(self.tcx.get_header_value('UnitId'))
    print(self.tcx.get_header_value('ProductID'))
    pass  


class TestCompareFileReaders(unittest.TestCase):

  def setUp(self):
    self.fit = FitFileReader('activity_files/4426508309.fit')
    self.tcx = TcxFileReader('activity_files/activity_4426508309.tcx')

    # Drop the elevation column from the .tcx DataFrame so we can
    # compare it to the .fit DataFrame, which has no file elevations.
    self.tcx.data.drop(columns=['elevation'], inplace=True)

  def test_dataframes_same(self):
    """Checks that dataframes are identical.

    Structure, indexes, columns, dtypes, and values.
    """
    assert_frame_equal(self.fit.data, self.tcx.data)


class TestFitFileReader(unittest.TestCase):
  # This file does not contain elevation or running dynamics data.
  fit_wahoo = FitFileReader(
      'activity_files/2019-05-11-144658-UBERDROID6944-216-1.fit')

  # This file does not contain elevation or running dynamics data.
  fit_garmin = FitFileReader('activity_files/3981100861.fit')

  def test_1(self):
    pass


class TestTcxFileReader(unittest.TestCase):
  # This file contains data for all available fields.
  tcx_full = TcxFileReader('activity_files/activity_4257833732.tcx')

  # This file contains no elevation, speed, or cadence data.
  tcx_sparse = TcxFileReader('activity_files/20190425_110505_Running.tcx')

  def test_1(self):
    pass


class TestActivityCsv(unittest.TestCase):
  act = Activity.from_csv('activity_files/4057357331.csv')
  print(act)

  def test_1(self):
    pass

class TestActivity(unittest.TestCase):

  # Create a DataFrame that is formatted correctly for consumption
  # by Activity. This DataFrame has all available fields.
  nT = 60
  v = 3.0
  data = dict(
    timestamp=[datetime.datetime(2019, 9, 1, second=i) for i in range(nT)],
    distance=[i * 3.0 for i in range(nT)],
    speed=[3.0 for i in range(nT)],
    elevation=[1.0 * i for i in range(nT)],
    lat=[40.0 + 0.0001*i for i in range(nT)],
    lon=[-105.4 - 0.0001*i for i in range(nT)],
    heart_rate=[140.0 + 5.0 * math.sin(i * math.pi/10) for i in range(nT)],
    cadence=[170.0 + 5.0 * math.cos(i * math.pi/10) for i in range(nT)],
    #running_smoothness=[170.0 + 5.0 * math.cos(i * math.pi/10) for i in range(nT)],
    #stance_time=[250.0 + 25.0 * math.cos(i * math.pi/10) for i in range(nT)],
    #vertical_oscillation=[12.5 + 2.0 * math.cos(i * math.pi/10) for i in range(nT)],
  )

  index = [[0 for i in range(nT)],
           [datetime.timedelta(seconds=i) for i in range(nT)]]

  df_single = pandas.DataFrame(data, index=index)
  df_single.index.names = ['block', 'offset']

  # Create an Activity with simulated input from a FileReader.
  act = Activity(df_single, remove_stopped_periods=False)

  # Create an Activity with simulated input from a FileReader
  # without elevation data.
  df_single_noel = df_single.drop(columns=['elevation'])
  act_noel = Activity(df_single_noel, remove_stopped_periods=False)

  # Create a MultiIndexed DataFrame to simulate data read from CSV etc.
  df_double = df_single.copy()
  index_tups = [(field_name, 'file') if field_name in Activity.ELEV_FIELDS
                else (field_name, '') for field_name in df_double.columns]
  multiindex = pandas.MultiIndex.from_tuples(index_tups,
                                             names=('field', 'elev_source'))
  df_double.columns = multiindex

  # Create an Activity with simulated input from a fully-formed 
  # DataFrame.
  act_double = Activity(df_double, remove_stopped_periods=False)

  # fit_wahoo = FitFileReader(
  #     'activity_files/2019-05-11-144658-UBERDROID6944-216-1.fit')
  # activity_wahoo = Activity(fit_wahoo.data,
  #                           remove_stopped_periods=False)
  # print(activity_wahoo.data.columns)
  # print(activity_wahoo.data)

  # Integration test: add a new elevation source to an 
  # existing activity.
  elevs = act.elevation('file').to_list()
  act.add_elevation_source(elevs, 'test_src')
  act_double.add_elevation_source(elevs, 'test_src')

  
  def test_create(self):
    assert_frame_equal(self.act.data, self.act_double.data,
                       'Activities do not match when loaded from FileReader'  \
                       ' vs. full DataFrame')

  def test_moving_time_type(self):
    self.assertIsInstance(self.act.moving_time,
                          datetime.timedelta,
                          'Moving time should be a timedelta')

  def test_moving_time(self):
    self.assertEqual(self.act.moving_time.total_seconds(),
                     59,
                     'Moving time not calculated correctly.')

  def test_mean_cadence_type(self):
    self.assertIsInstance(self.act.mean_cadence,
                          float,
                          'Mean cadence should be a float')

  def test_elevation_type(self):
    self.assertIsInstance(self.act.elevation(),
                          pandas.Series,
                          'Elevation should be a Series.')

  def test_grade_type(self):
    self.assertIsInstance(self.act.grade(),
                          pandas.Series,
                          'Grade should be a Series.')

  def test_grade_alt_type(self):
    self.assertIsInstance(self.act.grade(source_name='test_src'),
                          pandas.Series,
                          'Grade should be a Series.')

  def test_speed_type(self):
    self.assertIsInstance(self.act.speed,
                          pandas.Series,
                          'Speed should be a Series.')

  def test_power_type(self):
    self.assertIsInstance(self.act.power(),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_alt_type(self):
    self.assertIsInstance(self.act.power(source_name='test_src'),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_smooth_type(self):
    self.assertIsInstance(self.act.power_smooth(),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_smooth_alt_type(self):
    self.assertIsInstance(self.act.power_smooth(source_name='test_src'),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_mean_power_type(self):
    self.assertIsInstance(self.act.mean_power(),
                          float,
                          'Mean power should be a float')

  def test_mean_power_alt_type(self):
    self.assertIsInstance(self.act.mean_power(source_name='test_src'),
                          float,
                          'Mean power should be a float')

  def test_norm_power_type(self):
    self.assertIsInstance(self.act.norm_power(),
                          float,
                          'Normalized power should be a float')

  def test_norm_power_alt_type(self):
    self.assertIsInstance(self.act.norm_power(source_name='test_src'),
                          float,
                          'Normalized power should be a float')

  def test_power_intensity_type(self):
    pwr = pu.flat_run_power('6:30')
    self.assertIsInstance(self.act.power_intensity(pwr),
                          float,
                          'Power-based intensity should be a float')

  def test_power_intensity_alt_type(self):
    pwr = pu.flat_run_power('6:30')
    self.assertIsInstance(self.act.power_intensity(pwr,
                                                   source_name='test_src'),
                          float,
                          'Power-based intensity should be a float')

  def test_power_training_stress_type(self):
    pwr = pu.flat_run_power('6:30')
    self.assertIsInstance(self.act.power_training_stress(pwr),
                          float,
                          'Power-based training stress should be a float')

  def test_power_training_stress_alt_type(self):
    pwr = pu.flat_run_power('6:30')
    self.assertIsInstance(self.act.power_training_stress(pwr,
                                                         source_name='test_src'),
                          float,
                          'Power-based training stress should be a float')

  def test_mean_hr_type(self):
    self.assertIsInstance(self.act.mean_hr,
                          float,
                          'Mean heart rate should be a float')

  def test_hr_intensity_type(self):
    self.assertIsInstance(self.act.hr_intensity(160),
                          float,
                          'HR-based intensity should be a float')

  def test_hr_training_stress_type(self):
    self.assertIsInstance(self.act.hr_training_stress(160),
                          float,
                          'HR-based training stress should be a float')

  def test_source(self):
    self.assertTrue(self.act.has_source('file'))

  def test_equiv_speed_type(self):
    self.assertIsInstance(self.act.equiv_speed(),
                          pandas.Series,
                          'Equivalent pace should be a pandas.Series.')

  def test_equiv_speed_alt_type(self):
    self.assertIsInstance(self.act.equiv_speed(source_name='test_src'),
                          pandas.Series,
                          'Equivalent pace should be a pandas.Series.')

  def test_mean_speed_type(self):
    self.assertIsInstance(self.act.mean_speed,
                          float,
                          'Mean speed should be a float')

  def test_mean_equiv_speed_type(self):
    self.assertIsInstance(self.act.mean_equiv_speed(),
                          float,
                          'Mean equivalent speed should be a float')

  def test_mean_equiv_speed_alt_type(self):
    self.assertIsInstance(self.act.mean_equiv_speed(source_name='test_src'),
                          float,
                          'Mean equivalent speed should be a float')


class TestDuplicateTimestamp(unittest.TestCase):

  def print_diffs(self, vals):
    sum_diffs = 0
    for i in range(len(vals)-1):
      time_diff = vals[i+1] - vals[i]
      if time_diff.total_seconds() != 1:
        print('%s: %s' % (vals[i+1], time_diff.total_seconds() - 1))
        sum_diffs += time_diff.total_seconds() - 1
    print(sum_diffs)

  def setUp(self):
    # Start with a typical file with duplicated timestamps.
    reader = FitFileReader('activity_files/lexsort_4318998849.fit')
    #reader = FitFileReader('activity_files/lexsort_4318995334.fit')
    #reader = FitFileReader('activity_files/running_4390094641.fit')
    #reader = FitFileReader('activity_files/runningmo_4386919092.fit')

    #heartandsole.util.print_full(reader.data)
    #self.print_diffs(reader.data.index.get_level_values('offset'))

    activity = heartandsole.Activity(reader.data)
    #self.print_diffs(activity.data.index.get_level_values('offset'))

  def test_create(self):
    pass


if __name__ == '__main__':
  unittest.main()
