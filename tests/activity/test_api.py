import unittest

import pandas as pd

from heartandsole import Activity


class TestProperties(unittest.TestCase):
  
  def test_unique_records(self):
    act = Activity(pd.DataFrame.from_dict(dict(
      distance=[i % 50 for i in range(100)]
    )))
    self.assertEqual(len(act.records), 100)
    self.assertEqual(len(act.records_unique), 50)

  def test_lonlats(self):
    pass

  def test_latlons(self):
    pass