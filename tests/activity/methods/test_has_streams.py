import unittest

import pandas as pd

from heartandsole import Activity


expected_fields = ['timestamp', 'distance', 'speed', 'elevation', 'lat', 
  'lon', 'heartrate', 'cadence']


class TestHasStreams(unittest.TestCase):
  
  def test_convenience_methods(self):
    dummy_data = list(range(10))
    act = Activity(pd.DataFrame({
      key: dummy_data
      for key in expected_fields
    }))

    for fld in expected_fields:
      # self.assertIn(f'has_{fld}', dir(self.act))
      # self.assertTrue(getattr(self.act, f'has_{fld}'))
      self.assertTrue(act.has_streams(fld))

    self.assertTrue(act.has_position)

    self.assertFalse(act.has_streams('power'))