import unittest
import datetime
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas
#from pandas.util.testing import assert_frame_equal, assert_series_equal

from heartandsole.activity import Activity
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
  activity = Activity("activity_files/3981100861.fit",
                      remove_stopped_periods=False)

  def test_create(self):
    self.assertIsInstance(self.activity,
                          Activity,
                          "activity is not an Activity...")

  def test_moving_time(self):
    self.assertIsInstance(self.activity.moving_time,
                          datetime.timedelta,
                          "Moving time should be a timedelta")

  def test_mean_cadence(self):
    self.assertIsInstance(self.activity.mean_cadence,
                          float,
                          "Mean cadence should be a float")

  def test_mean_heart_rate(self):
    self.assertIsInstance(self.activity.mean_heart_rate,
                          float,
                          "Mean heart rate should be a float")

  def test_mean_power(self):
    self.assertIsInstance(self.activity.mean_power,
                          float,
                          "Mean power should be a float")

  def test_norm_power(self):
    self.assertIsInstance(self.activity.norm_power,
                          float,
                          "Normalized power should be a float")

  def test_intensity(self):
    self.assertIsInstance(self.activity.intensity(16.25),
                          float,
                          "Intensity should be a float")

  def test_training_stress(self):
    self.assertIsInstance(self.activity.training_stress(16.25),
                          float,
                          "Intensity should be a float")

if __name__ == '__main__':
    unittest.main()
