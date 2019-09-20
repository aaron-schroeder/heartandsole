import unittest
import datetime
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas
#from pandas.util.testing import assert_frame_equal, assert_series_equal

from heartandsole.activity import Activity
import heartandsole.spatialutils as su
import heartandsole.powerutils as pu


class TestElevFuncs(unittest.TestCase):

  # Generate some dummy data, both as lists and series.
  distances = [0.0, 100.0, 200.0, 300.0]
  elevations = [0.0, 50.0, 75.0, 75.0]
  #distances = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
  #elevations =[0.0,  5.0, 10.0, 15.0, 17.5, 20.0, 22.5, 22.5, 22.5, 22.5]
  expected_grades = [np.nan, 0.5, 0.25, 0.0]
  dist_series = pandas.Series(distances)
  elev_series = pandas.Series(elevations)
  expected_array = np.array(expected_grades)
  expected_elevs_array = np.array(elevations)

  # Integration test: calculate grade from lists, series, and a mixture.
  grade_list_smooth = su.grade_smooth(distances, elevations)
  grade_series_smooth = su.grade_smooth(dist_series, elev_series)
  grade_mixed_1_smooth = su.grade_smooth(dist_series, elevations)
  grade_mixed_2_smooth = su.grade_smooth(distances, elev_series)
  grade_list_raw = su.grade_raw(distances, elevations)
  grade_series_raw = su.grade_raw(dist_series, elev_series)
  grade_mixed_1_raw = su.grade_raw(dist_series, elevations)
  grade_mixed_2_raw = su.grade_raw(distances, elev_series)

  # Integration test: calculate smooth elevs from lists, series, and a mixture.
  elev_list_smooth = su.elevation_smooth(distances, elevations)
  elev_series_smooth = su.elevation_smooth(dist_series, elev_series)
  elev_mixed_1_smooth = su.elevation_smooth(dist_series, elevations)
  elev_mixed_2_smooth = su.elevation_smooth(distances, elev_series)

  def test_raw_grade(self):
    assert_array_equal(self.grade_list_raw,
                       self.expected_array,
                       "Raw grades are not correct.")

  def test_smooth_grade(self):
    assert_allclose(self.grade_list_smooth,
                    self.expected_array,
                    atol=0.10,
                    err_msg="Smooth grades are not sufficiently close.")

  def test_raw_grade_type(self):
    self.assertIsInstance(self.grade_list_raw,
                          np.ndarray,
                          "Raw grades are not a ndarray.")

  def test_smooth_grade_type(self):
    self.assertIsInstance(self.grade_list_smooth,
                          np.ndarray,
                          "Smooth grades are not a ndarray.")

  def test_elevation_smooth(self):
    assert_allclose(self.elev_list_smooth,
                    self.expected_elevs_array,
                    atol=10.0,
                    err_msg="Smooth elevs are not sufficiently close.")

  def test_smooth_grade_type(self):
    self.assertIsInstance(self.elev_list_smooth,
                          np.ndarray,
                          "Smooth elevs are not a ndarray.")

class TestElevation(unittest.TestCase):

  # Integration test: create an Elevation from a list of coordinates
  latlon_list = [[-105.0, 40.0], [-105.1, 40.0], [-105.1, 40.1], [-105.1, 40.2]]
  elevation = su.Elevation(latlon_list)

  def test_create(self):
    self.assertIsInstance(self.elevation,
                          su.Elevation,
                          "elevation is not an Elevation...")

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
