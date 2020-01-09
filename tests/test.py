import datetime

import fitparse
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas
#from pandas.util.testing import assert_frame_equal, assert_series_equal
import spatialfriend
import unittest

from heartandsole.activity import Activity
from heartandsole.filereaders import FitFileReader, TcxFileReader
import heartandsole.powerutils as pu
import heartandsole.util
#from heartandsole import config
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
  # Integration test: create a TcxFileReader from .tcx file.
  tcx = TcxFileReader('activity_files/20190425_110505_Running.tcx')#boulderhikes/activity_4257833732.tcx')

  def test_create(self):
    self.assertIsInstance(self.tcx,
                          TcxFileReader,
                          "tcx is not a TcxFileReader...")
  

class TestActivity(unittest.TestCase):

  # Integration test: create an Activity from a Wahoo fitness .fit file.
  # This file contains elevation data.
  fit_wahoo = FitFileReader(
      'activity_files/2019-05-11-144658-UBERDROID6944-216-1.fit')
  activity_wahoo = Activity(fit_wahoo.data,
                            remove_stopped_periods=False)

  # Integration test: create an Activity from a Garmin .fit file.
  # This file does not contain elevation or running dynamics data.
  fit_garmin = FitFileReader('activity_files/3981100861.fit')
  activity_garmin = Activity(fit_garmin.data,
                             remove_stopped_periods=False)

  # Integration test: create an Activity from a .tcx file that contains
  # data for all available fields.
  tcx_full = TcxFileReader('activity_files/activity_4257833732.tcx')
  activity_full = Activity(tcx_full.data,
                           remove_stopped_periods=False)

  # Integration test: create an Activity from a .tcx file with missing
  # fields. This file has no elevation, speed, or cadence data.
  tcx_sparse = TcxFileReader('activity_files/20190425_110505_Running.tcx')
  activity_sparse = Activity(tcx_sparse.data,
                             remove_stopped_periods=False)

  # Integration test: add a new elevation source to an 
  # existing activity.
  el_friend = spatialfriend.Elevation(activity_full.lonlats,
                                      user_gmaps_key=config.my_gmaps_key)
  elevs_google = el_friend.google(units='meters')
  activity_full.add_elevation_source(elevs_google, 'google')

  def test_create(self):
    self.assertIsInstance(self.activity_full,
                          Activity,
                          "activity is not an Activity...")

  def test_moving_time(self):
    print('Moving time = %0.1f mins' 
          % (self.activity_full.moving_time.total_seconds() / 60)) 
    self.assertIsInstance(self.activity_full.moving_time,
                          datetime.timedelta,
                          "Moving time should be a timedelta")

  def test_mean_cadence(self):
    print('Avg cadence = %0.1f spm' % self.activity_full.mean_cadence)
    self.assertIsInstance(self.activity_full.mean_cadence,
                          float,
                          "Mean cadence should be a float")

  def test_elevation(self):
    print('elevs') if self.activity_full.has_elevation else print('no elevs')
    self.assertIsInstance(self.activity_full.elevation(),
                          pandas.Series,
                          "Elevation should be a Series.")

  def test_grade(self):
    self.assertIsInstance(self.activity_full.grade(),
                          pandas.Series,
                          "Grade should be a Series.")

  def test_grade_alt(self):
    self.assertIsInstance(self.activity_full.grade(source_name='google'),
                          pandas.Series,
                          "Grade should be a Series.")

  def test_speed(self):
    print('speed') if self.activity_full.has_speed else print('no speed')
    self.assertIsInstance(self.activity_full.speed,
                          pandas.Series,
                          "Speed should be a Series.")

  def test_power(self):
    self.assertIsInstance(self.activity_full.power(),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_alt(self):
    self.assertIsInstance(self.activity_full.power(source_name='google'),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_smooth(self):
    self.assertIsInstance(self.activity_full.power_smooth(),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_power_smooth_alt(self):
    self.assertIsInstance(self.activity_full.power_smooth(source_name='google'),
                          pandas.Series,
                          'Power should be a pandas.Series.')

  def test_mean_power(self):
    print('Mean power = %0.1f W/kg' % self.activity_full.mean_power())
    self.assertIsInstance(self.activity_full.mean_power(),
                          float,
                          "Mean power should be a float")

  def test_mean_power_alt(self):
    print('Mean google power = %0.1f W/kg'
          % self.activity_full.mean_power(source_name='google'))
    self.assertIsInstance(self.activity_full.mean_power(source_name='google'),
                          float,
                          "Mean power should be a float")

  def test_norm_power(self):
    print('Norm power = %0.1f W/kg' % self.activity_full.norm_power())
    self.assertIsInstance(self.activity_full.norm_power(),
                          float,
                          "Normalized power should be a float")

  def test_norm_power_alt(self):
    print('Norm google power = %0.1f W/kg'
          % self.activity_full.norm_power(source_name='google'))
    self.assertIsInstance(self.activity_full.norm_power(source_name='google'),
                          float,
                          "Normalized power should be a float")

  def test_power_intensity(self):
    print('Testing power intensity assuming 6:30 threshold speed.')
    pwr = pu.flat_run_power('6:30')
    print('This speed generates a flat-ground power of %0.1f W/kg'
          % pwr)
    print('File IF = %0.3f'
          % self.activity_full.power_intensity(pwr))
    self.assertIsInstance(self.activity_full.power_intensity(pwr),
                          float,
                          "Power-based intensity should be a float")

  def test_power_intensity_alt(self):
    pwr = pu.flat_run_power('6:30')
    print('Google IF = %0.3f'
          % self.activity_full.power_intensity(pwr, source_name='google'))
    self.assertIsInstance(self.activity_full.power_intensity(
                              pwr,
                              source_name='google'),
                          float,
                          "Power-based intensity should be a float")

  def test_power_training_stress(self):
    pwr = pu.flat_run_power('6:30')
    print('pTSS = %0.0f' % self.activity_full.power_training_stress(pwr))
    self.assertIsInstance(self.activity_full.power_training_stress(pwr),
                          float,
                          "Power-based training stress should be a float")

  def test_power_training_stress_alt(self):
    pwr = pu.flat_run_power('6:30')
    print('Google pTSS = %0.0f'
          % self.activity_full.power_training_stress(pwr, source_name='google'))
    self.assertIsInstance(self.activity_full.power_training_stress(pwr),
                          float,
                          "Power-based training stress should be a float")

  def test_mean_hr(self):
    print('Mean HR = ' + str(self.activity_full.mean_hr))
    self.assertIsInstance(self.activity_full.mean_hr,
                          float,
                          "Mean heart rate should be a float")

  def test_hr_intensity(self):
    print('HR IF = ' + str(self.activity_full.hr_intensity(160)))
    self.assertIsInstance(self.activity_full.hr_intensity(160),
                          float,
                          "HR-based intensity should be a float")

  def test_hr_training_stress(self):
    print('hrTSS = ' + str(self.activity_full.hr_training_stress(160)))
    self.assertIsInstance(self.activity_full.hr_training_stress(160),
                          float,
                          "HR-based training stress should be a float")

  def test_source(self):
    self.assertTrue(self.activity_full.has_source('file'))

  def test_equiv_speed(self):
    self.assertIsInstance(self.activity_full.equiv_speed(),
                          pandas.Series,
                          'Equivalent pace should be a pandas.Series.')

  def test_equiv_speed_alt(self):
    self.assertIsInstance(self.activity_full.equiv_speed(source_name='google'),
                          pandas.Series,
                          'Equivalent pace should be a pandas.Series.')

  def test_mean_speed(self):
    print('Mean speed = ' + str(self.activity_full.mean_speed)+' m/s')
    self.assertIsInstance(self.activity_full.mean_speed,
                          float,
                          'Mean speed should be a float')

  def test_mean_equiv_speed(self):
    print('Mean equiv speed = %0.2f m/s'
          % self.activity_full.mean_equiv_speed())
    self.assertIsInstance(self.activity_full.mean_equiv_speed(),
                          float,
                          'Mean equivalent speed should be a float')

  def test_mean_equiv_speed_alt(self):
    print('Mean google equiv speed = %0.2f m/s'
          % self.activity_full.mean_equiv_speed(source_name='google'))
    self.assertIsInstance(
        self.activity_full.mean_equiv_speed(source_name='google'),
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
