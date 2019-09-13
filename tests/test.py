import unittest
import datetime
import numpy as np
from numpy.testing import assert_array_equal
import pandas
#from pandas.util.testing import assert_frame_equal, assert_series_equal

from fitanalysis.elevation import Grade, Elevation
from fitanalysis.activity import Activity
from fitanalysis.runpower import RunPower

class TestGrade(unittest.TestCase):

  # Generate some dummy data, both as lists and series.
  distances = [0.0, 100.0, 200.0, 300.0]
  elevations = [0.0, 50.0, 75.0, 75.0]
  expected_grades = [np.nan, 0.5, 0.25, 0.0]
  dist_series = pandas.Series(distances)
  elev_series = pandas.Series(elevations)
  expected_array = np.array(expected_grades)

  # Integration test: create a Grade from lists, series, and a mixture.
  grade_list = Grade(distances, elevations)
  grade_series = Grade(dist_series, elev_series)
  grade_mixed_1 = Grade(dist_series, elevations)
  grade_mixed_2 = Grade(distances, elev_series)

  def test_raw(self):
    assert_array_equal(self.grade_list.raw,
                        self.expected_array,
                        "Raw grades are not correct.")

  def test_raw_type(self):
    self.assertIsInstance(self.grade_list.raw,
                          np.ndarray,
                          "Raw grades are not a ndarray.")

  def test_smooth_type(self):
    """Basically just an integration test of the smoothing algorithm."""
    self.assertIsInstance(self.grade_list.smooth,
                          np.ndarray,
                          "Smooth grades are not a ndarray.")

class TestElevation(unittest.TestCase):

  # Integration test: create an Elevation from a list of coordinates
  latlon_list = [[-105.0, 40.0], [-105.1, 40.0], [-105.1, 40.1], [-105.1, 40.2]]
  elevation = Elevation(latlon_list)

  def test_create(self):
    self.assertIsInstance(self.elevation,
                          Elevation,
                          "elevation is not an Elevation...")

class TestRunPower(unittest.TestCase):

  # Generate some dummy data, both as lists and series.
  speeds_ms = [3.0, 3.0, 3.0, 3.0]
  grades = [0.1, 0.0, 0.2, 0.2]
  expected_powers = [0.0, 0.0, 0.0, 0.0] # calculate independently.
  speed_series = pandas.Series(speeds_ms)
  grade_series = pandas.Series(grades)
  expected_array = np.array(expected_powers)

  # Integration test: create a RunPower from lists, series, and mixture.
  from_list = RunPower(speeds_ms, grades)
  from_series = RunPower(speed_series, grade_series)
  from_mixed_1 = RunPower(speed_series, grades)
  from_mixed_2 = RunPower(speeds_ms, grade_series)

  def test_c_r_float_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list._c_r(self.speeds_ms[0], self.grades[0]),
                          float,
                          "Cr should be a float.")

  def test_c_r_series_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list._c_r(self.speed_series, self.grade_series),
                          pandas.Series,
                          "Cr should be a Series.")

  def test_calc_power_float_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list._calc_power(self.speeds_ms[0]),
                          float,
                          "_calc_power should return a float.")

  def test_calc_power_str_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list._calc_power('6:30'),
                          float,
                          "_calc_power should return a float.")

  def test_power_type(self):
    """Integration test. Actual validation test forthcoming."""
    self.assertIsInstance(self.from_list.power,
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
