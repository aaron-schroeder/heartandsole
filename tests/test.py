import unittest
import datetime
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas
#from pandas.util.testing import assert_frame_equal, assert_series_equal

from heartandsole.activity import Activity
from heartandsole.filereaders import FitActivity
import heartandsole.powerutils as pu


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


class TestActivity(unittest.TestCase):

  # Integration test: create an Activity from .fit file.
  fit = FitActivity("/home/aaronsch/webapps/aarontakesawalk/trailzealot/media/uploads/2019-05-11-144658-UBERDROID6944-216-1.fit",
  #activity = Activity("activity_files/3981100861.fit",
                      remove_stopped_periods=False)
  activity = Activity(fit.data,
                      fit.elapsed_time, 
                      remove_stopped_periods=False)

  def test_create(self):
    self.assertIsInstance(self.activity,
                          Activity,
                          "activity is not an Activity...")

  def test_moving_time(self):
    print('Moving time = %0.1f mins' 
          % (self.activity.moving_time.total_seconds() / 60)) # / 60.0)
    self.assertIsInstance(self.activity.moving_time,
                          datetime.timedelta,
                          "Moving time should be a timedelta")

  def test_mean_cadence(self):
    print('Avg cadence = %0.1f spm' % self.activity.mean_cadence)
    self.assertIsInstance(self.activity.mean_cadence,
                          float,
                          "Mean cadence should be a float")

  def test_elevation(self):
    print('elevs') if self.activity.has_elevation else print('no elevs')
    self.assertIsInstance(self.activity.elevation,
                          pandas.Series,
                          "Elevation should be a Series.")

  def test_grade(self):
    self.assertIsInstance(self.activity.grade,
                          pandas.Series,
                          "Grade should be a Series.")

  def test_speed(self):
    print('speed') if self.activity.has_speed else print('no speed')
    self.assertIsInstance(self.activity.speed,
                          pandas.Series,
                          "Speed should be a Series.")

  def test_mean_power(self):
    print('Mean power = %0.1f W/kg' % self.activity.mean_power)
    self.assertIsInstance(self.activity.mean_power,
                          float,
                          "Mean power should be a float")

  def test_norm_power(self):
    print('Norm power = %0.1f W/kg' % self.activity.norm_power)
    self.assertIsInstance(self.activity.norm_power,
                          float,
                          "Normalized power should be a float")

  def test_power_intensity(self):
    print('Testing power intensity assuming 6:30 threshold speed.')
    pwr = pu.flat_run_power('6:30')
    print('This speed generates a flat-ground power of %0.1f W/kg'
          % pwr)
    print('IF = '+str(self.activity.power_intensity(pwr)))
    self.assertIsInstance(self.activity.power_intensity(pwr),
                          float,
                          "Power-based intensity should be a float")

  def test_power_training_stress(self):
    pwr = pu.flat_run_power('6:30')
    print('pTSS = ' + str(self.activity.power_training_stress(pwr)))
    self.assertIsInstance(self.activity.power_training_stress(pwr),
                          float,
                          "Power-based training stress should be a float")

  def test_mean_hr(self):
    print('Mean HR = ' + str(self.activity.mean_hr))
    self.assertIsInstance(self.activity.mean_hr,
                          float,
                          "Mean heart rate should be a float")

  def test_hr_intensity(self):
    print('HR IF = ' + str(self.activity.hr_intensity(160)))
    self.assertIsInstance(self.activity.hr_intensity(160),
                          float,
                          "HR-based intensity should be a float")

  def test_hr_training_stress(self):
    print('hrTSS = ' + str(self.activity.hr_training_stress(160)))
    self.assertIsInstance(self.activity.hr_training_stress(160),
                          float,
                          "HR-based training stress should be a float")

  def test_equiv_speed(self):
    self.assertIsInstance(self.activity.equiv_speed,
                          pandas.Series,
                          'Equivalent pace should be a pandas.Series.')

  def test_mean_speed(self):
    print('Mean speed = ' + str(self.activity.mean_speed)+' m/s')
    self.assertIsInstance(self.activity.mean_speed,
                          float,
                          'Mean speed should be a float')

  def test_mean_equiv_speed(self):
    print('Mean equiv speed = ' + str(self.activity.mean_equiv_speed)+' m/s')
    self.assertIsInstance(self.activity.mean_equiv_speed,
                          float,
                          'Mean equivalent speed should be a float')

if __name__ == '__main__':
    unittest.main()
