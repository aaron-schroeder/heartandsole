import unittest

# from numpy.testing import assert_array_equal, assert_allclose
from pandas.testing import assert_frame_equal  # , assert_series_equal

from heartandsole import Activity
from tests.common import datapath


class TestCompareActivity(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.fit = Activity.from_fit(datapath('io', 'data', 'fit', 'activity.fit'))
    cls.tcx = Activity.from_tcx(datapath('io', 'data', 'tcx', 'activity.tcx'))
    cls.gpx = Activity.from_gpx(datapath('io', 'data', 'gpx', 'trk.gpx'))

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
